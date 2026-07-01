from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProposalType(str, Enum):
    OPTIMIZATION = "optimization"
    REFACTOR = "refactor"
    TEST = "test"
    SECURITY = "security"
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"
    CONFIG = "config"
    MONITORING = "monitoring"


class ProposalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"
    DEFERRED = "deferred"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Proposal:
    id: str
    type: ProposalType
    title: str
    description: str
    severity: Severity
    status: ProposalStatus = ProposalStatus.PENDING
    target_file: str = ""
    original_content: str = ""
    suggested_content: str = ""
    diff: str = ""
    impact: str = ""
    effort: str = ""
    metrics_before: dict[str, Any] = field(default_factory=dict)
    metrics_after: dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0
    approved_at: float = 0.0
    applied_at: float = 0.0
    rejected_reason: str = ""
    agent_recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "status": self.status.value,
            "target_file": self.target_file,
            "diff": self.diff,
            "impact": self.impact,
            "effort": self.effort,
            "created_at": self.created_at,
            "approved_at": self.approved_at,
        }


@dataclass
class AgentSnapshot:
    agent_name: str
    status: str
    call_count: int
    error_count: int
    avg_latency_ms: float
    success_rate: float
    tokens_used: int
    last_error: str = ""
    timestamp: float = 0.0

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "status": self.status,
            "call_count": self.call_count,
            "error_count": self.error_count,
            "avg_latency_ms": self.avg_latency_ms,
            "success_rate": self.success_rate,
            "tokens_used": self.tokens_used,
            "last_error": self.last_error,
        }


@dataclass
class PerformanceReport:
    period_hours: int = 24
    total_requests: int = 0
    total_agent_calls: int = 0
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
    agent_stats: list[AgentSnapshot] = field(default_factory=list)
    bottlenecks: list[dict] = field(default_factory=list)
    trends: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "period_hours": self.period_hours,
            "total_requests": self.total_requests,
            "total_agent_calls": self.total_agent_calls,
            "avg_latency_ms": self.avg_latency_ms,
            "error_rate": self.error_rate,
            "bottlenecks": self.bottlenecks,
            "trends": self.trends,
            "recommendations": self.recommendations,
            "agent_stats": [a.to_dict() for a in self.agent_stats],
        }


@dataclass
class ErrorLog:
    id: str
    source: str
    message: str
    traceback: str
    severity: Severity
    timestamp: float = 0.0
    context: dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "message": self.message[:200],
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "resolved": self.resolved,
            "context": {k: str(v)[:100] for k, v in self.context.items()},
        }
