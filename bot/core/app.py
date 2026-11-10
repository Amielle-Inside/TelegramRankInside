"""Nucleo - aplicacao principal que orquestra core + modulos."""

from __future__ import annotations

import time
import signal
import threading
from typing import Optional

from bot.core.storage import Storage
from bot.core.telegram import TelegramClient
from bot.core.commands import CommandRegistry, Command
from bot.core.permissions import Permissions
from bot.core.cooldowns import CooldownManager
from bot.core.modules import ModuleManager, ModuleManifest


class RankingApp:
    def __init__(self, config: dict):
        self.config = config
        self.storage = Storage(config.get("DB_PATH", "data/ranking.db"))
        self.telegram = TelegramClient(config["TELEGRAM_BOT_TOKEN"], self.storage)
        owner_ids = {int(x) for x in config.get("OWNER_IDS", "").split(",") if x.strip()}
        admin_ids = {int(x) for x in config.get("ADMIN_IDS", "").split(",") if x.strip()}
        self.permissions = Permissions(owner_ids, admin_ids)
        self.cooldowns = CooldownManager(
            self.storage,
            default_sec=int(config.get("COOLDOWN_PUBLIC_SEC", 300)),
        )
        self.commands = CommandRegistry()
        self.modules = ModuleManager()
        self._running = False
        self._lock = threading.Lock()

    def register_core_commands(self) -> None:
        # Comandos administrativos (registrados aqui, mas tratados por modulos quando existirem)
        pass

    def start(self) -> None:
        self.storage.connect()
        self.telegram.load_offset()
        self._running = True
        print("[app] iniciado. Offset carregado.")

    def stop(self) -> None:
        self._running = False
        self.storage.close()
        print("[app] parado.")

    def process_update(self, update: dict) -> None:
        """Distribui update para modulos habilitados."""
        # Primeiro, comandos (!xxx)
        msg = update.get("message") or update.get("edited_message")
        if msg and "text" in msg:
            text = msg["text"]
            from_user = msg.get("from", {})
            user_id = from_user.get("id")
            chat = msg.get("chat", {})
            chat_id = chat.get("id")
            parsed = self.commands.parse(text)
            if parsed:
                cmd_name, args = parsed
                cmd = self.commands.get(cmd_name)
                if cmd:
                    self._dispatch_command(cmd, user_id, chat_id, args, msg)
                    return  # comando nao pontua no ranking

        # Depois, modulos processam eventos de mensagem (ranking, etc.)
        handler = getattr(self, "ranking_handler", None)
        if handler and msg:
            handler.handle_message(msg, msg.get("chat", {}).get("id"))

    def _dispatch_command(self, cmd: Command, user_id: Optional[int],
                          chat_id: Optional[int], args: Optional[str], msg: dict) -> None:
        # Checagem de permissao
        if cmd.owner_only and not self.permissions.is_owner(user_id or 0):
            self.telegram.send_message(chat_id, "Comando restrito ao owner.")
            return
        if cmd.admin_only and not self.permissions.is_admin(user_id or 0):
            self.telegram.send_message(chat_id, "Comando restrito a administradores.")
            return

        # Cooldown para publico (no grupo). Admins/owner isentos.
        if cmd.public and chat_id and not self.permissions.is_admin(user_id or 0):
            scope = f"chat:{chat_id}"
            if not self.cooldowns.allowed(scope, cmd.name, cmd.cooldown_sec):
                rem = int(self.cooldowns.remaining(scope, cmd.name, cmd.cooldown_sec))
                mins = rem // 60
                secs = rem % 60
                self.telegram.send_message(
                    chat_id,
                    f"Aguarde {mins}m{secs}s antes de usar !{cmd.name} novamente (cooldown).",
                )
                return
            self.cooldowns.record(scope, cmd.name, cmd.cooldown_sec)

        # Executa
        try:
            cmd.handler(self, user_id, chat_id, args, msg)
        except Exception as e:
            print(f"[app] erro comando {cmd.name}: {e}")
            try:
                self.telegram.send_message(chat_id, f"Erro ao executar comando: {e}")
            except Exception:
                pass

    def run_loop(self) -> None:
        """Loop principal de long polling."""
        print("[app] loop iniciado.")
        while self._running:
            try:
                updates = self.telegram.get_updates()
                for upd in updates:
                    uid = upd["update_id"]
                    # pula se ja foi processado (dedup apos reinicio/dupla entregada)
                    already = self.storage.fetchone(
                        "SELECT processed FROM updates_received WHERE update_id = ?",
                        (uid,),
                    )
                    if already and already["processed"] == 1:
                        continue
                    self.process_update(upd)
                    self.telegram.mark_processed(uid)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[app] erro no loop: {e}")
                time.sleep(3)
