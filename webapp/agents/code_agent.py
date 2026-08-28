from __future__ import annotations
import json
import logging
import time

from .base_agent import BaseAgent, AgentContext, AgentResult, AgentStatus, AgentCapability

logger = logging.getLogger("webapp.agents.code")

CODE_PROMPT = """Sen AIDA Kod Agentisan — professional dasturchisan.
Quyidagilarni hisobga olgan holda sifatli kod yoz:

1. To'liq ishlaydigan kod — qisqartma yoki stub emas
2. Xatolarni qayta ishlash (error handling) va cheklov holatlari (edge cases)
3. Type hints va hujjatlar (documentation)
4. Eng yaxshi amaliyotlar (best practices) va dizayn naqshlari (patterns)
5. Tezlik va samaradorlik masalalari

Kodni to'g'ri formatda chiqar. Har doim o'zbek tilida tushuntirish ber."""


class CodeAgent(BaseAgent):
    def __init__(self, model: str = ""):
        super().__init__("code", model)
        self.capabilities = [AgentCapability.CODE]

    async def execute(self, ctx: AgentContext) -> AgentResult:
        start = time.monotonic()
        self.status = AgentStatus.RUNNING
        self._current_task_id = ctx.task_id
        try:
            from ..llm.base import Message, MessageRole
            from ..llm.gateway import get_gateway
            gw = get_gateway()

            if ctx.collaborators and "planner" in ctx.collaborators:
                plan_msg = await self.receive(timeout=3.0)
                if plan_msg and plan_msg.subject == "plan_ready":
                    ctx.metadata["plan"] = plan_msg.body

            msgs = self._build_prompt(ctx, ctx.system_prompt or CODE_PROMPT)
            result = await gw.chat(msgs)
            self.status = AgentStatus.DONE
            self._record(start, True)

            await self.broadcast("code_ready", result.content,
                                 thread_id=ctx.thread_id,
                                 metadata={"task_id": ctx.task_id, "language": ctx.metadata.get("language", "python")})

            return AgentResult(
                task_id=ctx.task_id, content=result.content,
                status=AgentStatus.DONE, latency_ms=int((time.monotonic()-start)*1000),
                usage=result.usage,
                metadata={"language": ctx.metadata.get("language", "python")},
            )
        except Exception as e:
            self.status = AgentStatus.ERROR
            self._record(start, False)
            return AgentResult(task_id=ctx.task_id, status=AgentStatus.ERROR, error=str(e))
