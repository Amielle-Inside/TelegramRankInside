#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Entry point do TelegramRankInside."""

from __future__ import annotations

import os
import sys
import time
import json
import threading
import signal
import subprocess
import shutil
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


def _load_snapshot_repo_config(config: dict) -> None:
    global SNAPSHOT_REPO_URL, SNAPSHOT_REPO_BRANCH, SNAPSHOT_REPO_USER, SNAPSHOT_REPO_TOKEN
    SNAPSHOT_REPO_URL = config.get("SNAPSHOT_REPO_URL") or None
    SNAPSHOT_REPO_BRANCH = config.get("SNAPSHOT_REPO_BRANCH", "main") or "main"
    SNAPSHOT_REPO_USER = config.get("SNAPSHOT_REPO_USER") or None
    SNAPSHOT_REPO_TOKEN = config.get("SNAPSHOT_REPO_TOKEN") or None
    if SNAPSHOT_REPO_URL:
        print(f"[snapshot] repo configurado: {SNAPSHOT_REPO_URL} (branch {SNAPSHOT_REPO_BRANCH})")


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


# ------------------------------------------------------------------ #
# Snapshot semanal
# ------------------------------------------------------------------ #
SNAPSHOT_DIR = HERE / "data" / "snapshots"
SNAPSHOT_REPO_DIR = HERE / "data" / "snapshot_repo"
SNAPSHOT_REPO_URL = None  # configurado via env
SNAPSHOT_REPO_BRANCH = "main"
SNAPSHOT_REPO_USER = None
SNAPSHOT_REPO_TOKEN = None


def _gerar_snapshot(app: RankingApp) -> int:
    """Gera snapshot JSON de todos os grupos com pontos na semana atual.
    Retorna quantos snapshots foram gerados."""
    from bot.modules.ranking.storage import week_start_for
    storage = app.storage
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    # lista de grupos com pontos
    chats = storage.fetchall("""
        SELECT DISTINCT chat_id FROM ranking_points
    """)
    ws = week_start_for(int(time.time()), app.config.get("TZ", "America/Sao_Paulo"))
    gerados = 0

    for row in chats:
        chat_id = row["chat_id"]
        # dados do ranking desta semana
        ranking = storage.fetchall("""
            SELECT rp.user_id,
                   SUM(rp.points) as total,
                   MAX(rm.username) as username,
                   MAX(rm.first_name) as first_name
            FROM ranking_points rp
            LEFT JOIN ranking_messages rm ON rm.chat_id = rp.chat_id AND rm.user_id = rp.user_id
            WHERE rp.chat_id = ? AND rp.week_start = ?
            GROUP BY rp.user_id
            ORDER BY total DESC
        """, (chat_id, ws))

        top10 = []
        for r in ranking:
            uid = r["user_id"]
            top10.append({
                "user_id": uid,
                "username": r["username"] or "",
                "first_name": r["first_name"] or "",
                "points": round(r["total"], 2),
            })

        snapshot = {
            "chat_id": chat_id,
            "week_start": ws,
            "generated_at": time.time(),
            "total_participantes": len(top10),
            "total_pontos": round(sum(t["points"] for t in top10), 2),
            "top10": top10,
        }

        file_name = f"snapshot_{chat_id}_{ws}.json"
        file_path = SNAPSHOT_DIR / file_name
        file_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

        # registra no log e tenta upload para repositorio remoto
        uploaded = 0
        upload_error = None
        if SNAPSHOT_REPO_URL:
            ok, err = _upload_snapshot_to_repo(file_path)
            uploaded = 1 if ok else 0
            upload_error = err
            if ok:
                print(f"[snapshot] upload OK: {file_name}")
            else:
                print(f"[snapshot] upload FALHOU: {file_name} -> {err}")

        try:
            with storage.transaction() as c:
                c.execute(
                    "INSERT OR REPLACE INTO snapshot_log (chat_id, week_start, file_name, records, uploaded, uploaded_at, upload_error, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (chat_id, ws, file_name, len(top10), uploaded, time.time() if uploaded else None, upload_error, time.time()),
                )
        except Exception:
            pass

        gerados += 1

    return gerados


def _init_snapshot_repo() -> bool:
    """Inicializa o repositorio local de snapshots se necessario."""
    if not SNAPSHOT_REPO_URL:
        return False
    SNAPSHOT_REPO_DIR.mkdir(parents=True, exist_ok=True)
    git_dir = SNAPSHOT_REPO_DIR / ".git"
    if not git_dir.exists():
        try:
            subprocess.run(["git", "init"], cwd=str(SNAPSHOT_REPO_DIR), check=True,
                           capture_output=True, timeout=30)
            subprocess.run(["git", "remote", "add", "origin", SNAPSHOT_REPO_URL],
                           cwd=str(SNAPSHOT_REPO_DIR), check=True, capture_output=True, timeout=30)
            # configura credenciais via token se disponivel
            if SNAPSHOT_REPO_TOKEN and SNAPSHOT_REPO_USER:
                subprocess.run(["git", "config", "user.name", SNAPSHOT_REPO_USER],
                               cwd=str(SNAPSHOT_REPO_DIR), check=True, capture_output=True)
                subprocess.run(["git", "config", "user.email", f"{SNAPSHOT_REPO_USER}@users.noreply.github.com"],
                               cwd=str(SNAPSHOT_REPO_DIR), check=True, capture_output=True)
            print("[snapshot] repositorio local inicializado")
        except subprocess.CalledProcessError as e:
            print(f"[snapshot] erro ao inicializar repo: {e.stderr.decode() if e.stderr else e}")
            return False
    return True


