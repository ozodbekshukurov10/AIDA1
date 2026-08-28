from __future__ import annotations
import json
import logging
import time

from .base_agent import BaseAgent, AgentContext, AgentResult, AgentStatus, AgentCapability

logger = logging.getLogger("webapp.agents.monitoring")

MONITORING_PROMPT = """Sen AIDA Monitoring Agentisan — tizim kuzatuvchisi va tahlilchisan.
Quyidagilarni kuzating va tahlil qiling:

1. Agentlar samaradorlik ko'rsatkichlari (kechikish, xato darajasi, chaqirishlar soni)
2. Tizim sog'ligi ko'rsatkichlari
3. Torliklar (bottlenecks) va optimizatsiya imkoniyatlari
4. Foydalanish namunalari va tendensiyalari
5. Anomaliyalarni aniqlash

Amaliy va foydali tavsiyalar bering.
Har doim o'zbek tilida javob ber."""


class MonitoringAgent(BaseAgent):
    def __init__(self, model: str = ""):
        super().__init__("monitoring", model)
        self.capabilities = [AgentCapability.MONITORING]
        self._snapshots: list[dict] = []

    async def execute(self, ctx: AgentContext) -> AgentResult:
        start = time.monotonic()
        self.status = AgentStatus.RUNNING
        self._current_task_id = ctx.task_id
        try:
            from ..llm.base import Message, MessageRole
            from ..llm.gateway import get_gateway
            from ..memory.metrics import get_metrics_collector

            gw = get_gateway()
            mc = get_metrics_collector()

            stats = mc.get_stats(hours=24)
            gateway_status = gw.get_status()
            snapshot = {
                "timestamp": time.time(),
                "stats": stats,
                "gateway": gateway_status,
            }
            self._snapshots.append(snapshot)

            ctx.metadata["stats"] = stats
            ctx.metadata["gateway"] = gateway_status

            msgs = self._build_prompt(ctx, ctx.system_prompt or MONITORING_PROMPT)
            result = await gw.chat(msgs)
            self.status = AgentStatus.DONE
            self._record(start, True)

            await self.broadcast("monitoring_report", result.content,
                                 thread_id=ctx.thread_id,
                                 metadata={"task_id": ctx.task_id, "snapshot": snapshot})

            return AgentResult(
                task_id=ctx.task_id, content=result.content,
                status=AgentStatus.DONE, latency_ms=int((time.monotonic()-start)*1000),
                usage=result.usage,
                metadata={"stats": stats},
            )
        except Exception as e:
            self.status = AgentStatus.ERROR
            self._record(start, False)
            return AgentResult(task_id=ctx.task_id, status=AgentStatus.ERROR, error=str(e))
