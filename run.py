#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Entry point do TelegramRankInside."""

from __future__ import annotations

import os
import sys
import time
import threading
import signal
from pathlib import Path

# garante que o pacote bot seja importavel
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from bot.core.app import RankingApp
from bot.modules.ranking import create_handler, register_commands, on_enable, manifest as ranking_manifest
from web.panel import start_panel


def load_env(path: Path) -> dict:
    env = {}
    if not path.exists():
        print(f"[config] .env nao encontrado: {path}")
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def _ensure_web_user(storage: Storage, config: dict) -> None:
    """Garante usuario web no banco sincronizado com o .env."""
    import hashlib
    user = config.get("WEB_USER", "admin")
    pwd = config.get("WEB_PASSWORD", "change_me")
    pw_hash = hashlib.sha256(pwd.encode("utf-8")).hexdigest()
    with storage.transaction() as c:
        c.execute(
            "INSERT OR REPLACE INTO web_users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (user, pw_hash, time.time()),
        )
    print(f"[web] usuario '{user}' sincronizado no banco.")


def main() -> None:
    env_path = HERE / "config" / "config.env"
    config = load_env(env_path)

    token = config.get("TELEGRAM_BOT_TOKEN", "")
    if not token or token == "SEU_TOKEN_AQUI":
        print("[ERRO] TELEGRAM_BOT_TOKEN nao configurado em config/config.env")
        sys.exit(1)

    app = RankingApp(config)

    # Conecta storage ANTES de criar tabelas/modulos
    app.start()

    # Garante usuario web default no banco (senha armazenada em hash simples)
    _ensure_web_user(app.storage, config)

    # registra modulo ranking
    man = ranking_manifest.build_manifest()
    app.modules.register(man)
    handler = create_handler(app, app.storage, config.get("TZ", "America/Sao_Paulo"))
    register_commands(app, handler)
    on_enable(app, app.storage, handler)

    # inicia painel web (localhost apenas)
    web_host = config.get("WEB_HOST", "127.0.0.1")
    web_port = int(config.get("WEB_PORT", "2020"))
    web_secret = config.get("WEB_SECRET", "change_me")
    panel_server = start_panel(app, web_host, web_port, secret=web_secret)
    panel_thread = threading.Thread(target=panel_server.serve_forever, daemon=True)
    panel_thread.start()

    # sinal para parada limpa
    def handle_sig(signum, frame):
        print(f"[sinal] {signum} recebido, parando...")
        app.stop()
        panel_server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)

    try:
        app.run_loop()
    finally:
        panel_server.shutdown()
        app.stop()


if __name__ == "__main__":
    main()
