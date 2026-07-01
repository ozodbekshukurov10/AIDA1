from __future__ import annotations
import logging
import time

from ..llm.base import Message, MessageRole
from ..llm.gateway import get_gateway
from .base_agent import (
    BaseAgent, AgentContext, AgentResult, AgentStatus,
)

logger = logging.getLogger("webapp.agents.general_agent")

GENERAL_SYSTEM_PROMPT = """You are AIDA General Agent — an intelligent, helpful AI assistant.
You answer questions, explain concepts, and help with various tasks.
Be concise, accurate, and clear in your responses."""


class GeneralAgent(BaseAgent):
    def __init__(self, name: str = "general", model: str = ""):
        super().__init__(name, model)
        self.gateway = get_gateway()

    async def execute(self, ctx: AgentContext) -> AgentResult:
        start = time.monotonic()
        self.status = AgentStatus.RUNNING
        try:
            ctx.system_prompt = ctx.system_prompt or GENERAL_SYSTEM_PROMPT
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
