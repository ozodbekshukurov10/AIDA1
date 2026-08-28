# AIDA — Layer Assignment Diagram

## 1. Complete Module-to-Layer Mapping

Every module in the system is assigned to exactly one layer. Cross-cutting concerns touch all layers but are defined in a dedicated location.

```
LAYER                    MODULES
──────────────────────────────────────────────────────────────────────────────
DOMAIN                   entities/*, events/*, exceptions/*, value_objects/*,
(pure business logic)    interfaces/*, value_objects/*
                         
APPLICATION              dtos/*, use_cases/*/,
(orchestration)          └─ chat/, agents/, tools/, memory/, models/,
                           knowledge/, codebase/, workflow/, projects/,
                           improvement/, search/

AI KERNEL                agents/*,          ── Agent Engine
(AI orchestration)       memory/*,          ── Memory Engine
                         tools/*,           ── Tool Engine
                         knowledge/*,       ── Knowledge Engine
                         models/*,          ── Model Gateway
                         codebase/*,        ── Repository Analyzer
                         
INFRASTRUCTURE           persistence/*,     ── Database adapters
(implementations)        ai/*,              ── AI infrastructure
                         storage/*,         ── File storage
                         network/*,         ── HTTP clients
                         security/*,        ── Auth implementations
                         config/*,          ── Config loaders
                         
PRESENTATION             api/v2/*,          ── REST API endpoints
(user interface)         api/v1/*,          ── Legacy API (deprecated)
                         cli/*,             ── Command line interface
                         websocket/*,       ── WebSocket handlers
                         sdk/*,             ── SDK client library

PLUGINS                  interfaces/*,      ── Plugin interfaces
(extension system)       loader.py,         ── Plugin discovery
                         registry.py,       ── Plugin registration
                         sandbox.py,        ── Plugin isolation
                         validator.py,      ── Plugin validation
                         permissions.py,    ── Plugin permissions
                         lifecycle.py       ── Plugin lifecycle

MONITORING               metrics/*,         ── Metrics collection & export
(cross-cutting)          logging/*,         ── Structured logging
                         health/*,          ── Health checks
                         tracing/*          ── Distributed tracing

SECURITY                 auth/*,            ── Authentication
(cross-cutting)          authorization/*,   ── Authorization & RBAC
                         validation/*,      ── Input validation
                         audit/*            ── Audit logging

CONFIGURATION            loader.py,         ── Config loading
(cross-cutting)          schema.py,         ── Config schema
                         defaults.py,       ── Default values
                         *.yaml             ── Environment-specific

DEPLOYMENT               docker/*,          ── Containerization
(infrastructure)         kubernetes/*,      ── Orchestration
                         scripts/*,         ── Automation scripts
```

## 2. Current Code → Target Layer Mapping

Every existing file mapped to its target layer:

### DOMAIN LAYER (Target)
```
Current File                              Target Module
───────────────────────────────────────────────────────────────────────
aidaos/domain/entities.py              →  domain/entities/*.py (split)
aidaos/domain/events.py                →  domain/events/*.py (split)
aidaos/domain/exceptions.py            →  domain/exceptions/*.py (split)
aidaos/domain/interfaces/__init__.py   →  domain/interfaces/*.py (split)
```

### APPLICATION LAYER (Target)
```
Current File                              Target Module
───────────────────────────────────────────────────────────────────────
aidaos/application/dtos.py             →  application/dtos/*.py (split)
aidaos/application/use_cases/chat.py   →  application/use_cases/chat/chat_use_case.py
aidaos/application/use_cases/agent.py  →  application/use_cases/agents/execute_agent.py
aidaos/application/use_cases/tool.py   →  application/use_cases/tools/execute_tool.py
aidaos/application/use_cases/code.py   →  application/use_cases/codebase/*.py
aidaos/application/use_cases/memory.py →  application/use_cases/memory/store_memory.py
aidaos/application/use_cases/workflow.py→ application/use_cases/workflow/*.py
aidaos/application/use_cases/improvement.py→ application/use_cases/improvement/*.py
aidaos/application/use_cases/search.py →  application/use_cases/search/search_all.py
aidaos/application/use_cases/project.py→  application/use_cases/projects/manage_projects.py
```

