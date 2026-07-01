from __future__ import annotations
import json
import logging
import time

from .base_agent import BaseAgent, AgentContext, AgentResult, AgentStatus, AgentCapability

logger = logging.getLogger("webapp.agents.research")

RESEARCH_PROMPT = """You are AIDA Research Agent — an expert information researcher.
Given a query, research the topic and provide:
1. Key findings and facts
2. Sources and references
3. Code examples if relevant
4. Best practices and recommendations
5. Potential pitfalls

Be thorough, accurate, and cite specific details."""


class ResearchAgent(BaseAgent):
    def __init__(self, model: str = ""):
        super().__init__("research", model)
        self.capabilities = [AgentCapability.RESEARCH]

    async def execute(self, ctx: AgentContext) -> AgentResult:
        start = time.monotonic()
        self.status = AgentStatus.RUNNING
        self._current_task_id = ctx.task_id
        try:
            from ..llm.base import Message, MessageRole
            from ..llm.gateway import get_gateway
            from ..tools.registry import get_tool_registry

            gw = get_gateway()
            registry = get_tool_registry()

            web_result = await registry.execute("web_search", query=ctx.prompt)
            if web_result.success and web_result.output:
                ctx.metadata["web_results"] = web_result.output

            msgs = self._build_prompt(ctx, ctx.system_prompt or RESEARCH_PROMPT)
            result = await gw.chat(msgs)
            self.status = AgentStatus.DONE
            self._record(start, True)

            await self.broadcast("research_result", result.content,
                                 thread_id=ctx.thread_id,
                                 metadata={"task_id": ctx.task_id})

            return AgentResult(
                task_id=ctx.task_id, content=result.content,
                status=AgentStatus.DONE, latency_ms=int((time.monotonic()-start)*1000),
                usage=result.usage,
                metadata={"sources": web_result.data if web_result.success else None},
            )
        except Exception as e:
            self.status = AgentStatus.ERROR
            self._record(start, False)
            return AgentResult(task_id=ctx.task_id, status=AgentStatus.ERROR, error=str(e))
