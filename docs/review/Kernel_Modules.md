# AIDA Kernel Modules

**Document:** Book 2, Chapter 1 — Kernel Modules
**Version:** 1.0.0
**Date:** 2026-07-04

---

## Overview

The AI Kernel is composed of **11 core modules**, each responsible for a specific aspect of request processing. Modules communicate exclusively through the **EventBus** and follow strict interface contracts.

---

## Module Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AI KERNEL                             │
│                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │  Request   │ │  Context   │ │  Planner   │              │
│  │  Manager   │ │  Manager   │ │  Manager   │              │
│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘              │
│        │              │              │                       │
│  ┌─────┴──────────────┴──────────────┴─────┐               │
│  │              EVENT BUS                    │               │
│  └─────┬──────────────┬──────────────┬─────┘               │
│        │              │              │                       │
│  ┌─────┴──────┐ ┌─────┴──────┐ ┌────┴───────┐              │
│  │   Model    │ │   Agent    │ │   Tool     │              │
│  │   Router   │ │   Router   │ │   Router   │              │
│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘              │
│        │              │              │                       │
│  ┌─────┴──────────────┴──────────────┴─────┐               │
│  │        WORKFLOW CONTROLLER                │               │
│  └─────┬──────────────┬──────────────┬─────┘               │
│        │              │              │                       │
│  ┌─────┴──────┐ ┌─────┴──────┐ ┌────┴───────┐              │
│  │  Response  │ │  Metrics   │ │  Security  │              │
│  │  Builder   │ │ Collector  │ │ Validator  │              │
│  └────────────┘ └────────────┘ └────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Definitions

### Module 1: RequestManager

**Purpose:** Entry point for all requests. Normalizes, validates, and prioritizes.

```python
class IRequestManager:
    async def receive(raw: RawRequest) -> NormalizedRequest
    async def validate(request: NormalizedRequest) -> ValidationResult
    async def enrich(request: NormalizedRequest) -> EnrichedRequest
    async def prioritize(request: EnrichedRequest) -> PrioritizedRequest
    async def respond(request_id: UUID, response: FinalResponse) -> None
```

**Dependencies:** SecurityValidator (for auth checks)
**Events Published:** RequestReceived, RequestValidated, ResponseDelivered
**Events Consumed:** ResponseReady
**Configuration:**
```yaml
request_manager:
  max_concurrent: 1000
  queue_size: 5000
  request_timeout: 300
  validation_timeout: 1
```

---

### Module 2: ContextManager

**Purpose:** Assembles all context needed for processing a request.

```python
class IContextManager:
    async def load(request: PrioritizedRequest) -> ExecutionContext
    async def inject_memory(context: ExecutionContext) -> ExecutionContext
    async def inject_history(context: ExecutionContext) -> ExecutionContext
    async def inject_knowledge(context: ExecutionContext) -> ExecutionContext
    async def inject_user_profile(context: ExecutionContext) -> ExecutionContext
    async def inject_system_context(context: ExecutionContext) -> ExecutionContext
```

**Dependencies:** MemoryStore, KnowledgeStore, UserProfileStore
**Events Published:** ContextLoaded
**Events Consumed:** RequestValidated
**Configuration:**
```yaml
context_manager:
  history_limit: 20
  memory_limit: 10
  knowledge_limit: 5
  cache_ttl: 60
  timeout: 5
```

---

### Module 3: PlannerManager

**Purpose:** Decomposes complex tasks into executable steps.

```python
class IPlannerManager:
    async def classify(context: ExecutionContext) -> TaskClassification
    async def plan(context: ExecutionContext, classification: TaskClassification) -> ExecutionPlan
    async def decompose(task: Task) -> list[Step]
    async def estimate(plan: ExecutionPlan) -> ResourceEstimate
    async def optimize(plan: ExecutionPlan) -> ExecutionPlan
```

**Dependencies:** ModelRouter (for LLM-assisted planning)
**Events Published:** PlanCreated, TaskClassified
**Events Consumed:** ContextLoaded
**Configuration:**
```yaml
planner_manager:
  strategies:
    simple: rule_based
    medium: llm_assisted
    complex: llm_full
    background: llm_full
  planning_model: deepseek-coder
  max_steps: 20
  timeout: 10
```

---

### Module 4: ModelRouter

**Purpose:** Selects the optimal model for each task step.

```python
class IModelRouter:
    async def select(task: Task, context: ExecutionContext) -> ModelSelection
    async def fallback(selection: ModelSelection, error: Exception) -> ModelSelection
    async def health_check(model_id: str) -> HealthStatus
    async def list_available(task_type: TaskType) -> list[Model]
    async def get_config(model_id: str) -> ModelConfig
```

**Dependencies:** ModelRegistry, HealthChecker
**Events Published:** ModelSelected, ModelFallback, ModelHealthChanged
**Events Consumed:** PlanCreated
**Configuration:**
```yaml
model_router:
  selection_strategy: capability_match
  health_check_interval: 30
  health_check_timeout: 5
  fallback_enabled: true
  cost_aware: true
  max_cost_multiplier: 3.0
```

