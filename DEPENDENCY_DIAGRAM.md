# AIDA — Dependency Diagram & Rules

## 1. Module Dependency Graph (Target)

```
                          ┌───────────────┐
                          │  Container.py │  (DI wiring — depends on EVERYTHING)
                          └───────┬───────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
   ┌────────────┐         ┌────────────┐         ┌────────────┐
   │Presentation│         │ Application│         │   Kernel   │
   └──────┬─────┘         └──────┬──────┘         └──────┬─────┘
          │                      │                       │
          │              ┌───────┴───────┐               │
          │              │    Domain     │◄──────────────┘
          │              └───────┬───────┘
          │                      │
          │              ┌───────┴───────┐
          └─────────────►│Infrastructure │◄────────────────┘
                         └───────────────┘

Cross-Cutting:  Security ──► (all layers)
                Monitoring ─► (all layers)  [read-only, no business logic]
                Config ─────► (all layers)  [read-only, no business logic]
                Events ─────► (all layers)  [in-process pub/sub]

Plugins:        Plugin Interfaces ──► Kernel Interfaces
                Plugin Implementations ──► Plugin Interfaces (only)
```

## 2. Detailed Module Dependencies

### 2.1 Domain Layer Dependencies

| Module | Depends On | Depended On By |
|---|---|---|
| `entities/` | — (nothing) | Application, Kernel, Infrastructure |
| `events/` | — (nothing) | Application, Kernel, Infrastructure |
| `exceptions/` | — (nothing) | Application, Kernel, Infrastructure |
| `value_objects/` | — (nothing) | Application, Kernel, Infrastructure |
| `interfaces/` | entities, exceptions | Infrastructure (implements), Application (uses) |

### 2.2 Application Layer Dependencies

| Module | Depends On | Depended On By |
|---|---|---|
| `dtos/` | — (nothing external) | Presentation |
| `use_cases/chat/` | domain (interfaces, entities), kernel (memory, models) | Presentation |
| `use_cases/agents/` | domain (interfaces, entities), kernel (agents, memory, models) | Presentation |
| `use_cases/tools/` | domain (interfaces, entities), kernel (tools) | Presentation |
| `use_cases/memory/` | domain (interfaces, entities), kernel (memory) | Presentation |
| `use_cases/models/` | domain (interfaces, entities), kernel (models) | Presentation |
| `use_cases/knowledge/` | domain (interfaces, entities), kernel (knowledge) | Presentation |
| `use_cases/codebase/` | domain (interfaces, entities), kernel (codebase) | Presentation |
| `use_cases/workflow/` | domain (interfaces, entities), kernel (agents, tools, memory) | Presentation |
| `use_cases/projects/` | domain (interfaces, entities) | Presentation |
| `use_cases/improvement/` | domain (interfaces, entities), kernel (codebase, models) | Presentation |
| `use_cases/search/` | domain (interfaces, entities), kernel (memory, knowledge, codebase) | Presentation |

### 2.3 AI Kernel Dependencies

| Module | Depends On | Depended On By |
|---|---|---|
| `agents/interfaces/` | domain (entities) | Application, Plugins |
| `agents/registry.py` | agents/interfaces, domain (entities) | Application |
| `agents/orchestrator.py` | agents/interfaces, memory, models, tools | Application |
| `agents/router.py` | agents/interfaces, domain (entities) | Application |
| `agents/scheduler.py` | agents/interfaces | Application |
| `agents/builtin/*` | agents/interfaces, tools, models, memory | agents/orchestrator |
| `memory/interfaces/` | domain (entities) | Application, Infrastructure |
| `memory/tiers/*` | memory/interfaces, domain (entities) | Application |
| `memory/manager.py` | memory/interfaces, memory/tiers | Application |
| `memory/compression.py` | memory/interfaces, models | memory/manager |
| `memory/ranking.py` | memory/interfaces, domain | memory/manager |
| `memory/retrieval.py` | memory/interfaces, memory/tiers | Application |
| `memory/pruning.py` | memory/interfaces | memory/manager |
| `tools/interfaces/` | domain (entities) | Application, Plugins |
| `tools/registry.py` | tools/interfaces, domain (entities) | Application |
| `tools/executor.py` | tools/interfaces, plugins/sandbox | Application |
| `tools/permissions.py` | tools/interfaces, domain (entities) | Application |
| `tools/rate_limiter.py` | — | tools/executor |
| `tools/builtin/*` | tools/interfaces, infrastructure/network | tools/registry |
| `knowledge/interfaces/` | domain (entities) | Application, Infrastructure |
| `knowledge/extractor.py` | knowledge/interfaces, models | knowledge/store |
| `knowledge/embedder.py` | knowledge/interfaces | knowledge/indexer |
| `knowledge/indexer.py` | knowledge/interfaces, knowledge/embedder | Application |
| `knowledge/searcher.py` | knowledge/interfaces | Application |
| `knowledge/graph.py` | knowledge/interfaces | Application |
| `models/interfaces/` | domain (entities) | Application, Infrastructure |
| `models/gateway.py` | models/interfaces | Application, Kernel (all) |
| `models/router.py` | models/interfaces, domain (entities) | models/gateway |
| `models/health.py` | models/interfaces | models/gateway |
| `models/cache.py` | — | models/gateway |
| `models/providers/*` | models/interfaces, infrastructure/network | models/gateway |
| `codebase/interfaces/` | domain (entities) | Application |
| `codebase/indexer.py` | codebase/interfaces | Application |
| `codebase/parsers/*` | codebase/interfaces | codebase/indexer |
| `codebase/analyzer.py` | codebase/interfaces | Application |
| `codebase/dependency_graph.py` | codebase/interfaces | Application |
| `codebase/search.py` | codebase/interfaces | Application |
| `codebase/impact.py` | codebase/interfaces, codebase/dependency_graph | Application |
| `codebase/structure.py` | codebase/interfaces | Application |

