# AIDA — Professional Folder Structure & Module Organization

## 1. Existing Folder Analysis

| Folder | Files | Purpose | Assessment | Action |
|---|---|---|---|---|
| `AIDA/` | 12 | Django project config (settings, urls, wsgi, asgi) | ✅ Correct placement, clean structure | KEEP — merge into `aida/infrastructure/django/` |
| `aidaos/` | 74 | Clean Architecture skeleton (domain, application, infrastructure, presentation) | ✅ Good architecture, incomplete adapters | KEEP — migrate to `aida/` target structure |
| `webapp/` | 239 | Legacy monolithic Django app (controller, views, agents, tools, memory, llm, api) | ❌ Monolith, mixed concerns, 4404-line controller | DECOMPOSE — split into `aida/kernel/`, `aida/infrastructure/`, `aida/presentation/` |
| `frontend/` | 9017 | Vite + React 19 SPA (including node_modules) | ✅ Modern stack, good location | KEEP — restructure `src/` internally |
| `tests/` | 3 | Custom test harness (158 assertions) | ❌ No framework, no legacy coverage | KEEP — migrate to pytest, expand |
| `docs/` | 3 | Architecture, Vision, Audit documents | ✅ Good content | KEEP — add more documents |
| `scripts/` | 5 | Installers, dev scripts, self-optimizer | ⚠️ Mixed (installers + optimizer) | RESTRUCTURE — move to `deployment/scripts/` |
| `data/` | 3 | SQLite databases (memory, knowledge, metrics) | ⚠️ Runtime data in project root | MOVE — to `var/data/` |
| `dist/` | 3 | Vite build output (app.js, app.css, index.html) | ✅ Build artifact, gitignored | KEEP |
| `logs/` | 1 | Runtime logs | ⚠️ Runtime data in project root | MOVE — to `var/logs/` |
| `templates/` | 1 | Django template (build_pending.html) | ✅ Minimal, single-purpose | KEEP |
| `bin/` | 1 | CLI launcher (aida.bat) | ✅ Minimal | KEEP |
| `code_workspace/` | 0 | Empty directory | ❌ Dead directory | REMOVE |
| `projects/` | 0 | Empty directory | ❌ Dead directory | REMOVE (or keep as `var/projects/`) |

## 2. Target Folder Structure

