# AIDA AI Kernel Architecture

**Document:** Book 2, Chapter 1
**Version:** 1.0.0
**Date:** 2026-07-04
**Author:** AI Architect / Distributed Systems Architect

---

## 1. Vision

The AI Kernel is the **central nervous system** of AIDA. It is a zero-business-logic coordination layer that receives every request, determines the optimal execution path, orchestrates agents/models/tools, and returns structured responses. The Kernel must be:

- **Stateless** — no request-specific state stored between calls
- **Extensible** — new agents, models, tools added via configuration, not code
- **Observable** — every decision logged, traced, and measurable
- **Resilient** — every failure handled with automatic recovery
- **Scalable** — horizontal scaling to 1000+ concurrent requests

---

## 2. Design Principles

### 2.1 Kernel as Microkernel
The Kernel implements a **microkernel pattern** — it contains only the minimal core (request routing, module coordination, lifecycle management) and delegates ALL business logic to external modules (agents, models, tools).

```
┌─────────────────────────────────────────────────┐
│                  AI KERNEL (Core)                │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Request  │→ │ Context  │→ │ Planner  │      │
│  │ Manager  │  │ Manager  │  │ Manager  │      │
│  └──────────┘  └──────────┘  └──────────┘      │
│       ↓              ↓              ↓            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  Model   │  │  Agent   │  │  Tool    │      │
│  │  Router  │  │  Router  │  │  Router  │      │
│  └──────────┘  └──────────┘  └──────────┘      │
│       ↓              ↓              ↓            │
│  ┌──────────────────────────────────────────┐   │
│  │         Workflow Controller               │   │
│  └──────────────────────────────────────────┘   │
│       ↓                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │Response  │  │ Metrics  │  │ Security │      │
│  │ Builder  │  │Collector │  │Validator │      │
│  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────┘
            ↕                    ↕
  ┌─────────────┐      ┌─────────────┐
  │   MODULES   │      │  EXTERNAL   │
  │ Agents      │      │  LLM APIs   │
  │ Models      │      │  Databases  │
  │ Tools       │      │  Services   │
  │ Plugins     │      │  Filesystem │
  └─────────────┘      └─────────────┘
```

### 2.2 Inversion of Control
The Kernel never calls modules directly. It publishes events to the **EventBus**, and modules subscribe to relevant events. This ensures:

- Kernel doesn't know about module implementations
- Modules can be added/removed without Kernel changes
- Cross-cutting concerns (logging, metrics) are handled by EventBus middleware

### 2.3 Convention Over Configuration
Modules register themselves with the Kernel via a **Module Descriptor** — a declarative manifest that specifies capabilities, dependencies, and configuration. The Kernel discovers modules at startup and routes requests based on these descriptors.

---

## 3. Architecture Overview

### 3.1 Layer Diagram

```
Layer 0: Transport Layer
  HTTP | WebSocket | gRPC | Message Queue

Layer 1: Kernel Core
  RequestManager → ContextManager → PlannerManager →
  ModelRouter → AgentRouter → ToolRouter →
  WorkflowController → ResponseBuilder →
  MetricsCollector → SecurityValidator

Layer 2: Module Layer
  AgentRegistry | ModelRegistry | ToolRegistry | PluginRegistry

Layer 3: Provider Layer
  LLM Providers | Vector Stores | Databases | External APIs

Layer 4: Infrastructure Layer
  Redis | PostgreSQL | Message Queue | Object Storage
```

### 3.2 Component Relationships

```
Transport Layer
      ↓ (inbound request)
Kernel Core
      ↓ (module resolution)
Module Layer
      ↓ (provider invocation)
Provider Layer
      ↓ (persistence / external calls)
Infrastructure Layer
      ↑ (response)
Kernel Core
      ↓ (outbound response)
Transport Layer
```

### 3.3 Data Flow

```
Request → Transport → Kernel Core → [10 stages] → Response
                    ↕                 ↕              ↕
              EventBus          Module Layer    Metrics/Logs
```

---

## 4. Kernel Core Modules

### 4.1 Request Manager
**Responsibility:** Receive, validate, and normalize all incoming requests.

```
Interface: IRequestManager
Methods:
  - receive(raw_request: RawRequest) → NormalizedRequest
  - validate(request: NormalizedRequest) → ValidationResult
  - enrich(request: NormalizedRequest) → EnrichedRequest
  - prioritize(request: EnrichedRequest) → PrioritizedRequest
```

