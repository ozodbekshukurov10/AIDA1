from __future__ import annotations
import asyncio
import logging
import time
from typing import Any

from .base import BaseTool, ToolResult, ToolSpec
from .permission import Permission, PermissionLevel, PermissionError
from .registry import ToolRegistry, get_tool_registry

logger = logging.getLogger("webapp.tools.manager")


class ProfessionalToolManager:
    def __init__(self):
        self._registry = ToolRegistry()
        self._call_counts: dict[str, int] = {}
        self._rate_limits: dict[str, int] = {}

        BaseTool._auto_registry = self._registry
        self._discover_existing()

        logger.info(f"ProfessionalToolManager initialized with {len(self._registry._tools)} tools")

    def _discover_existing(self):
        found = set()
        def _find(cls):
            for sub in cls.__subclasses__():
                if sub.__name__ not in found and not sub.__name__.startswith("_"):
                    found.add(sub.__name__)
                    try:
                        instance = sub()
                        if instance.spec.name not in self._registry._tools:
                            self._registry._tools[instance.spec.name] = instance
                            logger.debug(f"Discovered tool: {instance.spec.name}")
                    except TypeError:
                        pass
                _find(sub)
        _find(BaseTool)

    async def execute(self, tool_name: str, user_level: PermissionLevel = PermissionLevel.PUBLIC,
                       user_roles: list[str] | None = None, **kwargs) -> ToolResult:
        start = time.monotonic()
        tool = self._registry.get(tool_name)

        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found. Available: {list(self._registry._tools.keys())}",
                duration_ms=int((time.monotonic() - start) * 1000),
            )

        perm = tool.spec.permission or Permission()

        if not perm.check(user_level, user_roles):
            return ToolResult(
                success=False,
                error=f"Permission denied: '{tool_name}' requires {perm.level.name}",
                duration_ms=int((time.monotonic() - start) * 1000),
            )

        validation_error = tool.validate_parameters(**kwargs)
        if validation_error:
            return ToolResult(
                success=False,
                error=validation_error,
                duration_ms=int((time.monotonic() - start) * 1000),
            )

        if perm.max_calls_per_session > 0:
            key = f"{user_level.name}:{tool_name}"
            self._call_counts[key] = self._call_counts.get(key, 0) + 1
            if self._call_counts[key] > perm.max_calls_per_session:
                return ToolResult(
                    success=False,
                    error=f"Rate limit exceeded: max {perm.max_calls_per_session} calls per session",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

        try:
            result = await asyncio.wait_for(
                tool.execute(**kwargs),
                timeout=tool.spec.timeout,
            )
            result.duration_ms = int((time.monotonic() - start) * 1000)
            return result
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' timed out after {tool.spec.timeout}s",
                duration_ms=int((time.monotonic() - start) * 1000),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                duration_ms=int((time.monotonic() - start) * 1000),
            )

    def list_tools(self, user_level: PermissionLevel = PermissionLevel.PUBLIC) -> list[dict]:
        return [
            t.get_spec() for t in self._registry._tools.values()
            if (t.spec.permission or Permission()).check(user_level)
        ]

    def get_tool(self, name: str) -> BaseTool | None:
        return self._registry.get(name)

    def get_stats(self) -> dict:
        return {
            "total_tools": len(self._registry._tools),
            "tools_by_category": self._tools_by_category(),
            "auto_registration": BaseTool._auto_registry is not None,
        }

    def _tools_by_category(self) -> dict[str, int]:
        categories: dict[str, int] = {}
        for t in self._registry._tools.values():
            cat = t.spec.category
            categories[cat] = categories.get(cat, 0) + 1
        return categories


_manager_instance: ProfessionalToolManager | None = None


def get_tool_manager() -> ProfessionalToolManager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ProfessionalToolManager()
    return _manager_instance
