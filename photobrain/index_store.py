# photobrain/index_store.py

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from loguru import logger


_SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    path TEXT PRIMARY KEY,
    mtime REAL NOT NULL,
    hash TEXT NOT NULL,
    last_ingested_utc REAL NOT NULL
);
"""


@dataclass
class FileRecord:
    path: str
    mtime: float
    hash: str
    last_ingested_utc: float


class IndexStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute("PRAGMA journal_mode = WAL;")
        self._conn.execute(_SCHEMA)
        self._conn.commit()
        logger.info(f"[PhotoBrain] Index DB initialized at {self.db_path}")

    def close(self):
        self._conn.close()

    def get(self, path: str) -> Optional[FileRecord]:
        cur = self._conn.cursor()
        cur.execute("SELECT path, mtime, hash, last_ingested_utc FROM files WHERE path = ?", (path,))
        row = cur.fetchone()
        if not row:
            return None
        return FileRecord(*row)

    def upsert(self, record: FileRecord) -> None:
        self._conn.execute(
            """
            INSERT INTO files (path, mtime, hash, last_ingested_utc)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
              mtime = excluded.mtime,
              hash = excluded.hash,
              last_ingested_utc = excluded.last_ingested_utc;
            """,
            (record.path, record.mtime, record.hash, record.last_ingested_utc),
        )
        self._conn.commit()

