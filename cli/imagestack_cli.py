import argparse
import base64
import os
from pathlib import Path
import httpx

API_BASE = "http://localhost:8090"

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

def ocr_image(path: str):
    path = str(Path(path).resolve())
    if not os.path.exists(path):
        print(f"[error] file not found: {path}")
        return 1
    
    with open(path, "rb") as f:
        files = {"file": (os.path.basename(path), f, "image/jpeg")}
        resp = httpx.post(f"{API_BASE}/ocr/text", files=files, timeout=300.0)
        resp.raise_for_status()
        data = resp.json()
    
    print("=== OCR TEXT ===")
    print(data.get("text", ""))
    print()
    print(f"(lang: {data.get('language')}, conf: {data.get('confidence')})")
    return 0

def main():
    parser = argparse.ArgumentParser(prog="imagestack", description="ImageStack CLI")
    sub = parser.add_subparsers(dest="command")
    
    p_desc = sub.add_parser("describe", help="Describe an image")
    p_desc.add_argument("path", help="Path to image file")
    
    p_ocr = sub.add_parser("ocr", help="OCR an image")
    p_ocr.add_argument("path", help="Path to image file")
    
    args = parser.parse_args()
    
    if args.command == "describe":
        return describe_image(args.path)
    elif args.command == "ocr":
        return ocr_image(args.path)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    raise SystemExit(main())