**Design Decisions:**
- All request formats (HTTP, WebSocket, gRPC, MQ) are normalized to `NormalizedRequest`
- Validation is schema-based (JSON Schema or Pydantic)
- Priority is computed from: user tier (enterprise > premium > free) × request type × queue depth
- Rate limiting checked here (before any expensive processing)

### 4.2 Context Manager
**Responsibility:** Load and assemble all context needed for processing.

```
Interface: IContextManager
Methods:
  - load(request: PrioritizedRequest) → ExecutionContext
  - inject_memory(context: ExecutionContext) → ExecutionContext
  - inject_history(context: ExecutionContext) → ExecutionContext
  - inject_knowledge(context: ExecutionContext) → ExecutionContext
  - inject_user_profile(context: ExecutionContext) → ExecutionContext
```

**Context Assembly Order:**
1. User authentication + authorization
2. User profile + preferences
3. Conversation history (from memory store)
4. Learned facts (from knowledge base)
5. Task-specific context (from request metadata)
6. System context (time, version, capabilities)

**Design Decision:** Context is assembled **once** per request and passed as an immutable object through the pipeline. This ensures consistency and enables easy debugging.

### 4.3 Planner Manager
**Responsibility:** Decompose complex tasks into executable steps.

```
Interface: IPlannerManager
Methods:
  - plan(context: ExecutionContext) → ExecutionPlan
  - decompose(task: Task) → list[Step]
  - estimate(plan: ExecutionPlan) → ResourceEstimate
  - optimize(plan: ExecutionPlan) → ExecutionPlan
```

**Planning Strategies:**
| Strategy | When | Speed | Quality |
|----------|------|-------|---------|
| Direct | Simple tasks | Fast | Good |
| Sequential | Medium tasks | Medium | Better |
| Parallel | Independent subtasks | Fast | Best |
| Hierarchical | Complex projects | Slow | Best |

**Design Decision:** Planner uses **LLM-assisted decomposition** for complex tasks but falls back to rule-based planning for simple tasks. This balances speed and quality.

### 4.4 Model Router
**Responsibility:** Select the optimal model for each task.

```
Interface: IModelRouter
Methods:
  - select(task: Task, context: ExecutionContext) → ModelSelection
  - fallback(selection: ModelSelection, error: Exception) → ModelSelection
  - health_check(model: ModelId) → HealthStatus
  - list_available(task_type: TaskType) → list[Model]
```

**Routing Rules (declarative, not hardcoded):**
```yaml
model_routing:
  code_generation:
    primary: deepseek-coder
    fallback: [qwen2.5-coder, gpt-4]
    capabilities: [code, function_calling]
    max_tokens: 8192
    
  conversation:
    primary: qwen2.5
    fallback: [gpt-4o-mini, gemini-flash]
    capabilities: [chat, streaming]
    max_tokens: 4096
    
  vision:
    primary: gpt-4o
    fallback: [gemini-pro-vision]
    capabilities: [vision, chat]
    max_tokens: 4096
    
  embedding:
    primary: text-embedding-3-small
    fallback: [bge-small]
    capabilities: [embeddings]
    dimensions: 1536
```

**Design Decision:** Model selection is **config-driven**, not code-driven. Adding a new model requires only a YAML config change, not a code deployment.

### 4.5 Agent Router
**Responsibility:** Select and orchestrate agents for task execution.

```
Interface: IAgentRouter
Methods:
  - select(plan: ExecutionPlan) → AgentSelection
  - orchestrate(agents: list[Agent], plan: ExecutionPlan) → OrchestratorResult
  - monitor(agents: list[Agent]) → list[AgentStatus]
  - fallback(agent: Agent, error: Exception) → AgentSelection
```

**Agent Selection Logic:**
```
Task Type → Required Capabilities → Agent Capabilities → Match Score → Select Best
```

**Orchestration Patterns:**
| Pattern | Use Case | Description |
|---------|----------|-------------|
| Sequential | Linear workflows | Agent A → Agent B → Agent C |
| Parallel | Independent tasks | Agent A ∥ Agent B ∥ Agent C |
| Fan-out/fan-in | Complex analysis | Multiple agents → Merge results |
| Pipeline | Data processing | Agent A → Transform → Agent B |
| Debate | Quality assurance | Agent A argues FOR, Agent B argues AGAINST |

