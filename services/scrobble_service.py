"""
services/scrobble_service.py — lightweight listen-history backed by SQLite.
"""
import logging
import sqlite3
import threading
from datetime import datetime
from typing import Optional

log = logging.getLogger(__name__)

_DB_FILE = "scrobbles.db"
_SCHEMA  = """
CREATE TABLE IF NOT EXISTS scrobbles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id    TEXT    NOT NULL,
    title       TEXT    NOT NULL,
    artist      TEXT    NOT NULL,
    album       TEXT,
    album_id    TEXT,
    played_at   TEXT    NOT NULL,
    submission  INTEGER NOT NULL DEFAULT 1
);
"""


class ScrobbleService:
    def __init__(self, db_file: str = _DB_FILE):
        self._db   = db_file
        self._lock = threading.Lock()
        self._init_db()

    # ── setup ──────────────────────────────────────────────────────────────

    def _init_db(self):
        with self._connect() as con:
            con.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self._db)
        con.row_factory = sqlite3.Row
        return con

    # ── write ──────────────────────────────────────────────────────────────

    def add(self, *, video_id: str, title: str, artist: str,
            album: str = "", album_id: str = "", submission: bool = True):
        played_at = datetime.utcnow().isoformat()
        with self._lock, self._connect() as con:
            con.execute(
                """INSERT INTO scrobbles (video_id, title, artist, album, album_id, played_at, submission)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (video_id, title, artist, album, album_id, played_at, int(submission)),
            )
            # keep only last 1000 entries
            con.execute(
                """DELETE FROM scrobbles WHERE id NOT IN (
                       SELECT id FROM scrobbles ORDER BY id DESC LIMIT 1000
                   )"""
            )
        log.info("Scrobble: %r by %r (submission=%s)", title, artist, submission)

    # ── read ───────────────────────────────────────────────────────────────

    def get_history(self, limit: int = 50, since: Optional[str] = None) -> list[dict]:
        query  = "SELECT * FROM scrobbles WHERE submission = 1"
        params: list = []
        if since:
            query  += " AND played_at >= ?"
            params.append(since)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._connect() as con:
            rows = con.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_now_playing(self) -> Optional[dict]:
        """Return the most recent non-submission (now-playing) event."""
        with self._connect() as con:
            row = con.execute(
                "SELECT * FROM scrobbles WHERE submission = 0 ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return dict(row) if row else None


# Singleton
scrobble_service = ScrobbleService()
