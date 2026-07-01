"""Domain entities — pure business objects with no infrastructure dependencies."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable


class AgentCapability(Enum):
    PLAN = auto()
    CODE = auto()
    DEBUG = auto()
    RESEARCH = auto()
    TEST = auto()
    SECURITY = auto()
    DOCUMENTATION = auto()
    MEMORY = auto()
    MONITORING = auto()
    DEPLOYMENT = auto()


class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    DONE = "done"
    ERROR = "error"
    BLOCKED = "blocked"


@dataclass
class AgentSpec:
    name: str
    capabilities: list[AgentCapability]
    description: str
    model_preference: str = ""
    max_iterations: int = 10
    timeout_seconds: int = 120
    collaborator_names: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "capabilities": [c.name for c in self.capabilities],
            "description": self.description,
            "model_preference": self.model_preference,
            "max_iterations": self.max_iterations,
            "timeout_seconds": self.timeout_seconds,
            "collaborators": self.collaborator_names,
        }


@dataclass
class AgentContext:
    task_id: str
    prompt: str
    system_prompt: str = ""
    messages: list[dict] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    tools: list[str] = field(default_factory=list)
    max_iterations: int = 10
    thread_id: str = ""
    collaborators: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "prompt": self.prompt[:100],
            "thread_id": self.thread_id,
            "max_iterations": self.max_iterations,
        }


@dataclass
class AgentResult:
    task_id: str
    content: str = ""
    status: AgentStatus = AgentStatus.DONE
    error: str = ""
    iterations: int = 0
    latency_ms: int = 0
    usage: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    messages: list[dict] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.status == AgentStatus.DONE and not self.error

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "success": self.success,
            "error": self.error,
            "latency_ms": self.latency_ms,
        }


class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    role: MessageRole
    content: str
    name: str = ""
    tool_calls: list[dict] = field(default_factory=list)
    tool_call_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {"role": self.role.value, "content": self.content}
        if self.name:
            d["name"] = self.name
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        return d

    @classmethod
    def user(cls, content: str) -> Message:
        return cls(role=MessageRole.USER, content=content)

    @classmethod
    def system(cls, content: str) -> Message:
        return cls(role=MessageRole.SYSTEM, content=content)

    @classmethod
    def assistant(cls, content: str) -> Message:
        return cls(role=MessageRole.ASSISTANT, content=content)


@dataclass
class Completion:
    content: str
    role: MessageRole = MessageRole.ASSISTANT
    usage: dict[str, Any] = field(default_factory=dict)
    model: str = ""
    provider: str = ""
    latency_ms: int = 0
    finish_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "latency_ms": self.latency_ms,
            "finish_reason": self.finish_reason,
            "usage": self.usage,
        }


class ProviderStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class ProviderSpec:
    name: str
    model: str
    status: ProviderStatus = ProviderStatus.UNKNOWN
    priority: int = 100
    supports_streaming: bool = False
    supports_tools: bool = False
    max_tokens: int = 4096
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "model": self.model,
            "status": self.status.value,
            "priority": self.priority,
            "supports_streaming": self.supports_streaming,
            "supports_tools": self.supports_tools,
            "max_tokens": self.max_tokens,
        }


class PermissionLevel(Enum):
    PUBLIC = 0
    USER = 1
    ADMIN = 2
    SYSTEM = 3


@dataclass
class Permission:
    level: PermissionLevel = PermissionLevel.USER
    require_confirmation: bool = False
    require_key: bool = False
    max_calls_per_session: int = 100


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    permission: Permission = field(default_factory=Permission)
    category: str = "general"
    version: str = "1.0.0"
    timeout: int = 30

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "permission_level": self.permission.level.name,
            "require_confirmation": self.permission.require_confirmation,
            "category": self.category,
            "version": self.version,
            "timeout": self.timeout,
        }


@dataclass
class ToolResult:
    success: bool
    output: str = ""
    error: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output[:500] if self.output else "",
            "error": self.error[:500] if self.error else "",
            "duration_ms": self.duration_ms,
        }


class MemoryType(Enum):
    CONVERSATION = "conversation"
    PROJECT = "project"
    CODE = "code"
    USER = "user"
    KNOWLEDGE = "knowledge"
    VECTOR = "vector"


class MemoryImportance(Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class MemoryItem:
    id: str = ""
    content: str = ""
    memory_type: MemoryType = MemoryType.CONVERSATION
    importance: MemoryImportance = MemoryImportance.MEDIUM
    timestamp: float = 0.0
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    access_count: int = 0
    relevance_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content[:200],
            "memory_type": self.memory_type.value,
            "importance": self.importance.name,
            "timestamp": self.timestamp,
            "tags": self.tags[:5],
            "access_count": self.access_count,
            "relevance_score": self.relevance_score,
        }


@dataclass
class MemoryQuery:
    query: str = ""
    memory_type: MemoryType | None = None
    tags: list[str] = field(default_factory=list)
    limit: int = 10
    min_importance: MemoryImportance = MemoryImportance.LOW
    offset: int = 0
    sort_by: str = "relevance"

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "memory_type": self.memory_type.value if self.memory_type else None,
            "limit": self.limit,
            "min_importance": self.min_importance.name,
        }


@dataclass
class WorkflowTemplate:
    name: str
    description: str
    steps: list[str]
    parallel_groups: list[list[str]] = field(default_factory=list)
    timeout: int = 300

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
            "parallel_groups": self.parallel_groups,
        }


@dataclass
class Session:
    id: str = ""
    title: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0
    message_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": self.message_count,
        }


@dataclass
class Project:
    id: str = ""
    name: str = ""
    path: str = ""
    language: str = ""
    file_count: int = 0
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "language": self.language,
            "file_count": self.file_count,
        }


@dataclass
class CodeIndex:
    file_path: str
    language: str
    symbols: list[dict] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    classes: list[dict] = field(default_factory=list)
    functions: list[dict] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    last_indexed: float = 0.0
    content_hash: str = ""

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "language": self.language,
            "symbol_count": len(self.symbols),
            "import_count": len(self.imports),
            "class_count": len(self.classes),
            "function_count": len(self.functions),
            "dependency_count": len(self.dependencies),
        }


class ProposalType(Enum):
    OPTIMIZATION = "optimization"
    REFACTOR = "refactor"
    TEST = "test"
    SECURITY = "security"
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"
    CONFIG = "config"
    MONITORING = "monitoring"


class ProposalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Proposal:
    id: str = ""
    type: ProposalType = ProposalType.OPTIMIZATION
    title: str = ""
    description: str = ""
    severity: Severity = Severity.MEDIUM
    status: ProposalStatus = ProposalStatus.PENDING
    target_file: str = ""
    diff: str = ""
    impact: str = ""
    effort: str = ""
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "status": self.status.value,
            "target_file": self.target_file,
            "impact": self.impact,
            "effort": self.effort,
            "created_at": self.created_at,
        }


@dataclass
class AgentSnapshot:
    agent_name: str = ""
    status: str = ""
    call_count: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0
    success_rate: float = 0.0

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "status": self.status,
            "call_count": self.call_count,
            "error_count": self.error_count,
            "avg_latency_ms": self.avg_latency_ms,
            "success_rate": self.success_rate,
        }


@dataclass
class ErrorLog:
    id: str = ""
    source: str = ""
    message: str = ""
    severity: Severity = Severity.MEDIUM
    timestamp: float = 0.0
    resolved: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "message": self.message,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "resolved": self.resolved,
        }


@dataclass
class PerformanceReport:
    period_hours: int = 24
    total_requests: int = 0
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
    agent_stats: list[AgentSnapshot] = field(default_factory=list)
    health_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "period_hours": self.period_hours,
            "total_requests": self.total_requests,
            "avg_latency_ms": self.avg_latency_ms,
            "error_rate": self.error_rate,
            "health_score": self.health_score,
            "agent_stats": [a.to_dict() for a in self.agent_stats],
        }
