from __future__ import annotations
import json
import logging
import time

from .base_agent import BaseAgent, AgentContext, AgentResult, AgentStatus, AgentCapability

logger = logging.getLogger("webapp.agents.monitoring")

MONITORING_PROMPT = """You are AIDA Monitoring Agent — the system observability expert.
Track and analyze:
1. Agent performance metrics (latency, error rates, call counts)
2. System health indicators
3. Bottlenecks and optimization opportunities
4. Usage patterns and trends
5. Anomaly detection

Provide actionable insights and recommendations."""


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