---

### Module 5: AgentRouter

**Purpose:** Selects and orchestrates agents for task execution.

```python
class IAgentRouter:
    async def select(plan: ExecutionPlan) -> AgentSelection
    async def orchestrate(agents: list[Agent], plan: ExecutionPlan) -> OrchestratorResult
    async def monitor(agents: list[Agent]) -> list[AgentStatus]
    async def fallback(agent: Agent, error: Exception) -> AgentSelection
```

**Dependencies:** AgentRegistry, EventBus
**Events Published:** AgentSelected, AgentOrchestrationStarted, AgentOrchestrationCompleted
**Events Consumed:** PlanCreated, ModelSelected
**Configuration:**
```yaml
agent_router:
  orchestration_patterns:
    sequential: {max_agents: 5, timeout: 300}
    parallel: {max_agents: 10, timeout: 120}
    fan_out: {max_agents: 8, timeout: 180}
    hierarchical: {max_depth: 3, timeout: 600}
  selection_strategy: capability_match
  monitoring_interval: 5
```

---

### Module 6: ToolRouter

**Purpose:** Selects and invokes tools for agents.

```python
class IToolRouter:
    async def select(agent: Agent, task: Task) -> ToolSelection
    async def invoke(tool: Tool, params: dict) -> ToolResult
    async def validate(tool: Tool, params: dict) -> ValidationResult
    async def sandbox(tool: Tool) -> SandboxConfig
    async def list_available(agent: Agent) -> list[Tool]
```

**Dependencies:** ToolRegistry, SandboxManager
**Events Published:** ToolSelected, ToolInvoked, ToolFailed
**Events Consumed:** AgentSelected
**Configuration:**
```yaml
tool_router:
  sandbox_enabled: true
  default_timeout: 30
  max_concurrent_invocations: 50
  permission_check: strict
```

---

### Module 7: WorkflowController

**Purpose:** Executes multi-step workflows with dependency management.

```python
class IWorkflowController:
    async def execute(plan: ExecutionPlan) -> WorkflowResult
    async def step_complete(step: Step, result: StepResult) -> Optional[list[Step]]
    async def step_failed(step: Step, error: Exception) -> RecoveryAction
    async def abort(workflow: Workflow) -> AbortResult
    async def checkpoint(workflow: Workflow) -> Checkpoint
    async def resume(checkpoint: Checkpoint) -> WorkflowResult
    async def get_status(workflow_id: UUID) -> WorkflowStatus
```

**Dependencies:** AgentRouter, ModelRouter, ToolRouter, EventBus
**Events Published:** WorkflowStarted, StepStarted, StepCompleted, StepFailed, WorkflowCompleted, WorkflowFailed
**Events Consumed:** PlanCreated, AgentSelected, ModelSelected
**Configuration:**
```yaml
workflow_controller:
  max_concurrent_workflows: 100
  checkpoint_interval: 1
  max_retries_per_step: 3
  step_timeout: 60
  workflow_timeout: 300
  state_store: redis
```

---

### Module 8: ResponseBuilder

**Purpose:** Assembles final response from step results.

```python
class IResponseBuilder:
    async def build(results: list[StepResult], context: ExecutionContext) -> FinalResponse
    async def format(response: FinalResponse, format: ResponseFormat) -> Any
    async def filter(response: FinalResponse, filters: list[Filter]) -> FinalResponse
    async def stream(results: AsyncGenerator[StepResult]) -> AsyncGenerator[ResponseChunk]
```

**Dependencies:** SecurityValidator (for content filtering)
**Events Published:** ResponseReady
**Events Consumed:** WorkflowCompleted
**Configuration:**
```yaml
response_builder:
  default_format: json
  content_filters:
    - language_filter
    - safety_filter
    - secret_filter
  stream_chunk_size: 100
```

---

### Module 9: MetricsCollector

**Purpose:** Collects and emits metrics for all operations.

```python
class IMetricsCollector:
    async def record(metric: Metric) -> None
    async def counter(name: str, tags: dict) -> Counter
    async def histogram(name: str, tags: dict) -> Histogram
    async def gauge(name: str, tags: dict) -> Gauge
    async def trace(name: str) -> TraceSpan
    async def flush() -> None
```

**Dependencies:** None (standalone)
**Events Published:** MetricsEmitted
**Events Consumed:** All events (for metric collection)
**Configuration:**
```yaml
metrics_collector:
  enabled: true
  export_format: prometheus
  export_interval: 15
  buffer_size: 10000
  labels:
    environment: production
    version: 2.0.0
```

---

### Module 10: SecurityValidator

**Purpose:** Validates security for every request and action.

```python
class ISecurityValidator:
    async def authenticate(request: NormalizedRequest) -> AuthResult
    async def authorize(context: ExecutionContext, action: Action) -> bool
    async def validate_input(data: dict, schema: Schema) -> ValidationResult
    async def scan_content(content: str) -> SecurityScanResult
    async def audit(event: AuditEvent) -> None
```

