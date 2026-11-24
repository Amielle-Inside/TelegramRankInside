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
        self._last_schedule_check = 0.0

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

    def _check_schedule(self) -> None:
        """Fecha rodada semanal (domingo 23:59 SP) e ciclo mensal (4 semanas)."""
        from bot.modules.ranking.storage import (
            week_start_for, close_week_round, current_cycle, close_cycle_and_start_new,
        )
        from datetime import datetime, timezone, timedelta
        try:
            import zoneinfo
            tz = zoneinfo.ZoneInfo("America/Sao_Paulo")
        except Exception:
            tz = timezone(timedelta(hours=-3))

        now_dt = datetime.fromtimestamp(time.time(), tz=tz)
        now = time.time()
        if now - self._last_schedule_check < 60:
            return
        self._last_schedule_check = now
        today = now_dt.strftime("%Y-%m-%d")
        today_weekday = now_dt.weekday()  # 0=segunda, 6=domingo

        # Verifica se passou o domingo 23:59 SP da semana anterior
        # Se hoje é segunda-feira (0) e já passou um pouco, ou domingo após 23:59
        current_week = week_start_for(int(now))
        last_week_dt = now_dt - timedelta(days=7)
        last_week = last_week_dt.strftime("%Y-%m-%d")

        # Fecha rodada da semana anterior se ainda estiver aberta
        row = self.storage.fetchone(
            "SELECT week_start, state FROM ranking_rounds WHERE week_start = ?",
            (last_week,),
        )
        if row and row["state"] == "open":
            # só fecha se já passou do domingo 23:59 daquela semana
            sunday_of_last_week = last_week_dt + timedelta(days=(6 - last_week_dt.weekday()))
            sunday_end_ts = datetime(
                sunday_of_last_week.year, sunday_of_last_week.month, sunday_of_last_week.day,
                23, 59, 0, tzinfo=tz,
            ).timestamp()
            if now >= sunday_end_ts:
                podium = close_week_round(self.storage, last_week)
                if podium:
                    nomes = []
                    for p in podium:
                        nomes.append(f"usuario `{p['user_id']}` ({p['total']:.1f}pts)")
                    self.telegram.send_message(
                        -1002267119439,  # NewsInside Chat
                        f"*Rodada encerrada: {last_week}*\nPodio:\n" + "\n".join(
                            f"{i+1}. {n}" for i, n in enumerate(nomes)
                        ),
                    )

        # Verifica ciclo mensal (4 semanas)
        cycle = current_cycle(self.storage)
        if cycle:
            # conta semanas fechadas neste ciclo
            weeks_in_cycle = self.storage.fetchall("""
                SELECT week_start FROM ranking_rounds
                WHERE state = 'closed'
                ORDER BY week_start DESC
                LIMIT 4
            """)
            # Se já temos 4 semanas fechadas e o ciclo ainda está ativo, fecha e inicia novo
            if len(weeks_in_cycle) >= 4:
                old_cycle_id = cycle["cycle_id"]
                ano_mes = today[:7].replace("-", "")
                new_cycle_id = f"cycle-{ano_mes}"
                close_cycle_and_start_new(self.storage, old_cycle_id, new_cycle_id)
                self.telegram.send_message(
                    -1002267119439,
                    f"*Novo ciclo iniciado:* `{new_cycle_id}`\n"
                    "Rodizio de podio aplicado para o proximo mes.",
                )

    def _dispatch_command(self, cmd: Command, user_id: Optional[int],
                          chat_id: Optional[int], args: Optional[str], msg: dict) -> None:

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
                self._check_schedule()
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