### AI KERNEL (Target)
```
Current File                              Target Module
───────────────────────────────────────────────────────────────────────
webapp/agents/*.py                    →  kernel/agents/builtin/*.py
webapp/agents/orchestrator.py         →  kernel/agents/orchestrator.py
webapp/agents.py                      →  kernel/agents/router.py (merge)
webapp/memory/*.py                    →  kernel/memory/tiers/*.py
webapp/memory/manager.py             →  kernel/memory/manager.py
webapp/memory/compression.py         →  kernel/memory/compression.py
webapp/memory/ranking.py              →  kernel/memory/ranking.py
webapp/memory/retrieval.py            →  kernel/memory/retrieval.py
webapp/tools/*.py                     →  kernel/tools/*.py
webapp/tools/professional.py          →  kernel/tools/builtin/*.py (SPLIT into 9 files)
webapp/llm/gateway.py                →  kernel/models/gateway.py
webapp/llm/base.py                    →  kernel/models/providers/base_provider.py
webapp/llm/ollama.py                  →  kernel/models/providers/ollama_provider.py
webapp/llm/gemini.py                  →  kernel/models/providers/gemini_provider.py
webapp/llm/openai_compat.py           →  kernel/models/providers/openai_provider.py
webapp/llm/lmstudio.py                →  kernel/models/providers/lmstudio_provider.py
webapp/llm/local.py                   →  kernel/models/providers/local_provider.py
webapp/llm/providers/*.py             →  kernel/models/providers/*.py (consolidate)
webapp/repo_analyzer/*.py             →  kernel/codebase/*.py
webapp/knowledge_store.py             →  kernel/knowledge/*.py
webapp/code_fixer.py                  →  kernel/codebase/analyzer.py (merge)
aidaos/infrastructure/codebase/indexer.py → kernel/codebase/indexer.py
```

### INFRASTRUCTURE LAYER (Target)
```
Current File                              Target Module
───────────────────────────────────────────────────────────────────────
aidaos/infrastructure/persistence/*.py → infrastructure/persistence/repositories/*.py
aidaos/infrastructure/agents/*.py      → infrastructure/persistence/repositories/agent_repo.py
aidaos/infrastructure/tools/*.py       → infrastructure/persistence/repositories/tool_repo.py
aidaos/infrastructure/llm/*.py         → infrastructure/persistence/repositories/model_repo.py
aidaos/infrastructure/project/*.py     → infrastructure/persistence/repositories/project_repo.py
aidaos/infrastructure/workflow/*.py    → infrastructure/persistence/repositories/workflow_repo.py
aidaos/infrastructure/plugins/*.py     → plugins/*.py (moves to plugin layer)
aidaos/infrastructure/config/settings.py → configs/defaults.py
aidaos/infrastructure/logging/*.py     → monitoring/logging/*.py
webapp/models/*.py                     → infrastructure/persistence/models/*.py
webapp/security.py                     → security/auth/*.py (split)
webapp/sandbox.py                      → plugins/sandbox.py
webapp/code_assistants.py              → kernel/agents/builtin/code_agent.py (merge)
webapp/framework_assistants.py         → kernel/agents/builtin/code_agent.py (merge)
webapp/infrastructure_assistants.py    → kernel/agents/builtin/deployment_agent.py (merge)
webapp/learning_assistants.py          → kernel/agents/builtin/general_agent.py (merge)
webapp/model_discovery.py              → kernel/models/gateway.py (merge)
webapp/model_manager.py                → kernel/models/gateway.py (merge)
webapp/model_auto_start.py             → kernel/models/gateway.py (merge)
webapp/model_views.py                  → presentation/api/v2/endpoints/models.py
webapp/model_management_views.py       → presentation/api/v2/endpoints/models.py
server_manager.py                      → deployment/scripts/setup.py
```