```
AIDA1/
│
├── aida/                              # ─── MAIN PACKAGE ───
│   ├── __init__.py                    # Package init, version, public API exports
│   ├── container.py                   # DI Container — wires all modules
│   ├── config.py                      # Centralized configuration access
│   │
│   ├── domain/                        # ═══ LAYER 1: Pure Business Logic ═══
│   │   ├── __init__.py
│   │   ├── entities/                  # Business entities (one file per aggregate)
│   │   │   ├── __init__.py
│   │   │   ├── agent.py               # AgentSpec, AgentContext, AgentResult
│   │   │   ├── model.py               # ModelSpec, CapabilityAdvertisement
│   │   │   ├── tool.py                # ToolSpec, ToolResult
│   │   │   ├── message.py             # Message, Completion, StreamingChunk
│   │   │   ├── memory.py              # MemoryItem, MemoryQuery
│   │   │   ├── session.py             # Session, SessionConfig
│   │   │   ├── project.py             # Project, ProjectConfig
│   │   │   ├── knowledge.py           # KnowledgeItem, KnowledgeQuery
│   │   │   ├── workflow.py            # WorkflowTemplate, WorkflowStep
│   │   │   ├── workspace.py           # Workspace, MemberInfo
│   │   │   └── proposal.py            # Proposal, ProposalType, ProposalStatus
│   │   │
│   │   ├── value_objects/             # Immutable value objects
│   │   │   ├── __init__.py
│   │   │   ├── identifiers.py         # AgentID, SessionID, ToolID, TaskID, ProjectID
│   │   │   ├── permissions.py         # Permission, PermissionLevel
│   │   │   ├── metadata.py            # UsageStats, HealthStatus
│   │   │   └── errors.py              # ErrorLog, ErrorSeverity
│   │   │
│   │   ├── events/                    # Domain events (pub/sub)
│   │   │   ├── __init__.py
│   │   │   ├── event_bus.py           # EventBus, Subscription, DomainEvent
│   │   │   ├── agent_events.py        # AgentStarted, AgentCompleted, AgentFailed
│   │   │   ├── chat_events.py         # ChatStarted, ChatCompleted, MessageReceived
│   │   │   ├── tool_events.py         # ToolExecuted, ToolFailed
│   │   │   ├── memory_events.py       # MemoryStored, MemoryRetrieved, MemoryPruned
│   │   │   ├── model_events.py        # ProviderSwitched, ProviderFailed, ProviderDegraded
│   │   │   ├── workflow_events.py     # WorkflowStarted, WorkflowStepCompleted
│   │   │   └── system_events.py       # SystemStartup, SystemShutdown, ConfigReloaded
│   │   │
│   │   ├── exceptions/                # Typed exception hierarchy
│   │   │   ├── __init__.py
│   │   │   ├── base.py                # AIDAError (root) with code, status_code, message, details
│   │   │   ├── agent_errors.py        # AgentNotFoundError, AgentExecutionError, AgentTimeoutError
│   │   │   ├── tool_errors.py         # ToolNotFoundError, ToolPermissionError, ToolTimeoutError
│   │   │   ├── model_errors.py        # ProviderNotFoundError, ProviderOfflineError, ProviderAuthError
│   │   │   ├── memory_errors.py       # MemoryStorageError, MemoryRetrievalError
│   │   │   ├── session_errors.py      # SessionNotFoundError
│   │   │   ├── security_errors.py     # AuthenticationError, AuthorizationError
│   │   │   ├── validation_errors.py   # ValidationError
│   │   │   ├── config_errors.py       # ConfigurationError
│   │   │   └── plugin_errors.py       # PluginLoadError, PluginVersionError
│   │   │
│   │   └── interfaces/                # Repository interfaces (ports)
│   │       ├── __init__.py
│   │       ├── agent_repo.py          # AgentRepository (register, get, list, execute, get_status)
│   │       ├── tool_repo.py           # ToolRepository (register, get, list, execute)
│   │       ├── model_repo.py          # ModelRepository (register, get, list, chat, chat_stream, health)
│   │       ├── memory_repo.py         # MemoryRepository (store, get, search, update, delete, count, clear, stats)
│   │       ├── session_repo.py        # SessionRepository (create, get, list, update, delete, add_message, get_messages)
│   │       ├── project_repo.py        # ProjectRepository (open, close, get, list, get_files, read_file, write_file)
│   │       ├── knowledge_repo.py      # KnowledgeRepository (add, search, get, delete, get_stats)
│   │       ├── metrics_repo.py        # MetricsRepository (record_request, record_agent, get_stats, get_agent_stats, health_score)
│   │       ├── workspace_repo.py      # WorkspaceRepository (create, get, list, add_member, remove_member, get_members)
│   │       ├── codebase_repo.py       # CodebaseRepository (index_file, index_project, search, get_symbol, get_dependencies)
│   │       └── plugin_repo.py         # PluginRepository (register, get, list, enable, disable)
│   │
│   ├── application/                   # ═══ LAYER 2: Use Cases ═══
│   │   ├── __init__.py
│   │   ├── dtos/                      # Data Transfer Objects
│   │   │   ├── __init__.py
│   │   │   ├── chat_dtos.py           # ChatRequest, ChatResponse, StreamChunk
│   │   │   ├── agent_dtos.py          # AgentExecuteRequest, AgentExecuteResponse, AgentStatus
│   │   │   ├── tool_dtos.py           # ToolExecuteRequest, ToolExecuteResponse
│   │   │   ├── model_dtos.py          # ModelListResponse, ModelSwitchRequest
│   │   │   ├── memory_dtos.py         # MemorySearchRequest, MemorySearchResponse
│   │   │   ├── knowledge_dtos.py      # KnowledgeAddRequest, KnowledgeSearchRequest
│   │   │   ├── session_dtos.py        # SessionCreateRequest, SessionResponse
│   │   │   ├── workflow_dtos.py       # WorkflowExecuteRequest, WorkflowResponse
│   │   │   ├── project_dtos.py        # ProjectInfo, ProjectFile
│   │   │   ├── workspace_dtos.py      # WorkspaceResponse, MemberResponse
│   │   │   └── common.py              # Pagination, ErrorResponse, SuccessResponse
│   │   │
│   │   └── use_cases/                 # Application business logic
│   │       ├── __init__.py
│   │       ├── chat/                  # Chat & completion
│   │       │   ├── __init__.py
│   │       │   ├── send_message.py    # Send message, get completion
│   │       │   ├── stream_message.py  # Streaming version
│   │       │   └── manage_session.py  # Session lifecycle
│   │       ├── agents/                # Agent execution
│   │       │   ├── __init__.py
│   │       │   ├── execute_task.py    # Route and execute agent task
│   │       │   ├── delegate_task.py   # Delegate between agents
│   │       │   └── configure_agent.py # List, register, configure agents
│   │       ├── tools/                 # Tool execution
│   │       │   ├── __init__.py
│   │       │   ├── invoke_tool.py     # Execute a tool
│   │       │   └── manage_tools.py    # List, register, configure tools
│   │       ├── memory/                # Memory management
│   │       │   ├── __init__.py
│   │       │   ├── store_item.py      # Store to memory
│   │       │   ├── search_items.py    # Search across tiers
│   │       │   └── configure_memory.py # Prune, export, configure
│   │       ├── models/                # Model management
│   │       │   ├── __init__.py
│   │       │   ├── complete_chat.py   # Chat with model selection
│   │       │   └── manage_providers.py # List, switch, health check
│   │       ├── knowledge/             # Knowledge base
│   │       │   ├── __init__.py
│   │       │   ├── add_knowledge.py   # Add to knowledge base
│   │       │   ├── search_knowledge.py # Semantic search
│   │       │   └── manage_knowledge.py # Import, export, prune
│   │       ├── codebase/              # Code analysis
│   │       │   ├── __init__.py
│   │       │   ├── analyze_code.py    # Code quality analysis
│   │       │   ├── generate_code.py   # Code generation
│   │       │   └── search_code.py     # Symbol and code search
│   │       ├── workflow/              # Workflow execution
│   │       │   ├── __init__.py
│   │       │   ├── run_workflow.py    # Execute workflow
│   │       │   └── manage_workflows.py # CRUD for templates
│   │       ├── projects/              # Project management
│   │       │   ├── __init__.py
│   │       │   └── manage_projects.py # Open, close, list
│   │       ├── improvement/           # Self-improvement
│   │       │   ├── __init__.py
│   │       │   ├── scan_system.py     # Scan for improvements
│   │       │   └── review_proposals.py # Approve, reject
│   │       └── search/                # Unified search
│   │           ├── __init__.py
│   │           └── unified_search.py  # Cross-source search
│   │
│   ├── kernel/                        # ═══ AI KERNEL (Cross-Cutting) ═══
│   │   ├── __init__.py
│   │   │
│   │   ├── agents/                    # Agent Engine
│   │   │   ├── __init__.py
│   │   │   ├── interfaces.py          # BaseAgent, AgentRegistry interfaces
│   │   │   ├── registry.py            # Agent registry implementation
│   │   │   ├── orchestrator.py        # Multi-agent orchestration, task routing
│   │   │   ├── router.py              # Intent classification, agent selection
│   │   │   ├── scheduler.py           # Task scheduling, priority queue
│   │   │   ├── executor.py            # Agent execution lifecycle
│   │   │   ├── factory.py             # Agent instantiation
│   │   │   └── builtin/               # Built-in agent implementations
│   │   │       ├── __init__.py
│   │   │       ├── code.py            # Code generation & review agent
│   │   │       ├── debug.py           # Debug analysis agent
│   │   │       ├── planner.py         # Task planning agent
│   │   │       ├── researcher.py      # Web research agent
│   │   │       ├── tester.py          # Test generation agent
│   │   │       ├── security.py        # Security audit agent
│   │   │       ├── documentation.py   # Documentation agent
│   │   │       ├── deployment.py      # Deployment automation agent
│   │   │       ├── memory_manager.py  # Memory maintenance agent
│   │   │       ├── monitoring.py      # System monitoring agent
│   │   │       └── general.py         # General-purpose fallback agent
│   │   │
│   │   ├── memory/                    # Memory Engine
│   │   │   ├── __init__.py
│   │   │   ├── interfaces.py          # MemoryStore, MemoryRetriever interfaces
│   │   │   ├── manager.py             # Cross-tier coordinator
│   │   │   ├── retrieval.py           # Cross-tier retrieval with ranking
│   │   │   ├── ranking.py             # Importance scoring
│   │   │   ├── compression.py         # Conversation summarization
│   │   │   ├── pruning.py             # Memory maintenance, cleanup
│   │   │   └── tiers/                 # Memory tier implementations
│   │   │       ├── __init__.py
│   │   │       ├── session.py         # Ephemeral in-memory session
│   │   │       ├── conversation.py    # Persistent chat history
│   │   │       ├── project.py         # Project-specific context
│   │   │       ├── user.py            # User preferences, facts
│   │   │       ├── code.py            # Code symbols, references
│   │   │       └── vector.py          # Vector embeddings, semantic
│   │   │
│   │   ├── tools/                     # Tool Engine
│   │   │   ├── __init__.py
│   │   │   ├── interfaces.py          # BaseTool, ToolRegistry interfaces
│   │   │   ├── registry.py            # Tool registry implementation
│   │   │   ├── executor.py            # Tool execution with sandbox
│   │   │   ├── permissions.py         # Permission checking
│   │   │   ├── rate_limiter.py        # Rate limiting
│   │   │   └── builtin/               # Built-in tool implementations
│   │   │       ├── __init__.py
│   │   │       ├── file.py            # File read/write/delete
│   │   │       ├── shell.py           # Shell command execution
│   │   │       ├── python.py          # Python code execution
│   │   │       ├── git.py             # Git operations
│   │   │       ├── docker.py          # Docker container management
│   │   │       ├── browser.py         # Headless browser
│   │   │       ├── web_search.py      # Web search
│   │   │       ├── http.py            # HTTP requests
│   │   │       ├── database.py        # Database queries
│   │   │       └── memory.py          # Memory inspection tool
│   │   │
│   │   ├── models/                    # Model Gateway
│   │   │   ├── __init__.py
│   │   │   ├── interfaces.py          # ModelProvider, ModelGateway interfaces
│   │   │   ├── gateway.py             # Provider registry, routing, fallback
│   │   │   ├── router.py              # Capability-based model selection
│   │   │   ├── health.py              # Provider health monitoring
│   │   │   ├── cache.py               # Response caching
│   │   │   └── providers/             # Provider implementations
│   │   │       ├── __init__.py
│   │   │       ├── base.py            # Abstract base implementation
│   │   │       ├── ollama.py          # Ollama
│   │   │       ├── gemini.py          # Google Gemini
│   │   │       ├── openai.py          # OpenAI-compatible
│   │   │       ├── anthropic.py       # Anthropic Claude
│   │   │       ├── deepseek.py        # DeepSeek
│   │   │       ├── lmstudio.py        # LM Studio
│   │   │       ├── vllm.py            # vLLM
│   │   │       ├── tensorrt.py        # TensorRT-LLM
│   │   │       └── local.py           # Rule-based fallback
│   │   │
│   │   ├── knowledge/                 # Knowledge Engine
│   │   │   ├── __init__.py
│   │   │   ├── interfaces.py          # KnowledgeStore, KnowledgeRetriever
│   │   │   ├── extractor.py           # Fact extraction from text
│   │   │   ├── embedder.py            # Text-to-vector embedding
│   │   │   ├── indexer.py             # Knowledge indexing
│   │   │   ├── searcher.py            # Hybrid semantic + keyword search
│   │   │   └── graph.py               # Knowledge graph (future)
│   │   │
│   │   ├── codebase/                  # Repository Analyzer
│   │   │   ├── __init__.py
│   │   │   ├── interfaces.py          # CodebaseIndexer interface
│   │   │   ├── indexer.py             # AST-based indexing engine
│   │   │   ├── search.py              # Symbol search, cross-reference
│   │   │   ├── analyzer.py            # Code quality metrics
│   │   │   ├── dependency_graph.py    # Import/dependency graph
│   │   │   ├── impact.py              # Change impact analysis
│   │   │   ├── structure.py           # Project structure analysis
│   │   │   └── parsers/               # Language parsers
│   │   │       ├── __init__.py
│   │   │       ├── python_parser.py   # Python AST
│   │   │       ├── js_parser.py       # JavaScript/TypeScript
│   │   │       └── generic_parser.py  # Regex-based fallback
│   │   │
│   │   ├── workflow/                  # Workflow Engine
│   │   │   ├── __init__.py
│   │   │   ├── interfaces.py          # WorkflowExecutor interface
│   │   │   ├── executor.py            # DAG-based workflow execution
│   │   │   ├── templates.py           # Built-in workflow templates
│   │   │   └── state.py               # Workflow state persistence
│   │   │
│   │   └── rag/                       # RAG Engine (future)
│   │       ├── __init__.py
│   │       ├── interfaces.py          # RAGEngine interface
│   │       ├── engine.py              # Retrieval-Augmented Generation
│   │       ├── context_builder.py     # Context window assembly
│   │       └── citation.py            # Source citation tracking
│   │
│   ├── infrastructure/               # ═══ LAYER 3: Adapters ═══
│   │   ├── __init__.py
│   │   │
│   │   ├── persistence/               # Database adapters
│   │   │   ├── __init__.py
│   │   │   ├── database.py            # Connection management
│   │   │   ├── migrations/            # Schema migrations
│   │   │   │   ├── __init__.py
│   │   │   │   └── versions/
│   │   │   ├── repositories/          # Repository implementations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── session_repo.py    # SessionRepository → PostgreSQL/SQLite
│   │   │   │   ├── memory_repo.py     # MemoryRepository → PostgreSQL/SQLite
│   │   │   │   ├── knowledge_repo.py  # KnowledgeRepository → PostgreSQL/SQLite
│   │   │   │   ├── metrics_repo.py    # MetricsRepository → PostgreSQL/SQLite
│   │   │   │   ├── agent_repo.py      # AgentRepository → PostgreSQL/SQLite
│   │   │   │   ├── tool_repo.py       # ToolRepository → PostgreSQL/SQLite
│   │   │   │   ├── model_repo.py      # ModelRepository → PostgreSQL/SQLite
│   │   │   │   ├── project_repo.py    # ProjectRepository → filesystem + DB
│   │   │   │   ├── workspace_repo.py  # WorkspaceRepository → PostgreSQL/SQLite
│   │   │   │   ├── codebase_repo.py   # CodebaseRepository → filesystem + DB
│   │   │   │   └── plugin_repo.py     # PluginRepository → PostgreSQL/SQLite
│   │   │   └── models/               # ORM models
│   │   │       ├── __init__.py
│   │   │       ├── access_key.py      # API key model
│   │   │       ├── session.py         # Session model
│   │   │       ├── message.py         # Message model
│   │   │       ├── audit_log.py       # Audit entry model
│   │   │       └── workspace.py       # Workspace model
│   │   │
│   │   ├── cache/                     # Caching adapters
│   │   │   ├── __init__.py
│   │   │   ├── interfaces.py          # CacheProvider interface
│   │   │   ├── redis.py               # Redis implementation
│   │   │   └── memory.py              # In-memory fallback
│   │   │
│   │   ├── storage/                   # File storage adapters
│   │   │   ├── __init__.py
│   │   │   ├── interfaces.py          # StorageProvider interface
│   │   │   ├── local.py               # Local filesystem
│   │   │   └── s3.py                  # S3-compatible (future)
│   │   │
│   │   ├── network/                   # Network adapters
│   │   │   ├── __init__.py
│   │   │   ├── http_client.py         # HTTP client (httpx)
│   │   │   ├── web_search.py          # Web search API client
│   │   │   ├── webhook.py             # Webhook dispatcher
│   │   │   └── websocket.py           # WebSocket client
│   │   │
│   │   ├── ai/                        # AI infrastructure
│   │   │   ├── __init__.py
│   │   │   ├── embeddings.py          # Embedding model adapter
│   │   │   ├── tokenizer.py           # Token counting
│   │   │   └── context.py             # Context window management
│   │   │
│   │   ├── search/                    # Search engine adapters
│   │   │   ├── __init__.py
│   │   │   ├── vector_store.py        # Vector database adapter
│   │   │   └── full_text.py           # Full-text search adapter
│   │   │
│   │   └── plugins/                   # Plugin infrastructure
│   │       ├── __init__.py
│   │       ├── discovery.py           # Plugin discovery (filesystem, packages)
│   │       ├── loader.py              # Plugin loading (import, sandbox)
│   │       ├── validator.py           # Plugin validation (schema, security)
│   │       └── installer.py           # Plugin installation (pip, git, download)
│   │
│   ├── presentation/                  # ═══ LAYER 4: User Interfaces ═══
│   │   ├── __init__.py
│   │   │
│   │   ├── api/                       # REST API
│   │   │   ├── __init__.py
│   │   │   ├── router.py              # URL routing (Django URLs)
│   │   │   ├── middleware.py           # Auth, logging, rate limiting, CORS
│   │   │   ├── responses.py           # Standard response format
│   │   │   ├── errors.py              # Error handler mapping
│   │   │   ├── openapi.py             # OpenAPI schema generation
│   │   │   ├── v1/                    # Legacy API (deprecated)
│   │   │   │   ├── __init__.py
│   │   │   │   └── endpoints/
│   │   │   │       ├── chat.py
│   │   │   │       ├── code.py
│   │   │   │       └── models.py
│   │   │   └── v2/                    # Current API
│   │   │       ├── __init__.py
│   │   │       └── endpoints/
│   │   │           ├── __init__.py
│   │   │           ├── status.py      # GET /api/v2/status/
│   │   │           ├── chat.py        # POST /api/v2/chat/, /api/v2/chat/stream/
│   │   │           ├── agents.py      # GET/POST /api/v2/agents/
│   │   │           ├── tools.py       # GET/POST /api/v2/tools/
│   │   │           ├── models.py      # GET/POST /api/v2/models/
│   │   │           ├── memory.py      # GET/POST/DELETE /api/v2/memory/
│   │   │           ├── knowledge.py   # GET/POST/DELETE /api/v2/knowledge/
│   │   │           ├── sessions.py    # GET/POST/DELETE /api/v2/sessions/
│   │   │           ├── workflows.py   # GET/POST /api/v2/workflows/
│   │   │           ├── projects.py    # GET/POST /api/v2/projects/
│   │   │           ├── keys.py        # GET/POST /api/v2/keys/
│   │   │           ├── plugins.py     # GET/POST /api/v2/plugins/
│   │   │           ├── monitoring.py  # GET /api/v2/monitoring/
│   │   │           └── admin.py       # GET/POST /api/v2/admin/
│   │   │
│   │   ├── cli/                       # Command Line Interface
│   │   │   ├── __init__.py
│   │   │   ├── app.py                 # Main CLI entry point
│   │   │   ├── parser.py              # Argument parser configuration
│   │   │   ├── formatter.py           # Output formatting (table, JSON, text)
│   │   │   ├── completer.py           # Tab completion
│   │   │   └── commands/              # CLI commands (one file per command group)
│   │   │       ├── __init__.py
│   │   │       ├── chat.py            # Interactive chat
│   │   │       ├── agent.py           # Agent management
│   │   │       ├── tool.py            # Tool management
│   │   │       ├── model.py           # Model/provider management
│   │   │       ├── memory.py          # Memory management
│   │   │       ├── knowledge.py       # Knowledge management
│   │   │       ├── session.py         # Session management
│   │   │       ├── project.py         # Project management
│   │   │       ├── status.py          # System status
│   │   │       ├── plugin.py          # Plugin management
│   │   │       ├── config.py          # Configuration management
│   │   │       └── admin.py           # Administrative commands
│   │   │
│   │   ├── websocket/                 # WebSocket handlers (future)
│   │   │   ├── __init__.py
│   │   │   ├── chat_handler.py        # Real-time streaming chat
│   │   │   ├── agent_handler.py       # Agent status updates
│   │   │   └── monitoring_handler.py  # Live metrics stream
│   │   │
│   │   └── sdk/                       # Python SDK (future)
│   │       ├── __init__.py
│   │       ├── client.py              # Sync API client
│   │       ├── async_client.py        # Async API client
│   │       ├── models.py              # SDK data models
│   │       ├── exceptions.py          # SDK-specific exceptions
│   │       └── streaming.py           # Streaming response handling
│   │
│   └── plugins/                       # ═══ PLUGIN SYSTEM ═══
│       ├── __init__.py
│       ├── interfaces.py              # Plugin, AgentPlugin, ToolPlugin, ModelPlugin interfaces
│       ├── registry.py                # Plugin registry (central)
│       ├── manager.py                 # Plugin lifecycle manager
│       ├── sandbox.py                 # Plugin execution sandbox
│       ├── permissions.py             # Plugin permission model
│       ├── validation.py              # Plugin validation
│       ├── dependencies.py            # Dependency resolution
│       ├── versioning.py              # Version compatibility
│       └── marketplace.py             # Remote plugin marketplace (future)
│
├── frontend/                          # ═══ FRONTEND (React SPA) ═══
│   ├── public/                        # Static assets (favicon, manifest)
│   │   ├── index.html
│   │   └── manifest.json
│   ├── src/                           # Source code
│   │   ├── main.tsx                   # Entry point
│   │   ├── App.tsx                    # Root component
│   │   ├── router.tsx                 # Route definitions
│   │   ├── layouts/                   # Layout components
│   │   │   ├── MainLayout.tsx
│   │   │   └── AuthLayout.tsx
│   │   ├── pages/                     # Page components (one per route)
│   │   │   ├── Overview.tsx
│   │   │   ├── Chat.tsx
│   │   │   ├── AccessKeys.tsx
│   │   │   ├── Agents.tsx
│   │   │   ├── Tools.tsx
│   │   │   ├── Models.tsx
│   │   │   ├── Memory.tsx
│   │   │   ├── Knowledge.tsx
│   │   │   ├── Settings.tsx
│   │   │   ├── Admin.tsx
│   │   │   ├── Login.tsx
│   │   │   └── NotFound.tsx
│   │   ├── components/                # Reusable components
│   │   │   ├── common/                # Generic UI components
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   ├── Badge.tsx
│   │   │   │   ├── Spinner.tsx
│   │   │   │   └── Toast.tsx
│   │   │   ├── chat/                  # Chat-specific components
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   ├── Composer.tsx
│   │   │   │   ├── SessionList.tsx
│   │   │   │   └── TypingIndicator.tsx
│   │   │   ├── agent/                 # Agent-specific components
│   │   │   │   ├── AgentCard.tsx
│   │   │   │   ├── AgentStatus.tsx
│   │   │   │   └── AgentSelector.tsx
│   │   │   ├── model/                 # Model-specific components
│   │   │   │   ├── ModelSelector.tsx
│   │   │   │   ├── ProviderStatus.tsx
│   │   │   │   └── ModelPuller.tsx
│   │   │   ├── tool/                  # Tool-specific components
│   │   │   │   └── ToolList.tsx
│   │   │   └── dashboard/             # Dashboard components
│   │   │       ├── MetricCard.tsx
│   │   │       ├── ActivityFeed.tsx
│   │   │       └── PerformanceChart.tsx
│   │   ├── hooks/                     # Custom React hooks
│   │   │   ├── useApi.ts              # API calls with auth
│   │   │   ├── useSessions.ts         # Session management
│   │   │   ├── useLocalStorage.ts     # Persistent state
│   │   │   ├── useStreaming.ts        # SSE streaming
│   │   │   └── useWebSocket.ts        # WebSocket connection
│   │   ├── services/                  # API service layer
│   │   │   ├── api.ts                 # Base API client
│   │   │   ├── chat.ts                # Chat API calls
│   │   │   ├── agents.ts              # Agent API calls
│   │   │   ├── tools.ts               # Tool API calls
│   │   │   ├── models.ts              # Model API calls
│   │   │   ├── keys.ts                # Access key API calls
│   │   │   └── monitoring.ts          # Monitoring API calls
│   │   ├── stores/                    # State management
│   │   │   ├── sessionStore.ts        # Session state
│   │   │   ├── chatStore.ts           # Chat state
│   │   │   ├── agentStore.ts          # Agent state
│   │   │   └── uiStore.ts             # UI state
│   │   ├── utils/                     # Utility functions
│   │   │   ├── api.ts                 # Auth header helpers
│   │   │   ├── format.ts              # Formatting helpers
│   │   │   └── validation.ts          # Client-side validation
│   │   ├── types/                     # TypeScript type definitions
│   │   │   ├── api.ts                 # API request/response types
│   │   │   ├── chat.ts                # Chat types
│   │   │   ├── agent.ts               # Agent types
│   │   │   └── common.ts              # Shared types
│   │   ├── styles/                    # CSS / Tailwind
│   │   │   ├── globals.css            # Global styles, Tailwind imports
│   │   │   ├── themes.css             # Theme variables
│   │   │   └── animations.css         # Animation keyframes
│   │   └── assets/                    # Images, fonts, icons
│   │       ├── logo.svg
│   │       └── fonts/
│   ├── tests/                         # Frontend tests
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── services/
│   ├── scripts/                       # Build/dev scripts
│   │   └── dev.mjs
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── configs/                           # ═══ CONFIGURATION ═══
│   ├── __init__.py
│   ├── loader.py                      # Config loading, merging, validation
│   ├── schema.py                      # Config schema definitions
│   ├── defaults.py                    # Default configuration
│   ├── development.yaml               # Development environment
│   ├── testing.yaml                   # Testing environment
│   ├── staging.yaml                   # Staging environment
│   ├── production.yaml                # Production environment
│   ├── docker.yaml                    # Docker-specific overrides
│   ├── cloud.yaml                     # Cloud-specific overrides
│   ├── enterprise.yaml                # Enterprise-specific overrides
│   └── secrets/                       # Secret files (gitignored)
│       ├── .gitkeep
│       └── example.yaml
│
├── monitoring/                        # ═══ MONITORING ═══
│   ├── __init__.py
│   ├── metrics/                       # Metrics collection & export
│   │   ├── __init__.py
│   │   ├── collector.py               # Metrics registry
│   │   ├── exporters.py               # Prometheus, console, JSON
│   │   └── aggregator.py              # Aggregation & windowing
│   ├── logging/                       # Structured logging
│   │   ├── __init__.py
│   │   ├── formatters.py              # JSON, colored console, plain
│   │   ├── handlers.py                # File, console, remote
│   │   └── context.py                 # Correlation ID context
│   ├── health/                        # Health checks
│   │   ├── __init__.py
│   │   ├── checker.py                 # Health check registry
│   │   └── checks.py                  # Individual health checks
│   ├── tracing/                       # Distributed tracing (future)
│   │   ├── __init__.py
│   │   └── tracer.py
│   └── alerting/                      # Alerting rules (future)
│       ├── __init__.py
│       ├── rules.py                   # Alert rule definitions
│       └── notifiers.py               # Slack, email, PagerDuty
│
├── security/                          # ═══ SECURITY ═══
│   ├── __init__.py
│   ├── auth/                          # Authentication
│   │   ├── __init__.py
│   │   ├── api_keys.py                # API key generation & validation
│   │   ├── jwt.py                     # JWT token handling
│   │   ├── session.py                 # Session authentication
│   │   └── oauth.py                   # OAuth integration (future)
│   ├── authorization/                 # Authorization
│   │   ├── __init__.py
│   │   ├── rbac.py                    # Role-based access control
│   │   └── permissions.py             # Permission checking
│   ├── validation/                    # Input validation & sanitization
│   │   ├── __init__.py
│   │   ├── sanitizer.py               # Input sanitization
│   │   └── schema.py                  # Schema validation
│   ├── encryption/                    # Encryption utilities
│   │   ├── __init__.py
│   │   └── crypto.py                  # Encryption/decryption helpers
│   └── audit/                         # Audit logging
│       ├── __init__.py
│       ├── logger.py                  # Audit event writer
│       └── models.py                  # Audit entry models
│
├── deployment/                        # ═══ DEPLOYMENT ═══
│   ├── docker/                        # Docker configuration
│   │   ├── Dockerfile                 # Production image
│   │   ├── Dockerfile.dev             # Development image
│   │   ├── docker-compose.yml         # Multi-service setup
│   │   ├── docker-compose.prod.yml    # Production overrides
│   │   ├── docker-compose.monitoring.yml # Monitoring stack
│   │   └── .dockerignore
│   ├── kubernetes/                    # Kubernetes manifests (future)
│   │   ├── namespace.yaml
│   │   ├── configmap.yaml
│   │   ├── secrets.yaml
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── ingress.yaml
│   │   ├── hpa.yaml
│   │   └── pvc.yaml
│   ├── terraform/                     # Infrastructure as Code (future)
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── scripts/                       # Deployment scripts
│   │   ├── install.sh                 # Linux/macOS installer
│   │   ├── install.ps1                # Windows installer
│   │   ├── migrate.sh                 # Database migration
│   │   ├── backup.sh                  # Backup script
│   │   ├── restore.sh                 # Restore script
│   │   ├── healthcheck.sh             # Health check script
│   │   └── setup.py                   # First-run setup
│   └── monitoring/                    # Monitoring stack configs
│       ├── prometheus.yml
│       ├── grafana/
│       │   ├── datasources.yml
│       │   └── dashboards/
│       └── loki/
│           └── config.yml
│
├── plugins/                           # ═══ INSTALLED PLUGINS ═══
│   ├── __init__.py
│   ├── builtin/                       # Plugins shipped with AIDA (registered above)
│   └── external/                      # Third-party plugins (installed at runtime)
│       └── .gitkeep
│
├── tests/                             # ═══ TEST SUITE ═══
│   ├── __init__.py
│   ├── conftest.py                    # Global fixtures
│   ├── pytest.ini                     # Pytest configuration
│   ├── unit/                          # Unit tests
│   │   ├── domain/
│   │   │   ├── test_entities.py
│   │   │   ├── test_events.py
│   │   │   ├── test_exceptions.py
│   │   │   └── test_value_objects.py
│   │   ├── application/
│   │   │   ├── test_chat_use_cases.py
│   │   │   ├── test_agent_use_cases.py
│   │   │   ├── test_tool_use_cases.py
│   │   │   └── test_memory_use_cases.py
│   │   ├── kernel/
│   │   │   ├── test_agent_engine.py
│   │   │   ├── test_memory_engine.py
│   │   │   ├── test_tool_engine.py
│   │   │   ├── test_model_gateway.py
│   │   │   └── test_codebase_indexer.py
│   │   └── infrastructure/
│   │       ├── test_repositories.py
│   │       ├── test_cache.py
│   │       └── test_network.py
│   ├── integration/                   # Integration tests
│   │   ├── test_api_endpoints.py
│   │   ├── test_database_repos.py
│   │   └── test_authentication.py
│   ├── e2e/                           # End-to-end tests
│   │   └── test_chat_workflow.py
│   ├── performance/                   # Performance & load tests
│   │   └── test_load.py
│   ├── security/                      # Security tests
│   │   └── test_security.py
│   ├── mocks/                         # Shared mock implementations
│   │   ├── __init__.py
│   │   ├── mock_repositories.py       # In-memory repo implementations
│   │   ├── mock_providers.py          # Mock LLM providers
│   │   ├── mock_agents.py             # Mock agents
│   │   └── mock_tools.py              # Mock tools
│   └── fixtures/                      # Test data fixtures
│       ├── sample_code.py
│       └── sample_projects/
│
├── docs/                              # ═══ DOCUMENTATION ═══
│   ├── README.md                      # Project overview
│   ├── CONTRIBUTING.md                # Contribution guide
│   ├── CHANGELOG.md                   # Version history
│   ├── architecture/                  # Architecture documentation
│   │   ├── ARCHITECTURE.md
│   │   ├── FOLDER_STRUCTURE.md
│   │   ├── LAYER_DIAGRAM.md
│   │   ├── DEPENDENCY_DIAGRAM.md
│   │   └── DECISIONS.md               # Architecture Decision Records
│   ├── guides/                        # User & developer guides
│   │   ├── INSTALL.md
│   │   ├── CONFIGURATION.md
│   │   ├── API_REFERENCE.md
│   │   ├── CLI_REFERENCE.md
│   │   ├── PLUGIN_DEVELOPMENT.md
│   │   └── DEPLOYMENT.md
│   ├── security/                      # Security documentation
│   │   ├── THREAT_MODEL.md
│   │   └── SECURITY_POLICIES.md
│   └── api/                           # API specification (OpenAPI)
│       └── openapi.yaml
│
├── scripts/                           # ═══ ROOT SCRIPTS ═══
│   ├── dev.sh                         # Development startup (Unix)
│   ├── dev.ps1                        # Development startup (Windows)
│   ├── lint.sh                        # Run all linters
│   ├── test.sh                        # Run all tests
│   ├── typecheck.sh                   # Run type checker
│   └── clean.sh                       # Clean build artifacts
│
├── var/                               # ═══ RUNTIME DATA (gitignored) ═══
│   ├── data/                          # Persistent databases, files
│   │   ├── db.sqlite3                 # Django ORM database
│   │   ├── memory.db                  # Memory storage
│   │   ├── knowledge.db               # Knowledge base
│   │   ├── metrics.db                 # Metrics storage
│   │   └── projects/                  # Project workspaces
│   ├── logs/                          # Runtime logs
│   │   ├── aida.log
│   │   ├── access.log
│   │   └── error.log
│   ├── cache/                         # Cache files
│   ├── run/                           # PID files, sockets
│   └── tmp/                           # Temporary files
│
├── pyproject.toml                     # Python project metadata
├── requirements.txt                   # Python dependencies
├── requirements-dev.txt               # Dev dependencies
├── Makefile                           # Common commands
├── .env.example                       # Environment template
├── .env                               # Active environment (gitignored)
├── .gitignore
├── .dockerignore
├── .editorconfig                      # Editor configuration
├── .pre-commit-config.yaml            # Pre-commit hooks
├── .secrets.yaml                      # Secret scanning config
├── docker-compose.yml                 # Root docker-compose (links to deployment/)
└── README.md                          # Project overview
```

