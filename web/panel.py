"""Painel web administrativo - interface visual completa, localhost apenas."""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from html import escape

from bot.core.app import RankingApp


# --------------------------------------------------------------------------- #
# Utilitarios de HTML
# --------------------------------------------------------------------------- #
def _page(title: str, body: str, active: str = "", chat_id: int | None = None, chats: list | None = None) -> str:
    chats = chats or []
    selected = chat_id
    seletor = ""
    if chats:
        opts = ""
        for c in chats:
            nome = c.get("title") or c.get("username") or f"Chat {c['id']}"
            members = c.get("member_count", "?")
            sel = " selected" if c["id"] == selected else ""
            opts += f"<option value=\"{c['id']}\"{sel}>{escape(nome)} ({members} membros)</option>"
        seletor = f"""
        <div class="card" style="max-width:700px;margin:0 auto 1rem auto">
          <form method="GET" action="/painel/rankings" style="display:flex;gap:0.5rem;align-items:center">
            <label style="font-size:0.85rem;color:var(--muted);margin:0">Grupo:</label>
            <select name="chat_id" onchange="this.form.submit()" style="flex:1;padding:0.4rem;border:1px solid #334155;border-radius:6px;background:#0f172a;color:var(--text)">{opts}</select>
            <noscript><button class="btn primary" type="submit">Ir</button></noscript>
          </form>
          <p class="small">Selecione o grupo para ver seu ranking, participantes e exportações.</p>
        </div>"""
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)} - TelegramRankInside</title>
<style>
  :root{{--bg:#0f172a;--card:#1e293b;--accent:#38bdf8;--text:#e2e8f0;--muted:#94a3b8;--danger:#f87171;--ok:#4ade80;}}
  *{{box-sizing:border-box}}
  body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--text);margin:0}}
  .topbar{{background:var(--card);padding:0.75rem 1.5rem;display:flex;align-items:center;gap:1rem;border-bottom:1px solid #334155}}
  .topbar h1{{font-size:1rem;margin:0;color:var(--accent)}}
  .topbar a{{color:var(--accent);text-decoration:none;margin-left:auto;padding:0.4rem 0.8rem;border:1px solid var(--accent);border-radius:6px;font-size:0.85rem}}
  .topbar a:hover{{background:var(--accent);color:#0f172a}}
  .nav{{display:flex;gap:0.25rem;padding:0.5rem 1.5rem;overflow-x:auto;border-bottom:1px solid #334155}}
  .nav a{{padding:0.5rem 0.9rem;border-radius:6px;color:var(--muted);text-decoration:none;font-size:0.85rem;white-space:nowrap}}
  .nav a:hover{{background:#334155;color:var(--text)}}
  .nav a.active{{background:var(--accent);color:#0f172a}}
  .container{{padding:1rem;max-width:1200px}}
  .card{{background:var(--card);border-radius:8px;padding:1rem;margin-bottom:1rem;border:1px solid #334155}}
  .card h2{{font-size:1rem;margin:0 0 0.75rem;color:var(--accent);border-bottom:1px solid #334155;padding-bottom:0.4rem}}
  table{{width:100%;border-collapse:collapse;font-size:0.85rem}}
  th,td{{text-align:left;padding:0.5rem;border-bottom:1px solid #334155}}
  th{{color:var(--muted);font-size:0.75rem;text-transform:uppercase}}
  tr:hover td{{background:#334155}}
  .badge{{display:inline-block;padding:0.1rem 0.5rem;border-radius:4px;font-size:0.75rem;background:#334155;color:var(--muted)}}
  .badge.ok{{background:var(--ok);color:#0f172a}}
  .badge.warn{{background:#fbbf24;color:#0f172a}}
  .badge.danger{{background:var(--danger);color:#0f172a}}
  .btn{{padding:0.4rem 0.8rem;border:1px solid var(--accent);background:transparent;color:var(--accent);border-radius:6px;cursor:pointer;font-size:0.85rem}}
  .btn:hover{{background:var(--accent);color:#0f172a}}
  .btn.danger{{border-color:var(--danger);color:var(--danger)}}
  .btn.danger:hover{{background:var(--danger);color:#fff}}
  .btn.primary{{background:var(--accent);color:#0f172a}}
  input,select{{padding:0.4rem;border:1px solid #334155;border-radius:6px;background:#0f172a;color:var(--text);font-size:0.85rem}}
  .form-group{{margin-bottom:0.75rem}}
  .form-group label{{display:block;font-size:0.8rem;color:var(--muted);margin-bottom:0.25rem}}
  .grid2{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem}}
  .stat{{background:var(--card);border-radius:8px;padding:1rem;border:1px solid #334155}}
  .stat .v{{font-size:1.5rem;font-weight:bold;color:var(--accent)}}
  .stat .l{{font-size:0.75rem;color:var(--muted)}}
  .alert{{padding:0.75rem;border-radius:6px;margin-bottom:1rem;font-size:0.85rem}}
  .alert.error{{background:#7f1d1d;border:1px solid #991b1b;color:#fecaca}}
  .alert.ok{{background:#14532d;border:1px solid #16a34a;color:#bbf7d0}}
  .alert.info{{background:#1e3a5f;border:1px solid #1d4ed8;color:#bfdbfe}}
  .small{{font-size:0.8rem;color:var(--muted)}}
  .mono{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:0.8rem}}
  .masked{{color:var(--muted)}}
  .tabs{{display:flex;gap:0.5rem;margin-bottom:1rem}}
  .tabs a{{padding:0.5rem 1rem;border:1px solid #334155;border-radius:6px;text-decoration:none;color:var(--muted);font-size:0.85rem}}
  .tabs a.active{{background:var(--accent);color:#0f172a;border-color:var(--accent)}}
  .pagination{{display:flex;gap:0.25rem;justify-content:center;margin-top:0.75rem}}
  .pagination a{{padding:0.25rem 0.6rem;border:1px solid #334155;border-radius:4px;text-decoration:none;color:var(--accent);font-size:0.8rem}}
  .pagination a.active{{background:var(--accent);color:#0f172a}}
</style>
</head>
<body>
  <div class="topbar">
    <div><strong>TelegramRankInside</strong></div>
    <div style="margin-left:auto;display:flex;align-items:center;gap:0.5rem">
      <span class="badge small">localhost</span>
      <a href="/painel/sair">Sair</a>
    </div>
  </div>
  {seletor}
  <div class="nav">
    <a href="/painel/" class="{'active' if active=='overview' else ''}">Visão geral</a>
    <a href="/painel/rankings" class="{'active' if active=='rankings' else ''}">Rankings</a>
    <a href="/painel/ciclos" class="{'active' if active=='ciclos' else ''}">Ciclos e rodadas</a>
    <a href="/painel/participantes" class="{'active' if active=='participantes' else ''}">Participantes</a>
    <a href="/painel/regras" class="{'active' if active=='regras' else ''}">Pontuação e regras</a>
    <a href="/painel/comandos" class="{'active' if active=='comandos' else ''}">Comandos e cooldowns</a>
    <a href="/painel/modulos" class="{'active' if active=='modulos' else ''}">Módulos</a>
    <a href="/painel/operacao" class="{'active' if active=='operacao' else ''}">Operação e diagnósticos</a>
    <a href="/painel/exportar" class="{'active' if active=='exportar' else ''}">Backups e exportações</a>
    <a href="/painel/auditoria" class="{'active' if active=='auditoria' else ''}">Auditoria</a>
    <a href="/painel/config" class="{'active' if active=='config' else ''}">Configurações e acesso</a>
  </div>
  <div class="container">
    {body}
  </div>
</body>
</html>"""


def _alert(kind: str, msg: str) -> str:
    return f'<div class="alert {kind}">{escape(msg)}</div>'


def _table(headers: list, rows: list, page: int = 1, per_page: int = 20, total: int = 0) -> str:
    start = (page - 1) * per_page
    page_rows = rows[start:start + per_page]
    thead = "".join(f"<th>{escape(h)}</th>" for h in headers)
    tbody = ""
    for r in page_rows:
        tbody += "<tr>" + "".join(f"<td>{escape(str(c)) if c is not None else '-'}</td>" for c in r) + "</tr>"
    pages = max(1, (total + per_page - 1) // per_page)
    pag = ""
    if pages > 1:
        for p in range(1, pages + 1):
            cls = ' class="active"' if p == page else ""
            pag += f'<a href="?p={p}"{cls}>{p}</a>'
    return f'<table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table>' + (f'<div class="pagination">{pag}</div>' if pag else "")


# --------------------------------------------------------------------------- #
# Handler
# --------------------------------------------------------------------------- #
class PanelHandler(BaseHTTPRequestHandler):
    app: RankingApp = None

    # Cache de grupos conhecidos (TTL 5 min) para nao chamar API do Telegram a cada carregamento
    _chats_cache: list = []
    _chats_cache_ts: float = 0
    _chats_ttl: float = 300

    def log_message(self, format, *args):  # noqa: A002
        return

    # ---------------- sessao / auth ---------------- #
    def _current_user(self) -> str | None:
        cookie = self.headers.get("Cookie", "")
        token = None
        for part in cookie.split(";"):
            part = part.strip()
            if part.startswith("session="):
                token = part[8:]
                break
        if not token:
            return None
        row = self.app.storage.fetchone(
            "SELECT username, expires_at FROM web_sessions WHERE token = ?",
            (token,),
        )
        if row is None:
            return None
        if time.time() > float(row["expires_at"]):
            return None
        return row["username"]

    def _require_auth(self) -> bool:
        return self._current_user() is not None

    def _csrf_token(self) -> str | None:
        user = self._current_user()
        if not user:
            return None
        tok = secrets.token_urlsafe(24)
        now = time.time()
        with self.app.storage.transaction() as c:
            c.execute(
                "INSERT OR REPLACE INTO web_csrf_tokens (token, username, created_at, expires_at, used) VALUES (?, ?, ?, ?, 0)",
                (tok, user, now, now + 900),
            )
        return tok

    def _verify_csrf(self, token: str) -> bool:
        row = self.app.storage.fetchone(
            "SELECT used, expires_at FROM web_csrf_tokens WHERE token = ?",
            (token,),
        )
        if row is None:
            return False
        if row["used"] == 1:
            return False
        if time.time() > float(row["expires_at"]):
            return False
        with self.app.storage.transaction() as c:
            c.execute("UPDATE web_csrf_tokens SET used = 1 WHERE token = ?", (token,))
        return True

    def _known_chats(self) -> list:
        """Lista grupos conhecidos pelo banco (updates_received) enriquecidos com dados do Telegram."""
        import json, time
        now = time.time()
        # retorna cache se ainda valido
        if now - self._chats_cache_ts < self._chats_ttl and self._chats_cache:
            return self._chats_cache

        rows = self.app.storage.fetchall("""
            SELECT payload FROM updates_received
            WHERE type = 'message'
            ORDER BY received_at DESC
        """)
        seen = {}
        for r in rows:
            try:
                payload = json.loads(r["payload"])
                msg = payload.get("message") or payload.get("edited_message") or {}
                chat = msg.get("chat", {})
                cid = chat.get("id")
                if not cid or cid in seen:
                    continue
                seen[cid] = {
                    "id": cid,
                    "title": chat.get("title") or chat.get("username") or f"Chat {cid}",
                    "member_count": "?",
                }
            except Exception:
                continue

        chats = []
        for cid, info in seen.items():
            try:
                chat_resp = self.app.telegram.get_chat(cid)
                if chat_resp and chat_resp.get("ok"):
                    res = chat_resp["result"]
                    info["title"] = res.get("title") or res.get("username") or f"Chat {cid}"
            except Exception:
                pass
            try:
                mc = self.app.telegram.get_chat_member_count(cid)
                if mc and mc.get("ok"):
                    result = mc["result"]
                    info["member_count"] = result if isinstance(result, int) else result.get("member_count", "?")
            except Exception:
                pass
            chats.append(info)

        chats.sort(key=lambda c: c["id"])
        self._chats_cache = chats
        self._chats_cache_ts = now
        return chats

    def _send_html(self, code: int, html: str) -> None:
        body = html.encode("utf-8")
        try:
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send_json(self, code: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, path: str) -> None:
        self.send_response(302)
        self.send_header("Location", path)
        self.end_headers()

    # ---------------- rotas ---------------- #
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        qs = parse_qs(parsed.query)

        # login / logout (sem auth)
        if path == "/painel/login":
            if self._require_auth():
                self._redirect("/painel/")
                return
            self._send_html(200, _page("Login", self._login_html()))
            return
        if path == "/painel/sair":
            self._redirect("/painel/login")
            return

        if not self._require_auth():
            self._redirect("/painel/login")
            return

        user = self._current_user()
        is_owner = self.app.permissions.is_owner(
            int(user) if user and user.isdigit() else -1
        ) if user and user.isdigit() else False

        # extrai chat_id selecionado e lista de grupos conhecidos
        sel_chat_id = None
        if "chat_id" in qs:
            try:
                sel_chat_id = int(qs["chat_id"][0])
            except (ValueError, TypeError):
                sel_chat_id = None
        chats = self._known_chats()

        if path == "/painel/":
            self._send_html(200, _page("Visão geral", self._overview_html(), "overview", sel_chat_id, chats))
        elif path == "/painel/rankings":
            self._send_html(200, _page("Rankings", self._rankings_html(qs), "rankings", sel_chat_id, chats))
        elif path == "/painel/ciclos":
            self._send_html(200, _page("Ciclos e rodadas", self._ciclos_html(qs), "ciclos", sel_chat_id, chats))
        elif path == "/painel/participantes":
            self._send_html(200, _page("Participantes", self._participantes_html(qs), "participantes", sel_chat_id, chats))
        elif path == "/painel/regras":
            self._send_html(200, _page("Pontuação e regras", self._regras_html(), "regras", sel_chat_id, chats))
        elif path == "/painel/comandos":
            self._send_html(200, _page("Comandos e cooldowns", self._comandos_html(), "comandos", sel_chat_id, chats))
        elif path == "/painel/modulos":
            self._send_html(200, _page("Módulos", self._modulos_html(), "modulos", sel_chat_id, chats))
        elif path == "/painel/operacao":
            self._send_html(200, _page("Operação e diagnósticos", self._operacao_html(), "operacao", sel_chat_id, chats))
        elif path == "/painel/exportar":
            self._send_html(200, _page("Backups e exportações", self._exportar_html(qs), "exportar", sel_chat_id, chats))
        elif path == "/painel/auditoria":
            self._send_html(200, _page("Auditoria", self._auditoria_html(qs), "auditoria", sel_chat_id, chats))
        elif path == "/painel/config":
            self._send_html(200, _page("Configurações e acesso", self._config_html(qs, is_owner), "config", sel_chat_id, chats))
        else:
            self._send_html(404, _page("Não encontrado", "<p>Página não encontrada.</p>", chats=chats))

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        qs = parse_qs(parsed.query)

        if path == "/painel/login":
            self._handle_login()
            return

        if not self._require_auth():
            self._send_json(401, {"error": "não autenticado"})
            return

        # ler o body uma vez para reutilizar
        length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(length).decode("utf-8")
        body_params = parse_qs(body_raw)

        # CSRF pode vir na query string ou no body
        csrf = qs.get("csrf", [""])[0] or body_params.get("csrf", [""])[0] or ""
        if not self._verify_csrf(csrf):
            self._send_html(403, _page("CSRF inválido", _alert("error", "Token CSRF inválido ou expirado.")))
            return

        user = self._current_user()
        is_owner = self.app.permissions.is_owner(
            int(user) if user and user.isdigit() else -1
        ) if user and user.isdigit() else False

        if path == "/painel/config/salvar":
            self._config_salvar(body_params, is_owner)
        elif path == "/painel/config/resetar":
            self._config_resetar(body_params, is_owner)
        elif path == "/painel/exportar/gerar":
            self._exportar_gerar(body_params)
        elif path == "/painel/sessao/encerrar":
            self._sessao_encerrar(qs)
        else:
            self._send_json(404, {"error": "não encontrado"})

    # ---------------- login ---------------- #
    def _login_html(self) -> str:
        csrf = self._csrf_token() or ""
        return f"""
        <div class="card" style="max-width:380px;margin:2rem auto">
          <h2 style="margin-top:0">Entrar no painel</h2>
          <form method="POST" action="/painel/login">
            <input type="hidden" name="csrf" value="{escape(csrf)}">
            <div class="form-group">
              <label>Usuário</label>
              <input name="usuario" type="text" required autofocus>
            </div>
            <div class="form-group">
              <label>Senha</label>
              <input name="senha" type="password" required>
            </div>
            <button class="btn primary" type="submit">Entrar</button>
          </form>
          <p class="small">Acesso restrito a 127.0.0.1</p>
        </div>"""

    def _handle_login(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        params = parse_qs(body)
        usuario = params.get("usuario", [""])[0]
        senha = params.get("senha", [""])[0]

        row = self.app.storage.fetchone(
            "SELECT password_hash FROM web_users WHERE username = ?",
            (usuario,),
        )
        if not row:
            self._send_html(401, _page("Login", _alert("error", "Usuário ou senha inválidos") + self._login_html()))
            return
        pw_hash = hashlib.sha256(senha.encode("utf-8")).hexdigest()
        if pw_hash != row["password_hash"]:
            self._send_html(401, _page("Login", _alert("error", "Usuário ou senha inválidos") + self._login_html()))
            return

        token = secrets.token_urlsafe(32)
        now = time.time()
        with self.app.storage.transaction() as c:
            c.execute(
                "INSERT OR REPLACE INTO web_sessions (token, username, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (token, usuario, now, now + 3600),
            )
        self.send_response(302)
        self.send_header("Location", "/painel/")
        self.send_header(
            "Set-Cookie",
            f"session={token}; Path=/painel; HttpOnly; SameSite=Lax; Max-Age=3600",
        )
        self.end_headers()

    # ---------------- paginas ---------------- #
    def _overview_html(self) -> str:
        storage = self.app.storage
        total_msgs = storage.fetchone("SELECT COUNT(*) as c FROM ranking_messages")["c"]
        total_pts = storage.fetchone("SELECT COUNT(*) as c FROM ranking_points")["c"]
        rounds = storage.fetchall("SELECT week_start, state FROM ranking_rounds ORDER BY week_start DESC LIMIT 5")
        rounds_html = "".join(
            f"<tr><td>{r['week_start']}</td><td><span class='badge {'ok' if r['state']=='closed' else 'warn'}'>{r['state']}</span></td></tr>"
            for r in rounds
        )
        return f"""
        <div class="grid2">
          <div class="stat"><div class="v">{total_msgs}</div><div class="l">Mensagens armazenadas</div></div>
          <div class="stat"><div class="v">{total_pts}</div><div class="l">Lançamentos de pontos</div></div>
          <div class="stat"><div class="v badge ok">Online</div><div class="l">Bot em execução</div></div>
          <div class="stat"><div class="v">http://127.0.0.1:{self.app.config.get('WEB_PORT',2020)}/painel/</div><div class="l">Painel (localhost)</div></div>
        </div>
        <div class="card">
          <h2>Últimas rodadas</h2>
          <table>
            <thead><tr><th>Semana</th><th>Estado</th></tr></thead>
            <tbody>{rounds_html or '<tr><td colspan="2">Sem rodadas ainda.</td></tr>'}</tbody>
          </table>
        </div>
        <div class="card">
          <h2>Grupo monitorado</h2>
          <p>NewsInside Chat — <code>-1002267119439</code></p>
          <p class="small">O painel exibe dados deste grupo. Outros grupos podem ser adicionados pelo bot.</p>
        </div>"""

    def _rankings_html(self, qs) -> str:
        chat_id = int(qs.get("chat_id", ["-1002267119439"])[0])
        from bot.modules.ranking.storage import week_start_for
        ws = week_start_for(int(time.time()), self.app.config.get("TZ", "America/Sao_Paulo"))
        rows = self.app.storage.fetchall("""
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
        data = [[r["user_id"], round(r["total"], 2), r["username"], r["first_name"]] for r in rows]

        # Podio visual (top 3)
        podium_html = ""
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        if data:
            podium_items = []
            for i in range(min(3, len(data))):
                pos = i + 1
                medal = medals.get(pos, str(pos))
                uid, pts, uname, fname = data[i]
                nome = f"@{uname}" if uname else (fname or f"Usuário {uid}")
                podium_items.append(
                    f"<div style='display:flex;align-items:center;gap:0.75rem;padding:0.75rem;border-radius:8px;"
                    f"background:#334155;margin-bottom:0.5rem;border:1px solid #475569;'>"
                    f"<span style='font-size:1.5rem'>{medal}</span>"
                    f"<div><strong>#{pos}</strong> — <code>{nome}</code> (ID {uid})</div>"
                    f"<div style='margin-left:auto;color:#38bdf8;font-weight:bold'>{pts} pts</div>"
                    f"</div>"
                )
            podium_html = f"""
            <div class="card">
              <h2>Prévia do pódio semanal — {ws}</h2>
              <div style="display:flex;gap:0.5rem;flex-wrap:wrap">{''.join(podium_items)}</div>
            </div>"""

        return f"""
        {podium_html}
        <div class="card">
          <h2>Top 10 — Semana {ws}</h2>
          {_table(["Posição", "Usuário", "ID", "Pontos"], [[i+1, f"@{r[2]}" if r[2] else (r[3] or f'Usuário {r[0]}'), r[0], r[1]] for i, r in enumerate(data[:10])], total=len(data))}
          <p class="small">{len(data)} participante(s) pontuou(ram) nesta semana.</p>
        </div>"""

    def _ciclos_html(self, qs) -> str:
        rows = self.app.storage.fetchall("SELECT * FROM ranking_cycles ORDER BY started_at DESC LIMIT 10")
        data = [[r["cycle_id"], r["started_at"], r["state"], r["participants"]] for r in rows]
        return f"""
        <div class="card">
          <h2>Ciclos de pódio</h2>
          {_table(["ID do ciclo", "Início", "Estado", "Participantes (JSON)"], data, total=len(data))}
        </div>"""

    def _participantes_html(self, qs) -> str:
        chat_id = int(qs.get("chat_id", ["-1002267119439"])[0])
        rows = self.app.storage.fetchall("""
            SELECT user_id, COUNT(*) as msgs, SUM(points) as total
            FROM ranking_points
            WHERE chat_id = ?
            GROUP BY user_id
            ORDER BY total DESC
        """, (chat_id,))
        data = [[r["user_id"], r["msgs"], round(r["total"], 2)] for r in rows]
        return f"""
        <div class="card">
          <h2>Participantes — grupo {chat_id}</h2>
          {_table(["Usuário (ID)", "Mensagens pontuadas", "Pontos totais"], data, total=len(data))}
        </div>"""

    def _regras_html(self) -> str:
        return """
        <div class="card">
          <h2>Regras de pontuação (semanal)</h2>
          <ul>
            <li>Texto próprio: +0,7</li>
            <li>Resposta a outra pessoa: +1,1</li>
            <li>3 mensagens consecutivas de texto: +0,9 total</li>
            <li>4ª mensagem consecutiva: −0,1</li>
            <li>Vídeo com explicação própria: +0,7</li>
            <li>Link sem comentário: −0,3</li>
            <li>3 encaminhamentos consecutivos: −0,6</li>
            <li>Mensagem idêntica repetida em ≤10 min: sem pontos positivos</li>
          </ul>
          <p class="small">A pontuação reinicia toda semana (segunda-feira, 00:00, America/Sao_Paulo).</p>
        </div>"""

    def _comandos_html(self) -> str:
        return """
        <div class="card">
          <h2>Comandos públicos</h2>
          <table>
            <thead><tr><th>Comando</th><th>Descrição</th><th>Cooldown</th></tr></thead>
            <tbody>
              <tr><td>!rank</td><td>Top 10 da semana</td><td>5 min</td></tr>
              <tr><td>!rciclo</td><td>Ciclo atual e elegibilidade ao pódio</td><td>5 min</td></tr>
              <tr><td>!pontos</td><td>Sua pontuação</td><td>5 min</td></tr>
              <tr><td>!posicao</td><td>Sua posição no rodízio</td><td>5 min</td></tr>
              <tr><td>!historico</td><td>Rodadas anteriores</td><td>5 min</td></tr>
              <tr><td>!regras</td><td>Regras de pontuação</td><td>5 min</td></tr>
              <tr><td>!ajuda</td><td>Lista de comandos</td><td>5 min</td></tr>
            </tbody>
          </table>
        </div>
        <div class="card">
          <h2>Comandos administrativos (owner/admin)</h2>
          <table>
            <thead><tr><th>Comando</th><th>Permissão</th><th>Descrição</th></tr></thead>
            <tbody>
              <tr><td>!status</td><td>Admin / Owner</td><td>Saúde, sincronização, fila</td></tr>
              <tr><td>!check</td><td>Admin / Owner</td><td>Auditoria e recontagem</td></tr>
              <tr><td>!stop</td><td>Owner</td><td>Parar o bot</td></tr>
              <tr><td>!reboot</td><td>Owner</td><td>Reiniciar o bot</td></tr>
              <tr><td>!web</td><td>Owner</td><td>Info de acesso ao painel (privado)</td></tr>
            </tbody>
          </table>
        </div>"""

    def _modulos_html(self) -> str:
        mods = self.app.modules.list_enabled()
        rows = [[m.module_id, m.version, "Ativo" if m.enabled else "Inativo", ", ".join(c.name for c in m.commands)] for m in mods]
        return f"""
        <div class="card">
          <h2>Módulos instalados</h2>
          {_table(["ID", "Versão", "Estado", "Comandos"], rows, total=len(rows))}
        </div>"""

    def _operacao_html(self) -> str:
        storage = self.app.storage
        hb = storage.fetchone("SELECT MAX(ts) as ts FROM heartbeat")
        return f"""
        <div class="card">
          <h2>Saúde do bot</h2>
          <p>Processo: <span class="badge ok">Rodando</span></p>
          <p>Último heartbeat: {hb['ts'] if hb else '—'}</p>
          <p>Painel: <code>http://127.0.0.1:{self.app.config.get('WEB_PORT',2020)}/painel/</code></p>
        </div>
        <div class="card">
          <h2>Diagnósticos</h2>
          <p class="small">Use <code>!status</code> no grupo (privado ao admin) ou acesse <code>/painel/operacao</code> para detalhes.</p>
        </div>"""

    def _exportar_html(self, qs) -> str:
        json_dir = Path(self.app.config.get("JSON_DIR", "data/json"))
        files = []
        if json_dir.exists():
            for f in sorted(json_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
                files.append([f.name, f"{f.stat().st_size} bytes", time.ctime(f.stat().st_mtime)])
        return f"""
        <div class="card">
          <h2>Exportações JSON</h2>
          {_table(["Arquivo", "Tamanho", "Gerado em"], files, total=len(files)) if files else '<p class="small">Nenhuma exportação ainda.</p>'}
          <form method="POST" action="/painel/exportar/gerar" style="margin-top:1rem">
            <input type="hidden" name="csrf" value="{escape(self._csrf_token() or '')}">
            <div class="form-group">
              <label>Chat ID</label>
              <input name="chat_id" type="text" value="{qs.get('chat_id', ['-1002267119439'])[0]}" required>
            </div>
            <button class="btn primary" type="submit">Gerar snapshot desta semana</button>
          </form>
        </div>"""

    def _auditoria_html(self, qs) -> str:
        rows = self.app.storage.fetchall("SELECT id, actor_id, action, params, result, created_at FROM audit_log ORDER BY created_at DESC LIMIT 50")
        data = [[r["id"], r["actor_id"], r["action"], r["params"] or "", r["result"] or "", r["created_at"]] for r in rows]
        return f"""
        <div class="card">
          <h2>Log de auditoria</h2>
          {_table(["ID", "Ator (ID)", "Ação", "Parâmetros", "Resultado", "Em"], data, total=len(data))}
        </div>"""

    def _config_html(self, qs, is_owner: bool) -> str:
        storage = self.app.storage
        rows = storage.fetchall("SELECT key, value, scope, version FROM web_config ORDER BY key")
        data = [[r["key"], r["value"], r["scope"], r["version"]] for r in rows]
        csrf = self._csrf_token() or ""
        owner_disabled = "" if is_owner else "disabled"
        return f"""
        <div class="card">
          <h2>Configurações operacionais</h2>
          <p class="small">Alterações são validadas e auditadas. Algumas exigem reinicialização.</p>
          {_table(["Chave", "Valor", "Escopo", "Versão"], data, total=len(data))}
        </div>
        <div class="card">
          <h2>Editar configuração</h2>
          <form method="POST" action="/painel/config/salvar">
            <input type="hidden" name="csrf" value="{escape(csrf)}">
            <div class="form-group">
              <label>Chave</label>
              <input name="key" type="text" required>
            </div>
            <div class="form-group">
              <label>Valor</label>
              <input name="value" type="text" required>
            </div>
            <div class="form-group">
              <label>Escopo</label>
              <select name="scope"><option>global</option><option>chat</option></select>
            </div>
            <button class="btn primary" type="submit" {owner_disabled}>Salvar</button>
          </form>
          {_alert("info", "Somente o owner pode alterar configurações.") if not is_owner else ""}
        </div>"""

    # ---------------- ações ---------------- #
    def _exportar_gerar(self, qs) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        params = parse_qs(body)
        chat_id = int(params.get("chat_id", [0])[0])
        from bot.modules.ranking.storage import week_start_for
        ws = week_start_for(int(time.time()), self.app.config.get("TZ", "America/Sao_Paulo"))
        from bot.modules.ranking.commands import _top10
        top = _top10(self.app.storage, chat_id, ws)
        import json as _json
        json_dir = Path(self.app.config.get("JSON_DIR", "data/json"))
        json_dir.mkdir(parents=True, exist_ok=True)
        snapshot = {
            "schema_version": 1,
            "rules_version": "1.0.0",
            "generated_at": time.time(),
            "week_start": ws,
            "chat_id": chat_id,
            "top10": top,
        }
        tmp = json_dir / f"snapshot_{chat_id}_{ws}.json.tmp"
        final = json_dir / f"snapshot_{chat_id}_{ws}.json"
        tmp.write_text(_json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(final)
        self._redirect("/painel/exportar")

    def _sessao_encerrar(self, qs) -> None:
        self.send_response(302)
        self.send_header("Location", "/painel/login")
        self.send_header("Set-Cookie", "session=; Path=/painel; Max-Age=0")
        self.end_headers()

    def _config_salvar(self, qs, is_owner: bool) -> None:
        if not is_owner:
            self._send_html(403, _page("Sem permissão", _alert("error", "Apenas o owner pode alterar configurações.")))
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        params = parse_qs(body)
        key = params.get("key", [""])[0]
        value = params.get("value", [""])[0]
        scope = params.get("scope", ["global"])[0]
        with self.app.storage.transaction() as c:
            c.execute(
                "INSERT OR REPLACE INTO web_config (key, value, scope, updated_by, updated_at, version) VALUES (?, ?, ?, ?, ?, 1)",
                (key, value, scope, int(self._current_user()) if self._current_user() and self._current_user().isdigit() else None, time.time()),
            )
        self._redirect("/painel/config")

    def _config_resetar(self, qs, is_owner: bool) -> None:
        self._redirect("/painel/config")


def start_panel(app: RankingApp, host: str, port: int, secret: str) -> ThreadingHTTPServer:
    PanelHandler.app = app
    last_err = None
    for p in range(port, port + 20):
        try:
            server = ThreadingHTTPServer((host, p), PanelHandler)
            print(f"[web] painel administrativo em http://{host}:{p}/painel/ (somente localhost)")
            return server
        except OSError as e:
            last_err = e
            continue
    raise last_err
