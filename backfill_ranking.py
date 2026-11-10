#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backfill: reprocessa updates ja recebidos do Telegram e pontua no ranking."""

from __future__ import annotations

import sys
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from bot.core.app import RankingApp
from bot.modules.ranking import create_handler, manifest as ranking_manifest


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


def main() -> None:
    env_path = HERE / "config" / "config.env"
    config = load_env(env_path)

    app = RankingApp(config)
    app.start()

    man = ranking_manifest.build_manifest()
    app.modules.register(man)
    handler = create_handler(app, app.storage, config.get("TZ", "America/Sao_Paulo"))

    # Busca updates ja recebidos (processados ou nao), nao-comandos, ordem cronologica
    rows = app.storage.fetchall("""
        SELECT update_id, payload, processed, received_at
        FROM updates_received
        WHERE type = 'message'
        ORDER BY received_at ASC
    """)

    total = len(rows)
    comandos = 0
    processadas = 0
    pontuadas = 0
    erros = 0

    print(f"Encontradas {total} mensagens de updates para reprocessar.\n")

    for r in rows:
        payload = json.loads(r["payload"])
        msg = payload.get("message") or payload.get("edited_message")
        if not msg:
            continue

        text = msg.get("text", "")
        if text.startswith("!"):
            comandos += 1
            continue

        chat = msg.get("chat", {})
        chat_id = chat.get("id")

        try:
            handler.handle_message(msg, chat_id)
            processadas += 1
            pts = msg.get("text", "")[:40]
            print(f"  [{processadas}/{total}] update_id={r['update_id']} chat={chat_id} user={msg.get('from',{}).get('id')} texto='{pts}'")
        except Exception as e:
            erros += 1
            print(f"  ERRO update_id={r['update_id']}: {e}")

    print(f"\n=== Resumo ===")
    print(f"Total de mensagens de updates: {total}")
    print(f"Comandos ignorados: {comandos}")
    print(f"Mensagens processadas: {processadas}")
    print(f"Erros: {erros}")

    # Estatisticas finais
    total_msgs = app.storage.fetchone("SELECT COUNT(*) as c FROM ranking_messages")["c"]
    total_pts = app.storage.fetchone("SELECT COUNT(*) as c FROM ranking_points")["c"]
    print(f"\nMensagens no banco: {total_msgs}")
    print(f"Lancamentos de pontos: {total_pts}")

    app.stop()


if __name__ == "__main__":
    main()
