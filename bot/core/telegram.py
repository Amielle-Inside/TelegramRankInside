"""Nucleo - cliente Telegram (long polling) via urllib, sem dependencias externas."""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.parse
import urllib.error
from typing import Any, Optional

from bot.core.storage import Storage, now_utc


class TelegramClient:
    """Cliente minimo da Telegram Bot API.

    Garante: persistir update_id ANTES de confirmar offset no Telegram.
    """

    def __init__(self, token: str, storage: Storage, timeout: int = 30):
        self.token = token
        self.storage = storage
        self.timeout = timeout
        self.base = f"https://api.telegram.org/bot{token}"
        self.offset: Optional[int] = None

    # ---------------------- requisicoes HTTP ---------------------- #
    def _get(self, method: str, params: dict | None = None) -> dict:
        url = f"{self.base}/{method}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "TelegramRankInside/1.0"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _post(self, method: str, data: dict) -> dict:
        url = f"{self.base}/{method}"
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "User-Agent": "TelegramRankInside/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # ---------------------- updates ---------------------- #
    def load_offset(self) -> None:
        row = self.storage.fetchone(
            "SELECT value FROM core_state WHERE key = 'last_offset'"
        )
        self.offset = int(row["value"]) if row else None

    def save_offset(self, update_id: int) -> None:
        with self.storage.transaction() as c:
            c.execute(
                "INSERT OR REPLACE INTO core_state (key, value) VALUES (?, ?)",
                ("last_offset", str(update_id)),
            )
        self.offset = update_id

    def persist_update(self, update_id: int, utype: str, payload: dict) -> None:
        """Grava o update ANTES de qualquer processamento."""
        with self.storage.transaction() as c:
            c.execute(
                "INSERT OR IGNORE INTO updates_received (update_id, type, received_at, processed, payload) "
                "VALUES (?, ?, ?, 0, ?)",
                (update_id, utype, now_utc(), json.dumps(payload, ensure_ascii=False)),
            )

    def mark_processed(self, update_id: int) -> None:
        with self.storage.transaction() as c:
            c.execute(
                "UPDATE updates_received SET processed = 1 WHERE update_id = ?",
                (update_id,),
            )

    def get_updates(self) -> list[dict]:
        """Busca updates do Telegram, persiste cada um e retorna lista."""
        params: dict[str, Any] = {"timeout": 5, "allowed_updates": ["message", "edited_message", "chat_member"]}
        if self.offset is not None:
            params["offset"] = self.offset + 1
        try:
            data = self._get("getUpdates", params)
        except Exception as e:
            print(f"[telegram] erro getUpdates: {e}")
            return []

        if not data.get("ok"):
            print(f"[telegram] getUpdates nao ok: {data.get('description')}")
            return []

        result = data.get("result", [])
        for upd in result:
            uid = upd["update_id"]
            # detecta tipo
            utype = "message"
            if "edited_message" in upd:
                utype = "edited_message"
            elif "chat_member" in upd:
                utype = "chat_member"
            self.persist_update(uid, utype, upd)
            # avanca offset apenas depois de persistir
            self.save_offset(uid)

        return result

    # ---------------------- envios ---------------------- #
    def send_message(self, chat_id: int | str, text: str, parse_mode: str = "Markdown") -> dict:
        return self._post("sendMessage", {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        })

    def send_private(self, user_id: int, text: str) -> dict:
        return self.send_message(user_id, text)

    def get_chat(self, chat_id: int | str) -> dict:
        return self._get("getChat", {"chat_id": chat_id})

    def get_chat_administrators(self, chat_id: int | str) -> dict:
        return self._get("getChatAdministrators", {"chat_id": chat_id})

    def get_chat_member_count(self, chat_id: int | str) -> dict:
        return self._get("getChatMembersCount", {"chat_id": chat_id})

    def get_me(self) -> dict:
        return self._get("getMe")
