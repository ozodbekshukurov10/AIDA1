"""Domain layer tests — entities, events, exceptions."""

import sys, json, time
sys.path.insert(0, '.')
from aidaos.domain.entities import *
from aidaos.domain.events import EventBus, DomainEvent, DomainEventType
from aidaos.domain.exceptions import *

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL: {name}")

# ─── Entity Tests ───
print("=== Entity Tests ===")

msg = Message.user("hello")
check("Message.user() creates user role", msg.role == MessageRole.USER)
check("Message.content is correct", msg.content == "hello")
check("Message.to_dict() has role+content", set(msg.to_dict().keys()) == {"role", "content"})

msg2 = Message.system("system prompt")
check("Message.system() creates system role", msg2.role == MessageRole.SYSTEM)

msg3 = Message.assistant("response")
check("Message.assistant() creates assistant role", msg3.role == MessageRole.ASSISTANT)

comp = Completion(content="Hi!", model="gpt-4", provider="openai", latency_ms=1500)
check("Completion fields", comp.model == "gpt-4" and comp.latency_ms == 1500)

spec = AgentSpec(name="code", capabilities=[AgentCapability.CODE], description="Code agent")
check("AgentSpec.name", spec.name == "code")
check("AgentSpec.capabilities", AgentCapability.CODE in spec.capabilities)

ctx = AgentContext(task_id="t1", prompt="write code")
check("AgentContext.task_id", ctx.task_id == "t1")
check("AgentContext.to_dict()", "task_id" in ctx.to_dict())

result = AgentResult(task_id="t1", content="done", status=AgentStatus.DONE)
check("AgentResult.success", result.success is True)
result2 = AgentResult(task_id="t2", status=AgentStatus.ERROR, error="fail")
check("AgentResult.success=False on error", result2.success is False)

t_spec = ToolSpec(name="search", description="Search tool")
check("ToolSpec.name", t_spec.name == "search")
check("ToolSpec.to_dict()", "name" in t_spec.to_dict())

t_result = ToolResult(success=True, output="found")
check("ToolResult.success", t_result.success is True)

mem_item = MemoryItem(id="m1", content="test", memory_type=MemoryType.CONVERSATION)
check("MemoryItem.to_dict()", mem_item.to_dict()["id"] == "m1")

mem_query = MemoryQuery(query="test", limit=5, memory_type=MemoryType.CODE)
check("MemoryQuery.query", mem_query.query == "test")

session = Session(id="s1", title="Test Session")
check("Session.to_dict()", session.to_dict()["id"] == "s1")

proj = Project(id="p1", name="test-project", path="/tmp/test")
check("Project.name", proj.name == "test-project")

wt = WorkflowTemplate(name="test", description="Test workflow", steps=["a", "b"])
check("WorkflowTemplate.steps", len(wt.steps) == 2)

prop = Proposal(id="pr1", type=ProposalType.REFACTOR, title="Refactor X",
                severity=Severity.MEDIUM)
check("Proposal.to_dict()", prop.to_dict()["type"] == "refactor")

snap = AgentSnapshot(agent_name="test", call_count=10, error_count=2, avg_latency_ms=500)
check("AgentSnapshot.to_dict()", snap.to_dict()["call_count"] == 10)

err_log = ErrorLog(id="e1", source="test", message="test error", severity=Severity.HIGH)
check("ErrorLog.to_dict()", err_log.to_dict()["severity"] == "high")

report = PerformanceReport(period_hours=24, total_requests=100, avg_latency_ms=200)
check("PerformanceReport.to_dict()", report.to_dict()["total_requests"] == 100)

code_idx = CodeIndex(file_path="test.py", language="python", symbols=[{"name": "fn"}])
check("CodeIndex.to_dict()", code_idx.to_dict()["language"] == "python")

