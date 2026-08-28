# AIDA — Architecture Goals

## 1. Architecture Style: Clean Architecture + Event-Driven + Modular Monolith

AIDA adopts a **Clean Architecture** core with **Event-Driven** communication and a **Modular Monolith** deployment strategy. This combination provides:

- **Testability** — every use case can be tested with mock adapters
- **Independence** — frameworks (Django, DRF, SQLite) are details, not constraints
- **Evolvability** — modules can be extracted to microservices when scale demands
- **Observability** — every significant action publishes a domain event

## 2. Layer Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                            │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐   │
│  │  REST API (DRF)  │  │   CLI (argparse) │  │   WebSocket   │   │
│  │  /api/v2/*       │  │  aidaos:cli      │  │   (future)    │   │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬───────┘   │
│           │                     │                      │          │
│           └──────────┬──────────┴──────────┬───────────┘          │
│                      │                     │                      │
│                      ▼                     ▼                      │
│              ┌─────────────────────────────────────┐              │
│              │       APPLICATION LAYER              │              │
│              │                                      │              │
│              │  ┌──────────────────────────────┐    │              │
│              │  │        Use Cases             │    │              │
│              │  │  Chat  Agent  Tool  Code     │    │              │
│              │  │  Memory Workflow Improvement │    │              │
│              │  └──────────────┬───────────────┘    │              │
│              │                 │                     │              │
│              │  ┌──────────────┴───────────────┐    │              │
│              │  │          DTOs                │    │              │
│              │  └──────────────────────────────┘    │              │
│              └──────────────────┬──────────────────┘              │
│                                 │                                 │
│                                 ▼                                 │
│              ┌─────────────────────────────────────┐              │
│              │          DOMAIN LAYER                │              │
│              │                                      │              │
│              │  ┌────────────┐  ┌────────────────┐  │              │
│              │  │  Entities  │  │  Value Objects  │  │              │
│              │  │  AgentSpec │  │  Completion     │  │              │
│              │  │  ToolSpec  │  │  StreamingChunk │  │              │
│              │  │  MemoryItem│  │  AgentResult    │  │              │
│              │  └────────────┘  └────────────────┘  │              │
│              │                                      │              │
│              │  ┌────────────┐  ┌────────────────┐  │              │
│              │  │  Events    │  │  Exceptions     │  │              │
│              │  │  EventBus  │  │  AIDAError      │  │              │
│              │  │  DomainEvent│  │  AgentError    │  │              │
│              │  └────────────┘  └────────────────┘  │              │
│              │                                      │              │
│              │  ┌────────────────────────────────┐  │              │
│              │  │  Repository Interfaces (Ports)  │  │              │
│              │  │  ProviderRepo  AgentRepo        │  │              │
│              │  │  ToolRepo      MemoryRepo       │  │              │
│              │  │  SessionRepo   MetricsRepo      │  │              │
│              │  │  KnowledgeRepo ProjectRepo      │  │              │
│              │  │  WorkflowRepo                    │  │              │
│              │  └────────────────────────────────┘  │              │
│              └──────────────────┬──────────────────┘              │
│                                 │                                 │
│                                 ▼                                 │
│              ┌─────────────────────────────────────┐              │
│              │      INFRASTRUCTURE LAYER            │              │
│              │                                      │              │
│              │  ┌──────────┐  ┌─────────┐  ┌─────┐  │              │
│              │  │  LLM     │  │ Agents  │  │Tools│  │              │
│              │  │  Gateway │  │ Adapter │  │Adptr│  │              │
│              │  └──────────┘  └─────────┘  └─────┘  │              │
│              │  ┌──────────┐  ┌─────────┐  ┌─────┐  │              │
│              │  │ Persist. │  │ Codebase│  │Plugin│  │              │
│              │  │ SQLite   │  │ Indexer │  │Loader│  │              │
│              │  └──────────┘  └─────────┘  └─────┘  │              │
│              │  ┌──────────┐  ┌────────────────────┐ │              │
│              │  │  Config  │  │  Monitoring         │ │              │
│              │  │  Settings│  │  Metrics + Logging   │ │              │
│              │  └──────────┘  └────────────────────┘ │              │
│              └──────────────────────────────────────┘              │
└──────────────────────────────────────────────────────────────────┘

                        DI Container (wires everything)
```

## 3. Key Architecture Decisions

### Decision 1: Modular Monolith (Not Microservices)

**Context**: AIDA is early-stage with a single developer. Microservices would introduce network latency, distributed debugging complexity, and operational overhead without proven need for independent scaling.

**Decision**: Build as a modular monolith with strict module boundaries, domain events, and interface-based communication. Each module (`agents`, `tools`, `memory`, `providers`) is a well-defined package with explicit public API. When scale demands independent deployment of a module (e.g., agent execution as a separate service), the interface boundary makes extraction trivial.

**Consequence**: Single process deployment, shared memory for EventBus, simpler debugging. Future extraction of hot modules is cheap due to interface-based boundaries.

### Decision 2: Custom DI Container (Not Django's Built-in)

**Context**: Django's dependency injection is implicit (middleware, context processors, global request). Clean Architecture requires explicit, testable dependency injection at the application boundary.

**Decision**: Custom `AIDAContainer` in `aidaos/container.py` that registers repositories by interface and resolves use cases with their dependencies. Provides `singleton` and `transient` lifetimes, and a validated `initialize()` method.

**Consequence**: Slightly more boilerplate than auto-wiring frameworks (like `inject` or `dependency-injector`), but zero external dependency, full control over lifecycle, and simple to understand.

### Decision 3: SQLite for Development/Small Deployments, PostgreSQL for Production

**Context**: SQLite is zero-config, file-based, and sufficient for single-user development and small teams. It does not support concurrent writes at scale.

**Decision**: All repository adapters implement `ProviderRepository`, `MemoryRepository`, etc. against SQLite for development. PostgreSQL adapter variants will be added when production deployment requires concurrent session support. The interface abstraction makes this a drop-in replacement.

**Consequence**: Phase 0-1 uses multiple SQLite files (one per domain concern). Phase 2+ migrates to PostgreSQL with a migration strategy.

### Decision 4: Synchronous Django with Async Bridge (Not Full ASGI)

**Context**: Django's synchronous ORM, middleware, and ecosystem are mature. Full ASGI migration would be a massive refactor. However, LLM streaming and concurrent agent execution need async.

**Decision**: Keep Django WSGI for the API layer. Use `ThreadPoolExecutor` + `asyncio.run_coroutine_threadsafe` pattern for async operations (LLM calls, agent execution). The `aidaos/use_cases/` are written as async functions but called through the sync-to-async bridge.

**Consequence**: Some overhead from thread pool management. Future option to port hot paths to ASGI (e.g., streaming endpoint) while keeping CRUD endpoints on WSGI.

### Decision 5: Custom Test Framework (Not pytest)

**Context**: The project currently uses a custom minimal test harness with `check()` functions and global counters. This was chosen for simplicity and zero-dependency testing.

**Decision**: Migrate to `pytest` in Phase 1. The custom harness lacks fixtures, parametrization, reporting, and CI integration. `pytest` is the Python standard and provides all needed features.

**Consequence**: Migration effort is minimal (158 tests). The custom `check()` pattern is easily translatable to `assert`.

## 4. Module Boundaries & Contracts

Each module defines its contract through:

1. **Repository Interface** in `domain/interfaces/` — the contract the domain expects
2. **Adapter Class** in `infrastructure/*/` — the implementation that satisfies the contract
3. **DTO** in `application/dtos.py` — the data shape crossing application boundaries
4. **Domain Events** in `domain/events.py` — the communication channel between modules

## 5. Dependency Injection

```python
# container.py — wire everything
container = AIDAContainer()
container.register_provider_repo(ProviderRepoAdapter())
container.register_agent_repo(AgentRepoAdapter())
container.register_tool_repo(ToolRepoAdapter())
container.register_memory_repo(MemoryRepoAdapter())

