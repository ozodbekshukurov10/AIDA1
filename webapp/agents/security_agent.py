from __future__ import annotations
import json
import logging
import time

from .base_agent import BaseAgent, AgentContext, AgentResult, AgentStatus, AgentCapability

logger = logging.getLogger("webapp.agents.security")

SECURITY_PROMPT = """You are AIDA Security Agent — an expert in application security.
Analyze code/architecture for:
1. OWASP Top 10 vulnerabilities (injection, XSS, broken auth, etc.)
2. Data exposure and privacy issues
3. Insecure dependencies or configurations
4. Missing authentication/authorization
5. Hardcoded secrets or credentials
6. Input validation weaknesses

For each issue: severity (critical/high/medium/low), location, fix recommendation."""


class SecurityAgent(BaseAgent):
    def __init__(self, model: str = ""):
        super().__init__("security", model)
        self.capabilities = [AgentCapability.SECURITY]

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

            msgs = self._build_prompt(ctx, ctx.system_prompt or SECURITY_PROMPT)
            result = await gw.chat(msgs)
            self.status = AgentStatus.DONE
            self._record(start, True)

            await self.broadcast("security_report", result.content,
                                 thread_id=ctx.thread_id,
                                 metadata={"task_id": ctx.task_id})

            return AgentResult(
                task_id=ctx.task_id, content=result.content,
                status=AgentStatus.DONE, latency_ms=int((time.monotonic()-start)*1000),
                usage=result.usage,
                metadata={"severity": ctx.metadata.get("severity", "unknown")},
            )
        except Exception as e:
            self.status = AgentStatus.ERROR
            self._record(start, False)
            return AgentResult(task_id=ctx.task_id, status=AgentStatus.ERROR, error=str(e))
