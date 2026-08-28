# AIDA Request Lifecycle

**Document:** Book 2, Chapter 1 — Request Lifecycle
**Version:** 1.0.0
**Date:** 2026-07-04

---

## Overview

Every request to AIDA follows a **15-stage lifecycle** through the AI Kernel. This document defines each stage, its inputs/outputs, and the Kernel module responsible.

---

## Lifecycle Stages

```
Stage 1:  RECEIVE REQUEST
Stage 2:  VALIDATE REQUEST
Stage 3:  AUTHENTICATE
Stage 4:  AUTHORIZE
Stage 5:  CONTEXT LOADING
Stage 6:  MEMORY RETRIEVAL
Stage 7:  TASK CLASSIFICATION
Stage 8:  PLANNING
Stage 9:  MODEL SELECTION
Stage 10: AGENT SELECTION
Stage 11: TOOL SELECTION
Stage 12: EXECUTION
Stage 13: RESPONSE VALIDATION
Stage 14: RESPONSE GENERATION
Stage 15: DELIVERY + AUDIT
```

---

## Detailed Stage Definitions

### Stage 1: Receive Request

**Module:** RequestManager
**Input:** Raw HTTP/WebSocket/gRPC/MQ request
**Output:** NormalizedRequest

```python
class NormalizedRequest:
    request_id: UUID              # Generated unique ID
    source: RequestSource         # HTTP | WebSocket | gRPC | MQ
    user_id: Optional[str]        # From auth token
    session_id: Optional[str]     # Conversation session
    request_type: RequestType     # CHAT | CODE | DEBUG | ...
    payload: dict                 # Request body
    metadata: RequestMetadata     # Headers, IP, user-agent
    timestamp: datetime           # When received
    priority: int                 # Computed priority
```

**Processing:**
1. Assign unique `request_id`
2. Parse raw request into normalized format
3. Extract user identity (if authenticated)
4. Compute priority (user tier × request type × queue depth)
5. Add to priority queue
6. Emit `RequestReceived` event

**Timeout:** 5 seconds
**Failure:** Return 400 Bad Request

---

### Stage 2: Validate Request

**Module:** RequestManager
**Input:** NormalizedRequest
**Output:** ValidatedRequest

```python
class ValidatedRequest:
    request: NormalizedRequest
    validation_result: ValidationResult
    is_valid: bool
    errors: list[ValidationError]
```

**Validation Rules:**
| Rule | Check | Action on Fail |
|------|-------|----------------|
| Schema | JSON Schema compliance | 400 + error details |
| Length | payload < max_prompt_length | 400 + "prompt too long" |
| Type | request_type is supported | 400 + "unsupported type" |
| Format | Required fields present | 400 + missing fields |
| Content | No blocked patterns | 400 + "content blocked" |

**Timeout:** 1 second
**Failure:** Return 400 with validation errors

---

### Stage 3: Authenticate

**Module:** SecurityValidator
**Input:** ValidatedRequest
**Output:** AuthenticatedRequest

```python
class AuthenticatedRequest:
    request: ValidatedRequest
    auth_method: AuthMethod      # JWT | API_KEY | SESSION
    user_id: str
    user_tier: UserTier          # FREE | PREMIUM | ENTERPRISE
    permissions: list[str]
    auth_confidence: float       # 0.0 - 1.0
```

**Authentication Flow:**
```
Extract credentials → Check JWT → Check API Key → Check Session → Fail
                          ↓              ↓              ↓
                    Verify signature  Hash & lookup  Cookie validate
                          ↓              ↓              ↓
                    Decode payload   Check expiry   Load session
                          ↓              ↓              ↓
                    Load user        Load user      Load user
```

**Timeout:** 2 seconds
**Failure:** Return 401 Unauthorized

---

### Stage 4: Authorize

**Module:** SecurityValidator
**Input:** AuthenticatedRequest
**Output:** AuthorizedRequest

```python
class AuthorizedRequest:
    request: AuthenticatedRequest
    authorized_actions: list[Action]
    rate_limit_remaining: int
    quota_remaining: int
```

