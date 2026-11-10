"""Nucleo - controle de cooldown por (escopo, comando). Persistido no SQLite."""

from __future__ import annotations

import time
from typing import Optional

from bot.core.storage import Storage


class CooldownManager:
    def __init__(self, storage: Storage, default_sec: int = 300):
        self.storage = storage
        self.default_sec = default_sec

    def _now(self) -> float:
        return time.time()

    def allowed(self, scope: str, command: str, cooldown_sec: Optional[int] = None) -> bool:
        cd = cooldown_sec if cooldown_sec is not None else self.default_sec
        row = self.storage.fetchone(
            "SELECT next_allowed FROM cooldowns WHERE scope = ? AND command = ?",
            (scope, command),
        )
        now = self._now()
        if row is None:
            return True
        return now >= float(row["next_allowed"])

    def record(self, scope: str, command: str, cooldown_sec: Optional[int] = None) -> None:
        cd = cooldown_sec if cooldown_sec is not None else self.default_sec
        next_allowed = self._now() + cd
        with self.storage.transaction() as c:
            c.execute(
                "INSERT OR REPLACE INTO cooldowns (scope, command, next_allowed) VALUES (?, ?, ?)",
                (scope, command, next_allowed),
            )

    def remaining(self, scope: str, command: str, cooldown_sec: Optional[int] = None) -> float:
        cd = cooldown_sec if cooldown_sec is not None else self.default_sec
        row = self.storage.fetchone(
            "SELECT next_allowed FROM cooldowns WHERE scope = ? AND command = ?",
            (scope, command),
        )
        if row is None:
            return 0.0
        return max(0.0, float(row["next_allowed"]) - time.time())
