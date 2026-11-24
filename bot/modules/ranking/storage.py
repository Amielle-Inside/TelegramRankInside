"""Modulo ranking - tabelas especificas no SQLite."""

from __future__ import annotations

import json
import time
from bot.core.storage import Storage


def ensure_tables(storage: Storage) -> None:
    with storage.transaction() as c:
        # Mensagens recebidas (evidencia operacional)
        c.execute("""
            CREATE TABLE IF NOT EXISTS ranking_messages (
                chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                text TEXT,
                caption TEXT,
                is_reply INTEGER NOT NULL DEFAULT 0,
                reply_to_user_id INTEGER,
                is_forward INTEGER NOT NULL DEFAULT 0,
                has_video INTEGER NOT NULL DEFAULT 0,
                has_link INTEGER NOT NULL DEFAULT 0,
                date_unix INTEGER NOT NULL,
                received_at REAL NOT NULL,
                processed INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (chat_id, message_id)
            );
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_ranking_messages_user ON ranking_messages(user_id, received_at);")
        c.execute("CREATE INDEX IF NOT EXISTS idx_ranking_messages_chat ON ranking_messages(chat_id, received_at);")

        # Lançamentos de pontos (auditavel, rastreavel até origem)
        c.execute("""
            CREATE TABLE IF NOT EXISTS ranking_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                message_id INTEGER,
                rule TEXT NOT NULL,
                points REAL NOT NULL,
                week_start TEXT NOT NULL,   -- YYYY-MM-DD (segunda-feira)
                cycle_id TEXT,
                created_at REAL NOT NULL,
                revision INTEGER NOT NULL DEFAULT 1
            );
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_ranking_points_user_week ON ranking_points(user_id, week_start);")

        # Rodadas semanais
        c.execute("""
            CREATE TABLE IF NOT EXISTS ranking_rounds (
                week_start TEXT PRIMARY KEY,
                state TEXT NOT NULL DEFAULT 'open',   -- open, closing, closed
                closed_at REAL,
                rules_version TEXT NOT NULL
            );
        """)

        # Ciclos de podio
        c.execute("""
            CREATE TABLE IF NOT EXISTS ranking_cycles (
                cycle_id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                state TEXT NOT NULL DEFAULT 'active',  -- active, closed
                participants TEXT NOT NULL DEFAULT '[]'  -- JSON lista de user_ids elegiveis
            );
        """)

        # Pódios conquistados (historico para rodizio)
        c.execute("""
            CREATE TABLE IF NOT EXISTS ranking_podiums (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id TEXT NOT NULL,
                week_start TEXT NOT NULL,
                position INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                points REAL NOT NULL
            );
        """)

        # Cooldowns especificos ja existem no core, mas aqui deixamos registro de comandos usados
        c.execute("""
            CREATE TABLE IF NOT EXISTS ranking_command_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                command TEXT NOT NULL,
                created_at REAL NOT NULL
            );
        """)


def week_start_for(ts_unix: int, tz_name: str = "America/Sao_Paulo") -> str:
    """Retorna YYYY-MM-DD da segunda-feira da semana do timestamp (UTC)."""
    from datetime import datetime, timezone, timedelta
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        tz = timezone(timedelta(hours=-3))  # fallback America/Sao_Paulo
    dt = datetime.fromtimestamp(ts_unix, tz=tz)
    # segunda-feira = 0
    monday = dt - timedelta(days=dt.weekday())
    return monday.strftime("%Y-%m-%d")


def sunday_end_for(ts_unix: int, tz_name: str = "America/Sao_Paulo") -> str:
    """Retorna YYYY-MM-DD do domingo da semana do timestamp (SP)."""
    from datetime import datetime, timezone, timedelta
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        tz = timezone(timedelta(hours=-3))
    dt = datetime.fromtimestamp(ts_unix, tz=tz)
    sunday = dt + timedelta(days=(6 - dt.weekday()))
    return sunday.strftime("%Y-%m-%d")


