"""Modulo ranking - manifest."""

from bot.core.commands import Command

MODULE_ID = "ranking"
VERSION = "1.0.0"
EVENTS_USED = ["message", "edited_message"]

COMMANDS = [
    Command("rank", None, public=True, cooldown_sec=300, description="Top 10 da semana atual"),
    Command("rciclo", None, public=True, cooldown_sec=300, description="Ciclo atual e elegibilidade ao podio"),
    Command("pontos", None, public=True, cooldown_sec=300, description="Sua pontuacao na semana"),
    Command("posicao", None, public=True, cooldown_sec=300, description="Sua posicao e situacao no rodizio"),
    Command("historico", None, public=True, cooldown_sec=300, description="Rodadas e pódios anteriores"),
    Command("regras", None, public=True, cooldown_sec=300, description="Regras vigentes"),
    Command("ajuda", None, public=True, cooldown_sec=300, description="Ajuda de comandos"),
]


def build_manifest() -> "ModuleManifest":
    from bot.core.modules import ModuleManifest
    return ModuleManifest(
        module_id=MODULE_ID,
        version=VERSION,
        commands=COMMANDS,
        events_used=EVENTS_USED,
        config={},
    )
