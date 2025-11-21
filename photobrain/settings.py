# photobrain/settings.py

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


def _env_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return default
    return [x.strip() for x in raw.split(os.pathsep) if x.strip()]


@dataclass
class PhotoBrainSettings:
    """
    Configuration for the PhotoBrain ingestor.

    Override via environment variables:

    - PHOTOBRAIN_BASE_URL           (default: http://localhost:8090)
    - PHOTOBRAIN_WATCH_DIRS         (PATHSEP-separated list; default: Pictures, Downloads/Screenshots)
    - PHOTOBRAIN_POLL_INTERVAL      (seconds; default: 30)
    - PHOTOBRAIN_INDEX_DB           (path to sqlite db; default: ~/.photobrain/index.db)
    """

    base_url: str = field(default_factory=lambda: os.getenv("PHOTOBRAIN_BASE_URL", "http://localhost:8090"))
    poll_interval_seconds: int = field(default_factory=lambda: int(os.getenv("PHOTOBRAIN_POLL_INTERVAL", "30")))
    index_db_path: Path = field(
        default_factory=lambda: Path(os.getenv("PHOTOBRAIN_INDEX_DB", str(Path.home() / ".photobrain" / "index.db")))
    )
    watch_dirs: List[Path] = field(default_factory=list)
    include_extensions: set[str] = field(
        default_factory=lambda: {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}
    )

    @classmethod
    def load(cls) -> "PhotoBrainSettings":
        # Defaults for watched dirs
        default_dirs = [
            str(Path.home() / "Pictures"),
            str(Path.home() / "Pictures" / "Screenshots"),
            str(Path.home() / "Downloads"),
        ]
        watch_dir_strs = _env_list("PHOTOBRAIN_WATCH_DIRS", default_dirs)
        watch_dirs = [Path(d).expanduser() for d in watch_dir_strs]

        cfg = cls()
        cfg.watch_dirs = watch_dirs
        return cfg


settings = PhotoBrainSettings.load()

