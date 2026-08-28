from __future__ import annotations
import json
import logging
import time

from .base_agent import BaseAgent, AgentContext, AgentResult, AgentStatus, AgentCapability

logger = logging.getLogger("webapp.agents.docs")

DOCS_PROMPT = """Sen AIDA Hujjat Agentisan — professional texnik yozuvchi.
Aniq va to'liq hujjatlar yozing:

1. Umumiy ko'rinish — bu nima va nima uchun kerak
2. O'rnatish/yaratish ko'rsatmalari
3. Ishlatish misollari (kod bloklari bilan)
4. API havolasi (parametrlar, qaytarilgan qiymatlar)
5. Konfiguratsiya variantlari
6. Muammolarni hal qilish qo'llanmasi

Markdown formatini ishlating. Qisqa va to'liq bo'ling.
Maqsadli auditoriya: dasturchilar.
Har doim o'zbek tilida javob ber."""


class DocumentationAgent(BaseAgent):
    def __init__(self, model: str = ""):
        super().__init__("documentation", model)
        self.capabilities = [AgentCapability.DOCUMENTATION]

    async def execute(self, ctx: AgentContext) -> AgentResult:
        start = time.monotonic()
        self.status = AgentStatus.RUNNING
        self._current_task_id = ctx.task_id
        try:
            from ..llm.base import Message, MessageRole
            from ..llm.gateway import get_gateway
            gw = get_gateway()

            code_sources = []
            for collaborator in ctx.collaborators:
                if collaborator in ("code", "debug", "test", "security"):
                    msg = await self.receive(timeout=2.0)
                    if msg:
                        code_sources.append({"from": msg.sender, "subject": msg.subject, "body": msg.body[:2000]})
            if code_sources:
                ctx.metadata["code_sources"] = code_sources

            msgs = self._build_prompt(ctx, ctx.system_prompt or DOCS_PROMPT)
            result = await gw.chat(msgs)
            self.status = AgentStatus.DONE
            self._record(start, True)

            await self.broadcast("documentation_ready", result.content,
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
