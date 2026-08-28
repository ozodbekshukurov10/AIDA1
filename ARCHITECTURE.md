# AIDA — Clean Architecture & System Design

## 1. Architectural Philosophy

AIDA is designed as an **AI Operating System** — not an LLM wrapper, not a chatbot, not a code assistant. It is a **horizontal platform** where every component (agents, tools, models, memory, knowledge) is a pluggable module orchestrated by a lightweight kernel.

The architecture follows **Clean Architecture** with **Domain-Driven Design** tactical patterns, deployed as a **Modular Monolith** with extraction points for future microservice decomposition.

## 2. Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ REST API │  │   CLI    │  │ WebSocket │  │   SDK    │  │   IPC    │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                         APPLICATION LAYER                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Use Cases│  │   DTOs   │  │ Services │  │Workflows │  │Orchestr. │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                          DOMAIN LAYER                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Entities │  │  Value   │  │  Events  │  │  Domain  │  │  Domain  │  │
│  │          │  │  Objects │  │          │  │Services  │  │Interfaces│  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                        INFRASTRUCTURE LAYER                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Adapters │  │Persistence│  │   LLM    │  │   File   │  │ Network  │  │
│  │          │  │          │  │ Providers │  │   System  │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                   AI KERNEL (Cross-Cutting)                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Agent   │  │  Memory  │  │   Tool   │  │ Knowledge│  │  Model   │  │
│  │  Engine  │  │  Engine  │  │   Engine  │  │  Engine  │  │ Gateway  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                     CROSS-CUTTING CONCERNS                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Security │  │ Monitoring│  │  Config  │  │  Logging │  │  Events  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

        Dependency Direction: Presentation → Application → Domain ← Infrastructure
                           AI Kernel extends horizontally
                     Cross-cutting concerns touch all layers
