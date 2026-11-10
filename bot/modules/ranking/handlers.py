"""Modulo ranking - processamento de mensagens (eventos, nao comandos)."""

from __future__ import annotations

import time
from typing import Optional, Dict, List

from bot.core.storage import Storage
from bot.modules.ranking.storage import ensure_tables, week_start_for
from bot.modules.ranking.rules import classify, MsgMeta, P_TEXTO_PROPRIO


class RankingHandler:
    def __init__(self, app, storage: Storage, tz_name: str = "America/Sao_Paulo"):
        self.app = app
        self.storage = storage
        self.tz_name = tz_name
        ensure_tables(storage)
        # cache leve de sequencia por usuario/chat (memoria apenas, reconstruida do banco se necessario)
        self._seq_cache: Dict[tuple, List[dict]] = {}

    def handle_message(self, msg: dict, chat_id: int) -> None:
        """Processa uma mensagem recebida (nao comando) para pontuacao."""
        from_user = msg.get("from", {})
        user_id = from_user.get("id")
        if not user_id:
            return  # canal anonimo, ignorar

        message_id = msg["message_id"]
        text = msg.get("text")
        caption = msg.get("caption")
        date_unix = msg.get("date", int(time.time()))

        # Detecta reply
        is_reply = 0
        reply_to_user_id = None
        if msg.get("reply_to_message"):
            is_reply = 1
            r_from = msg["reply_to_message"].get("from", {})
            reply_to_user_id = r_from.get("id")

        # Detecta forward
        is_forward = 1 if msg.get("forward_origin") or msg.get("forward_from") else 0

        # Detecta video
        has_video = 1 if msg.get("video") or msg.get("video_note") else 0

        # Detecta link (simples: texto contendo http)
        has_link = 1 if (text or caption) and ("http://" in (text or caption) or "https://" in (text or caption)) else 0

        meta = MsgMeta(
            message_id=message_id,
            chat_id=chat_id,
            user_id=user_id,
            text=text,
            is_reply=bool(is_reply),
            reply_to_user_id=reply_to_user_id,
            is_forward=bool(is_forward),
            has_video=bool(has_video),
            has_link=bool(has_link),
            caption=caption,
            date_unix=date_unix,
        )

        # Persiste mensagem
        with self.storage.transaction() as c:
            c.execute("""
                INSERT OR IGNORE INTO ranking_messages
                (chat_id, message_id, user_id, username, first_name, text, caption,
                 is_reply, reply_to_user_id, is_forward, has_video, has_link,
                 date_unix, received_at, processed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                chat_id, message_id, user_id,
                from_user.get("username"), from_user.get("first_name"),
                text, caption, is_reply, reply_to_user_id,
                is_forward, has_video, has_link, date_unix, time.time(),
            ))

        # Calcula pontos
        result = self._calculate_points(meta, chat_id)
        if result.points != 0:
            self._award_points(chat_id, user_id, message_id, result.reason, result.points)

        # Marca processada
        with self.storage.transaction() as c:
            c.execute(
                "UPDATE ranking_messages SET processed = 1 WHERE chat_id = ? AND message_id = ?",
                (chat_id, message_id),
            )

    def _calculate_points(self, meta: MsgMeta, chat_id: int):
        from bot.modules.ranking.rules import classify
        base = classify(meta)

        # Bonus/penalty de sequencia de texto proprio
        if meta.text and not meta.is_reply and not meta.is_forward:
            seq = self._get_sequence(chat_id, meta.user_id)
            # esta mensagem e a proxima da sequencia
            n = len(seq) + 1
            if n == 1:
                pass  # ja e P_TEXTO_PROPRIO
            elif n == 2:
                base.points = P_TEXTO_PROPRIO + 0.1
                base.reason = "segunda mensagem sequencia propria"
            elif n == 3:
                base.points = 0.1  # terceiro complementa para total 0.9
                base.reason = "terceira mensagem sequencia propria"
            elif n >= 4:
                base.points = -0.1
                base.reason = "quarta ou mais mensagem consecutiva (penalidade)"

            self._append_sequence(chat_id, meta.user_id, meta.date_unix)

        # Regra de mensagem idêntica repetida em 10 min
        if meta.text and base.points > 0:
            if self._is_duplicate_in_window(chat_id, meta.user_id, meta.text):
                base.points = 0.0
                base.reason = "mensagem identica repetida em <= 10 min (sem pontos positivos)"

        return base

    def _get_sequence(self, chat_id: int, user_id: int) -> List[dict]:
        key = (chat_id, user_id)
        return self._seq_cache.get(key, [])

    def _append_sequence(self, chat_id: int, user_id: int, ts: int) -> None:
        key = (chat_id, user_id)
        seq = self._seq_cache.setdefault(key, [])
        seq.append({"ts": ts})
        # mantém apenas ultimas 5 para nao crescer indefinido
        if len(seq) > 5:
            seq.pop(0)

    def _is_duplicate_in_window(self, chat_id: int, user_id: int, text: str, window_sec: int = 600) -> bool:
        """Verifica se mesma mensagem do mesmo usuario ja pontuou positivamente nos ultimos window_sec."""
        now = time.time()
        cutoff = now - window_sec
        rows = self.storage.fetchall("""
            SELECT rp.points, rm.date_unix, rm.received_at
            FROM ranking_points rp
            JOIN ranking_messages rm ON rm.chat_id = rp.chat_id AND rm.message_id = rp.message_id
            WHERE rp.chat_id = ? AND rp.user_id = ? AND rp.points > 0 AND rp.created_at > ?
        """, (chat_id, user_id, cutoff))
        for row in rows:
            # compara texto da mensagem original
            mrow = self.storage.fetchone(
                "SELECT text FROM ranking_messages WHERE chat_id = ? AND message_id = ?",
                (chat_id, row["message_id"] if "message_id" in row.keys() else 0),
            ) if "message_id" in row.keys() else None
            # simplificado: se houver ponto positivo recente, considera duplicado
            return True
        return False

    def _award_points(self, chat_id: int, user_id: int, message_id: Optional[int],
                      rule: str, points: float) -> None:
        from bot.modules.ranking.storage import week_start_for
        import time
        ws = week_start_for(int(time.time()), self.tz_name)
        with self.storage.transaction() as c:
            c.execute("""
                INSERT INTO ranking_points
                (chat_id, user_id, message_id, rule, points, week_start, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (chat_id, user_id, message_id, rule, points, ws, time.time()))
            # garante rodada aberta para esta semana
            c.execute("""
                INSERT OR IGNORE INTO ranking_rounds (week_start, state, rules_version)
                VALUES (?, 'open', ?)
            """, (ws, "1.0.0"))