### 2.4 Infrastructure Layer Dependencies

| Module | Depends On | Depended On By |
|---|---|---|
| `persistence/database.py` | — | persistence/repositories |
| `persistence/repositories/*` | domain (interfaces), persistence/database | Container (wiring) |
| `persistence/models/*` | — | persistence/repositories |
| `persistence/cache/*` | — | persistence/repositories |
| `ai/embeddings.py` | — | kernel/knowledge/embedder |
| `ai/tokenizer.py` | — | kernel/models/gateway |
| `ai/context.py` | — | kernel/memory/manager |
| `storage/*` | — | kernel/tools/builtin/file_tool |
| `network/*` | — | kernel/models/providers, kernel/tools/builtin |
| `security/*` | domain (entities) | Presentation (middleware) |
| `config/*` | — | container.py |

### 2.5 Presentation Layer Dependencies

| Module | Depends On | Depended On By |
|---|---|---|
| `api/v2/endpoints/*` | application (use cases), application (dtos), security | — |
| `api/v2/router.py` | api/v2/endpoints/* | — |
| `api/v2/responses.py` | — | api/v2/endpoints/* |
| `cli/commands/*` | application (use cases), application (dtos) | — |
| `cli/parser.py` | — | cli |
| `websocket/*` | application (use cases) | — |
| `sdk/*` | application (dtos) | External consumers |

### 2.6 Plugin Layer Dependencies

| Module | Depends On | Depended On By |
|---|---|---|
| `interfaces/*` | kernel (interfaces) | Plugins (implementations) |
| `loader.py` | interfaces, config | Container |
| `registry.py` | interfaces, loader | Container |
| `sandbox.py` | — | kernel/tools/executor |
| `validator.py` | interfaces | loader |
| `permissions.py` | domain (entities) | registry |
| `lifecycle.py` | interfaces, registry | Container |

### 2.7 Cross-Cutting Dependencies

| Module | Depends On | Depended On By |
|---|---|---|
| `monitoring/metrics/*` | — (collects data, no deps) | All layers (import interface) |
| `monitoring/logging/*` | — | All layers (import interface) |
| `monitoring/health/*` | All layers (checks) | Presentation (health endpoint) |
| `monitoring/tracing/*` | — | All layers (import interface) |
| `security/auth/*` | domain (entities) | Presentation (middleware) |
| `security/authorization/*` | domain (entities) | Presentation (middleware) |
| `security/validation/*` | — | Presentation (middleware) |
| `security/audit/*` | domain (events) | All layers (import interface) |
| `configs/loader.py` | — | Container |
| `configs/schema.py` | — | configs/loader |

## 3. Circular Dependencies (Current — to be eliminated)

### Detected:
1. **Infrastructure → Application → Infrastructure**
   - `infrastructure/workflow/__init__.py` imports `application/use_cases/workflow.py`
   - `application/use_cases/workflow.py` uses domain interfaces
   - `domain/interfaces/` is implemented by `infrastructure/workflow/`
   - **Fix:** Move workflow orchestration to `kernel/workflow/` — break the cycle

2. **Application Services ↔ Infrastructure**
   - `application/services/chat_service.py` imports `infrastructure/logging/`
   - `application/services/system_service.py` imports `infrastructure/logging/`
   - `application/services/provider_service.py` imports `infrastructure/logging/`
   - **Fix:** Move logging to cross-cutting layer; inject via interface, not direct import

### Prevention Rules:
- `import-linter` in CI with layers defined as contracts
- `pylint` with custom plugin for circular import detection
- Every PR must pass: `import-linter check —layers aida/`

## 4. Forbidden Dependencies (Enforced in CI)

| Rule ID | Description | Error Message |
|---|---|---|
| DEP-001 | Domain must not import application | `domain/` → `application/` ❌ |
| DEP-002 | Domain must not import infrastructure | `domain/` → `infrastructure/` ❌ |
| DEP-003 | Domain must not import presentation | `domain/` → `presentation/` ❌ |
| DEP-004 | Domain must not import kernel | `domain/` → `kernel/` ❌ |
| DEP-005 | Application must not import infrastructure | `application/` → `infrastructure/` ❌ |
| DEP-006 | Application must not import presentation | `application/` → `presentation/` ❌ |
| DEP-007 | Application must not import plugins | `application/` → `plugins/` ❌ |
| DEP-008 | Kernel must not import infrastructure | `kernel/` → `infrastructure/` ❌ |
| DEP-009 | Kernel must not import presentation | `kernel/` → `presentation/` ❌ |
| DEP-010 | Infrastructure must not import application | `infrastructure/` → `application/` ❌ |
| DEP-011 | Infrastructure must not import presentation | `infrastructure/` → `presentation/` ❌ |
| DEP-012 | Presentation must not import infrastructure | `presentation/` → `infrastructure/` ❌ |
| DEP-013 | Plugins must not import application | `plugins/` → `application/` ❌ |
| DEP-014 | Plugins must not import presentation | `plugins/` → `presentation/` ❌ |

## 5. Allowed Dependency Patterns

### Pattern 1: Interface → Implementation
```
Domain Interface        ←  Infrastructure Implementation
┌─────────────────┐         ┌──────────────────────────┐
│ MemoryRepository│◄───────│ MemoryRepoAdapter(SQLite) │
└─────────────────┘         └──────────────────────────┘
```

### Pattern 2: Use Case → Kernel Interface
```
Application Use Case     ←  Kernel Interface (as dependency)
┌──────────────┐              ┌──────────────┐
│ ChatUseCase  │─────────────►│ ModelGateway │
└──────────────┘              └──────────────┘
```

### Pattern 3: Event → Subscriber
```
Any Module        EventBus      Any Module
┌──────────┐     ┌────────┐     ┌──────────────┐
│ Producer │────►│ publish│────►│ Consumer(s)   │
└──────────┘     └────────┘     └──────────────┘
```

### Pattern 4: Plugin → Interface
```
Plugin Package         Kernel Interface
┌────────────────┐     ┌────────────────┐
│ MyCustomAgent  │────►│ BaseAgent      │
└────────────────┘     └────────────────┘
```

## 6. Dependency Injection Wiring

```
                ┌─────────────────────────────┐
                │       Container.py           │
                │                              │
                │  register(Interface, Impl)   │
                │  resolve(UseCase) → auto-wire│
                │  resolve(Service) → auto-wire│
                └──────────────┬──────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
   │ ChatUseCase   │   │ AgentUseCase  │   │ ToolUseCase   │
   │               │   │               │   │               │
   │ ModelGateway←─┤   │ AgentEngine←──┤   │ ToolEngine←───┤
   │ MemoryEngine←─┤   │ ModelGateway←─┤   │ Permission←───┤
   │ SessionRepo←──┤   │ MemoryEngine←─┤   │ Sandbox←──────┤
   └───────────────┘   │ ToolEngine←───┤   └───────────────┘
                       └───────────────┘
```

## 7. Dependency Health Checks

| Metric | Target | Tool |
|---|---|---|
| Circular dependencies | 0 | `pip install import-linter` |
| Layer violations | 0 | `import-linter` |
| Direct infra imports in app | 0 | Custom grep CI check |
| Direct Django imports in domain | 0 | Custom grep CI check |
| Maximum module depth | < 4 levels | Code review |
| Module cohesion (LCOM) | > 0.8 | Custom metric |
| Module coupling (CBO) | < 10 | Custom metric |