### 4.6 Tool Router
**Responsibility:** Select and invoke tools for agents.

```
Interface: IToolRouter
Methods:
  - select(agent: Agent, task: Task) → ToolSelection
  - invoke(tool: Tool, params: dict) → ToolResult
  - validate(tool: Tool, params: dict) → ValidationResult
  - sandbox(tool: Tool) → SandboxConfig
```

**Tool Registry:**
```yaml
tools:
  git:
    capabilities: [version_control, diff, log]
    sandbox: none
    permissions: [read, write]
    
  python:
    capabilities: [code_execution, data_analysis]
    sandbox: docker
    permissions: [execute]
    timeout: 30s
    
  browser:
    capabilities: [web_browsing, screenshot]
    sandbox: docker
    permissions: [network]
    timeout: 60s
    
  database:
    capabilities: [query, schema]
    sandbox: readonly
    permissions: [read]
    timeout: 10s
```

### 4.7 Workflow Controller
**Responsibility:** Execute multi-step workflows with dependency management.

```
Interface: IWorkflowController
Methods:
  - execute(plan: ExecutionPlan) → WorkflowResult
  - step_complete(step: Step, result: StepResult) → next[Step]
  - step_failed(step: Step, error: Exception) → RecoveryAction
  - abort(workflow: Workflow) → AbortResult
  - checkpoint(workflow: Workflow) → Checkpoint
  - resume(checkpoint: Checkpoint) → WorkflowResult
```

**Workflow State Machine:**
```
PENDING → RUNNING → STEP_COMPLETE → NEXT_STEP → ...
                    ↓
                  STEP_FAILED → RECOVERY → RETRY/ABORT
                    ↓
                  WORKFLOW_COMPLETE → DONE
                    ↓
                  WORKFLOW_FAILED → CLEANUP → ERROR
```

**Design Decision:** Workflow state is stored in Redis (not memory) to survive restarts. Each step completion creates a **checkpoint** enabling resume-after-failure.

### 4.8 Response Builder
**Responsibility:** Assemble final response from step results.

```
Interface: IResponseBuilder
Methods:
  - build(results: list[StepResult], context: ExecutionContext) → Response
  - format(response: Response, format: ResponseFormat) → formatted
  - filter(response: Response, filters: list[Filter]) → Response
  - stream(results: AsyncGenerator[StepResult]) → AsyncGenerator[ResponseChunk]
```

**Response Assembly:**
1. Collect all step results
2. Merge partial results
3. Apply content filters (language, safety, quality)
4. Format output (JSON, SSE, WebSocket)
5. Add metadata (model used, tokens, latency, agent trace)

### 4.9 Metrics Collector
**Responsibility:** Collect and emit metrics for all operations.

```
Interface: IMetricsCollector
Methods:
  - record(metric: Metric) → void
  - counter(name: str, tags: dict) → Counter
  - histogram(name: str, tags: dict) → Histogram
  - gauge(name: str, tags: dict) → Gauge
  - trace(name: str) → TraceSpan
```

**Metrics Categories:**
| Category | Examples |
|----------|----------|
| Request | latency, throughput, error_rate, queue_depth |
| Model | tokens_per_sec, first_token_latency, cost_per_request |
| Agent | execution_time, success_rate, retry_count |
| Tool | invocation_count, error_rate, timeout_count |
| System | cpu_usage, memory_usage, connection_count |

### 4.10 Security Validator
**Responsibility:** Validate security for every request and action.

```
Interface: ISecurityValidator
Methods:
  - authenticate(request: NormalizedRequest) → AuthResult
  - authorize(context: ExecutionContext, action: Action) → bool
  - validate_input(data: dict, schema: Schema) → ValidationResult
  - scan_content(content: str) → SecurityScanResult
  - audit(event: AuditEvent) → void
```

**Security Checks (in order):**
1. Authentication (JWT / API Key / Session)
2. Authorization (RBAC / ABAC)
3. Rate limiting (per user, per IP, per endpoint)
4. Input validation (schema, type, length, content)
5. Content scanning (prompt injection, harmful content)
6. Output filtering (secrets, PII, harmful content)
7. Audit logging (every decision)

---

