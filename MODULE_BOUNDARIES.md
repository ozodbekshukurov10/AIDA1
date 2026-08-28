# AIDA — Module Boundaries

## 1. Module Contract Template

Every module in AIDA has a formal contract defined by:

- **Responsibilities** — what this module owns
- **Boundaries** — what this module explicitly does NOT do
- **Entry Points** — how other modules interact with it
- **Exit Points** — how this module interacts with other modules
- **Dependencies** — what this module requires from other modules
- **Independencies** — what this module does NOT depend on

## 2. Domain Layer Modules

### 2.1 `domain/entities/`

| Aspect | Definition |
|---|---|
| **Responsibility** | Define business entities, value objects, and enumerations |
| **Boundary** | No behavior, no persistence, no serialization beyond `to_dict()` |
| **Entry Points** | Imported by all layers |
| **Exit Points** | Entities used as parameters and return types in interfaces |
| **Dependencies** | None (zero imports outside Python stdlib) |
| **Independent from** | ALL other modules |

### 2.2 `domain/events/`

| Aspect | Definition |
|---|---|
| **Responsibility** | Define domain events and the in-process EventBus |
| **Boundary** | No persistence of events, no guaranteed delivery |
| **Entry Points** | `EventBus.subscribe()`, `EventBus.publish()` |
| **Exit Points** | Event notifications to subscribers |
| **Dependencies** | None (zero imports outside Python stdlib) |
| **Independent from** | ALL other modules |

### 2.3 `domain/exceptions/`

| Aspect | Definition |
|---|---|
| **Responsibility** | Define typed exception hierarchy |
| **Boundary** | No error handling, no logging |
| **Entry Points** | `raise AgentNotFoundError(...)` |
| **Exit Points** | Caught by outer layers for error mapping |
| **Dependencies** | None (zero imports outside Python stdlib) |
| **Independent from** | ALL other modules |

### 2.4 `domain/interfaces/`

| Aspect | Definition |
|---|---|
| **Responsibility** | Define repository contracts (ports) |
| **Boundary** | No implementations, no concrete classes |
| **Entry Points** | Imported by Infrastructure (to implement) and Application (to use) |
| **Exit Points** | Interface methods define the contract |
| **Dependencies** | `domain/entities/` (for parameter/return types) |
| **Independent from** | Application, Kernel, Infrastructure, Presentation |

## 3. Application Layer Modules

### 3.1 `application/use_cases/chat/`

| Aspect | Definition |
|---|---|
| **Responsibility** | Orchestrate chat completion: validate input, retrieve context, call model, store history |
| **Boundary** | Does NOT make HTTP calls, does NOT access database directly |
| **Entry Points** | `SendMessageUseCase.execute(ChatRequest) → ChatResponse` |
| **Exit Points** | Calls `ModelGateway.chat()`, `MemoryStore.store()`, `SessionRepository.add_message()` |
| **Dependencies** | `domain/interfaces/SessionRepository`, `kernel/models/ModelGateway`, `kernel/memory/MemoryStore` |
| **Independent from** | Infrastructure (directly), Presentation, Plugins |

### 3.2 `application/use_cases/agents/`

| Aspect | Definition |
|---|---|
| **Responsibility** | Route tasks, manage agent execution lifecycle |
| **Boundary** | Does NOT implement agent logic |
| **Entry Points** | `ExecuteTaskUseCase.execute(AgentExecuteRequest) → AgentExecuteResponse` |
| **Exit Points** | Calls `AgentRegistry.find_best()`, `AgentEngine.execute()` |
| **Dependencies** | `kernel/agents/AgentRegistry`, `kernel/agents/BaseAgent`, `kernel/memory/MemoryStore` |
| **Independent from** | Infrastructure (directly), Presentation, Plugins |

### 3.3 `application/use_cases/tools/`

| Aspect | Definition |
|---|---|
| **Responsibility** | Validate, execute, and return tool results |
| **Boundary** | Does NOT implement tool logic |
| **Entry Points** | `InvokeToolUseCase.execute(ToolExecuteRequest) → ToolExecuteResponse` |
| **Exit Points** | Calls `ToolRegistry.get()`, `ToolExecutor.execute()` |
| **Dependencies** | `kernel/tools/ToolRegistry`, `kernel/tools/BaseTool`, `security/authorization/PermissionChecker` |
| **Independent from** | Infrastructure (directly), Presentation, Plugins |

## 4. Kernel Layer Modules

### 4.1 `kernel/agents/`

| Aspect | Definition |
|---|---|
| **Responsibility** | Agent lifecycle management, task routing, intent classification, multi-agent orchestration |
| **Boundary** | Does NOT implement agent-specific logic (that belongs in `builtin/`) |
| **Entry Points** | `AgentRegistry.register()`, `AgentEngine.execute()`, `TaskRouter.classify()` |
| **Exit Points** | Calls `BaseAgent.execute()`, `ModelGateway.chat()`, `MemoryStore.store()` |
| **Dependencies** | `domain/entities/AgentSpec`, `kernel/memory/MemoryStore`, `kernel/models/ModelGateway`, `kernel/tools/ToolRegistry` |
| **Independent from** | Infrastructure (directly), Application, Presentation |

