from __future__ import annotations
import json
import logging
import time
import uuid

from .base_agent import BaseAgent, AgentContext, AgentResult, AgentStatus, AgentCapability, AgentMessage

logger = logging.getLogger("webapp.agents.planner")

PLANNER_PROMPT = """Sen AIDA Reja Agentisan — professional loyiha rejalashtiruvchisan.
So'rovni tahlil qilib, quyidagilarni chiqar:

1. Vazifalarni ajratish — maqsadni aniq qadamlarga bo'ling
2. Bog'liqliklar — qaysi vazifalar boshqasiga bog'liq
3. Tavsiya etilgan agentlar — har bir qadamni qaysi agent bajarishi
4. Murakkablik darajasi — har bir qadam uchun past/o'rta/yuqori
5. Vaqt jadvali — bajarilish tartibi

Natijani tuzilgan JSON formatida chiqar: tasks[], dependencies[], assignments[].
Har doim o'zbek tilida javob ber."""


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
