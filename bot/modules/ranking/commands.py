"""Modulo ranking - comandos publicos e administrativos."""

from __future__ import annotations

from typing import Optional
from datetime import datetime, timezone, timedelta

try:
    import zoneinfo
except Exception:
    zoneinfo = None

from bot.core.app import RankingApp
from bot.core.storage import Storage
from bot.modules.ranking.storage import week_start_for
import time
import json


def _tz():
    if zoneinfo:
        try:
            return zoneinfo.ZoneInfo("America/Sao_Paulo")
        except Exception:
            pass
    return timezone(timedelta(hours=-3))


def _semana_termino(ws: str) -> str:
    """Retorna 'DD/MM/YYYY HH:MM' do fim da semana (domingo 23:59 SP)."""
    ano, mes, dia = (int(x) for x in ws.split("-"))
    segunda = datetime(ano, mes, dia, tzinfo=_tz())
    domingo = segunda + timedelta(days=6, hours=23, minutes=59)
    return domingo.strftime("%d/%m/%Y %H:%M")


def _ciclo_termino(started_at: str, participantes: list) -> str:
    """Retorna 'DD/MM/YYYY HH:MM' do fim estimado do ciclo (3 pódios/semana)."""
    try:
        inicio = datetime.fromisoformat(started_at)
    except Exception:
        inicio = datetime.now(_tz())
    if not inicio.tzinfo:
        inicio = inicio.replace(tzinfo=_tz())
    n = len(participantes) if participantes else 0
    semanas = -(-n // 3) if n > 0 else 1  # ceil(n/3), min 1 semana
    termino = inicio + timedelta(weeks=semanas)
    return termino.strftime("%d/%m/%Y %H:%M")


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
    # ciclo ativo primeiro; se nao houver, o ultimo fechado
    row = storage.fetchone("SELECT * FROM ranking_cycles WHERE state = 'active' ORDER BY started_at DESC LIMIT 1")
    if not row:
        row = storage.fetchone("SELECT * FROM ranking_cycles ORDER BY started_at DESC LIMIT 1")
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
        "active": row["state"] == "active",
        "cycle_id": row["cycle_id"],
        "started_at": row["started_at"],
        "state": row["state"],
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
    lines.append(f"\nSemana termina em: {_semana_termino(ws)}")
    app.telegram.send_message(chat_id, "\n".join(lines))


def cmd_rciclo(app: RankingApp, user_id: Optional[int], chat_id: Optional[int],
               args: Optional[str], msg: dict) -> None:
    if not chat_id:
        return
    storage: Storage = app.storage
    info = _cycle_info(storage, chat_id)
    if not info.get("cycle_id"):
        app.telegram.send_message(chat_id, "Nenhum ciclo encontrado.")
        return
    estado = "ativo" if info.get("active") else "encerrado"
    termino = _ciclo_termino(info.get("started_at", ""), info["participants"])
    lines = [f"*Ciclo:* `{info['cycle_id']}` ({estado})"]
    lines.append(f"Iniciado em: {info.get('started_at', '—')}")
    lines.append(f"Término estimado: {termino}")
    lines.append(f"Participantes elegíveis: {len(info['participants'])}")
    if info["podiums"]:
        lines.append("*Pódios já conquistados neste ciclo:*")
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
        ORDER BY week_start DESC LIMIT 5
    """)
    if not rows:
        app.telegram.send_message(chat_id, "Nenhuma rodada encontrada.")
        return
    lines = ["*Rodadas:*"]
    for r in rows:
        tag = "encerrada" if r["state"] == "closed" else "aberta"
        lines.append(f"- {r['week_start']} ({tag})")
    app.telegram.send_message(chat_id, "\n".join(lines))


def cmd_regras(app: RankingApp, user_id: Optional[int], chat_id: Optional[int],
               args: Optional[str], msg: dict) -> None:
    texto = (
        "*RankingInside — como funciona*\n\n"
        "*O que é:* minigame de participação semanal no grupo. Quem mais interage com mensagens próprias, respostas e vídeos sobe no top 10 da semana.\n\n"
        "*Pontuação por mensagem:*\n"
        "• Texto próprio (não resposta): +0.7\n"
        "• Resposta a outra pessoa: +1.1\n"
        "• 3 msgs consecutivas de texto: +0.9 total\n"
        "• 4ª msg consecutiva e seguintes: -0.1 cada\n"
        "• Vídeo com explicação própria: +0.7\n"
        "• Link sem comentário: -0.3\n"
        "• 3 encaminhamentos consecutivos: -0.6\n"
        "• Mensagem idêntica repetida em <=10 min: sem pontos positivos\n\n"
        "*Ciclo e pódio:*\n"
        "• Cada semana é uma rodada. O top 3 da semana ganha pódio.\n"
        "• O pódio tem rodízio por ciclo: quem já ficou no top 3 fica fora da elegibilidade até rodar todos.\n"
        "• Use !rciclo para ver o ciclo atual e sua elegibilidade.\n\n"
        "*Comandos (cooldown 5 min no grupo):*\n"
        "!rank — Top 10 da semana | !pontos — Sua pontuação | !posicao — Sua posição\n"
        "!historico — Rodadas anteriores | !regras — esta mensagem | !ajuda — lista de comandos\n"
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
    # recontagem em modo auditoria: recalcula pontos da semana atual
    if not chat_id:
        return
    storage: Storage = app.storage
    from bot.modules.ranking.storage import week_start_for
    import time
    ws = week_start_for(int(time.time()), app.config.get("TZ", "America/Sao_Paulo"))

    # recontar pontos por usuario nesta semana
    rows = storage.fetchall("""
        SELECT user_id, SUM(points) as total, COUNT(*) as qtd
        FROM ranking_points
        WHERE chat_id = ? AND week_start = ?
        GROUP BY user_id
        ORDER BY total DESC
    """, (chat_id, ws))

    total_usuarios = len(rows)
    total_pontos = round(sum(r["total"] for r in rows), 2)
    total_launchs = sum(r["qtd"] for r in rows)

    # registrar auditoria
    try:
        params = {
            "chat_id": chat_id,
            "week_start": ws,
            "usuarios_recontados": total_usuarios,
            "total_pontos": total_pontos,
            "total_lancamentos": total_launchs,
        }
        with storage.transaction() as c:
            c.execute(
                "INSERT INTO audit_log (actor_id, action, params, result, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, "check", json.dumps(params), f"{total_usuarios} usuarios, {total_pontos} pts, {total_launchs} lancamentos", time.time()),
            )
    except Exception:
        pass

    linhas = [
        f"*Auditoria !check — Semana {ws}*",
        f"Usuarios recontados: {total_usuarios}",
        f"Total de pontos: {total_pontos}",
        f"Total de lançamentos: {total_launchs}",
    ]
    if rows:
        linhas.append("\n*Top 5 após recontagem:*")
        for i, r in enumerate(rows[:5], 1):
            linhas.append(f"{i}. usuario `{r['user_id']}`: {round(r['total'], 2)} pts ({r['qtd']} lançamentos)")
    app.telegram.send_message(chat_id, "\n".join(linhas))


def cmd_stop(app: RankingApp, user_id: Optional[int], chat_id: Optional[int],
             args: Optional[str], msg: dict) -> None:
    app.telegram.send_message(chat_id, "Parando o bot...")
    app.stop()


def cmd_reboot(app: RankingApp, user_id: Optional[int], chat_id: Optional[int],
               args: Optional[str], msg: dict) -> None:
    app.telegram.send_message(chat_id, "Reiniciando o bot...")
    app.stop()
    raise SystemExit(0)
