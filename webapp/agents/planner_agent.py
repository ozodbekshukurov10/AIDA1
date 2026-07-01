from __future__ import annotations
import json
import logging
import time
import uuid

from .base_agent import BaseAgent, AgentContext, AgentResult, AgentStatus, AgentCapability, AgentMessage

logger = logging.getLogger("webapp.agents.planner")

PLANNER_PROMPT = """You are AIDA Planner Agent — a professional software project planner.
Analyze the request and produce:
1. Task decomposition — break the goal into concrete steps
2. Dependencies — which tasks depend on others
3. Recommended agents — which agent should handle each step
4. Estimated complexity — low/medium/high for each step
5. Timeline — order of execution

Output as structured JSON with: tasks[], dependencies[], assignments[]."""


class PlannerAgent(BaseAgent):
    def __init__(self, model: str = ""):
        super().__init__("planner", model)
        self.capabilities = [AgentCapability.PLAN]

    async def execute(self, ctx: AgentContext) -> AgentResult:
        start = time.monotonic()
        self.status = AgentStatus.RUNNING
        self._current_task_id = ctx.task_id
        try:
            from ..llm.base import Message, MessageRole
            from ..llm.gateway import get_gateway
            gw = get_gateway()
            msgs = self._build_prompt(ctx, ctx.system_prompt or PLANNER_PROMPT)
            result = await gw.chat(msgs)
            self.status = AgentStatus.DONE
            self._record(start, True)
            plan_data = self._parse_plan(result.content)
            await self.broadcast("plan_ready", json.dumps(plan_data),
                                 thread_id=ctx.thread_id, metadata={"task_id": ctx.task_id})
            return AgentResult(
                task_id=ctx.task_id, content=result.content,
                status=AgentStatus.DONE, latency_ms=int((time.monotonic()-start)*1000),
                usage=result.usage,
                metadata={"plan": plan_data},
            )
        except Exception as e:
            self.status = AgentStatus.ERROR
            self._record(start, False)
            return AgentResult(task_id=ctx.task_id, status=AgentStatus.ERROR, error=str(e))

    def _parse_plan(self, content: str) -> dict:
        try:
            start = content.index("{")
            end = content.rindex("}") + 1
            return json.loads(content[start:end])
        except (ValueError, json.JSONDecodeError):
            return {"tasks": [{"title": "Analyze", "agent": "general"}], "dependencies": []}
