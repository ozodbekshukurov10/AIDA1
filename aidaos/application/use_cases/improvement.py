"""Self-improvement use case — all improvement proposals go through this."""

from __future__ import annotations
import logging
import time
from typing import Any

from ...domain.entities import (
    AgentSnapshot, ErrorLog, PerformanceReport,
    Proposal, ProposalType, ProposalStatus, Severity,
)
from ...domain.exceptions import ProposalNotFoundError
from ...domain.interfaces import AgentRepository, MetricsRepository

logger = logging.getLogger("aidaos.application.improvement")


class SelfImprovementUseCase:
    def __init__(self, agent_repo: AgentRepository, metrics_repo: MetricsRepository):
        self._agents = agent_repo
        self._metrics = metrics_repo
        self._proposals: list[Proposal] = []

    async def scan_performance(self) -> list[Proposal]:
        proposals = []
        try:
            stats = await self._metrics.get_stats(hours=24)
            agent_stats = await self._metrics.get_agent_stats(hours=24)
        except Exception:
            return proposals

        for a in agent_stats:
            name = a.get("agent_name", "")
            avg_lat = a.get("avg_latency_ms", 0)
            err_rate = a.get("error_rate", 0)

            if avg_lat > 5000:
                proposals.append(Proposal(
                    id=f"perf_{name}_{int(time.time())}",
                    type=ProposalType.PERFORMANCE,
                    title=f"High latency: {name} ({avg_lat}ms)",
                    description=f"Agent {name} avg latency {avg_lat}ms exceeds threshold of 5000ms",
                    severity=Severity.HIGH,
                    created_at=time.time(),
                ))
            if err_rate > 20:
                proposals.append(Proposal(
                    id=f"err_{name}_{int(time.time())}",
                    type=ProposalType.PERFORMANCE,
                    title=f"High error rate: {name} ({err_rate}%)",
                    severity=Severity.HIGH,
                    created_at=time.time(),
                ))

        self._proposals.extend(proposals)
        return proposals

    async def get_pending_proposals(self) -> list[Proposal]:
        return [p for p in self._proposals if p.status == ProposalStatus.PENDING]

    async def get_all_proposals(self) -> list[Proposal]:
        return self._proposals

    async def approve_proposal(self, proposal_id: str) -> dict:
        for p in self._proposals:
            if p.id == proposal_id and p.status == ProposalStatus.PENDING:
                p.status = ProposalStatus.APPROVED
                return {"success": True, "id": proposal_id, "status": "approved"}
        raise ProposalNotFoundError(f"Proposal '{proposal_id}' not found or not pending")

    async def reject_proposal(self, proposal_id: str, reason: str = "") -> dict:
        for p in self._proposals:
            if p.id == proposal_id and p.status == ProposalStatus.PENDING:
                p.status = ProposalStatus.REJECTED
                return {"success": True, "id": proposal_id, "status": "rejected"}
        raise ProposalNotFoundError(f"Proposal '{proposal_id}' not found or not pending")

    async def get_report(self) -> dict:
        try:
            stats = await self._metrics.get_stats(hours=24)
            health = await self._metrics.get_health_score()
        except Exception:
            stats = {}
            health = 0
        return {
            "stats": stats,
            "health_score": health,
            "pending_proposals": len(await self.get_pending_proposals()),
            "total_proposals": len(self._proposals),
        }