```

## 3. Core Architectural Decisions

### Decision 1: Modular Monolith with Extraction Points

**Context:** AIDA is single-developer project. Microservices would add network latency, distributed debugging, and operational overhead without proven scaling need.

**Decision:** Build as a modular monolith with strict module boundaries. Every module has a single public interface. Internal implementation is encapsulated. When a module needs independent scaling (e.g., agent execution under heavy load), the module boundary makes extraction trivial.

**Extraction Path:** Module → Separate Process → Separate Service (in 3 steps without API change)

### Decision 2: AI Kernel as a Cross-Cutting Layer

**Context:** Traditional Clean Architecture places AI/LLM logic in infrastructure. But AIDA's core value is AI orchestration — treating AI as mere infrastructure obscures its central role.

**Decision:** AI Kernel is a distinct cross-cutting layer that spans domain logic (agent definitions, tool specifications) and infrastructure (LLM providers, embedding models). The Kernel defines interfaces for agents, tools, memory, knowledge, and models — all other layers depend on these interfaces.

### Decision 3: Event-Driven Module Communication

**Context:** Modules must communicate without tight coupling. Direct imports create circular dependencies and reduce testability.

**Decision:** All inter-module communication goes through domain events or interface calls resolved by the DI container. The EventBus is the backbone for asynchronous communication (task completion, agent status, memory updates). Synchronous calls go through repository interfaces.

### Decision 4: Plugin Architecture for All Extension Points

**Context:** AIDA must support adding new agents, tools, models, memory types, and providers without modifying core code.

**Decision:** Every extensible component has a registration interface. A central PluginManager discovers, validates, and registers plugins. The core defines interfaces; plugins provide implementations. Zero code changes in core for new plugin types.

### Decision 5: Configuration as a First-Class Citizen

**Context:** AIDA runs in development, testing, staging, production, Docker, cloud, and air-gapped environments. Configuration must adapt without code changes.

**Decision:** Layered configuration system: defaults → config files → environment variables → secrets vault → runtime overrides. Each layer overrides the previous. Configuration is validated at startup and accessible through a typed `Config` object.

## 4. Layer Definitions

### 4.1 Domain Layer

**Purpose:** Pure business logic with zero external dependencies. Contains entities, value objects, domain events, domain services, and repository interfaces.

**Must NOT contain:**
- Framework imports (Django, DRF, httpx)
- Database access
- Network calls
- File I/O
- LLM calls
- Serialization (except `to_dict()` for domain events)

**Rules:**
- `from django.db import models` → ❌ FORBIDDEN
- `import httpx` → ❌ FORBIDDEN
- `import sqlite3` → ❌ FORBIDDEN
- `import json` → ⚠️ Only for serialization of domain events
- `from __future__ import annotations` → ✅ REQUIRED
- `from dataclasses import dataclass` → ✅ ALLOWED
- `from enum import Enum` → ✅ ALLOWED
- `from typing import ...` → ✅ ALLOWED
- `from abc import ABC, abstractmethod` → ✅ ALLOWED

### 4.2 Application Layer

**Purpose:** Orchestrates business workflows by coordinating domain objects. Contains use cases, DTOs, application services, and workflow definitions.

**Must NOT contain:**
- Direct infrastructure imports
- Framework code (Django, DRF)
- Database queries
- LLM provider calls

**Rules:**
- `from aida.infrastructure.*` → ❌ FORBIDDEN
- `from aida.domain import *` → ✅ ALLOWED
- `from django.db import connection` → ❌ FORBIDDEN
- `from aida.kernel import *` → ✅ ALLOWED (kernel interfaces)
- Must raise domain exceptions, never infrastructure exceptions
- Must accept and return domain objects or DTOs

### 4.3 Infrastructure Layer

**Purpose:** Implements domain interfaces. Contains database adapters, LLM provider implementations, file system access, network clients, and third-party integrations.

**Rules:**
- Must implement domain repository interfaces
- May depend on frameworks (Django, DRF, httpx, sqlite3)
- Must wrap external exceptions in domain exceptions at the adapter boundary
- Must not call application use cases directly (no circular dependencies)
- Must not contain business logic — only technical implementation

### 4.4 Presentation Layer

**Purpose:** User-facing interfaces. Contains API endpoints, CLI commands, WebSocket handlers, and SDK entry points.

**Rules:**
- Must call application use cases or services
- Must not call infrastructure directly
- Must use DTOs for request/response, never domain entities in API contracts
- Must validate input at the boundary (DTO validation)
- Must convert domain exceptions to appropriate HTTP responses

### 4.5 AI Kernel

**Purpose:** Core AI orchestration layer that defines and manages agents, tools, memory, knowledge, and model interactions.

**Contains:**
- **Agent Engine** — agent lifecycle, execution, routing, delegation
- **Memory Engine** — multi-tier memory (session, conversation, vector, episodic)
- **Tool Engine** — tool registration, execution, sandboxing, permissions
- **Knowledge Engine** — knowledge base, semantic search, extraction
- **Model Gateway** — LLM provider abstraction, routing, fallback, streaming

**Rules:**
- Kernel modules may import from Domain layer
- Kernel modules may import from other Kernel modules only through interfaces
- Kernel modules must not import from Infrastructure layer directly
- Kernel modules must not import from Presentation layer

### 4.6 Cross-Cutting Concerns

| Concern | Scope | Implementation |
|---|---|---|
| Security | All layers | Authentication, authorization, input validation, audit |
| Monitoring | All layers | Metrics collection, health checks, structured logging |
| Configuration | All layers | Layered config with environment overrides |
| Events | All layers | EventBus for decoupled communication |
| DI Container | All layers | Dependency injection, service location |

## 5. Module Dependency Rules

```
Presentation  ─────► Application ─────► Domain
    │                                       │
    │                                       ▼
    │                               Infrastructure
    │                                       │
    └──────► AI Kernel ◄────────────────────┘
                │
                ▼
           Cross-Cutting
