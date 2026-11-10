"""Nucleo - permissoes e papéis."""

from __future__ import annotations

from typing import Set


class Permissions:
    """Verifica papéis: owner, admin, participante."""

    def __init__(self, owner_ids: Set[int], admin_ids: Set[int]):
        self.owner_ids = set(owner_ids)
        self.admin_ids = set(admin_ids)

    def is_owner(self, user_id: int) -> bool:
        return user_id in self.owner_ids

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids or self.is_owner(user_id)

    def is_participant(self, user_id: int) -> bool:
        return True  # qualquer um pode consultar publico
