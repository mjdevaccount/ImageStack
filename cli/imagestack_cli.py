# cli/imagestack_cli.py

import argparse
import os
from pathlib import Path
import datetime as dt

import httpx


API_BASE = "http://localhost:8090"


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _print_matches(matches):
    if not matches:
        print("[no results]")
        return

    for m in matches:
        print(f"\n--- Match (score {m.get('score'):.4f}) ---")
        print(f"ID: {m.get('id')}")
        print(f"File: {m.get('filename')}")
        print(f"Raw Path: {m.get('path_raw')}")
        if m.get("ocr_text"):
            print("OCR:")
            print(m["ocr_text"])
        if m.get("metadata", {}).get("exif"):
            ex = m["metadata"]["exif"]
            dt_orig = ex.get("datetime_original")
            dev = ex.get("device_model") or ex.get("Model")
            if dt_orig:
                print(f"Captured: {dt_orig}")
            if dev:
                print(f"Device: {dev}")


# ---------------------------------------------------------
# New sugar commands
# ---------------------------------------------------------

def photobrain_find(query: str, days: int | None = None, tag: str | None = None):
    payload = {"query": query, "top_k": 12}

    print(f"[find] Searching PhotoBrain: {query!r}")
    resp = httpx.post(
        f"{API_BASE}/photobrain/search/text",
        json=payload,
        timeout=120.0,
    )
    resp.raise_for_status()
    data = resp.json()

    matches = data.get("matches", [])

    # optional client-side filters
    if days is not None:
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
        def _within_days(m):
            ts = m.get("ingested_at")
            try:
                if ts:
                    d = dt.datetime.fromisoformat(ts)
                    return d >= cutoff
            except Exception:
                pass
            return False

        matches = [m for m in matches if _within_days(m)]

    if tag is not None:
        tag = tag.lower().strip()
        def _has_tag(m):
            meta = m.get("metadata", {})
            tags = meta.get("tags") or []
            return any(tag in t.lower() for t in tags)

        matches = [m for m in matches if _has_tag(m)]

    _print_matches(matches)
    return 0


def photobrain_ask(question: str, top_k: int = 8):
    payload = {"question": question, "top_k": top_k}

    print(f"[ask] Asking PhotoBrain: {question!r}")
    resp = httpx.post(
        f"{API_BASE}/photobrain/query",
        json=payload,
        timeout=240.0,
    )
    resp.raise_for_status()
    data = resp.json()

    print("\n=== ANSWER ===")
    print(data.get("answer", ""))
    print()

    print("=== MATCHES ===")
    _print_matches(data.get("matches", []))
    print()

    return 0


# ---------------------------------------------------------
# Existing commands preserved
# ---------------------------------------------------------

def describe_image(path: str):
    path = str(Path(path).resolve())
    if not os.path.exists(path):
        print(f"[error] file not found: {path}")
        return 1

    with open(path, "rb") as f:
        files = {"file": (os.path.basename(path), f, "image/jpeg")}

        resp = httpx.post(f"{API_BASE}/vision/describe", files=files, timeout=300.0)
        resp.raise_for_status()
        data = resp.json()

    print("=== DESCRIPTION ===")
    print(data.get("description", ""))
    print()
    print("=== TAGS ===")
    print(", ".join(data.get("tags", [])))
    print()
    print(f"(model: {data.get('model')})")
    return 0


def ocr_image(path: str, preprocess: bool = False):
    path = str(Path(path).resolve())
    if not os.path.exists(path):
        print(f"[error] file not found: {path}")
        return 1

    with open(path, "rb") as f:
        files = {"file": (os.path.basename(path), f, "image/jpeg")}
        params = {"preprocess": "true"} if preprocess else {}

        resp = httpx.post(
            f"{API_BASE}/ocr/text",
            params=params,
            files=files,
            timeout=300.0,
        )
        resp.raise_for_status()
        data = resp.json()

    print("=== OCR TEXT ===")
    print(data.get("text", ""))
    print()
    print(f"(lang: {data.get('language')}, conf: {data.get('confidence')})")
    return 0


# ---------------------------------------------------------
# Watcher command
# ---------------------------------------------------------

def run_watcher():
    """
    Run the PhotoBrain background watcher (real-time ingestion).
    """
    print("[watch] Starting PhotoBrain watcher (Ctrl+C to stop)...")
    print("[watch] Drop images into watched folders for instant ingestion with auto-tagging")
    print()
    
    try:
        from python_server.services.photobrain_watcher import main as watcher_main
        watcher_main()
    except KeyboardInterrupt:
        print("\n[watch] Stopped")
        return 0
    except Exception as ex:
        print(f"[error] Watcher failed: {ex}")
        return 1
    
    return 0


# ---------------------------------------------------------
# Main CLI parser
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(prog="imagestack", description="ImageStack / PhotoBrain CLI")
    sub = parser.add_subparsers(dest="command")

    # describe
    p_desc = sub.add_parser("describe", help="Describe an image with vision AI")
    p_desc.add_argument("path", help="Path to image file")

    # ocr
    p_ocr = sub.add_parser("ocr", help="Extract text from image (OCR)")
    p_ocr.add_argument("path", help="Path to image file")
    p_ocr.add_argument("--preprocess", action="store_true", help="Apply OCR preprocessing")

    # find (text search)
    p_find = sub.add_parser("find", help="Semantic search over your image memory")
    p_find.add_argument("query", help="Search text (e.g., 'beach sunset' or 'receipt Home Depot')")
    p_find.add_argument("--days", type=int, help="Limit to images from last N days")
    p_find.add_argument("--tag", type=str, help="Filter by tag (client-side)")

    # ask (LLM QA over PhotoBrain)
    p_ask = sub.add_parser("ask", help="Ask questions about your stored images")
    p_ask.add_argument("question", help="Natural language question (e.g., 'What is my generator serial number?')")
    p_ask.add_argument("--top-k", type=int, default=8, help="Number of images to consider")

    # watch (background watcher)
    p_watch = sub.add_parser("watch", help="Run PhotoBrain background watcher (real-time auto-ingestion)")

    args = parser.parse_args()

    if args.command == "describe":
        return describe_image(args.path)
    elif args.command == "ocr":
        return ocr_image(args.path, preprocess=getattr(args, "preprocess", False))
    elif args.command == "find":
        return photobrain_find(args.query, days=args.days, tag=args.tag)
    elif args.command == "ask":
        return photobrain_ask(args.question, top_k=args.top_k)
    elif args.command == "watch":
        return run_watcher()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