```

### Strict Rules:
1. **Domain** has zero imports from any other layer
2. **Application** imports only from Domain, Kernel interfaces, and DTOs
3. **Infrastructure** imports from Domain (to implement interfaces) and Kernel interfaces
4. **Presentation** imports from Application and DTOs
5. **AI Kernel** imports from Domain and Kernel-internal interfaces
6. **Cross-Cutting** imports are allowed everywhere but must not contain business logic
7. **No circular dependencies** — enforced by import linter
8. **No infrastructure imports in application** — enforced by CI

## 6. Module Isolation Boundaries

Each module has:
1. **Public Interface** — what other modules can depend on
2. **Internal Implementation** — encapsulated, can change freely
3. **Dependencies** — what this module needs (resolved by DI container)
4. **Published Events** — events this module emits
5. **Consumed Events** — events this module subscribes to

### Module Template:
```
Module/
├── interfaces/       # Public contracts (what others depend on)
│   └── __init__.py  # Interface definitions
├── models/          # Internal data models (not exposed)
├── services/        # Internal business logic
├── adapters/        # External integrations (infrastructure)
├── config.py        # Module-specific configuration
├── events.py        # Module-specific events
├── container.py     # DI registration for this module
└── __init__.py      # Public API (re-exports interfaces)
```

## 7. Data Flow: Chat Request (Target)

```
HTTP POST /api/v2/chat/  (Presentation: API Endpoint)
    │
    ▼
ChatRequest DTO validation  (Application: DTO)
    │
    ▼
ChatUseCase.execute(request)  (Application: Use Case)
    │
    ├──► EventBus.publish(ChatStarted)
    │
    ├──► MemoryEngine.retrieve_context(session_id)  (Kernel: Memory)
    │     └──► MemoryRepoAdapter.get_session()  (Infrastructure: Persistence)
    │
    ├──► ModelGateway.chat(messages, context)  (Kernel: Model Gateway)
    │     └──► ProviderAdapter.chat()  (Infrastructure: LLM Provider)
    │           └──► HTTP call to Ollama/Gemini/OpenAI
    │
    ├──► ToolEngine.execute(tool_calls)  (Kernel: Tools - if needed)
    │     └──► ToolAdapter.execute()  (Infrastructure: Tool Execution)
    │
    ├──► MemoryEngine.store(session_id, messages)  (Kernel: Memory)
    │
    ├──► EventBus.publish(ChatCompleted)
    │
    └──► ChatResponse DTO  (Application: DTO)
          │
          ▼
HTTP 200 / SSE stream  (Presentation)
```

## 8. Data Flow: Agent Task (Target)

```
HTTP POST /api/v2/agents/execute/  (Presentation)
    │
    ▼
AgentExecuteRequest DTO  (Application)
    │
    ▼
AgentExecuteUseCase.execute(request)  (Application)
    │
    ├──► AgentEngine.classify_task(request)  (Kernel: Agent Engine)
    │     └──► IntentAnalysisService.analyze()
    │
    ├──► AgentEngine.select_agent(task_type)  (Kernel: Agent Engine)
    │     └──► AgentRegistry.get(task_type)
    │
    ├──► AgentEngine.execute(agent_spec, context)  (Kernel: Agent Engine)
    │     ├──► MemoryEngine.retrieve(agent_context)
    │     ├──► ModelGateway.chat(agent_prompt)
    │     ├──► ToolEngine.execute(tool_calls)
    │     └──► MemoryEngine.store(result)
    │
    ├──► EventBus.publish(AgentTaskCompleted)
    │
    └──► AgentExecuteResponse DTO  (Application)