**Authorization Checks:**
1. RBAC: Does user role allow this request type?
2. ABAC: Do attribute conditions match? (time, location, device)
3. Rate limiting: Has user exceeded rate limit?
4. Quota: Has user exceeded usage quota?
5. Content policy: Does user tier allow this content?

**Timeout:** 1 second
**Failure:** Return 403 Forbidden or 429 Too Many Requests

---

### Stage 5: Context Loading

**Module:** ContextManager
**Input:** AuthorizedRequest
**Output:** ExecutionContext

```python
class ExecutionContext:
    request: AuthorizedRequest
    user_profile: UserProfile
    conversation_history: list[Message]
    system_context: SystemContext
    capabilities: list[str]      # Available capabilities
    config: UserConfig           # User preferences
```

**Context Assembly:**
```
1. Load user profile from DB
2. Load conversation history (last N messages)
3. Load user preferences
4. Build system context (time, version, features)
5. Determine available capabilities
6. Assemble ExecutionContext
```

**Data Sources:**
| Source | Data | Latency |
|--------|------|---------|
| PostgreSQL | User profile, preferences | 5-10ms |
| Redis | Session data, recent history | 1-3ms |
| Memory DB | Conversation history | 5-20ms |
| Knowledge DB | Learned facts | 10-50ms |

**Timeout:** 5 seconds
**Failure:** Degrade gracefully (process without context)

---

### Stage 6: Memory Retrieval

**Module:** ContextManager (Memory sub-module)
**Input:** ExecutionContext
**Output:** ExecutionContext (enriched with memory)

```python
class MemoryContext:
    relevant_facts: list[Fact]        # From knowledge base
    similar_conversations: list[Conv]  # From vector search
    learned_preferences: list[Pref]    # From user memory
    project_context: Optional[Project] # From project memory
```

**Retrieval Pipeline:**
```
Query → Embed → Vector Search → TF-IDF Search → Merge → Rank → Top-K
```

**Retrieval Strategy:**
| Query Type | Primary Search | Secondary Search |
|------------|---------------|-----------------|
| Factual | Knowledge DB (vector) | Memory DB (keyword) |
| Conversational | Memory DB (vector) | Session history |
| Code-related | Code memory (AST) | Project memory |
| User-specific | User memory (profile) | Preference store |

**Timeout:** 10 seconds
**Failure:** Degrade gracefully (process without memory)

---

### Stage 7: Task Classification

**Module:** PlannerManager (Classification sub-module)
**Input:** ExecutionContext
**Output:** TaskClassification

```python
class TaskClassification:
    task_type: TaskType          # CHAT | CODE | DEBUG | PLANNING | ...
    complexity: Complexity       # SIMPLE | MEDIUM | COMPLEX
    estimated_duration: int      # seconds
    required_capabilities: list[str]
    suggested_agents: list[str]
    suggested_model: str
    is_streaming: bool
    is_background: bool
```

**Classification Rules:**
```yaml
classification:
  simple:
    keywords: [hello, thanks, status, help]
    model: fast_chat
    agent: none
    duration: <5s
    
  medium:
    keywords: [write code, explain, summarize, translate]
    model: standard
    agent: single
    duration: 5-30s
    
  complex:
    keywords: [build project, refactor, debug complex, full review]
    model: reasoning
    agent: multi
    duration: 30-300s
    
  background:
    keywords: [analyze repository, generate tests, full audit]
    model: reasoning
    agent: pipeline
    duration: >300s
```

**Timeout:** 1 second
**Failure:** Default to MEDIUM complexity

---

### Stage 8: Planning

**Module:** PlannerManager
**Input:** TaskClassification + ExecutionContext
**Output:** ExecutionPlan

```python
class ExecutionPlan:
    plan_id: UUID
    steps: list[Step]
    dependencies: dict[str, list[str]]  # step_id → [dependency_ids]
    estimated_total_duration: int
    estimated_cost: float
    required_models: list[str]
    required_agents: list[str]
    required_tools: list[str]
    
class Step:
    step_id: str
    description: str
    agent: str
    model: str
    tools: list[str]
    input_schema: dict
    output_schema: dict
    timeout: int
    retry_policy: RetryPolicy
```

**Planning Strategies:**