## 5. Event-Driven Architecture

### 5.1 EventBus

The Kernel communicates with modules exclusively through an **EventBus** — an in-process async event system.

```python
class EventBus:
    """Central event dispatcher — all Kernel communication goes through here."""
    
    async def publish(event: DomainEvent) -> None: ...
    async def subscribe(event_type: Type, handler: EventHandler) -> None: ...
    async def unsubscribe(event_type: Type, handler: EventHandler) -> None: ...
```

### 5.2 Domain Events

| Event | Publisher | Subscribers |
|-------|-----------|-------------|
| `RequestReceived` | RequestManager | ContextManager, MetricsCollector |
| `ContextLoaded` | ContextManager | PlannerManager, SecurityValidator |
| `PlanCreated` | PlannerManager | AgentRouter, ModelRouter |
| `ModelSelected` | ModelRouter | AgentRouter, MetricsCollector |
| `AgentSelected` | AgentRouter | WorkflowController, MetricsCollector |
| `ToolRequired` | AgentRouter | ToolRouter, MetricsCollector |
| `StepStarted` | WorkflowController | MetricsCollector |
| `StepCompleted` | WorkflowController | ResponseBuilder, MetricsCollector |
| `StepFailed` | WorkflowController | RecoveryManager, MetricsCollector |
| `ResponseReady` | ResponseBuilder | RequestManager |
| `MetricsEmitted` | MetricsCollector | (external sinks) |
| `SecurityViolation` | SecurityValidator | RequestManager, MetricsCollector |

### 5.3 Event Flow

```
Request
  → RequestManager.publish(RequestReceived)
    → ContextManager.handle(RequestReceived)
      → ContextManager.publish(ContextLoaded)
        → PlannerManager.handle(ContextLoaded)
          → PlannerManager.publish(PlanCreated)
            → ModelRouter.handle(PlanCreated)
              → ModelRouter.publish(ModelSelected)
                → AgentRouter.handle(ModelSelected)
                  → AgentRouter.publish(AgentSelected)
                    → WorkflowController.handle(AgentSelected)
                      → [Execution loop]
                        → WorkflowController.publish(StepCompleted)
                          → ResponseBuilder.publish(ResponseReady)
                            → RequestManager.deliver(Response)
```

---

## 6. Module System

### 6.1 Module Descriptor

Every module (agent, model, tool, plugin) registers with the Kernel via a **Module Descriptor**:

```python
class ModuleDescriptor:
    id: str                          # Unique identifier
    type: ModuleType                 # AGENT | MODEL | TOOL | PLUGIN
    version: str                     # Semantic version
    capabilities: list[str]          # What this module can do
    dependencies: list[str]          # Required modules
    config_schema: dict              # Configuration schema
    health_check: Callable           # Health check function
    priority: int                    # Routing priority (lower = preferred)
    max_concurrency: int             # Max concurrent executions
    timeout: int                     # Default timeout in seconds
    retry_policy: RetryPolicy        # Retry configuration
    sandbox: SandboxConfig           # Security sandbox requirements
```

### 6.2 Module Registry

```python
class ModuleRegistry:
    """Registry of all available modules."""
    
    def register(descriptor: ModuleDescriptor, module: Module) -> None: ...
    def unregister(module_id: str) -> None: ...
    def get(module_id: str) -> Module: ...
    def list_by_type(type: ModuleType) -> list[Module]: ...
    def list_by_capability(capability: str) -> list[Module]: ...
    def health_check_all() -> dict[str, HealthStatus]: ...
```

### 6.3 Module Lifecycle

```
DISCOVERED → REGISTERED → INITIALIZED → READY → RUNNING → STOPPED
                ↓              ↓           ↓         ↓
            FAILED        FAILED      DEGRADED   FAILED
```

### 6.4 Adding a New Module

To add a new agent/model/tool:
1. Create module class implementing the module interface
2. Create Module Descriptor (declarative)
3. Register with ModuleRegistry
4. Add routing rules to configuration
5. **No Kernel code changes required**

---

## 7. Configuration System

### 7.1 Kernel Configuration

