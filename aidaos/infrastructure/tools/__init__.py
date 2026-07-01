"""Tool repository adapter — wraps the existing ProfessionalToolManager."""

from __future__ import annotations
import logging
from typing import Any

from ...domain.entities import ToolSpec, ToolResult, Permission, PermissionLevel
from ...domain.interfaces import ToolRepository

logger = logging.getLogger("aidaos.infrastructure.tools")


class ToolRepoAdapter(ToolRepository):
    def __init__(self):
        self._manager = None

    def _get_manager(self):
        if self._manager is None:
            from webapp.tools.manager import get_tool_manager
            self._manager = get_tool_manager()
        return self._manager

    async def register(self, spec: ToolSpec, execute_fn) -> None:
        logger.info(f"Tool registered: {spec.name}")

    async def get(self, name: str) -> ToolSpec | None:
        mgr = self._get_manager()
        try:
            tools = mgr.list_tools()
            for t in tools:
                if t["name"] == name or t.get("spec", {}).get("name") == name:
                    spec = t.get("spec", t)
                    return ToolSpec(
                        name=spec.get("name", name),
                        description=spec.get("description", ""),
                        parameters=spec.get("parameters", {}),
                        category=spec.get("category", "general"),
                        version=spec.get("version", "1.0"),
                    )
        except Exception as e:
            logger.debug(f"Tool lookup failed: {e}")
        return None

    async def list(self) -> list[ToolSpec]:
        mgr = self._get_manager()
        specs = []
        try:
            tools = mgr.list_tools()
            for t in tools:
                spec = t.get("spec", t)
                specs.append(ToolSpec(
                    name=spec.get("name", "unknown"),
                    description=spec.get("description", ""),
                    parameters=spec.get("parameters", {}),
                    category=spec.get("category", "general"),
                ))
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
        return specs

    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        mgr = self._get_manager()
        try:
            result = await mgr.execute(tool_name, kwargs)
            return ToolResult(
                success=result.success,
                output=result.output,
                error=result.error,
                data=result.data or {},
                duration_ms=result.duration_ms,
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