def ensure_week_round(storage: Storage, week_start: str) -> None:
    """Garante que exista uma rodada aberta para a semana dada."""
    row = storage.fetchone("SELECT week_start, state FROM ranking_rounds WHERE week_start = ?", (week_start,))
    if not row:
        storage.execute(
            "INSERT INTO ranking_rounds (week_start, state, rules_version) VALUES (?, 'open', '1.1.0')",
            (week_start,),
        )
    elif row["state"] != "open":
        storage.execute(
            "UPDATE ranking_rounds SET state = 'open' WHERE week_start = ?",
            (week_start,),
        )


def close_week_round(storage: Storage, week_start: str) -> list[dict]:
    """Fecha a rodada da semana, gera pódio (top 3) e retorna o pódio."""
    # fecha rodada
    storage.execute(
        "UPDATE ranking_rounds SET state = 'closed', closed_at = ? WHERE week_start = ?",
        (time.time(), week_start),
    )
    # top 3 por pontos naquela semana
    top = storage.fetchall("""
        SELECT user_id, SUM(points) as total
        FROM ranking_points
        WHERE week_start = ? AND points > 0
        GROUP BY user_id
        ORDER BY total DESC, user_id ASC
        LIMIT 3
    """, (week_start,))
    # insere pódios
    for pos, r in enumerate(top, start=1):
        storage.execute(
            "INSERT INTO ranking_podiums (cycle_id, week_start, position, user_id, points) VALUES (?, ?, ?, ?, ?)",
            (f"cycle-{week_start[:4]}-{week_start[5:7]}", week_start, pos, r["user_id"], r["total"]),
        )
    return top


def current_cycle(storage: Storage) -> dict | None:
    """Retorna o ciclo ativo ou o mais recente."""
    row = storage.fetchone("SELECT * FROM ranking_cycles WHERE state = 'active' ORDER BY started_at DESC LIMIT 1")
    if not row:
        row = storage.fetchone("SELECT * FROM ranking_cycles ORDER BY started_at DESC LIMIT 1")
    if not row:
        return None
    return dict(row)


def ensure_cycle(storage: Storage, cycle_id: str) -> None:
    """Garante que exista um ciclo ativo."""
    row = storage.fetchone("SELECT cycle_id, state FROM ranking_cycles WHERE cycle_id = ?", (cycle_id,))
    if not row:
        storage.execute(
            "INSERT INTO ranking_cycles (cycle_id, started_at, state, participants) VALUES (?, ?, 'active', '[]')",
            (cycle_id, time.time()),
        )
    elif row["state"] != "active":
        storage.execute(
            "UPDATE ranking_cycles SET state = 'active' WHERE cycle_id = ?",
            (cycle_id,),
        )


def close_cycle_and_start_new(storage: Storage, old_cycle_id: str, new_cycle_id: str) -> None:
    """Fecha o ciclo antigo e inicia um novo com rodízio de pódio."""
    # fecha ciclo antigo
    storage.execute(
        "UPDATE ranking_cycles SET state = 'closed' WHERE cycle_id = ?",
        (old_cycle_id,),
    )
    # calcula quem já teve pódio no ciclo antigo (para rodízio no novo)
    podium_users = storage.fetchall("""
        SELECT DISTINCT user_id FROM ranking_podiums WHERE cycle_id = ?
    """, (old_cycle_id,))
    podium_ids = {r["user_id"] for r in podium_users}
    # todos os usuários que pontuaram no ciclo antigo (aprox: nas últimas 4 semanas)
    all_users = storage.fetchall("""
        SELECT DISTINCT user_id FROM ranking_points
        WHERE cycle_id = ?
    """, (old_cycle_id,))
    all_ids = [r["user_id"] for r in all_users]
    # rodízio: quem ainda não teve pódio entra primeiro; quem já teve, depois
    without_podium = [u for u in all_ids if u not in podium_ids]
    with_podium = [u for u in all_ids if u in podium_ids]
    new_participants = without_podium + with_podium
    import json
    storage.execute(
        "INSERT INTO ranking_cycles (cycle_id, started_at, state, participants) VALUES (?, ?, 'active', ?)",
        (new_cycle_id, time.time(), json.dumps(new_participants)),
    )