# ─── Enum Tests ───
check("AgentCapability has CODE", AgentCapability.CODE in AgentCapability)
check("AgentStatus has DONE", AgentStatus.DONE in AgentStatus)
check("MemoryType has 6 variants", len(MemoryType) == 6)
check("ProposalType has 8 variants", len(ProposalType) == 8)
check("ProposalStatus has 5 variants", len(ProposalStatus) == 5)
check("Severity has 5 variants", len(Severity) == 5)
check("PermissionLevel.PUBLIC.value", PermissionLevel.PUBLIC.value == 0)
check("PermissionLevel.SYSTEM.value", PermissionLevel.SYSTEM.value == 3)

# ─── Event Bus Tests ───
print("\n=== Event Bus Tests ===")
bus = EventBus()

events = []
def handler1(e):
    events.append(("h1", e.event_type.name))

bus.subscribe(DomainEventType.AGENT_STARTED, handler1)
bus.subscribe(DomainEventType.AGENT_COMPLETED, handler1)

bus.publish(DomainEvent(DomainEventType.AGENT_STARTED, "test", {"agent": "a1"}))
check("Event published", len(events) == 1)
check("Event type correct", events[0][1] == "AGENT_STARTED")

bus.publish(DomainEvent(DomainEventType.AGENT_COMPLETED, "test", {"agent": "a1"}))
check("Second event received", len(events) == 2)

bus.unsubscribe(DomainEventType.AGENT_STARTED, handler1)
bus.publish(DomainEvent(DomainEventType.AGENT_STARTED, "test", {}))
check("Unsubscribe works", len(events) == 2)

history = bus.get_history()
check("History returns events", len(history) >= 2)
bus.clear()
check("Clear works", len(bus.get_history()) == 0)

# ─── Exception Tests ───
print("\n=== Exception Tests ===")

try:
    raise AgentNotFoundError("missing")
except AgentNotFoundError as e:
    check("AgentNotFoundError.code", e.code == "AGENT_NOT_FOUND")
    check("AgentNotFoundError.status", e.status_code == 404)

try:
    raise ToolPermissionError("no access")
except ToolPermissionError as e:
    check("ToolPermissionError.code", e.code == "TOOL_PERMISSION_DENIED")
    check("ToolPermissionError.status", e.status_code == 403)

try:
    raise ProviderOfflineError("provider down")
except ProviderOfflineError as e:
    check("ProviderOfflineError.code", e.code == "PROVIDER_OFFLINE")
    check("ProviderOfflineError.status", e.status_code == 503)

try:
    raise ValidationError("bad input")
except ValidationError as e:
    check("ValidationError.code", e.code == "VALIDATION_ERROR")
    check("ValidationError.status", e.status_code == 400)

# Check that all exceptions inherit from AIDAError
all_exceptions = [
    AgentError, AgentNotFoundError, AgentExecutionError,
    ToolError, ToolNotFoundError, ToolPermissionError, ToolTimeoutError,
    ProviderError, ProviderNotFoundError, ProviderOfflineError, ProviderFallbackError,
    MemoryError, MemoryNotFoundError, MemoryStorageError,
    WorkflowError, WorkflowStepError,
    SessionError, SessionNotFoundError,
    ValidationError, ConfigurationError,
    PluginError, PluginNotFoundError,
    ProposalError, ProposalNotFoundError,
    CodeError, DatabaseError,
]
for exc in all_exceptions:
    check(f"{exc.__name__} inherits AIDAError", issubclass(exc, AIDAError))

# ─── Permission Tests ───
print("\n=== Permission Tests ===")
p = Permission(level=PermissionLevel.ADMIN, require_confirmation=True)
check("Permission.level", p.level == PermissionLevel.ADMIN)
check("Permission.require_confirmation", p.require_confirmation is True)

# ─── Value Object Tests ───
print("\n=== Value Object Tests ===")
check("ProviderStatus has ONLINE", ProviderStatus.ONLINE in ProviderStatus)
ps = ProviderSpec(name="ollama", model="llama3", status=ProviderStatus.ONLINE)
check("ProviderSpec.to_dict()", ps.to_dict()["status"] == "online")

# Results
total = passed + failed
print(f"\n{'='*40}")
print(f"Results: {passed}/{total} passed, {failed} failed")
if failed > 0:
    sys.exit(1)
print("All domain tests passed!")