def _upload_snapshot_to_repo(file_path: Path) -> tuple[bool, str]:
    """Faz commit e push de um arquivo de snapshot para o repositorio remoto.
    Retorna (sucesso, mensagem_erro)."""
    if not SNAPSHOT_REPO_URL:
        return False, "repositorio nao configurado"
    if not _init_snapshot_repo():
        return False, "falha ao inicializar repositorio local"

    try:
        # copia o arquivo para o repo local
        dest = SNAPSHOT_REPO_DIR / file_path.name
        shutil.copy2(str(file_path), str(dest))

        # git add
        subprocess.run(["git", "add", str(dest.name)], cwd=str(SNAPSHOT_REPO_DIR),
                       check=True, capture_output=True, timeout=30)

        # git commit (so se houver mudancas)
        commit_result = subprocess.run(
            ["git", "commit", "-m", f"snapshot: {dest.name}"],
            cwd=str(SNAPSHOT_REPO_DIR), capture_output=True, timeout=30
        )
        # se nao houver mudancas para commit, nao é erro

        # git push com autenticacao via token
        env = os.environ.copy()
        if SNAPSHOT_REPO_TOKEN and SNAPSHOT_REPO_USER:
            # usa https com token embutido na URL para auth
            repo_url = SNAPSHOT_REPO_URL
            if repo_url.startswith("https://"):
                token_url = repo_url.replace("https://", f"https://{SNAPSHOT_REPO_USER}:{SNAPSHOT_REPO_TOKEN}@")
                push_result = subprocess.run(
                    ["git", "push", "origin", f"HEAD:{SNAPSHOT_REPO_BRANCH}"],
                    cwd=str(SNAPSHOT_REPO_DIR), capture_output=True, timeout=60, env=env
                )
                # nao imprime o token em logs
            else:
                push_result = subprocess.run(
                    ["git", "push", "origin", f"HEAD:{SNAPSHOT_REPO_BRANCH}"],
                    cwd=str(SNAPSHOT_REPO_DIR), capture_output=True, timeout=60, env=env
                )
        else:
            push_result = subprocess.run(
                ["git", "push", "origin", f"HEAD:{SNAPSHOT_REPO_BRANCH}"],
                cwd=str(SNAPSHOT_REPO_DIR), capture_output=True, timeout=60, env=env
            )

        if push_result.returncode != 0:
            stderr = push_result.stderr.decode("utf-8", errors="replace")
            # remove possiveis tokens do stderr
            if SNAPSHOT_REPO_TOKEN:
                stderr = stderr.replace(SNAPSHOT_REPO_TOKEN, "[TOKEN]")
            return False, stderr.strip()[:200]

        return True, ""
    except Exception as e:
        return False, str(e)[:200]


def _snapshot_thread(app: RankingApp, stop_event: threading.Event) -> None:
    """Thread de background: gera snapshot semanal toda segunda-feira."""
    print("[snapshot] thread iniciada.")
    ultimo_dia = -1
    while not stop_event.is_set():
        stop_event.wait(300)  # checa a cada 5 min
        try:
            import zoneinfo
            try:
                tz = zoneinfo.ZoneInfo(app.config.get("TZ", "America/Sao_Paulo"))
            except Exception:
                from datetime import timezone, timedelta
                tz = timezone(timedelta(hours=-3))
            agora = time.localtime()
            # segunda-feira = 0
            if agora.tm_wday == 0 and agora.tm_hour == 0 and agora.tm_min < 5:
                if ultimo_dia != agora.tm_yday:
                    n = _gerar_snapshot(app)
                    print(f"[snapshot] semanal gerado: {n} grupos")
                    ultimo_dia = agora.tm_yday
        except Exception as e:
            print(f"[snapshot] erro: {e}")


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
    _load_snapshot_repo_config(config)

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

    # inicia thread de snapshot semanal
    snapshot_stop = threading.Event()
    snapshot_th = threading.Thread(target=_snapshot_thread, args=(app, snapshot_stop), daemon=True)
    snapshot_th.start()

    # sinal para parada limpa
    def handle_sig(signum, frame):
        print(f"[sinal] {signum} recebido, parando...")
        snapshot_stop.set()
        app.stop()
        panel_server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)

    try:
        app.run_loop()
    finally:
        snapshot_stop.set()
        panel_server.shutdown()
        app.stop()


if __name__ == "__main__":
    main()
