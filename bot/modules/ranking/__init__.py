"""Modulo ranking - inicializacao e registro."""

from __future__ import annotations

from bot.core.modules import ModuleManifest
from bot.core.commands import Command
from bot.modules.ranking import manifest as _manifest
from bot.modules.ranking.handlers import RankingHandler
from bot.modules.ranking import commands as _commands


def create_handler(app, storage, tz_name="America/Sao_Paulo") -> RankingHandler:
    return RankingHandler(app, storage, tz_name)


def register_commands(app: RankingApp, handler: RankingHandler) -> None:
    """Conecta os comandos declarados aos handlers reais."""
    cmd_map = {
        "rank": _commands.cmd_rank,
        "rciclo": _commands.cmd_rciclo,
        "pontos": _commands.cmd_pontos,
        "posicao": _commands.cmd_posicao,
        "historico": _commands.cmd_historico,
        "regras": _commands.cmd_regras,
        "ajuda": _commands.cmd_ajuda,
        "status": _commands.cmd_status,
        "check": _commands.cmd_check,
        "stop": _commands.cmd_stop,
        "reboot": _commands.cmd_reboot,
    }

    for cmd in _manifest.COMMANDS:
        cmd.handler = cmd_map.get(cmd.name)
        app.commands.register(cmd)

    # Comandos administrativos adicionais (nao estao em manifest publico)
    admin_cmds = [
        Command("status", _commands.cmd_status, admin_only=True, public=False, description="Status do bot"),
        Command("check", _commands.cmd_check, admin_only=True, public=False, description="Auditoria/recontagem"),
        Command("stop", _commands.cmd_stop, owner_only=True, public=False, description="Parar o bot"),
        Command("reboot", _commands.cmd_reboot, owner_only=True, public=False, description="Reiniciar o bot"),
    ]
    for cmd in admin_cmds:
        app.commands.register(cmd)


def on_enable(app: RankingApp, storage, handler: RankingHandler) -> None:
    """Chamado quando o modulo eh habilitado."""
    app.ranking_handler = handler


def on_disable(app: RankingApp) -> None:
    """Chamado quando o modulo eh desabilitado."""
    pass
