# python_server/config/watcher_config.py

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class WatcherSettings:
    watch_dirs: List[Path]
    api_base: str
    processed_subdir: str = "processed"
    failed_subdir: str = "failed"
    debounce_seconds: float = 1.0
    image_extensions: tuple = (".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff")


def _default_watch_dirs() -> List[Path]:
    # Prefer explicit env
    env = os.getenv("PHOTOBRAIN_WATCH_DIRS")
    if env:
        parts = [p.strip() for p in env.replace(";", ",").split(",") if p.strip()]
        return [Path(p).expanduser().resolve() for p in parts]

    # Fallbacks: Windows vs *nix
    if os.name == "nt":
        return [Path(r"C:\PhotoBrain\Inbox")]
    else:
        return [Path("~/PhotoBrain/inbox").expanduser()]


def load_watcher_settings() -> WatcherSettings:
    watch_dirs = _default_watch_dirs()
    api_base = os.getenv("PHOTOBRAIN_API_BASE", "http://localhost:8090")

    return WatcherSettings(
        watch_dirs=watch_dirs,
        api_base=api_base.rstrip("/"),
    )

