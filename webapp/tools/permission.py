from __future__ import annotations
from enum import IntEnum, auto
from dataclasses import dataclass, field


class PermissionLevel(IntEnum):
    PUBLIC = 0
    USER = 1
    ADMIN = 2
    SYSTEM = 3


@dataclass
class Permission:
    level: PermissionLevel = PermissionLevel.PUBLIC
    roles: list[str] = field(default_factory=list)
    require_key: bool = False
    require_confirmation: bool = False
    max_calls_per_session: int = 0

    def check(self, user_level: PermissionLevel | None = None, user_roles: list[str] | None = None) -> bool:
        if self.level == PermissionLevel.PUBLIC:
            return True
        if user_level is None:
            return False
        if user_level.value < self.level.value:
            return False
        if self.roles and user_roles:
            if not any(r in user_roles for r in self.roles):
                return False
        return True


class PermissionError(Exception):
    def __init__(self, tool_name: str, required: PermissionLevel):
        self.tool_name = tool_name
        self.required = required
        super().__init__(f"Permission denied: '{tool_name}' requires {required.name}")
