import hashlib
from datetime import datetime, timezone

from database import Database


class FavoritesRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def add(self, text: str) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        h = self._hash(text)
        try:
            self._db.connection.execute(
                "INSERT OR IGNORE INTO favorites (text, hash, created_at, updated_at) VALUES (?, ?, ?, ?);",
                (text, h, now, now),
            )
            self._db.connection.commit()
            return True
        except Exception:
            return False

    def remove(self, text: str) -> bool:
        h = self._hash(text)
        try:
            cur = self._db.connection.execute(
                "DELETE FROM favorites WHERE hash = ?;", (h,)
            )
            self._db.connection.commit()
            return cur.rowcount > 0
        except Exception:
            return False

    def is_favorite(self, text: str) -> bool:
        h = self._hash(text)
        try:
            cur = self._db.connection.execute(
                "SELECT 1 FROM favorites WHERE hash = ? LIMIT 1;", (h,)
            )
            return cur.fetchone() is not None
        except Exception:
            return False

    def list_all(self) -> list[str]:
        try:
            cur = self._db.connection.execute(
                "SELECT text FROM favorites ORDER BY updated_at DESC;"
            )
            return [row["text"] for row in cur.fetchall()]
        except Exception:
            return []
