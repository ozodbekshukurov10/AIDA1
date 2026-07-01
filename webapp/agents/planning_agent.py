from __future__ import annotations
import logging
import time

from ..llm.base import Message, MessageRole
from ..llm.gateway import get_gateway
from .base_agent import (
    BaseAgent, AgentContext, AgentResult, AgentStatus,
)

logger = logging.getLogger("webapp.agents.planning_agent")

PLAN_SYSTEM_PROMPT = """You are AIDA Planning Agent. Create detailed step-by-step plans.
Break down complex tasks into manageable steps.
Consider dependencies, risks, and resource requirements.
Output in clear structured format."""


class PlanningAgent(BaseAgent):
    def __init__(self, name: str = "plan", model: str = ""):
        super().__init__(name, model)
        self.gateway = get_gateway()

    async def execute(self, ctx: AgentContext) -> AgentResult:
        start = time.monotonic()
        self.status = AgentStatus.RUNNING
        try:
            ctx.system_prompt = ctx.system_prompt or PLAN_SYSTEM_PROMPT
            messages = self._build_messages(ctx)
            result = await self.gateway.chat(messages, model=self.model or None)
            self.status = AgentStatus.DONE
            self._record_metrics(start, success=True)
            return AgentResult(
                task_id=ctx.task_id,
                content=result.content,
                status=AgentStatus.DONE,
                latency_ms=int((time.monotonic() - start) * 1000),
            )
        except Exception as e:
            self.status = AgentStatus.ERROR
            self._record_metrics(start, success=False)
            return AgentResult(
                task_id=ctx.task_id,
                content="",
                status=AgentStatus.ERROR,
                error=str(e),
                latency_ms=int((time.monotonic() - start) * 1000),
            )
