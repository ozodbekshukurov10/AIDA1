from __future__ import annotations
import json
import logging
import time

from .base_agent import BaseAgent, AgentContext, AgentResult, AgentStatus, AgentCapability

logger = logging.getLogger("webapp.agents.docs")

DOCS_PROMPT = """You are AIDA Documentation Agent — an expert technical writer.
Generate clear, comprehensive documentation:
1. Overview — what this does and why
2. Installation/setup instructions
3. Usage examples with code snippets
4. API reference (parameters, return values)
5. Configuration options
6. Troubleshooting guide

Use Markdown formatting. Be concise yet thorough.
Target audience: developers."""


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
