from __future__ import annotations
import json
import logging
import time

from .base_agent import BaseAgent, AgentContext, AgentResult, AgentStatus, AgentCapability

logger = logging.getLogger("webapp.agents.deployment")

DEPLOYMENT_PROMPT = """Sen AIDA Deploy Agentisan — DevOps va joylashtirish bo'yicha mutaxassis.
Joylashtirish konfiguratsiyalarini yozing:

1. Dockerfile — ko'p bosqichli build, xavfsizlik amaliyotlari
2. docker-compose.yml — xizmatlar aniqlash, tarmoq sozlash
3. CI/CD pipeline konfiguratsiyasi (GitHub Actions/GitLab CI)
4. Muhit konfiguratsiyasi
5. Sog'liqni saqlash tekshiruvi va monitoring o'rnatish
6. Masshtablash masalalari

Ishlab chiqishga tayyor konfiguratsiyalarni tushuntirishlar bilan chiqaring.
Har doim o'zbek tilida javob ber."""


class DeploymentAgent(BaseAgent):
    def __init__(self, model: str = ""):
        super().__init__("deployment", model)
        self.capabilities = [AgentCapability.DEPLOYMENT]

    async def execute(self, ctx: AgentContext) -> AgentResult:
        start = time.monotonic()
        self.status = AgentStatus.RUNNING
        self._current_task_id = ctx.task_id
        try:
            from ..llm.base import Message, MessageRole
            from ..llm.gateway import get_gateway
            gw = get_gateway()

            if ctx.collaborators and "security" in ctx.collaborators:
                sec_msg = await self.receive(timeout=3.0)
                if sec_msg and sec_msg.subject == "security_report":
                    ctx.metadata["security_requirements"] = sec_msg.body[:2000]

            msgs = self._build_prompt(ctx, ctx.system_prompt or DEPLOYMENT_PROMPT)
            result = await gw.chat(msgs)
            self.status = AgentStatus.DONE
            self._record(start, True)

            await self.broadcast("deployment_ready", result.content,
                                 thread_id=ctx.thread_id,
                                 metadata={"task_id": ctx.task_id})

            return AgentResult(
                task_id=ctx.task_id, content=result.content,
                status=AgentStatus.DONE, latency_ms=int((time.monotonic()-start)*1000),
                usage=result.usage,
                metadata={"target": ctx.metadata.get("target", "docker")},
            )
        except Exception as e:
            self.status = AgentStatus.ERROR
            self._record(start, False)
            return AgentResult(task_id=ctx.task_id, status=AgentStatus.ERROR, error=str(e))