```yaml
kernel:
  max_concurrent_requests: 1000
  request_timeout: 300
  default_model: auto
  
  routing:
    strategy: capability_match
    fallback_chain: [local, ollama, openai, anthropic]
    
  recovery:
    max_retries: 3
    retry_delay: [1, 2, 5]
    circuit_breaker:
      failure_threshold: 5
      recovery_timeout: 30
      
  monitoring:
    metrics_enabled: true
    tracing_enabled: true
    audit_enabled: true
    
  security:
    max_prompt_length: 100000
    blocked_patterns: [...]
    content_filter: moderate
```

### 7.2 Model Configuration

```yaml
models:
  deepseek-coder:
    provider: deepseek
    type: code_generation
    capabilities: [code, function_calling, streaming]
    max_tokens: 8192
    cost_per_1k_tokens: 0.001
    priority: 1
    
  qwen2.5:
    provider: ollama
    type: conversation
    capabilities: [chat, streaming]
    max_tokens: 4096
    cost_per_1k_tokens: 0
    priority: 1
```

### 7.3 Agent Configuration

```yaml
agents:
  planner:
    capabilities: [planning, decomposition]
    model: deepseek-coder
    tools: []
    max_iterations: 5
    
  code:
    capabilities: [code_generation, refactoring]
    model: deepseek-coder
    tools: [git, python, filesystem]
    max_iterations: 10
    
  security:
    capabilities: [security_audit, vulnerability_scan]
    model: gpt-4
    tools: [git, filesystem, database]
    max_iterations: 5
```

---

## 8. Fault Tolerance

### 8.1 Circuit Breaker Pattern

```
CLOSED (normal) → [failure_count ≥ threshold] → OPEN (all calls fail fast)
                                                    ↓
                                              [recovery_timeout]
                                                    ↓
                                            HALF_OPEN (one test call)
                                                    ↓
                                          [success] → CLOSED
                                          [failure] → OPEN
```

### 8.2 Retry Strategy

| Error Type | Retry? | Max Retries | Delay |
|------------|--------|-------------|-------|
| Timeout | YES | 3 | exponential backoff |
| Rate limit | YES | 5 | respect Retry-After |
| Auth failure | NO | 0 | — |
| Model unavailable | YES (fallback) | 1 | immediate |
| Tool failure | YES | 2 | 1s, 2s |
| Network error | YES | 3 | exponential backoff |
| Validation error | NO | 0 | — |

### 8.3 Fallback Chain

```
Primary Model → Fallback Model 1 → Fallback Model 2 → Local Model → Error
```

### 8.4 Graceful Degradation

| Scenario | Degradation |
|----------|-------------|
| Primary model down | Use fallback model |
| All models down | Use local rule-based response |
| Memory system down | Process without memory context |
| Tool unavailable | Inform agent, continue without tool |
| Cache unavailable | Direct database query |
| Redis down | In-memory fallback (single worker) |

---

## 9. Concurrency Model

### 9.1 Request Processing

```
                    ┌─────────────┐
                    │   Incoming   │
                    │   Requests   │
                    └──────┬──────┘
                           ↓
                    ┌─────────────┐
                    │   Priority   │
                    │    Queue     │
                    └──────┬──────┘
                           ↓
              ┌────────────┼────────────┐
              ↓            ↓            ↓
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Worker 1 │ │ Worker 2 │ │ Worker N │
        └──────────┘ └──────────┘ └──────────┘
              ↓            ↓            ↓
        ┌──────────────────────────────────────┐
        │           Shared Resources            │
        │  Redis | PostgreSQL | EventBus       │
        └──────────────────────────────────────┘
```

### 9.2 Async Architecture

- All Kernel modules are **async-native** (Python asyncio)
- I/O operations use `asyncio.gather()` for parallel execution
- CPU-bound work delegated to thread pool via `asyncio.to_thread()`
- Long-running tasks moved to Celery workers

### 9.3 Backpressure

When the system is overloaded:
1. Priority queue drops lowest-priority requests
2. Circuit breakers activate for slow providers
3. New requests receive `503 Service Unavailable` with `Retry-After`
4. Monitoring alerts fire for SRE attention

---

## 10. Observability

### 10.1 Three Pillars

| Pillar | Tool | What |
|--------|------|------|
| **Metrics** | Prometheus | Counters, histograms, gauges |
| **Logs** | ELK / Loki | Structured JSON logs |
| **Traces** | Jaeger / Tempo | Distributed request traces |

### 10.2 Key Metrics

