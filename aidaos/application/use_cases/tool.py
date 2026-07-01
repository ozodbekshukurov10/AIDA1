"""Tool use cases — execute and manage tools."""

from __future__ import annotations
import logging
import time
from typing import Any

from ...domain.entities import ToolSpec, ToolResult, PermissionLevel, Permission
from ...domain.exceptions import ToolNotFoundError, ToolPermissionError, ValidationError
from ...domain.interfaces import ToolRepository
from ..dtos import ToolExecuteRequest

logger = logging.getLogger("aidaos.application.tool")


class ToolExecuteUseCase:
    def __init__(self, tool_repo: ToolRepository):
        self._tools = tool_repo

    async def execute(self, request: ToolExecuteRequest) -> ToolResult:
        errors = request.validate()
        if errors:
            raise ValidationError("; ".join(errors))

        spec = await self._tools.get(request.tool_name)
        if not spec:
            raise ToolNotFoundError(f"Tool '{request.tool_name}' not found")

        if spec.permission.require_confirmation and not request.require_confirmation:
            return ToolResult(
                success=False,
                error=f"Tool '{request.tool_name}' requires user confirmation",
            )

        start = time.monotonic()
        try:
            result = await self._tools.execute(request.tool_name, **request.params)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

        result.duration_ms = int((time.monotonic() - start) * 1000)
        return result

    async def validate_params(self, tool_name: str, params: dict) -> list[str]:
        spec = await self._tools.get(tool_name)
        if not spec:
            return [f"Tool '{tool_name}' not found"]
        errors = []
        required = spec.parameters.get("required", [])
        for r in required:
            if r not in params:
                errors.append(f"Missing required parameter: '{r}'")
        return errors


class ToolManageUseCase:
    def __init__(self, tool_repo: ToolRepository):
        self._tools = tool_repo

    async def list_tools(self) -> list[dict]:
        specs = await self._tools.list()
        return [s.to_dict() for s in specs]

    async def get_tool(self, name: str) -> dict:
        spec = await self._tools.get(name)
        if not spec:
            raise ToolNotFoundError(f"Tool '{name}' not found")
        return spec.to_dict()
