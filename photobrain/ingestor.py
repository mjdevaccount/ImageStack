# photobrain/ingestor.py

from __future__ import annotations

import hashlib
import mimetypes
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import httpx
from loguru import logger

from .settings import settings
from .index_store import IndexStore, FileRecord


def _iter_candidate_files(root_dirs: Iterable[Path], include_exts: set[str]) -> Iterable[Path]:
    for root in root_dirs:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # Skip some typical junk dirs
            dirpath_path = Path(dirpath)
            if any(skip in dirpath_path.parts for skip in (".git", "__pycache__", "node_modules", ".venv", "env")):
                continue

            for name in filenames:
                ext = Path(name).suffix.lower()
                if ext not in include_exts:
                    continue
                yield Path(dirpath) / name


def _hash_file(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _now_utc_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def ingest_file_to_imagestack(path: Path) -> dict:
    """
    Sends the file to ImageStack's PhotoBrain image-ingest endpoint.

    Assumes an API like:

        POST {base_url}/photobrain/ingest
        form-data: file=@...

    Returns: parsed JSON response (dict)
    """
    url = f"{settings.base_url.rstrip('/')}/photobrain/ingest"
    mime, _ = mimetypes.guess_type(str(path))
    if not mime or not mime.startswith("image/"):
        # Fallback, the server will still try to decode
        mime = "image/jpeg"

    with path.open("rb") as f, httpx.Client(timeout=300.0) as client:
        files = {"file": (path.name, f, mime)}
        logger.info(f"[PhotoBrain] Ingesting {path} → {url}")
        resp = client.post(url, files=files)
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"[PhotoBrain] Ingested {path.name} → {data}")
        return data


def scan_once(store: IndexStore) -> int:
    """
    Run a single scan over all watched directories.

    Returns: number of files ingested this run.
    """
    logger.info("[PhotoBrain] Scan started")

    ingested_count = 0
    for path in _iter_candidate_files(settings.watch_dirs, settings.include_extensions):
        try:
            stat = path.stat()
        except FileNotFoundError:
            continue

        mtime = stat.st_mtime
        rec = store.get(str(path))

        # Fast path: known file with same mtime → skip
        if rec and rec.mtime == mtime:
            continue

        # New or modified file → compute hash
        file_hash = _hash_file(path)

        # If existing record with same hash & mtime, skip
        if rec and rec.hash == file_hash and rec.mtime == mtime:
            continue

        # Otherwise ingest
        try:
            data = ingest_file_to_imagestack(path)
        except Exception as ex:
            logger.error(f"[PhotoBrain] Failed ingest for {path}: {ex}")
            continue

        store.upsert(
            FileRecord(
                path=str(path),
                mtime=mtime,
                hash=file_hash,
                last_ingested_utc=_now_utc_ts(),
            )
        )
        ingested_count += 1

    logger.info(f"[PhotoBrain] Scan completed, ingested={ingested_count}")
    return ingested_count


def run_daemon() -> None:
    """
    Main loop: periodically scan and ingest new images.
    """
    logger.info("[PhotoBrain] Daemon starting up")
    logger.info(f"[PhotoBrain] Base URL: {settings.base_url}")
    logger.info(f"[PhotoBrain] Watch dirs: {', '.join(str(d) for d in settings.watch_dirs)}")
    logger.info(f"[PhotoBrain] Poll interval: {settings.poll_interval_seconds}s")

    store = IndexStore(settings.index_db_path)

    try:
        while True:
            try:
                scan_once(store)
            except Exception as ex:
                logger.error(f"[PhotoBrain] Scan failed: {ex}")
            time.sleep(settings.poll_interval_seconds)
    except KeyboardInterrupt:
        logger.info("[PhotoBrain] Shutting down via KeyboardInterrupt")
    finally:
        store.close()


def main(argv: list[str] | None = None) -> int:
    """
    CLI entrypoint.

    Usage:
        python -m photobrain.ingestor run        # run daemon
        python -m photobrain.ingestor once       # single scan
    """
    import argparse

    parser = argparse.ArgumentParser(prog="photobrain", description="PhotoBrain - ImageStack Ingestor")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("run", help="Run continuous watch/ingest loop")
    sub.add_parser("once", help="Run a single scan and exit")

    args = parser.parse_args(argv)

    store = IndexStore(settings.index_db_path)

    if args.command == "run":
        store.close()  # will be reopened in run_daemon
        run_daemon()
        return 0
    elif args.command == "once":
        try:
            scan_once(store)
        finally:
            store.close()
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

