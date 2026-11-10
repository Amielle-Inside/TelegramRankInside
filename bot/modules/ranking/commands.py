"""Modulo ranking - comandos publicos e administrativos."""

from __future__ import annotations

from typing import Optional

from bot.core.app import RankingApp
from bot.core.storage import Storage
from bot.modules.ranking.storage import week_start_for
import time


def _top10(storage: Storage, chat_id: int, week_start: str) -> list:
    rows = storage.fetchall("""
        SELECT rp.user_id,
               SUM(rp.points) as total,
               MAX(rm.username) as username,
               MAX(rm.first_name) as first_name
        FROM ranking_points rp
        LEFT JOIN ranking_messages rm ON rm.chat_id = rp.chat_id AND rm.user_id = rp.user_id
        WHERE rp.chat_id = ? AND rp.week_start = ?
        GROUP BY rp.user_id
        ORDER BY total DESC, rp.user_id ASC
        LIMIT 10
    """, (chat_id, week_start))
    return [
        {
            "user_id": r["user_id"],
            "points": round(r["total"], 2),
            "username": r["username"],
            "first_name": r["first_name"],
        }
        for r in rows
    ]


def _cycle_info(storage: Storage, chat_id: int) -> dict:
    # ciclo ativo
    row = storage.fetchone("SELECT * FROM ranking_cycles WHERE state = 'active' ORDER BY started_at DESC LIMIT 1")
    if not row:
        return {"active": False}
    import json
    participants = json.loads(row["participants"] or "[]")
    # pódios já conquistados neste ciclo
    podiums = storage.fetchall("""
        SELECT user_id, COUNT(*) as qtd FROM ranking_podiums
        WHERE cycle_id = ? GROUP BY user_id
    """, (row["cycle_id"],))
    podium_map = {r["user_id"]: r["qtd"] for r in podiums}
    return {
        "active": True,
        "cycle_id": row["cycle_id"],
        "participants": participants,
        "podiums": podium_map,
    }


def cmd_rank(app: RankingApp, user_id: Optional[int], chat_id: Optional[int],
             args: Optional[str], msg: dict) -> None:
    if not chat_id:
        return
    storage: Storage = app.storage
    ws = week_start_for(int(time.time()), app.config.get("TZ", "America/Sao_Paulo"))
    top = _top10(storage, chat_id, ws)
    lines = [f"*Top 10 - Semana {ws}*"]
    for i, entry in enumerate(top, 1):
        nome = f"@{entry['username']}" if entry["username"] else (entry["first_name"] or f"usuario {entry['user_id']}")
        lines.append(f"{i}. {nome} — {entry['points']} pts")
    if not top:
        lines.append("Nenhum ponto nesta semana ainda.")
    app.telegram.send_message(chat_id, "\n".join(lines))


def cmd_rciclo(app: RankingApp, user_id: Optional[int], chat_id: Optional[int],
               args: Optional[str], msg: dict) -> None:
    if not chat_id:
        return
    storage: Storage = app.storage
    info = _cycle_info(storage, chat_id)
    if not info.get("active"):
        app.telegram.send_message(chat_id, "Nenhum ciclo ativo no momento.")
        return
    lines = [f"*Ciclo:* `{info['cycle_id']}`"]
    lines.append(f"Participantes elegiveis: {len(info['participants'])}")
    if info["podiums"]:
        lines.append("*Pódios ja conquistados neste ciclo:*")
        for uid, qtd in sorted(info["podiums"].items(), key=lambda x: -x[1]):
            lines.append(f"- usuario `{uid}`: {qtd} pódio(s)")
    app.telegram.send_message(chat_id, "\n".join(lines))


def cmd_pontos(app: RankingApp, user_id: Optional[int], chat_id: Optional[int],
               args: Optional[str], msg: dict) -> None:
    if not chat_id or not user_id:
        return
    storage: Storage = app.storage
    ws = week_start_for(int(time.time()), app.config.get("TZ", "America/Sao_Paulo"))
    row = storage.fetchone("""
        SELECT SUM(points) as total FROM ranking_points
        WHERE chat_id = ? AND user_id = ? AND week_start = ?
    """, (chat_id, user_id, ws))
    total = round(row["total"], 2) if row and row["total"] is not None else 0.0
    app.telegram.send_message(chat_id, f"Seus pontos esta semana ({ws}): *{total}*")