# Use cases pull their dependencies from the container
chat_uc = container.chat_use_case()  # auto-wired with all repos
result = await chat_uc.execute(ChatRequest(...))
```

## 6. Event Bus Architecture

```
┌─────────┐     ┌───────────┐     ┌──────────┐
│ Producer│────▶│ EventBus  │────▶│ Consumer │
└─────────┘     │           │     └──────────┘
                 │ publish() │
                 │ subscribe()│
                 │            │
                 │ DomainEvent│
                 │ ┌────────┐│
                 │ │type    ││
                 │ │payload ││
                 │ │metadata││
                 │ └────────┘│
                 └───────────┘
```

- Synchronous in-process (Phase 0-1)
- Future: async message broker (Redis Streams / NATS) for cross-process events
- All events logged for audit trail

## 7. Data Flow: Chat Request

```
HTTP POST /api/v2/chat/  (REST API)
  │
  ▼
ChatRequest DTO  (validates input)
  │
  ▼
ChatUseCase.execute(request)  (application layer)
  │
  ├──► EventBus.publish(TASK_CREATED)
  │
  ├──► ProviderGateway.complete(messages)  (via ProviderRepo interface)
  │     │
  │     ├──► ProviderAdapter.complete()     (infrastructure)
  │     │     │
  │     │     └──► LLM API call (Ollama/Gemini/OpenAI)
  │     │
  │     └──◄── Completion response
  │
  ├──► MemoryUseCase.store(conversation)   (via MemoryRepo)
  │
  ├──► EventBus.publish(TASK_COMPLETED)
  │
  └──► ChatResponse DTO
        │
        ▼
