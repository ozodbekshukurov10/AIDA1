from __future__ import annotations
import logging
import time
import traceback
import uuid
from collections import defaultdict
from threading import Lock
from typing import Any

from .config import AgentSnapshot, ErrorLog, PerformanceReport, Severity

logger = logging.getLogger("webapp.self_improvement.monitor")


class SystemMonitor:
    _instance: SystemMonitor | None = None
    _lock: Lock = Lock()

    def __init__(self):
        self._error_logs: list[ErrorLog] = []
        self._snapshots: list[dict] = []
        self._performance_history: list[PerformanceReport] = []
        self._error_counts: dict[str, int] = defaultdict(int)
        self._agent_call_times: dict[str, list[float]] = defaultdict(list)
        self._agent_error_times: dict[str, list[float]] = defaultdict(list)
        self._max_history = 1000

    @classmethod
    def get_instance(cls) -> SystemMonitor:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def record_error(self, source: str, message: str, severity: Severity = Severity.MEDIUM,
                     context: dict | None = None) -> ErrorLog:
        err = ErrorLog(
            id=str(uuid.uuid4())[:8],
            source=source,
            message=message,
            traceback=traceback.format_exc(),
            severity=severity,
            timestamp=time.time(),
            context=context or {},
        )
        self._error_logs.append(err)
        self._error_counts[source] += 1
        if len(self._error_logs) > self._max_history:
            self._error_logs = self._error_logs[-self._max_history:]
        logger.warning(f"[SELF-IMPROVEMENT] Error in {source}: {message[:100]}")
        return err

    def record_agent_call(self, agent_name: str, latency_ms: float, success: bool):
        self._agent_call_times[agent_name].append(latency_ms)
        if len(self._agent_call_times[agent_name]) > 1000:
            self._agent_call_times[agent_name] = self._agent_call_times[agent_name][-1000:]
        if not success:
            self._agent_error_times[agent_name].append(time.time())
            if len(self._agent_error_times[agent_name]) > 100:
                self._agent_error_times[agent_name] = self._agent_error_times[agent_name][-100:]

    def snapshot(self, orchestrator=None, gateway=None, metrics_collector=None) -> dict:
        snap = {"timestamp": time.time(), "agents": {}, "gateway": {}, "system": {}}
        if orchestrator:
            try:
                agents_info = orchestrator.list_agents() if hasattr(orchestrator, 'list_agents') else {}
                for name, agent in (agents_info.items() if isinstance(agents_info, dict) else []):
                    snap["agents"][name] = {
                        "status": getattr(agent, "status", "unknown"),
                        "capabilities": [str(c) for c in getattr(agent, "capabilities", [])],
                    }
            except Exception as e:
                logger.debug(f"Snapshot agent info failed: {e}")
        if gateway:
            try:
                snap["gateway"] = gateway.get_status() if hasattr(gateway, "get_status") else {}
            except Exception:
                pass
        if metrics_collector:
            try:
                stats = metrics_collector.get_stats(hours=1) if hasattr(metrics_collector, "get_stats") else {}
                snap["metrics"] = stats
            except Exception:
                pass
        self._snapshots.append(snap)
        if len(self._snapshots) > 100:
            self._snapshots = self._snapshots[-100:]
        return snap

    def get_agent_snapshots(self) -> list[AgentSnapshot]:
        results = []
        for agent_name, times in self._agent_call_times.items():
            total = len(times)
            errors = len(self._agent_error_times.get(agent_name, []))
            avg_lat = sum(times) / total if total > 0 else 0
            success_rate = max(0, (total - errors) / max(total, 1)) * 100
            last_err = ""
            err_logs = [e for e in self._error_logs if e.source == agent_name]
            if err_logs:
                last_err = err_logs[-1].message[:100]
            results.append(AgentSnapshot(
                agent_name=agent_name,
                status="active" if success_rate >= 80 else "degraded",
                call_count=total,
                error_count=errors,
                avg_latency_ms=round(avg_lat, 1),
                success_rate=round(success_rate, 1),
                tokens_used=0,
                last_error=last_err,
                timestamp=time.time(),
            ))
        return results

    def get_errors(self, hours: int = 24, source: str = "", severity: str = "",
                   unresolved: bool = False) -> list[ErrorLog]:
        cutoff = time.time() - hours * 3600
        results = [
            e for e in self._error_logs
            if e.timestamp >= cutoff
            and (not source or e.source == source)
            and (not severity or e.severity.value == severity)
            and (not unresolved or not e.resolved)
        ]
        return results[-100:]

    def get_error_summary(self, hours: int = 24) -> dict:
        cutoff = time.time() - hours * 3600
        recent = [e for e in self._error_logs if e.timestamp >= cutoff]
        by_source: dict[str, int] = defaultdict(int)
        by_severity: dict[str, int] = defaultdict(int)
        for e in recent:
            by_source[e.source] += 1
            by_severity[e.severity.value] += 1
        return {
            "total_errors": len(recent),
            "by_source": dict(by_source),
            "by_severity": dict(by_severity),
            "unresolved": sum(1 for e in recent if not e.resolved),
        }

    def resolve_error(self, error_id: str, resolution: str = "") -> bool:
        for e in self._error_logs:
            if e.id == error_id:
                e.resolved = True
                e.resolution = resolution
                return True
        return False

    def get_performance_report(self, hours: int = 24) -> PerformanceReport:
        report = PerformanceReport(period_hours=hours)
        from ..memory.metrics import get_metrics_collector
        try:
            mc = get_metrics_collector()
            stats = mc.get_stats(hours=hours)
            report.total_requests = stats.get("total_requests", 0)
            report.total_agent_calls = stats.get("total_agent_calls", 0)
            report.avg_latency_ms = stats.get("avg_latency_ms", 0)
            report.error_rate = stats.get("error_rate", 0)
        except Exception:
            pass
        report.agent_stats = self.get_agent_snapshots()
        report.bottlenecks = self._detect_bottlenecks(report)
        report.trends = self._detect_trends()
        report.recommendations = self._generate_recommendations(report)
        self._performance_history.append(report)
        if len(self._performance_history) > 100:
            self._performance_history = self._performance_history[-100:]
        return report

    def _detect_bottlenecks(self, report: PerformanceReport) -> list[dict]:
        bottlenecks = []
        for agent in report.agent_stats:
            if agent.avg_latency_ms > 5000:
                bottlenecks.append({
                    "agent": agent.agent_name,
                    "type": "latency",
                    "value": agent.avg_latency_ms,
                    "threshold": 5000,
                    "recommendation": f"{agent.agent_name} has high avg latency ({agent.avg_latency_ms}ms). Consider optimizing or using a faster model.",
                })
            if agent.success_rate < 80:
                bottlenecks.append({
                    "agent": agent.agent_name,
                    "type": "error_rate",
                    "value": agent.success_rate,
                    "threshold": 80,
                    "recommendation": f"{agent.agent_name} has low success rate ({agent.success_rate}%). Check for recurring errors.",
                })
            if agent.call_count > 100 and agent.error_count > agent.call_count * 0.2:
                bottlenecks.append({
                    "agent": agent.agent_name,
                    "type": "failure_rate",
                    "value": round(agent.error_count / max(agent.call_count, 1) * 100, 1),
                    "recommendation": f"{agent.agent_name} has >20% failure rate. Investigate root cause.",
                })
        if report.avg_latency_ms > 10000:
            bottlenecks.append({
                "agent": "system",
                "type": "overall_latency",
                "value": report.avg_latency_ms,
                "recommendation": "Overall system latency exceeds 10s. Consider optimizing providers or reducing model size.",
            })
        return bottlenecks

    def _detect_trends(self) -> dict:
        trends = {}
        if len(self._performance_history) >= 3:
            recent = self._performance_history[-3:]
            latencies = [r.avg_latency_ms for r in recent]
            errors = [r.error_rate for r in recent]
            if len(latencies) >= 2 and latencies[-1] > latencies[0] * 1.2:
                trends["latency"] = "increasing"
            elif len(latencies) >= 2 and latencies[-1] < latencies[0] * 0.8:
                trends["latency"] = "decreasing"
            else:
                trends["latency"] = "stable"
            if len(errors) >= 2 and errors[-1] > errors[0] * 1.2:
                trends["error_rate"] = "increasing"
            elif len(errors) >= 2 and errors[-1] < errors[0] * 0.8:
                trends["error_rate"] = "decreasing"
            else:
                trends["error_rate"] = "stable"
        return trends

    def _generate_recommendations(self, report: PerformanceReport) -> list[str]:
        recs = []
        for b in report.bottlenecks:
            recs.append(b.get("recommendation", ""))
        if report.error_rate > 10:
            recs.append(f"Error rate is {report.error_rate}% (>10%). Review recent errors and fix root causes.")
        if report.total_requests == 0:
            recs.append("No requests in the last period. Check if agents are idle or misconfigured.")
        if self._error_counts:
            top = sorted(self._error_counts.items(), key=lambda x: -x[1])[:3]
            for src, count in top:
                recs.append(f"Source '{src}' has {count} errors. Consider investigating.")
        return [r for r in recs if r]

    def get_metrics(self) -> dict:
        return {
            "total_errors_logged": len(self._error_logs),
            "total_snapshots": len(self._snapshots),
            "performance_reports": len(self._performance_history),
            "error_counts_by_source": dict(self._error_counts),
            "agents_tracked": list(self._agent_call_times.keys()),
        }