def cmd_posicao(app: RankingApp, user_id: Optional[int], chat_id: Optional[int],
                args: Optional[str], msg: dict) -> None:
    if not chat_id or not user_id:
        return
    storage: Storage = app.storage
    ws = week_start_for(int(time.time()), app.config.get("TZ", "America/Sao_Paulo"))
    rows = storage.fetchall("""
        SELECT user_id, SUM(points) as total
        FROM ranking_points
        WHERE chat_id = ? AND week_start = ?
        GROUP BY user_id
        ORDER BY total DESC
    """, (chat_id, ws))
    pos = None
    for i, r in enumerate(rows, 1):
        if r["user_id"] == user_id:
            pos = i
            break
    if pos:
        app.telegram.send_message(chat_id, f"Sua posicao esta semana: {pos}º (entre {len(rows)})")
    else:
        app.telegram.send_message(chat_id, "Voce nao pontuou nesta semana ainda.")


def cmd_historico(app: RankingApp, user_id: Optional[int], chat_id: Optional[int],
                  args: Optional[str], msg: dict) -> None:
    if not chat_id:
        return
    storage: Storage = app.storage
    rows = storage.fetchall("""
        SELECT week_start, state FROM ranking_rounds
        WHERE state = 'closed' ORDER BY week_start DESC LIMIT 5
    """)
    if not rows:
        app.telegram.send_message(chat_id, "Nenhuma rodada encerrada ainda.")
        return
    lines = ["*Rodadas anteriores:*"]
    for r in rows:
        lines.append(f"- {r['week_start']} ({r['state']})")
    app.telegram.send_message(chat_id, "\n".join(lines))


def cmd_regras(app: RankingApp, user_id: Optional[int], chat_id: Optional[int],
               args: Optional[str], msg: dict) -> None:
    texto = (
        "*Regras de pontuacao (semanal)*\n"
        "• Texto proprio: +0.7\n"
        "• Resposta a outra pessoa: +1.1\n"
        "• 3 msgs consecutivas texto: +0.9 total\n"
        "• 4a msg consecutiva: -0.1\n"
        "• Video com explicacao propria: +0.7\n"
        "• Link sem comentario: -0.3\n"
        "• 3 encaminhamentos consecutivos: -0.6\n"
        "• Msg identica repetida em <=10 min: sem pontos positivos\n"
        "• Top 3 tem rodizio por ciclo\n"
    )
    app.telegram.send_message(chat_id, texto)


def cmd_ajuda(app: RankingApp, user_id: Optional[int], chat_id: Optional[int],
              args: Optional[str], msg: dict) -> None:
    texto = (
        "*Comandos publicos (cooldown 5 min no grupo):*\n"
        "!rank — Top 10 da semana\n"
        "!rciclo — Ciclo atual e elegibilidade ao podio\n"
        "!pontos — Sua pontuacao\n"
        "!posicao — Sua posicao no rodizio\n"
        "!historico — Rodadas anteriores\n"
        "!regras — Regras de pontuacao\n"
        "!ajuda — esta mensagem\n"
    )
    app.telegram.send_message(chat_id, texto)


# --------------------------------------------------------------------------- #
# Comandos administrativos (owner/admin)
# --------------------------------------------------------------------------- #

def cmd_status(app: RankingApp, user_id: Optional[int], chat_id: Optional[int],
               args: Optional[str], msg: dict) -> None:
    storage: Storage = app.storage
    total_msgs = storage.fetchone("SELECT COUNT(*) as c FROM ranking_messages")["c"]
    total_pts = storage.fetchone("SELECT COUNT(*) as c FROM ranking_points")["c"]
    rounds = storage.fetchall("SELECT week_start, state FROM ranking_rounds ORDER BY week_start DESC LIMIT 3")
    lines = [f"*Status do bot*\nMensagens armazenadas: {total_msgs}\nLancamentos de pontos: {total_pts}"]
    lines.append("*Ultimas rodadas:*")
    for r in rounds:
        lines.append(f"- {r['week_start']}: {r['state']}")
    dest = chat_id
    # admin prefere privado, mas se nao for possivel, envia no grupo
    try:
        app.telegram.send_private(user_id, "\n".join(lines)) if user_id else None
    except Exception:
        app.telegram.send_message(dest, "\n".join(lines))


def cmd_check(app: RankingApp, user_id: Optional[int], chat_id: Optional[int],
              args: Optional[str], msg: dict) -> None:
    # placeholder de auditoria (recontagem)
    if not chat_id:
        return
    app.telegram.send_message(chat_id, "!check: recontagem em modo auditoria. (implementacao base pronta)")


def cmd_stop(app: RankingApp, user_id: Optional[int], chat_id: Optional[int],
             args: Optional[str], msg: dict) -> None:
    app.telegram.send_message(chat_id, "Parando o bot...")
    app.stop()


def cmd_reboot(app: RankingApp, user_id: Optional[int], chat_id: Optional[int],
               args: Optional[str], msg: dict) -> None:
    app.telegram.send_message(chat_id, "Reiniciando o bot...")
    app.stop()
    raise SystemExit(0)
