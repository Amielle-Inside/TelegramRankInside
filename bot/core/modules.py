"""Nucleo - gerenciador de modulos."""

from __future__ import annotations
from typing import Dict, List, Optional


class ModuleManifest:
    def __init__(self, module_id: str, version: str, commands: list,
                 events_used: list, config: dict | None = None):
        self.module_id = module_id
        self.version = version
        self.commands = commands  # lista de Command
        self.events_used = events_used
        self.config = config or {}
        self.enabled = True


class ModuleManager:
    def __init__(self):
        self.modules: Dict[str, ModuleManifest] = {}
        self._command_owner: dict[str, str] = {}  # nome comando -> module_id

    def register(self, manifest: ModuleManifest) -> None:
        self.modules[manifest.module_id] = manifest
        for cmd in manifest.commands:
            self._command_owner[cmd.name] = manifest.module_id

    def get(self, module_id: str) -> Optional[ModuleManifest]:
        return self.modules.get(module_id)

    def list_enabled(self) -> List[ModuleManifest]:
        return [m for m in self.modules.values() if m.enabled]

    def enable(self, module_id: str) -> None:
        if module_id in self.modules:
            self.modules[module_id].enabled = True

    def disable(self, module_id: str) -> None:
        if module_id in self.modules:
            self.modules[module_id].enabled = False

    def owner_of_command(self, name: str) -> Optional[str]:
        return self._command_owner.get(name)