**Dependencies:** UserRepository, TokenStore
**Events Published:** SecurityViolation, AuthenticationFailed, AuthorizationDenied
**Events Consumed:** RequestReceived (for auth)
**Configuration:**
```yaml
security_validator:
  auth_methods: [jwt, api_key, session]
  jwt_secret_env: AIDA_JWT_SECRET
  max_prompt_length: 100000
  blocked_patterns: [...]
  content_filter: moderate
  audit_enabled: true
```

---

### Module 11: RecoveryManager

**Purpose:** Handles failures and implements recovery strategies.

```python
class IRecoveryManager:
    async def handle_step_failure(step: Step, error: Exception) -> RecoveryAction
    async def handle_model_failure(model: str, error: Exception) -> ModelSelection
    async def handle_agent_failure(agent: str, error: Exception) -> AgentSelection
    async def handle_tool_failure(tool: str, error: Exception) -> ToolSelection
    async def handle_workflow_failure(workflow: Workflow, error: Exception) -> RecoveryAction
    async def get_circuit_breaker(component: str) -> CircuitBreaker
```

**Dependencies:** ModelRouter, AgentRouter, ToolRouter, EventBus
**Events Published:** RecoveryStarted, RecoveryCompleted, CircuitBreakerOpened, CircuitBreakerClosed
**Events Consumed:** StepFailed, ModelFailed, AgentFailed, ToolFailed
**Configuration:**
```yaml
recovery_manager:
  max_retries: 3
  retry_delays: [1, 2, 5]
  circuit_breaker:
    failure_threshold: 5
    recovery_timeout: 30
    half_open_max_calls: 3
  fallback_enabled: true
```

---

## Module Communication Matrix

| From → To | RequestManager | ContextManager | PlannerManager | ModelRouter | AgentRouter | ToolRouter | WorkflowController | ResponseBuilder | MetricsCollector | SecurityValidator | RecoveryManager |
|-----------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **RequestManager** | — | ✓ | | | | | | ✓ | ✓ | ✓ | |
| **ContextManager** | | — | ✓ | | | | | | ✓ | | |
| **PlannerManager** | | | — | ✓ | ✓ | | | | ✓ | | |
| **ModelRouter** | | | | — | ✓ | | ✓ | | ✓ | | ✓ |
| **AgentRouter** | | | | | — | ✓ | ✓ | | ✓ | | ✓ |
| **ToolRouter** | | | | | | — | ✓ | | ✓ | | ✓ |
| **WorkflowController** | | | | | | | — | ✓ | ✓ | | ✓ |
| **ResponseBuilder** | ✓ | | | | | | | — | ✓ | ✓ | |
| **MetricsCollector** | | | | | | | | | — | | |
| **SecurityValidator** | ✓ | | | | | | | ✓ | ✓ | — | |
| **RecoveryManager** | | | | ✓ | ✓ | ✓ | | | ✓ | | — |

---

## Module Lifecycle

### Startup Order

```
1. MetricsCollector      (no dependencies)
2. SecurityValidator     (no dependencies)
3. RecoveryManager       (no dependencies)
4. RequestManager        (depends on SecurityValidator)
5. ContextManager        (depends on MetricsCollector)
6. PlannerManager        (depends on ModelRouter)
7. ModelRouter           (depends on RecoveryManager)
8. AgentRouter           (depends on ModelRouter, RecoveryManager)
9. ToolRouter            (depends on RecoveryManager)
10. WorkflowController   (depends on AgentRouter, ModelRouter, ToolRouter)
11. ResponseBuilder      (depends on SecurityValidator, MetricsCollector)
```

### Shutdown Order

```
1. RequestManager        (stop accepting new requests)
2. WorkflowController    (finish running workflows)
3. ResponseBuilder       (flush pending responses)
4. AgentRouter           (stop agent orchestration)
5. ToolRouter            (stop tool invocations)
6. ModelRouter           (drain model connections)
7. PlannerManager        (finish active plans)
8. ContextManager        (flush context cache)
9. RecoveryManager       (close circuit breakers)
10. SecurityValidator    (close auth connections)
11. MetricsCollector     (flush remaining metrics)
```

---

## Module Health Monitoring

Each module exposes a health check endpoint:

```python
class HealthStatus:
    module: str
    status: str           # healthy | degraded | unhealthy | down
    latency_ms: float
    last_check: datetime
    details: dict         # Module-specific health details
    uptime_seconds: float
    error_rate: float
    active_requests: int
```

Health checks are aggregated into a system-wide health endpoint:

```
GET /api/v1/health/
{
    "status": "healthy",
    "kernel": {
        "request_manager": "healthy",
        "context_manager": "healthy",
        "planner_manager": "healthy",
        "model_router": "degraded",
        "agent_router": "healthy",
        "tool_router": "healthy",
        "workflow_controller": "healthy",
        "response_builder": "healthy",
        "metrics_collector": "healthy",
        "security_validator": "healthy",
        "recovery_manager": "healthy"
    },
    "uptime": 86400,
    "version": "2.0.0"
}
```