## 3. Migration Strategy (File-by-File)

| Current Location | Target Location | Strategy |
|---|---|---|
| `webapp/aida_controller.py` | `aida/kernel/agents/` + `aida/kernel/memory/` + `aida/kernel/tools/` + `aida/infrastructure/persistence/` | DECOMPOSE — extract classes by concern |
| `webapp/views.py` | `aida/presentation/api/v2/endpoints/` | SPLIT — one file per endpoint group |
| `webapp/agents/*.py` | `aida/kernel/agents/builtin/` | MOVE — files stay mostly the same |
| `webapp/agents.py` | `aida/kernel/agents/router.py` | MERGE — routing logic |
| `webapp/llm/*.py` | `aida/kernel/models/` | RESTRUCTURE — split into interfaces, gateway, providers |
| `webapp/memory/*.py` | `aida/kernel/memory/tiers/` | MOVE — split into tier files |
| `webapp/tools/*.py` | `aida/kernel/tools/` | RESTRUCTURE — split professional.py |
| `webapp/api/*.py` | `aida/presentation/api/v2/endpoints/` | MOVE — rename to endpoints |
| `webapp/security.py` | `aida/security/auth/` | SPLIT — extract into modules |
| `webapp/sandbox.py` | `aida/plugins/sandbox.py` | MOVE — belongs to plugin system |
| `webapp/repo_analyzer/*.py` | `aida/kernel/codebase/` | MOVE — rename module |
| `webapp/self_improvement/*.py` | `aida/application/use_cases/improvement/` | MOVE — use case layer |
| `webapp/knowledge_store.py` | `aida/kernel/knowledge/` | MOVE — kernel engine |
| `webapp/code_fixer.py` | `aida/kernel/codebase/analyzer.py` | MERGE |
| `aidaos/domain/*.py` | `aida/domain/` | RESTRUCTURE — split into sub-packages |
| `aidaos/application/*.py` | `aida/application/` | RESTRUCTURE — split into sub-packages |
| `aidaos/infrastructure/*.py` | `aida/infrastructure/` | MOVE — merge with infrastructure |
| `aidaos/presentation/*.py` | `aida/presentation/` | MOVE |
| `aidaos/container.py` | `aida/container.py` | MOVE |
| `AIDA/settings.py` | `aida/infrastructure/persistence/database.py` | EXTRACT — Django settings stay |
| `AIDA/urls.py` | `aida/presentation/api/router.py` | MOVE |
| `AIDA/wsgi.py` | `deployment/` | MOVE — entry point |
| `frontend/src/App.tsx` | `frontend/src/App.tsx` | RESTRUCTURE — extract components |
| `data/*.db` | `var/data/` | MOVE |
| `logs/*.log` | `var/logs/` | MOVE |
| `scripts/*.py` | `deployment/scripts/` or `scripts/` | SORT — dev scripts stay, deploy scripts move |
| `core_agi.py` | DELETE | Toy script, not needed |
| `aida_autonomous.py` | DELETE or `aida/kernel/agents/autonomous.py` | REWRITE as real autonomous agent |
| `aida_master_controller.py` | `aida/presentation/cli/app.py` | MOVE and refactor |
| `aida_voice.py` | DELETE | Duplicate of master controller |
| `server_manager.py` | `deployment/scripts/` | MOVE |