HTTP 200 / SSE stream
```

## 8. Data Flow: Agent Task

```
HTTP POST /api/v2/agents/execute/
  │
  ▼
AgentExecuteRequest DTO
  │
  ▼
AgentExecuteUseCase.execute(request)
  │
  ├──► TaskRouter.classify(request)
  │     └──► Intent analysis → Agent selection
  │
  ├──► AgentRepository.execute(agent_spec, context)
  │     │
  │     ├──► AgentOrchestrator.execute()
  │     │     │
  │     │     ├──► memory_retrieve()  (past context)
  │     │     │
  │     │     ├──► tool_execute()     (if needed)
  │     │     │
  │     │     ├──► llm_complete()     (core reasoning)
  │     │     │
  │     │     └──► memory_store()     (new context)
  │     │
  │     └──► AgentResult
  │
  ├──► EventBus.publish(AGENT_COMPLETED)
  │
  └──► AgentExecuteResponse DTO
```

## 9. Technology Choices

| Component | Choice | Rationale |
|---|---|---|
| Language | Python 3.10+ | AI/ML ecosystem, clean syntax, async support |
| Web Framework | Django 4.2+ | Mature ORM, admin, auth, DRF integration |
| API Framework | DRF 3.15+ | Browsable API, serialization, auth, throttling |
| Database (dev) | SQLite | Zero-config, file-based, sufficient for dev |
| Database (prod) | PostgreSQL | Concurrency, JSONB, full-text search, extensions |
| Cache | Redis | Session store, rate limiting, provider health cache |
| Async Bridge | ThreadPoolExecutor | Sync Django with async LLM calls |
| Container | Docker | Reproducible environments, CI/CD, deployment |
| Frontend | React 19 + TypeScript | Component model, type safety, ecosystem |
| Build | Vite 6 | Fast HMR, Tailwind v4 integration |
| Testing | pytest (planned) | Fixtures, parametrization, CI integration |
| CI/CD | GitHub Actions (planned) | Ecosystem, matrix testing, Docker build |

## 10. Architecture Rules (Enforced)

| Rule | Enforcement | Severity |
|---|---|---|
| Domain: zero imports from outer layers | `pylint` / `import-linter` | BLOCKER |
| Application: only imports `domain.*` | `import-linter` | BLOCKER |
| Infrastructure: must implement domain interfaces | Type check on adapter registration | ERROR |
| Presentation: calls use cases, not infrastructure directly | Code review | WARNING |
| DTO validation at all API boundaries | DRF serializer / DTO validator | BLOCKER |
| No `eval()`/`exec()` with unsanitized input | `bandit` SAST | BLOCKER |
| No raw SQL without table-name whitelist | `bandit` + code review | BLOCKER |
| Every public method must have type hints | `mypy --strict` | ERROR |
| Every use case must have a corresponding test | Coverage CI gate | WARNING |
| All events must be logged | Middleware / decorator | WARNING |