### 4.2 `kernel/memory/`

| Aspect | Definition |
|---|---|
| **Responsibility** | Multi-tier memory: storage, retrieval, ranking, compression, pruning |
| **Boundary** | Does NOT implement persistence (delegates to `MemoryRepository` interface) |
| **Entry Points** | `MemoryManager.store()`, `MemoryRetriever.retrieve()`, `MemorySearch.search()` |
| **Exit Points** | Calls `MemoryRepository.store()`, `MemoryRepository.search()` |
| **Dependencies** | `domain/interfaces/MemoryRepository`, `domain/entities/MemoryItem` |
| **Independent from** | Application, Presentation, Plugins |

### 4.3 `kernel/tools/`

| Aspect | Definition |
|---|---|
| **Responsibility** | Tool registration, execution with sandboxing, permission checking, rate limiting |
| **Boundary** | Does NOT implement tool-specific logic (that belongs in `builtin/`) |
| **Entry Points** | `ToolRegistry.register()`, `ToolExecutor.execute()` |
| **Exit Points** | Calls `BaseTool.execute()`, `PluginSandbox.run()`, `RateLimiter.check()` |
| **Dependencies** | `domain/entities/ToolSpec`, `plugins/Sandbox`, `monitoring/MetricsCollector` |
| **Independent from** | Application, Presentation |

### 4.4 `kernel/models/`

| Aspect | Definition |
|---|---|
| **Responsibility** | LLM provider registration, capability-based routing, automatic fallback, health monitoring |
| **Boundary** | Does NOT make HTTP calls directly (delegates to `ModelProvider` implementations) |
| **Entry Points** | `ModelGateway.chat()`, `ModelGateway.chat_stream()`, `ModelRouter.select_model()` |
| **Exit Points** | Calls `ModelProvider.chat()`, `HealthChecker.check()`, `CacheProvider.get()` |
| **Dependencies** | `domain/entities/Message`, `domain/entities/Completion`, `infrastructure/cache/CacheProvider` |
| **Independent from** | Application, Presentation |

### 4.5 `kernel/knowledge/`

| Aspect | Definition |
|---|---|
| **Responsibility** | Fact extraction, text embedding, knowledge indexing, semantic search |
| **Boundary** | Does NOT implement vector storage directly (delegates to `KnowledgeRepository`) |
| **Entry Points** | `KnowledgeEngine.add()`, `KnowledgeEngine.search()`, `KnowledgeExtractor.extract()` |
| **Exit Points** | Calls `KnowledgeRepository.add()`, `EmbeddingService.embed()` |
| **Dependencies** | `domain/interfaces/KnowledgeRepository`, `domain/entities/KnowledgeItem` |
| **Independent from** | Application, Presentation |

### 4.6 `kernel/codebase/`

| Aspect | Definition |
|---|---|
| **Responsibility** | AST-based code indexing, symbol search, dependency graph, quality analysis |
| **Boundary** | Does NOT modify code, does NOT execute code |
| **Entry Points** | `CodebaseIndexer.index_project()`, `CodebaseSearcher.search()`, `CodebaseAnalyzer.analyze()` |
| **Exit Points** | Reads files from filesystem, returns analysis results |
| **Dependencies** | Python `ast` module, `domain/entities/CodeIndex` |
| **Independent from** | Application, Presentation, Models |

### 4.7 `kernel/workflow/`

| Aspect | Definition |
|---|---|
| **Responsibility** | DAG-based workflow execution, state persistence, error handling |
| **Boundary** | Does NOT implement step logic (delegates to agents/tools) |
| **Entry Points** | `WorkflowExecutor.execute(template, context) → WorkflowResult` |
| **Exit Points** | Calls `AgentEngine.execute()`, `ToolExecutor.execute()` |
| **Dependencies** | `kernel/agents/AgentEngine`, `kernel/tools/ToolExecutor`, `kernel/memory/MemoryStore` |
| **Independent from** | Infrastructure (directly), Presentation |

## 5. Infrastructure Layer Modules

### 5.1 `infrastructure/persistence/repositories/`

| Aspect | Definition |
|---|---|
| **Responsibility** | Implement domain repository interfaces against concrete databases |
| **Boundary** | Does NOT contain business logic |
| **Entry Points** | Implements `SessionRepository`, `MemoryRepository`, `KnowledgeRepository`, etc. |
| **Exit Points** | SQL queries, cache operations |
| **Dependencies** | `domain/interfaces/*` (all repository interfaces) |
| **Independent from** | Application use cases, Presentation |

### 5.2 `infrastructure/persistence/cache/`

| Aspect | Definition |
|---|---|
| **Responsibility** | Provide caching interface implementations (Redis, in-memory) |
| **Boundary** | Does NOT make caching decisions — only implements |
| **Entry Points** | `CacheProvider.get(key)`, `CacheProvider.set(key, value, ttl)` |
| **Exit Points** | Redis commands, in-memory dict operations |
| **Dependencies** | None (standalone interface) |
| **Independent from** | All business logic modules |

