"""Nucleo - registro e dispatch de comandos."""

from __future__ import annotations

import re
from typing import Callable, Optional

COMMAND_RE = re.compile(r"^!([a-zA-Z0-9_]+)(?:\s+(.*))?$")


class Command:
    def __init__(self, name: str, handler: Callable, *, admin_only: bool = False,
                 owner_only: bool = False, public: bool = True,
                 cooldown_sec: int = 300, description: str = ""):
        self.name = name
        self.handler = handler
        self.admin_only = admin_only
        self.owner_only = owner_only
        self.public = public
        self.cooldown_sec = cooldown_sec
        self.description = description


class CommandRegistry:
    def __init__(self):
        self._commands: dict[str, Command] = {}

    def register(self, cmd: Command) -> None:
        self._commands[cmd.name] = cmd

    def get(self, name: str) -> Optional[Command]:
        return self._commands.get(name)

    def list_public(self) -> list[Command]:
        return [c for c in self._commands.values() if c.public]

    def parse(self, text: str) -> Optional[tuple[str, Optional[str]]]:
        m = COMMAND_RE.match(text.strip())
        if not m:
            return None
        return m.group(1), m.group(2)
