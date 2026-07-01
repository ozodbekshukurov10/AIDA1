from __future__ import annotations
import logging
import time

from .base_agent import BaseAgent, AgentContext, AgentResult, AgentStatus, AgentCapability

logger = logging.getLogger("webapp.agents.debug")

DEBUG_PROMPT = """You are AIDA Debug Agent — an expert debugger and bug hunter.
Analyze the code/error and:
1. Identify the root cause of the bug
2. Explain why it happens
3. Provide a fixed version of the code
4. Suggest preventive measures

Be thorough — check for: logic errors, edge cases, race conditions,
memory leaks, type mismatches, API misuse."""


class DebugAgent(BaseAgent):
    def __init__(self, model: str = ""):
        super().__init__("debug", model)
        self.capabilities = [AgentCapability.DEBUG]

    async def execute(self, ctx: AgentContext) -> AgentResult:
        start = time.monotonic()
        self.status = AgentStatus.RUNNING
        self._current_task_id = ctx.task_id
        try:
            from ..llm.base import Message, MessageRole
            from ..llm.gateway import get_gateway
            gw = get_gateway()

            if ctx.collaborators and "test" in ctx.collaborators:
                test_msg = await self.receive(timeout=2.0)
                if test_msg and test_msg.subject == "test_failures":
                    ctx.metadata["test_results"] = test_msg.body

            msgs = self._build_prompt(ctx, ctx.system_prompt or DEBUG_PROMPT)
            result = await gw.chat(msgs)
            self.status = AgentStatus.DONE
            self._record(start, True)

            await self.broadcast("debug_result", result.content,
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