```yaml
metrics:
  request:
    - aida_request_total
    - aida_request_duration_seconds
    - aida_request_queue_depth
    - aida_request_error_total
    
  model:
    - aida_model_tokens_per_second
    - aida_model_first_token_latency_seconds
    - aida_model_cost_dollars
    - aida_model_health_status
    
  agent:
    - aida_agent_execution_duration_seconds
    - aida_agent_success_rate
    - aida_agent_retry_total
    
  system:
    - aida_kernel_cpu_usage
    - aida_kernel_memory_usage
    - aida_kernel_active_requests
```

### 10.3 Distributed Tracing

Every request gets a unique `trace_id` that follows the request through:
1. Request Manager → Context Manager → Planner → Router → Agent → Tool → Response

Each span records:
- Module name
- Start/end time
- Input/output sizes
- Model used
- Tokens consumed
- Errors encountered

---

## 11. Future Extensibility

### 11.1 AGI Readiness

The Kernel is designed to support future AGI capabilities:

| AGI Capability | Kernel Support |
|----------------|----------------|
| Self-improvement | Plugin system enables self-modifying modules |
| Multi-modal | Model router supports vision, audio, video models |
| Tool creation | Tool router can register new tools at runtime |
| Goal decomposition | Planner supports arbitrary task decomposition |
| Memory consolidation | Context manager supports memory lifecycle |
| Cross-domain reasoning | Agent router supports agent collaboration |

### 11.2 Plugin API

```python
class AIDAKernelPlugin:
    """Base class for all Kernel plugins."""
    
    def on_request(self, request: Request) -> Request: ...
    def on_response(self, response: Response) -> Response: ...
    def on_error(self, error: Exception) -> RecoveryAction: ...
    def on_metric(self, metric: Metric) -> None: ...
```

### 11.3 Extension Points

| Extension Point | When | Use Case |
|----------------|------|----------|
| Pre-request middleware | Before processing | Auth, rate limiting, logging |
| Post-request middleware | After processing | Response transformation, caching |
| Model interceptor | Before/after LLM call | Prompt injection, response filtering |
| Agent interceptor | Before/after agent | Permission checking, audit |
| Tool interceptor | Before/after tool | Sandboxing, permission checking |
| Error handler | On any error | Custom recovery, alerting |

---

## 12. Migration Path from Current Architecture

### Phase 1: Kernel Core (Week 1-2)
- Implement RequestManager, ContextManager, ResponseBuilder
- Wire into existing Django views
- No changes to existing modules

### Phase 2: Routing System (Week 3-4)
- Implement ModelRouter, AgentRouter, ToolRouter
- Migrate existing provider system to Module Registry
- Keep existing providers as registered modules

### Phase 3: Workflow Engine (Week 5-6)
- Implement WorkflowController
- Migrate agent orchestration to Kernel workflows
- Add checkpoint/resume capability

### Phase 4: Production Hardening (Week 7-8)
- Add circuit breakers, retry strategies
- Implement distributed tracing
- Add Prometheus metrics
- Load testing to 1000 concurrent requests

---

## Appendix A: Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.14 | Existing codebase, async support |
| Async Framework | asyncio + uvicorn | Native Python async |
| Message Bus | In-process EventBus | Low latency, no external dependency |
| Cache / State | Redis | Fast, supports pub/sub, distributed |
| Task Queue | Celery + Redis | Proven, supports retry, monitoring |
| Metrics | Prometheus | Industry standard, open source |
| Tracing | OpenTelemetry | Vendor-neutral, auto-instrumentation |
| Logging | structlog + JSON | Structured, filterable, production-ready |
| Config | YAML + Pydantic | Declarative, validated, typed |

## Appendix B: Comparison with Existing Architecture

| Aspect | Current (webapp) | Kernel (Book 2) |
|--------|-------------------|-----------------|
| Entry point | AIDAController.chat() | Kernel.receive() |
| Model selection | Hardcoded if/else | Declarative routing rules |
| Agent selection | Keyword matching | Capability-based matching |
| Tool selection | Manual | Registry-based |
| Error handling | try/except blocks | Circuit breaker + retry |
| Observability | Print statements | Prometheus + tracing |
| Extensibility | Code changes | Plugin registration |
| Scalability | Single process | Distributed workers |
| State | In-memory | Redis-backed |
| Configuration | Hardcoded | YAML-driven |
