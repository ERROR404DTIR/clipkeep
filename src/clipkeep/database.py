import sqlite3
from pathlib import Path

from constants import APP_NAME, get_db_path


_SCHEMA = """
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_favorites_hash ON favorites(hash);
"""


class Database:
    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or get_db_path())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        try:
            self.path.chmod(0o600)
        except FileNotFoundError:
            pass

    @property
    def connection(self) -> sqlite3.Connection:
        return self._conn

    def close(self) -> None:
        try:
            self._conn.close()
        except sqlite3.Error:
            pass
