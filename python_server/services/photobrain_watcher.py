# python_server/services/photobrain_watcher.py

from __future__ import annotations

import hashlib
import mimetypes
import os
import time
from pathlib import Path
from typing import Set

import httpx
from loguru import logger
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileMovedEvent
from watchdog.observers import Observer

from ..config.watcher_config import WatcherSettings, load_watcher_settings


def _guess_mime(path: Path) -> str:
    mt, _ = mimetypes.guess_type(str(path))
    if mt is None:
        return "image/jpeg"
    return mt


def _hash_file(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _ensure_subdir(base: Path, name: str) -> Path:
    d = base / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def _wait_for_stable(path: Path, timeout: float = 30.0, interval: float = 0.5) -> bool:
    """
    Wait until file size stops changing (to avoid ingesting during write).
    Returns True if stable, False if timeout.
    """
    end = time.time() + timeout
    try:
        last_size = path.stat().st_size
    except FileNotFoundError:
        return False

    while time.time() < end:
        time.sleep(interval)
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            return False
        if size == last_size:
            return True
        last_size = size

    return False


class _IngestHandler(FileSystemEventHandler):
    def __init__(self, settings: WatcherSettings):
        super().__init__()
        self.settings = settings
        self._seen_hashes: Set[str] = set()

    def on_created(self, event):
        if isinstance(event, FileCreatedEvent) and not event.is_directory:
            self._handle_path(Path(event.src_path))

    def on_moved(self, event):
        if isinstance(event, FileMovedEvent) and not event.is_directory:
            self._handle_path(Path(event.dest_path))

    def _handle_path(self, path: Path):
        # Ignore temp/hidden/system-ish files
        if path.name.startswith("~") or path.name.startswith("."):
            return

        if not path.suffix.lower() in self.settings.image_extensions:
            return

        logger.info(f"[Watcher] Detected new file: {path}")

        # Wait until file is stable
        if not _wait_for_stable(path):
            logger.warning(f"[Watcher] File not stable or disappeared: {path}")
            return

        try:
            digest = _hash_file(path)
        except Exception as ex:
            logger.error(f"[Watcher] Failed hashing {path}: {ex}")
            return

        if digest in self._seen_hashes:
            logger.info(f"[Watcher] Duplicate hash, skipping: {path}")
            return

        self._seen_hashes.add(digest)
        self._ingest_file(path, digest)

    def _ingest_file(self, path: Path, digest: str):
        base_dir = path.parent
        processed_dir = _ensure_subdir(base_dir, self.settings.processed_subdir)
        failed_dir = _ensure_subdir(base_dir, self.settings.failed_subdir)

        logger.info(f"[Watcher] Ingesting {path} (hash={digest[:8]}...)")

        mime = _guess_mime(path)
        params = {
            "ocr": "true",
            "vision": "false",
            "preprocess": "true",
            "embed": "true",
            "auto_tag": "true",
        }

        try:
            with path.open("rb") as f:
                files = {"file": (path.name, f, mime)}

                with httpx.Client(base_url=self.settings.api_base, timeout=300.0) as client:
                    resp = client.post("/photobrain/ingest", params=params, files=files)
                    resp.raise_for_status()
                    data = resp.json()

            logger.info(
                f"[Watcher] Ingest OK: {path.name} "
                f"→ id={data.get('id')}, category={data.get('metadata', {}).get('category')}"
            )

            dest = processed_dir / path.name
            try:
                path.rename(dest)
            except Exception as ex_move:
                logger.warning(f"[Watcher] Failed to move to processed: {ex_move}")

        except Exception as ex:
            logger.error(f"[Watcher] Ingest FAILED for {path}: {ex}")
            dest = failed_dir / path.name
            try:
                path.rename(dest)
            except Exception as ex_move:
                logger.warning(f"[Watcher] Failed to move to failed: {ex_move}")


class PhotoBrainWatcher:
    def __init__(self, settings: WatcherSettings | None = None):
        self.settings = settings or load_watcher_settings()
        self.observer = Observer()

    def start(self):
        logger.info("[Watcher] Starting PhotoBrain watcher")
        for d in self.settings.watch_dirs:
            d.mkdir(parents=True, exist_ok=True)
            logger.info(f"[Watcher] Watching: {d}")
            handler = _IngestHandler(self.settings)
            self.observer.schedule(handler, str(d), recursive=False)

        self.observer.start()

    def run_forever(self):
        self.start()
        try:
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
            logger.info("[Watcher] Stopping on KeyboardInterrupt")
        finally:
            self.observer.stop()
            self.observer.join()


def main():
    settings = load_watcher_settings()
    logger.info(
        f"[Watcher] API base: {settings.api_base}, dirs: "
        f"{', '.join(str(d) for d in settings.watch_dirs)}"
    )
    watcher = PhotoBrainWatcher(settings)
    watcher.run_forever()


if __name__ == "__main__":
    main()

