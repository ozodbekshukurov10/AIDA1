from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from .permission import Permission, PermissionLevel


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict | None = None
    requires_auth: bool = False
    requires_sandbox: bool = False
    permission: Permission | None = None
    category: str = "general"
    version: str = "1.0.0"
    timeout: int = 30


@dataclass
class ToolResult:
    success: bool
    output: str = ""
    error: str | None = None
    data: dict | None = None
    duration_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "data": self.data,
            "duration_ms": self.duration_ms,
        }


class BaseTool(ABC):
    _auto_registry: Any = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if BaseTool._auto_registry is not None:
            try:
                instance = cls()
                BaseTool._auto_registry.register(instance)
            except TypeError:
                pass

    def __init__(self, spec: ToolSpec):
        self.spec = spec

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        ...

    def validate_parameters(self, **kwargs) -> str | None:
        if not self.spec.parameters:
            return None
        required = {k for k, v in self.spec.parameters.items() if "default" not in v}
        missing = required - set(kwargs.keys())
        if missing:
            return f"Missing required parameters: {', '.join(missing)}"
        return None

    def get_spec(self) -> dict:
        return {
            "name": self.spec.name,
            "description": self.spec.description,
            "parameters": self.spec.parameters or {},
            "requires_auth": self.spec.requires_auth,
            "requires_sandbox": self.spec.requires_sandbox,
            "permission": self.spec.permission.level.name.lower() if self.spec.permission else "public",
            "category": self.spec.category,
            "version": self.spec.version,
            "timeout": self.spec.timeout,
        }
