from __future__ import annotations
import json
import logging
import time

from .base_agent import BaseAgent, AgentContext, AgentResult, AgentStatus, AgentCapability

logger = logging.getLogger("webapp.agents.deployment")

DEPLOYMENT_PROMPT = """You are AIDA Deployment Agent — a DevOps and deployment expert.
Generate deployment configurations:
1. Dockerfile — multi-stage builds, security best practices
2. docker-compose.yml — service definitions, networking
3. CI/CD pipeline config (GitHub Actions/GitLab CI)
4. Environment configuration
5. Health check and monitoring setup
6. Scaling considerations

Output production-ready configurations with explanations."""


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
