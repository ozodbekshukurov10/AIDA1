"""Agent repository adapter — wraps the existing MultiAgentOrchestrator."""

from __future__ import annotations
import logging
import time
from typing import Any

from ...domain.entities import AgentSpec, AgentContext, AgentResult, AgentStatus, AgentCapability
from ...domain.interfaces import AgentRepository

logger = logging.getLogger("aidaos.infrastructure.agents")


class AgentRepoAdapter(AgentRepository):
    def __init__(self):
        self._orch = None

    def _get_orch(self):
        if self._orch is None:
            from webapp.agents.orchestrator import get_orchestrator
            self._orch = get_orchestrator()
        return self._orch

    async def register(self, spec: AgentSpec) -> None:
        logger.info(f"Agent registered: {spec.name}")

    async def get(self, name: str) -> AgentSpec | None:
        orch = self._get_orch()
        try:
            agents = orch.list_agents()
            if name in agents:
                agent = agents[name]
                caps = []
                for c in getattr(agent, "capabilities", []):
                    try:
                        caps.append(AgentCapability[c.name.upper()])
                    except (KeyError, AttributeError):
                        caps.append(AgentCapability.GENERAL)
                return AgentSpec(
                    name=name,
                    capabilities=caps or [AgentCapability.CODE],
                    description=getattr(agent, "description", "") or f"{name} agent",
                )
        except Exception as e:
            logger.debug(f"Agent lookup failed: {e}")
        return None

    async def list(self) -> list[AgentSpec]:
        orch = self._get_orch()
        specs = []
        try:
            agents = orch.list_agents()
            for name, agent in agents.items():
                caps = []
                for c in getattr(agent, "capabilities", []):
                    try:
                        caps.append(AgentCapability[c.name.upper()])
                    except (KeyError, AttributeError):
                        caps.append(AgentCapability.CODE)
                specs.append(AgentSpec(
                    name=name,
                    capabilities=caps or [AgentCapability.CODE],
                    description=getattr(agent, "description", "") or f"{name} agent",
                ))
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
        return specs

    async def execute(self, agent_name: str, ctx: AgentContext) -> AgentResult:
        orch = self._get_orch()
        try:
            from webapp.agents.base_agent import AgentContext as WAC, AgentResult as WAR
            wctx = WAC(
                task_id=ctx.task_id,
                prompt=ctx.prompt,
                system_prompt=ctx.system_prompt,
                messages=ctx.messages,
                metadata=ctx.metadata,
                tools=ctx.tools,
                max_iterations=ctx.max_iterations,
                thread_id=ctx.thread_id,
                collaborators=ctx.collaborators,
            )
            result = await orch.execute_single(agent_name, wctx)
            return AgentResult(
                task_id=result.task_id,
                content=result.content,
                status=AgentStatus.DONE if result.status.name == "DONE" else AgentStatus.ERROR,
                error=result.error,
                latency_ms=result.latency_ms,
                usage=result.usage or {},
                metadata=result.metadata or {},
            )
        except Exception as e:
            return AgentResult(task_id=ctx.task_id, status=AgentStatus.ERROR, error=str(e))

    async def get_status(self, agent_name: str) -> AgentStatus:
        orch = self._get_orch()
        try:
            status = orch.get_status().get(agent_name, {}).get("status", "idle")
            return AgentStatus(status)
        except Exception:
            return AgentStatus.IDLE