```

## 9. Configuration Architecture

```
                                ┌─────────────────────┐
                                │   Runtime Overrides  │  (in-memory, ephemeral)
                                ├─────────────────────┤
                                │   Environment Vars   │  (os.environ, .env file)
                                ├─────────────────────┤
                                │   Secrets Vault      │  (Vault, AWS Secrets, etc.)
                                ├─────────────────────┤
                                │   Config Files       │  (config/*.yaml, *.toml)
                                ├─────────────────────┤
                                │   Default Values     │  (code-level defaults)
                                └─────────────────────┘
                                      Override Direction
```

## 10. Database Architecture (Target)

```
┌────────────────────────────────────────────────────────────┐
│                     PostgreSQL (Primary)                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  AIDA      │  │  Sessions  │  │  Workspaces│            │
│  │  Metadata  │  │            │  │            │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Access    │  │  Audit     │  │  Metrics   │            │
│  │  Keys      │  │  Log       │  │  History   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
├────────────────────────────────────────────────────────────┤
│                  Redis (Cache + Pub/Sub)                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Session   │  │  Provider  │  │  Rate      │            │
│  │  Cache     │  │  Health    │  │  Limiter   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
├────────────────────────────────────────────────────────────┤
│                  Vector Store (pgvector / Qdrant)            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Knowledge  │  │  Memory    │  │  Codebase  │            │
│  │ Embeddings │  │  Vectors   │  │  Vectors   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└────────────────────────────────────────────────────────────┘
```

## 11. Security Architecture

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────▶│  API GW  │────▶│  Auth    │────▶│  Service │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                       │               │
                       ▼               ▼
                 ┌──────────┐     ┌──────────┐
                 │  Rate    │     │  Audit   │
                 │  Limiter │     │  Logger  │
                 └──────────┘     └──────────┘

Layers:
  Perimeter: Rate limiting, IP whitelist, TLS termination
  Identity: JWT tokens, API keys (Authorization header)
  Authorization: Role-based (RBAC), permission-based (PBAC)
  Input: DTO validation, sanitization, size limits
  Audit: All access logged with correlation IDs
  Data: Encryption at rest, encrypted secrets
```

## 12. Scaling Strategy

```
Single Instance ───► Vertical Scale ───► Horizontal Scale ───► Microservices
    │                      │                      │                    │
    ▼                      ▼                      ▼                    ▼
Modular Monolith     More CPU/RAM           Multiple API         Agent workers
SQLite               PostgreSQL +           instances + LB       Memory service
                     Connection Pool                            Knowledge service

Extraction Order (by scaling need):
  1. Agent Engine → separate worker pool
  2. Model Gateway → dedicated proxy service
  3. Memory Engine → read replicas
  4. Knowledge Engine → dedicated search service
  5. Plugin Manager → sandboxed execution environment
```

## 13. Migration Path: Current → Target

```
Phase 0 (Current):
  webapp/ (legacy monolith) + aidaos/ (partial Clean Architecture)

Phase 1 (Restructure):
  Create target folder structure
  Move files to correct layers WITHOUT changing code
  Add __init__.py, interfaces, module boundaries

Phase 2 (Interface Extraction):
  Extract interfaces from all modules
  Wrap legacy implementations behind adapters
  Remove direct dependencies between modules

Phase 3 (Implementation Migration):
  One module at a time: rewrite internal implementation
  Keep interface unchanged
  Verify tests pass after each module migration

Phase 4 (Legacy Deletion):
  Delete legacy code that has been fully migrated
  Remove adapter wrappers where direct implementation exists

Phase 5 (Optimization):
  Add caching, async, streaming
  Performance tuning
  Production hardening
```

## 14. Principle Enforcement

| Principle | Enforcement | Tool |
|---|---|---|
| No circular dependencies | CI check | `import-linter` / custom script |
| Domain has zero external deps | CI check | `pylint` with custom rule |
| Application doesn't import infrastructure | CI check | `import-linter` |
| All interfaces have type hints | CI check | `mypy --strict` |
| All use cases have tests | CI gate | Coverage check |
| Module boundaries respected | CI check | Custom boundary test |
| No eval/exec with user input | CI check | `bandit` SAST |
| No hardcoded secrets | CI check | `truffleHog` / `gitleaks` |
