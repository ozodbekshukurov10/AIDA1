from __future__ import annotations
import logging
import time
from typing import Any

from .base import BaseTool, ToolResult
from .builtin import (
    WebSearchTool, FileReadTool, PythonExecTool,
    ShellTool, KnowledgeAddTool, KnowledgeSearchTool,
)

logger = logging.getLogger("webapp.tools.registry")

_BUILTIN_TOOLS = [
    WebSearchTool,
    FileReadTool,
    PythonExecTool,
    ShellTool,
    KnowledgeAddTool,
    KnowledgeSearchTool,
]


class ToolRegistry:
    _instance: ToolRegistry | None = None

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._load_builtins()

    def _load_builtins(self):
        for tool_cls in _BUILTIN_TOOLS:
            instance = tool_cls()
            self._tools[instance.spec.name] = instance

    def register(self, tool: BaseTool):
        self._tools[tool.spec.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        return [t.get_spec() for t in self._tools.values()]

    async def execute(self, name: str, **kwargs) -> ToolResult:
        start = time.monotonic()
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found. Available: {list(self._tools.keys())}",
                duration_ms=int((time.monotonic() - start) * 1000),
            )
        try:
            result = await tool.execute(**kwargs)
            result.duration_ms = int((time.monotonic() - start) * 1000)
            return result
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                duration_ms=int((time.monotonic() - start) * 1000),
            )


_registry_instance: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ToolRegistry()
    return _registry_instance
