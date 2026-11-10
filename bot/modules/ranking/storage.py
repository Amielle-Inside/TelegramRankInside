"""Modulo ranking - tabelas especificas no SQLite."""

from __future__ import annotations

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