| Complexity | Strategy | Description |
|------------|----------|-------------|
| SIMPLE | Direct | Single agent, single model, no tools |
| MEDIUM | Sequential | 2-3 steps, sequential execution |
| COMPLEX | DAG | Directed acyclic graph of steps |
| BACKGROUND | Pipeline | Long-running pipeline with checkpoints |

**Plan Example (Complex):**
```
Step 1: Research (ResearchAgent + Gemini)
    ↓
Step 2: Plan (PlannerAgent + DeepSeek)
    ↓
Step 3: Code (CodeAgent + DeepSeek-Coder) [parallel with Step 4]
Step 4: Tests (TestAgent + Qwen) [parallel with Step 3]
    ↓
Step 5: Review (SecurityAgent + GPT-4)
    ↓
Step 6: Document (DocAgent + Qwen)
```

**Timeout:** 10 seconds
**Failure:** Simplify plan (reduce steps)

---

### Stage 9: Model Selection

**Module:** ModelRouter
**Input:** ExecutionPlan + ExecutionContext
**Output:** ModelSelection (per step)

```python
class ModelSelection:
    step_id: str
    primary_model: str
    fallback_models: list[str]
    config: ModelConfig           # temperature, max_tokens, etc.
    estimated_cost: float
    estimated_latency: int
```

**Selection Algorithm:**
```
1. Get required capabilities from step
2. Filter models by capability
3. Filter by availability (health check)
4. Filter by user tier (enterprise gets premium models)
5. Sort by: priority × availability × cost_efficiency
6. Select top model
7. Prepare fallback chain
```

**Health-Aware Routing:**
```
Model Health Check (cached 30s):
  - Last 10 requests: success_rate > 95%? → HEALTHY
  - Last 10 requests: success_rate > 80%? → DEGRADED
  - Last 10 requests: success_rate ≤ 80%? → UNHEALTHY → skip
```

**Timeout:** 2 seconds
**Failure:** Use fallback model

---

### Stage 10: Agent Selection

**Module:** AgentRouter
**Input:** ExecutionPlan + ModelSelection
**Output:** AgentSelection (per step)

```python
class AgentSelection:
    step_id: str
    agent_id: str
    agent_type: str
    model: ModelSelection
    tools: list[ToolSelection]
    config: AgentConfig
    max_iterations: int
```

**Selection Algorithm:**
```
1. Get required capabilities from step
2. Filter agents by capability
3. Filter by availability
4. Score: capability_match × success_rate × speed
5. Select best agent
```

**Timeout:** 2 seconds
**Failure:** Use fallback agent

---

### Stage 11: Tool Selection

**Module:** ToolRouter
**Input:** AgentSelection
**Output:** ToolSelection (per agent)

```python
class ToolSelection:
    agent_id: str
    tools: list[SelectedTool]
    sandbox_config: SandboxConfig
    permissions: list[str]
    
class SelectedTool:
    tool_id: str
    config: dict
    timeout: int
    sandbox: str
```

**Selection Algorithm:**
```
1. Get agent's required tools from Agent Descriptor
2. Filter by availability
3. Check permissions (user tier, sandbox requirements)
4. Configure sandbox (if needed)
5. Return tool list
```

**Timeout:** 1 second
**Failure:** Skip unavailable tools (agent adapts)

---

### Stage 12: Execution

**Module:** WorkflowController
**Input:** ExecutionPlan + ModelSelection + AgentSelection + ToolSelection
**Output:** ExecutionResult

```python
class ExecutionResult:
    plan_id: UUID
    step_results: list[StepResult]
    status: ExecutionStatus       # SUCCESS | PARTIAL | FAILED
    total_duration: int
    total_tokens: int
    total_cost: float
    
class StepResult:
    step_id: str
    status: StepStatus
    output: dict
    tokens_used: int
    model_used: str
    agent_used: str
    tools_used: list[str]
    duration: int
    error: Optional[Exception]
```

**Execution Loop:**
```
for step in plan.steps:
    1. Check dependencies satisfied
    2. Checkpoint workflow state
    3. Execute step (agent + model + tools)
    4. Validate step output
    5. If failed → trigger recovery
    6. If succeeded → update checkpoint
    7. Emit StepCompleted event
    8. Continue to next step
```

