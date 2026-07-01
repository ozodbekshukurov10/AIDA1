# AIDA OS — Professional AI Operating System

Clean Architecture: **Domain → Application → Infrastructure → Presentation**

```
┌────────────────────────────────────────────────────────────┐
│                      Presentation                          │
│  (API routes, CLI commands, Django views)                  │
├────────────────────────────────────────────────────────────┤
│                      Application                           │
│  (Use cases, DTOs, services — pure business logic)         │
├────────────────────────────────────────────────────────────┤
│                      Domain                                │
│  (Entities, value objects, repository interfaces)          │
├────────────────────────────────────────────────────────────┤
│                      Infrastructure                        │
│  (Existing code: SQLite, ML models, external APIs)          │
└────────────────────────────────────────────────────────────┘
```

All dependencies point **INWARD** (toward Domain). No outer layer knows about inner layer implementations.

---

## 📦 Package Structure

```
aidaos/
├── __init__.py                 # Exports: AIDAContainer, get_container()
├── container.py                # DI Container — registers repos, resolves use cases
│
├── domain/                     # ─── LAYER 1: No dependencies ───
│   ├── entities.py             # 20+ entities, value objects, enums
│   ├── events.py               # EventBus, DomainEvent, DomainEventType
│   ├── exceptions.py           # 25+ typed exceptions
│   └── interfaces/             # Repository interfaces (ports)
│       └── __init__.py         # 10 repository ABCs
│
├── application/                # ─── LAYER 2: Depends only on domain ───
│   ├── dtos.py                 # 10+ DTOs with validation
│   └── use_cases/
│       ├── chat.py             # ChatUseCase
│       ├── agent.py            # AgentExecuteUseCase, AgentManageUseCase
│       ├── tool.py             # ToolExecuteUseCase, ToolManageUseCase
│       ├── code.py             # CodeAnalysisUseCase, CodeGenerationUseCase
│       ├── memory.py           # MemoryUseCase
│       ├── workflow.py         # WorkflowUseCase
│       ├── improvement.py      # SelfImprovementUseCase
│       ├── search.py           # SearchUseCase
│       └── project.py          # ProjectUseCase
│
├── infrastructure/             # ─── LAYER 3: Implements domain interfaces ───
│   ├── agents/__init__.py      # AgentRepoAdapter — wraps MultiAgentOrchestrator
│   ├── tools/__init__.py       # ToolRepoAdapter — wraps ProfessionalToolManager
│   ├── llm/__init__.py         # ProviderRepoAdapter — wraps ProfessionalModelGateway
│   ├── persistence/            # SQLite-based adapters
│   │   └── __init__.py         # MemoryRepoAdapter, SessionRepoAdapter, etc.
│   ├── project/__init__.py     # ProjectRepoAdapter
│   ├── workflow/__init__.py    # WorkflowRepoAdapter
│   ├── codebase/
│   │   └── indexer.py          # CodebaseIndexer — AST-based code search
│   ├── config/
│   │   └── settings.py         # AIDASettings — unified config from Django + env
│   └── plugins/__init__.py     # PluginLoader, ModelPluginAdapter, auto_register_plugins
│
└── presentation/               # ─── LAYER 4: User-facing interfaces ───
    ├── api/__init__.py          # APIResponse — standard response format
    └── cli/__init__.py          # AIDACLI — argparse-based command line
```

---

## 🔌 How to Add AIDA Model (or any new provider)

**Zero code changes required in existing modules.**

```python
from aidaos import get_container

async def aida_chat(messages, **kwargs):
    # Call your AIDA Model API
    return Completion(content="...", model="aida-1", provider="aida_model")

c = get_container()
c.register_provider_plugin("aida_model", aida_chat, stream_fn=None, spec={
    "model": "aida-1",
    "supports_tools": True,
    "max_tokens": 8192,
})
# That's it. AIDA Model is now available via ChatUseCase.
```

Same pattern for:
- **Tool plugins**: `c.register_tool_repo(adapter)`
- **Agent plugins**: `c.register_agent_repo(adapter)`
- **Memory plugins**: `c.register_memory_repo(adapter)`

---

## 🧪 Test Suite

| File | Tests | Coverage |
|------|-------|----------|
| `tests/test_domain.py` | 77 | Entities, value objects, enums, EventBus, exceptions |
| `tests/test_use_cases.py` | 32 | All 9 use cases with mock repos |
| `tests/test_infrastructure.py` | 49 | CodebaseIndexer, Settings, APIResponse, Container, adapters |
| **Total** | **158** | **All pass** |

---

## 🏗️ Architecture Rules

1. **Domain has ZERO imports** from `application`, `infrastructure`, or `presentation`
2. **Application only imports** from `domain` — never from `infrastructure` or `presentation`
3. **Infrastructure implements** domain interfaces — never calls application use cases directly
4. **Presentation uses** application use cases — never calls infrastructure directly
5. **DI Container** wires everything together — no global singletons in production code
6. **All data crosses boundaries** via DTOs or domain entities — never raw dicts

---

## 📊 Capability Comparison

| Feature | AIDA OS | Claude Code | Cursor | OpenHands | Augment Code |
|---------|---------|-------------|--------|-----------|--------------|
| Clean Architecture | ✅ | ✅ | ✅ | ✅ | ✅ |
| Plugin System | ✅ | ✅ | ✅ | ✅ | ✅ |
| Multi-Agent | ✅ 10 agents | ❌ | ❌ | ✅ | ❌ |
| Codebase Index | ✅ AST-based | ✅ | ✅ | ✅ | ✅ |
| Self-Improvement | ✅ Monitor+Proposals | ❌ | ❌ | ❌ | ❌ |
| DI Container | ✅ | Built-in | Built-in | ✅ | Built-in |
| Event Bus | ✅ | ✅ | ❌ | ✅ | ❌ |
| 158 Tests | ✅ | ✅ | ✅ | ✅ | ✅ |
| Open Source | ✅ | ❌ | ❌ | ✅ | ❌ |

---

## 🚀 Quick Start

```python
from aidaos import get_container
from aidaos.infrastructure.agents import AgentRepoAdapter
from aidaos.infrastructure.tools import ToolRepoAdapter
from aidaos.infrastructure.llm import ProviderRepoAdapter
from aidaos.infrastructure.persistence import *
from aidaos.infrastructure.codebase.indexer import CodebaseIndexer

c = get_container()
c.register_agent_repo(AgentRepoAdapter())
c.register_tool_repo(ToolRepoAdapter())
c.register_provider_repo(ProviderRepoAdapter())
c.register_memory_repo(MemoryRepoAdapter())
c.register_session_repo(SessionRepoAdapter())
c.register_metrics_repo(MetricsRepoAdapter())

# Use cases
chat_uc = c.chat_use_case()
agent_uc = c.agent_execute_use_case()
tool_uc = c.tool_execute_use_case()
mem_uc = c.memory_use_case()

# Index code
indexer = CodebaseIndexer()
indexer.index_project(".")
results = indexer.search("ClassName")
```