### PRESENTATION LAYER (Target)
```
Current File                              Target Module
───────────────────────────────────────────────────────────────────────
webapp/urls.py                         →  presentation/api/v2/router.py
webapp/views.py                        →  presentation/api/v2/endpoints/*.py (SPLIT)
webapp/api/*.py                        →  presentation/api/v2/endpoints/*.py
webapp/admin.py                        →  presentation/api/v2/endpoints/admin.py
webapp/apps.py                         →  REMOVE (Django app config, not needed)
aidaos/presentation/api/*.py           →  presentation/api/v2/responses.py
aidaos/presentation/cli/*.py           →  presentation/cli/*.py
aida_master_controller.py              →  presentation/cli/commands/chat.py (merge)
aida_voice.py                          →  REMOVE (duplicate)
core_agi.py                            →  REMOVE (toy demo)
aida_autonomous.py                     →  REMOVE or redesign as autonomous worker
```

### CROSS-CUTTING — MONITORING (Target)
```
Current File                              Target Module
───────────────────────────────────────────────────────────────────────
webapp/monitoring/metrics.py           →  monitoring/metrics/collector.py
```

### CROSS-CUTTING — SELF-IMPROVEMENT (moves to Application)
```
Current File                              Target Module
───────────────────────────────────────────────────────────────────────
webapp/self_improvement/*.py           →  application/use_cases/improvement/*.py
```

## 3. Layer Boundary Rules (Enforced)

```
ALLOWED DEPENDENCIES:

  Domain      →  (nothing external)
  Application →  Domain, Kernel (interfaces only), DTOs
  Kernel      →  Domain, Kernel (other module interfaces only)
  Infrastructure → Domain (interfaces), Kernel (interfaces only)
  Presentation → Application (use cases), DTOs
  Plugins     →  Kernel (interfaces only)
  Monitoring  →  All layers (read-only metrics)
  Security    →  All layers (read-only validation)
  Config      →  All layers (read-only access)

FORBIDDEN DEPENDENCIES:

  Domain      →  ANY external import (Django, httpx, sqlite3) ❌
  Application →  Infrastructure ❌
  Application →  Presentation ❌
  Kernel      →  Infrastructure (directly) ❌
  Kernel      →  Presentation ❌
  Infrastructure → Application (use cases) ❌
  Infrastructure → Presentation ❌
  Presentation → Infrastructure (directly) ❌
  Plugins     →  Application ❌
  Plugins     →  Presentation ❌
```

## 4. Visual Layer Diagram

```
                         ┌──────────────────────────────────┐
                         │          PRESENTATION            │
                         │  API v2 │ CLI │ WebSocket │ SDK  │
                         └────────────┬─────────────────────┘
                                      │ depends on
                         ┌────────────▼─────────────────────┐
                         │          APPLICATION              │
                         │  Use Cases │ DTOs │ Workflows    │
                         └────────────┬─────────────────────┘
                                      │ depends on
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│       DOMAIN        │   │     AI KERNEL        │   │    INFRASTRUCTURE   │
│  Entities │ Events  │   │ Agents │ Memory      │   │  Persistence │ AI   │
│  Exceptions │ VOs   │   │ Tools  │ Knowledge   │   │  Network │ Security │
│  Interfaces (ports) │   │ Models │ Codebase    │   │  Storage │ Config   │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
        ▲                           ▲                          ▲
        │                           │                          │
        └───────────────────────────┼──────────────────────────┘
                                    │
                         ┌──────────┴──────────┐
                         │   DI CONTAINER       │
                         │   (Wires Everything) │
                         └─────────────────────┘

Cross-Cutting:  [Security]  [Monitoring]  [Configuration]  [Events]
                (touch all layers above)
```

## 5. Current Layer Violations & Resolution

| Violation | Current Location | Target Location | Resolution |
|---|---|---|---|
| App→Infra (logging) | `application/services/*.py` | `monitoring/logging/` | Move logging to cross-cutting; inject via interface |
| Infra→App (circular) | `infrastructure/workflow/__init__.py` | `kernel/workflow/` | Move workflow to kernel; break the cycle |
| App→Webapp | `application/services/provider_service.py` | `kernel/models/gateway.py` | Move provider service logic to kernel |
| Domain→Django | None (clean) | — | ✅ Already clean |
| App→Django | None (clean) | — | ✅ Already clean |
| Presentation→Infra | `webapp/views.py` | `presentation/api/v2/` | Wrap infrastructure calls behind use cases |
| Presentation→Infra | `webapp/api/*.py` | `presentation/api/v2/endpoints/` | Same pattern |