## 6. Presentation Layer Modules

### 6.1 `presentation/api/v2/`

| Aspect | Definition |
|---|---|
| **Responsibility** | Handle HTTP requests, validate input, call use cases, format responses |
| **Boundary** | Does NOT contain business logic, does NOT access infrastructure directly |
| **Entry Points** | HTTP endpoints |
| **Exit Points** | Calls Application use cases, returns HTTP responses |
| **Dependencies** | `application/use_cases/*`, `application/dtos/*`, `security/auth/*` |
| **Independent from** | Infrastructure directly, Kernel directly |

### 6.2 `presentation/cli/`

| Aspect | Definition |
|---|---|
| **Responsibility** | Provide command-line interface for all platform functions |
| **Boundary** | Does NOT contain business logic |
| **Entry Points** | Command invocation |
| **Exit Points** | Calls Application use cases, formats output |
| **Dependencies** | `application/use_cases/*`, `application/dtos/*` |
| **Independent from** | Infrastructure directly, API layer |

## 7. Cross-Cutting Modules

### 7.1 `plugins/`

| Aspect | Definition |
|---|---|
| **Responsibility** | Plugin discovery, loading, validation, registration, sandboxing, lifecycle management |
| **Boundary** | Does NOT implement plugin functionality |
| **Entry Points** | `PluginManager.discover_and_load()`, `PluginRegistry.register()`, `PluginSandbox.execute()` |
| **Exit Points** | Calls `Plugin.initialize()`, `Plugin.execute()` |
| **Dependencies** | `kernel/agents/interfaces/BaseAgent`, `kernel/tools/interfaces/BaseTool`, `kernel/models/interfaces/ModelProvider` |
| **Independent from** | Application use cases, Presentation |

### 7.2 `security/`

| Aspect | Definition |
|---|---|
| **Responsibility** | Authentication, authorization, input validation, audit logging |
| **Boundary** | Does NOT make business decisions |
| **Entry Points** | `AuthProvider.authenticate()`, `PermissionChecker.check()` |
| **Exit Points** | Authentication results, authorization decisions, audit events |
| **Dependencies** | `domain/entities` (for permission models) |
| **Independent from** | Application use cases, Kernel, Infrastructure |

### 7.3 `monitoring/`

| Aspect | Definition |
|---|---|
| **Responsibility** | Metrics collection, structured logging, health checks, distributed tracing |
| **Boundary** | Does NOT affect system behavior — only observes |
| **Entry Points** | `MetricsCollector.increment()`, `Logger.info()`, `HealthChecker.check()` |
| **Exit Points** | Metrics export, log output, health status |
| **Dependencies** | None (standalone) |
| **Independent from** | All business logic modules |

## 8. Module Interaction Matrix

```
                ┌─────────────────────────────────────────────────────────────────┐
                │                    DEPENDS ON                                    │
                │  domain  app  kernel  infra  pres  plugins  security  monitoring │
┌───────────────┼─────────────────────────────────────────────────────────────────┤
│    domain     │   ✅    ❌    ❌     ❌     ❌     ❌       ❌         ❌        │
│    app        │   ✅    ✅    ✅     ❌     ❌     ❌       ❌         ✅        │
│   kernel      │   ✅    ❌    ✅     ❌     ❌     ❌       ❌         ✅        │
│   infra       │   ✅    ❌    ✅     ✅     ❌     ❌       ❌         ✅        │
│   pres        │   ❌    ✅    ❌     ❌     ✅     ❌       ✅         ❌        │
│  plugins      │   ✅    ❌    ✅     ❌     ❌     ✅       ✅         ❌        │
│  security     │   ✅    ❌    ❌     ❌     ❌     ❌       ✅         ❌        │
│ monitoring    │   ❌    ❌    ❌     ❌     ❌     ❌       ❌         ✅        │
└───────────────┴─────────────────────────────────────────────────────────────────┘

Legend: ✅ = allowed dependency, ❌ = forbidden dependency
```

## 9. Module Coupling Limits

| Metric | Limit | Enforcement |
|---|---|---|
| Outgoing dependencies per module | < 5 | `pylint` |
| Incoming dependencies per module | < 10 | Code review |
| Interface methods per module | < 8 | ISP enforcement |
| Circular dependency chains | 0 | `import-linter` |
| Layer violation distance | 0 violations | `import-linter` |

## 10. New Module Checklist

When adding a new module, verify:

```
[ ] Module directory follows naming convention
[ ] Module has all required files (__init__.py, interfaces.py, config.py, exceptions.py, service.py)
[ ] Module responsibilities are clearly documented in README.md
[ ] Module boundaries are documented (does / does not do)
[ ] Module dependencies are within allowed layer rules
[ ] Module does NOT create circular dependencies
[ ] Module interfaces have complete type hints
[ ] Module configuration has sensible defaults
[ ] Module exceptions inherit from AIDAError
[ ] Module has tests in tests/ directory
[ ] Module is registered in the DI container
[ ] Module is registered in import-linter config
