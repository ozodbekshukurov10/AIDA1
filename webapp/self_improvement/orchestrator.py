from __future__ import annotations
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any

from .config import Proposal, ProposalStatus, ProposalType, Severity
from .monitor import SystemMonitor
from .analyzer import ImprovementAnalyzer
from .approval import ApprovalSystem
from .test_writer import TestWriter
from .refactorer import Refactorer

logger = logging.getLogger("webapp.self_improvement.orchestrator")


@dataclass
class ImprovementContext:
    orchestrator: Any = None
    gateway: Any = None
    metrics_collector: Any = None
    repo_path: str = ""
    files: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "has_orchestrator": self.orchestrator is not None,
            "has_gateway": self.gateway is not None,
            "has_metrics": self.metrics_collector is not None,
            "repo_path": self.repo_path,
            "file_count": len(self.files),
        }


class SelfImprovementSystem:
    _instance: SelfImprovementSystem | None = None
    _lock: Lock = Lock()

    def __init__(self):
        self.monitor = SystemMonitor.get_instance()
        self.analyzer = ImprovementAnalyzer(self.monitor)
        self.approval = ApprovalSystem.get_instance()
        self.test_writer = TestWriter()
        self.refactorer = Refactorer()
        self._ctx = ImprovementContext()
        self._auto_scan_interval = 3600
        self._last_scan: float = 0
        self._scanning = False

    @classmethod
    def get_instance(cls) -> SelfImprovementSystem:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def configure(self, orchestrator=None, gateway=None, metrics_collector=None,
                  repo_path: str = ""):
        self._ctx.orchestrator = orchestrator
        self._ctx.gateway = gateway
        self._ctx.metrics_collector = metrics_collector
        self._ctx.repo_path = repo_path
        logger.info("[SELF-IMPROVEMENT] Configured with context")

    async def snapshot(self) -> dict:
        snap = self.monitor.snapshot(
            orchestrator=self._ctx.orchestrator,
            gateway=self._ctx.gateway,
            metrics_collector=self._ctx.metrics_collector,
        )
        return snap

    async def scan_for_improvements(self, full: bool = False) -> list[Proposal]:
        if self._scanning:
            logger.warning("[SELF-IMPROVEMENT] Scan already in progress")
            return []
        self._scanning = True
        try:
            self._last_scan = time.time()
            logger.info("[SELF-IMPROVEMENT] Starting improvement scan")

            proposals = self.analyzer.generate_all_proposals()

            if full and self._ctx.repo_path:
                repo_path = Path(self._ctx.repo_path)
                if repo_path.exists():
                    files = []
                    for ext in (".py", ".js", ".ts", ".jsx", ".tsx"):
                        for f in repo_path.rglob(f"*{ext}"):
                            if "node_modules" in str(f) or "__pycache__" in str(f) or ".git" in str(f):
                                continue
                            rel_path = str(f.relative_to(repo_path))
                            ext_lower = f.suffix.lower()
                            try:
                                src = f.read_text(encoding="utf-8", errors="replace")
                            except Exception:
                                continue
                            files.append({"path": rel_path, "abs_path": str(f), "extension": ext_lower, "source": src})

                    if files:
                        logger.info(f"[SELF-IMPROVEMENT] Scanning {len(files)} files")
                        extra = self.analyzer.analyze_coverage(files, str(repo_path))
                        proposals.extend(extra)

                        for f in files:
                            ext = f.get("extension", "")
                            source = f.get("source", "")
                            rel = f["path"]

                            code_props = self.analyzer.analyze_code_quality(rel, source)
                            proposals.extend(code_props)
                            test_props = self.test_writer.propose_tests(rel, source)
                            proposals.extend(test_props)
                            refactor_props = self.refactorer.propose_refactors(rel, source)
                            proposals.extend(refactor_props)

            self.analyzer.add_proposals(proposals)
            for p in proposals:
                self.approval.propose(p)

            logger.info(f"[SELF-IMPROVEMENT] Scan complete: {len(proposals)} proposals generated")
            return proposals
        finally:
            self._scanning = False

    def get_pending_proposals(self) -> list[Proposal]:
        return self.analyzer.get_pending_proposals()

    def get_all_proposals(self) -> list[Proposal]:
        return self.analyzer.get_all_proposals()

    def get_proposal(self, proposal_id: str) -> Proposal | None:
        return self.analyzer.get_proposal(proposal_id)

    def approve_proposal(self, proposal_id: str) -> dict:
        proposal = self.analyzer.get_proposal(proposal_id)
        if not proposal:
            return {"success": False, "error": "Proposal not found"}
        self.approval.approve(proposal)
        if proposal.target_file and proposal.suggested_content:
            success = self.approval.apply_change(proposal)
            return {"success": success, "proposal_id": proposal_id,
                    "status": proposal.status.value,
                    "message": f"Changes applied to {proposal.target_file}" if success else "Apply failed"}
        return {"success": True, "proposal_id": proposal_id,
                "status": proposal.status.value,
                "message": "Proposal approved (no file changes needed)"}

    def reject_proposal(self, proposal_id: str, reason: str = "") -> dict:
        proposal = self.analyzer.get_proposal(proposal_id)
        if not proposal:
            return {"success": False, "error": "Proposal not found"}
        self.approval.reject(proposal, reason)
        return {"success": True, "proposal_id": proposal_id, "status": "rejected"}

    def defer_proposal(self, proposal_id: str) -> dict:
        proposal = self.analyzer.get_proposal(proposal_id)
        if not proposal:
            return {"success": False, "error": "Proposal not found"}
        self.approval.defer(proposal)
        return {"success": True, "proposal_id": proposal_id, "status": "deferred"}

    def rollback_proposal(self, proposal_id: str) -> dict:
        proposal = self.analyzer.get_proposal(proposal_id)
        if not proposal:
            return {"success": False, "error": "Proposal not found"}
        ok = self.approval.rollback(proposal)
        return {"success": ok, "proposal_id": proposal_id,
                "message": f"Rolled back {proposal.target_file}" if ok else "Rollback failed"}

    def get_report(self) -> dict:
        perf = self.monitor.get_performance_report(hours=24)
        errors = self.monitor.get_error_summary(hours=24)
        pending = len(self.get_pending_proposals())
        approval_stats = self.approval.get_stats()
        return {
            "performance": perf.to_dict(),
            "errors": errors,
            "pending_proposals": pending,
            "approval_stats": approval_stats,
            "last_scan": self._last_scan,
            "context": self._ctx.to_dict(),
        }

    def get_errors(self, hours: int = 24, source: str = "",
                   unresolved: bool = False) -> list[dict]:
        errors = self.monitor.get_errors(hours=hours, source=source, unresolved=unresolved)
        return [e.to_dict() for e in errors]

    def resolve_error(self, error_id: str, resolution: str = "") -> bool:
        return self.monitor.resolve_error(error_id, resolution)

    def record_error(self, source: str, message: str,
                     severity: str = "medium", context: dict | None = None):
        sev = Severity(severity) if severity in Severity._value2member_map_ else Severity.MEDIUM
        self.monitor.record_error(source, message, sev, context)

    def record_agent_call(self, agent_name: str, latency_ms: float, success: bool):
        self.monitor.record_agent_call(agent_name, latency_ms, success)

    def get_summary(self) -> dict:
        report = self.get_report()
        proposals = self.get_all_proposals()
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        for p in proposals:
            by_type[p.type.value] = by_type.get(p.type.value, 0) + 1
            by_status[p.status.value] = by_status.get(p.status.value, 0) + 1
        return {
            "performance": {
                "avg_latency_ms": report["performance"]["avg_latency_ms"],
                "error_rate": report["performance"]["error_rate"],
                "bottlenecks": len(report["performance"]["bottlenecks"]),
            },
            "errors": report["errors"],
            "proposals": {
                "total": len(proposals),
                "pending": report["pending_proposals"],
                "by_type": by_type,
                "by_status": by_status,
            },
            "approval": report["approval_stats"],
            "last_scan": report["last_scan"],
        }
