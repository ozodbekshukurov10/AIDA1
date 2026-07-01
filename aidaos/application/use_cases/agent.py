"""Agent use cases — execute, manage, and monitor agents."""

from __future__ import annotations
import time
import logging
from typing import Any

from ...domain.entities import AgentContext, AgentResult, AgentSpec, AgentStatus
from ...domain.exceptions import AgentNotFoundError, AgentExecutionError, ValidationError
from ...domain.interfaces import AgentRepository, MetricsRepository
from ..dtos import AgentExecuteRequest

logger = logging.getLogger("aidaos.application.agent")


class AgentExecuteUseCase:
    def __init__(self, agent_repo: AgentRepository, metrics_repo: MetricsRepository):
        self._agents = agent_repo
        self._metrics = metrics_repo

    async def execute(self, request: AgentExecuteRequest) -> AgentResult:
        errors = request.validate()
        if errors:
            raise ValidationError("; ".join(errors))

        spec = await self._agents.get(request.agent_name)
        if not spec:
            raise AgentNotFoundError(f"Agent '{request.agent_name}' not found")

        start = time.monotonic()
        ctx = AgentContext(
            task_id=f"task_{int(start)}",
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            thread_id=request.thread_id,
            max_iterations=request.max_iterations,
            metadata=request.metadata,
        )

        try:
            result = await self._agents.execute(request.agent_name, ctx)
        except Exception as e:
            latency = int((time.monotonic() - start) * 1000)
            await self._metrics.record_agent_call(
                request.agent_name, "execute", False, latency,
            )
            raise AgentExecutionError(f"Agent execution failed: {e}")

        latency = int((time.monotonic() - start) * 1000)
        result.latency_ms = latency

        await self._metrics.record_agent_call(
            request.agent_name, "execute", result.success, latency,
        )
        return result


class AgentManageUseCase:
    def __init__(self, agent_repo: AgentRepository):
        self._agents = agent_repo

    async def list_agents(self) -> list[dict]:
        specs = await self._agents.list()
        return [s.to_dict() for s in specs]

    async def get_agent(self, name: str) -> dict:
        spec = await self._agents.get(name)
        if not spec:
            raise AgentNotFoundError(f"Agent '{name}' not found")
        status = await self._agents.get_status(name)
        result = spec.to_dict()
        result["status"] = status.value
        return result

    async def get_agent_status(self, name: str) -> str:
        status = await self._agents.get_status(name)
        return status.value

    async def register_agent(self, spec: AgentSpec) -> dict:
        await self._agents.register(spec)
        return {"success": True, "agent": spec.name}