**Concurrency:**
- Independent steps execute in parallel via `asyncio.gather()`
- Dependent steps execute sequentially
- Each step has its own timeout

**Timeout:** Per step (configurable, default 60s)
**Failure:** Trigger recovery strategy

---

### Stage 13: Response Validation

**Module:** SecurityValidator + ResponseBuilder
**Input:** ExecutionResult
**Output:** ValidatedResponse

**Validation Checks:**
| Check | Description | Action |
|-------|-------------|--------|
| Content safety | No harmful content | Filter or reject |
| Language | Correct language (Uzbek) | Attempt correction |
| Completeness | Response addresses request | Flag if incomplete |
| Secrets | No API keys, passwords | Redact |
| PII | No personal information | Redact (if configured) |
| Format | Matches expected format | Reformat if needed |

**Timeout:** 2 seconds
**Failure:** Apply filters or return error

---

### Stage 14: Response Generation

**Module:** ResponseBuilder
**Input:** ValidatedResponse
**Output:** FinalResponse

```python
class FinalResponse:
    request_id: UUID
    status: ResponseStatus
    content: str | dict
    metadata: ResponseMetadata
    streaming: Optional[StreamingGenerator]
    
class ResponseMetadata:
    model_used: str
    agent_used: str
    tokens_total: int
    tokens_input: int
    tokens_output: int
    cost_usd: float
    latency_ms: int
    steps_executed: int
    tools_used: list[str]
    trace_id: str
```

**Format Options:**
| Format | Content-Type | Use Case |
|--------|-------------|----------|
| JSON | application/json | REST API |
| SSE | text/event-stream | Streaming |
| WebSocket | text/plain | Real-time |
| Markdown | text/markdown | Documentation |

**Timeout:** 5 seconds
**Failure:** Return minimal error response

---

### Stage 15: Delivery + Audit

**Module:** RequestManager + MetricsCollector
**Input:** FinalResponse
**Output:** Delivered (HTTP response / WebSocket message / MQ ack)

**Delivery Steps:**
1. Send response to client
2. Record metrics (latency, tokens, cost)
3. Write audit log
4. Update user quota
5. Store conversation in memory
6. Emit `ResponseDelivered` event
7. Clean up temporary resources

**Post-Delivery:**
- Metrics exported to Prometheus (async)
- Audit log written to database (async)
- Memory updated (async)
- No blocking on client response

---

## Lifecycle Timing

| Stage | Target Latency | Maximum |
|-------|---------------|---------|
| 1. Receive | <1ms | 5ms |
| 2. Validate | <1ms | 1s |
| 3. Authenticate | <5ms | 2s |
| 4. Authorize | <1ms | 1s |
| 5. Context Load | <50ms | 5s |
| 6. Memory Retrieval | <100ms | 10s |
| 7. Classification | <10ms | 1s |
| 8. Planning | <50ms | 10s |
| 9. Model Selection | <10ms | 2s |
| 10. Agent Selection | <5ms | 2s |
| 11. Tool Selection | <5ms | 1s |
| 12. Execution | Variable | 300s |
| 13. Response Validation | <10ms | 2s |
| 14. Response Generation | <10ms | 5s |
| 15. Delivery + Audit | <20ms | 5s |
| **TOTAL (simple)** | **<200ms** | **320s** |
| **TOTAL (complex)** | **<30s** | **600s** |

---

## Error Handling Per Stage

| Stage | Error | Recovery |
|-------|-------|----------|
| 1 | Malformed request | 400 Bad Request |
| 2 | Validation failure | 400 + error details |
| 3 | Auth failure | 401 Unauthorized |
| 4 | Forbidden | 403 Forbidden |
| 4 | Rate limited | 429 + Retry-After |
| 5 | Context load failure | Degrade (no context) |
| 6 | Memory failure | Degrade (no memory) |
| 7 | Classification failure | Default to MEDIUM |
| 8 | Planning failure | Simplify plan |
| 9 | Model unavailable | Fallback model |
| 10 | Agent unavailable | Fallback agent |
| 11 | Tool unavailable | Skip tool |
| 12 | Execution failure | Recovery strategy |
| 13 | Validation failure | Apply filters |
| 14 | Build failure | Minimal response |
| 15 | Delivery failure | Retry / MQ fallback |
