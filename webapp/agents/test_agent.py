from __future__ import annotations
import json
import logging
import time

from .base_agent import BaseAgent, AgentContext, AgentResult, AgentStatus, AgentCapability

logger = logging.getLogger("webapp.agents.test")

TEST_PROMPT = """You are AIDA Test Agent — an expert in software testing.
Generate comprehensive tests including:
1. Unit tests — test individual functions/classes
2. Edge cases — empty inputs, boundaries, error conditions
3. Integration tests — component interaction
4. Performance tests — basic benchmarks

Use pytest style. Include fixtures and mocks where appropriate.
Aim for >80% code coverage."""


class TestAgent(BaseAgent):
    def __init__(self, model: str = ""):
        super().__init__("test", model)
        self.capabilities = [AgentCapability.TEST]

    async def execute(self, ctx: AgentContext) -> AgentResult:
        start = time.monotonic()
        self.status = AgentStatus.RUNNING
        self._current_task_id = ctx.task_id
        try:
            from ..llm.base import Message, MessageRole
            from ..llm.gateway import get_gateway
            gw = get_gateway()

            if ctx.collaborators and "code" in ctx.collaborators:
                code_msg = await self.receive(timeout=3.0)
                if code_msg and code_msg.subject == "code_ready":
                    ctx.metadata["code"] = code_msg.body

            msgs = self._build_prompt(ctx, ctx.system_prompt or TEST_PROMPT)
            result = await gw.chat(msgs)
            self.status = AgentStatus.DONE
            self._record(start, True)

            await self.broadcast("test_ready", result.content,
                                 thread_id=ctx.thread_id,
                                 metadata={"task_id": ctx.task_id})

            return AgentResult(
                task_id=ctx.task_id, content=result.content,
                status=AgentStatus.DONE, latency_ms=int((time.monotonic()-start)*1000),
                usage=result.usage,
            )
        except Exception as e:
            self.status = AgentStatus.ERROR
            self._record(start, False)
            return AgentResult(task_id=ctx.task_id, status=AgentStatus.ERROR, error=str(e))
