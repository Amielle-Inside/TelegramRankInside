"""Nucleo do bot - armazenamento SQLite com durabilidade."""

from __future__ import annotations

import sqlite3
import os
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Any, Dict, List

PRAGMAS = [
    "PRAGMA journal_mode = WAL;",
    "PRAGMA synchronous = FULL;",
    "PRAGMA foreign_keys = ON;",
    "PRAGMA busy_timeout = 5000;",
]


class Storage:
    """Camada de persistencia SQLite. Unica gravadora serializada."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        for pragma in PRAGMAS:
            self._conn.execute(pragma)
        self._conn.commit()
        self._ensure_core_tables()

    @contextmanager
    def transaction(self):
        """Transacao serializada. Commit automatico se sem excecao."""
        assert self._conn is not None, "Storage nao conectado"
        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        assert self._conn is not None
        return self._conn.execute(sql, params)

    def executemany(self, sql: str, params: list[tuple]) -> sqlite3.Cursor:
        assert self._conn is not None
        return self._conn.executemany(sql, params)

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        assert self._conn is not None
        return self._conn.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        assert self._conn is not None
        return self._conn.execute(sql, params).fetchall()

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    # ------------------------------------------------------------------ #
    # Tabelas centrais (compartilhadas por todos os modulos)
    # ------------------------------------------------------------------ #
    def _ensure_core_tables(self) -> None:
        with self.transaction() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS core_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at REAL NOT NULL
                );
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS updates_received (
                    update_id INTEGER PRIMARY KEY,
                    type TEXT NOT NULL,
                    received_at REAL NOT NULL,
                    processed INTEGER NOT NULL DEFAULT 0,
                    payload TEXT NOT NULL
                );
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS core_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS cooldowns (
                    scope TEXT NOT NULL,
                    command TEXT NOT NULL,
                    next_allowed REAL NOT NULL,
                    PRIMARY KEY (scope, command)
                );
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor_id INTEGER,
                    action TEXT NOT NULL,
                    params TEXT,
                    result TEXT,
                    created_at REAL NOT NULL
                );
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS heartbeat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    note TEXT
                );
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS web_users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS web_sessions (
                    token TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    FOREIGN KEY (username) REFERENCES web_users(username)
                );
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS web_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    scope TEXT NOT NULL DEFAULT 'global',  -- global ou chat_id
                    updated_by INTEGER,
                    updated_at REAL NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1
                );
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS web_csrf_tokens (
                    token TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    used INTEGER NOT NULL DEFAULT 0
                );
            """)


def now_utc() -> float:
    import time
    return time.time()


def utc_timestamp(dt=None) -> float:
    import time, calendar
    if dt is None:
        dt = time.gmtime()
    return calendar.timegm(dt.timetuple())
