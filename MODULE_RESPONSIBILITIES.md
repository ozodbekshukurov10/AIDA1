# AIDA — Module Responsibilities

## 1. Domain Layer

### 1.1 entities/

#### `entities/agents.py`
- **Does:** Defines AgentSpec, AgentContext, AgentResult — the core agent data model
- **Does NOT:** Execute agents, route tasks, manage agent lifecycle
- **Works with:** All layers (universal data model)
- **Independent from:** Infrastructure, framework code

#### `entities/models.py`
- **Does:** Defines ModelSpec, CapabilityAdvertisement — LLM model metadata
- **Does NOT:** Make API calls, manage providers, handle authentication
- **Works with:** Model Gateway, Application use cases
- **Independent from:** Specific LLM providers

#### `entities/tools.py`
- **Does:** Defines ToolSpec, ToolResult — tool specification and execution results
- **Does NOT:** Execute anything, access files, make network calls
- **Works with:** Tool Engine, Application use cases
- **Independent from:** Operating system, filesystem

#### `entities/memory.py`
- **Does:** Defines MemoryItem, MemoryQuery — memory data structures
- **Does NOT:** Store or retrieve from databases
- **Works with:** Memory Engine, Application use cases
- **Independent from:** Database technology

#### `entities/messages.py`
- **Does:** Defines Message, Completion, StreamingChunk — chat data structures
- **Does NOT:** Send messages, manage sessions
- **Works with:** Model Gateway, Chat use cases
- **Independent from:** Transport protocol (HTTP/WebSocket/IPC)

#### `entities/sessions.py`
- **Does:** Defines Session, SessionConfig — user session model
- **Does NOT:** Create or manage sessions in database
- **Works with:** Session repository, Chat use cases
- **Independent from:** Authentication mechanism

#### `entities/projects.py`
- **Does:** Defines Project, ProjectConfig — project workspace model
- **Does NOT:** Access filesystem, run processes
- **Works with:** Project repository, Codebase analysis
- **Independent from:** Version control system

#### `entities/workflows.py`
- **Does:** Defines WorkflowTemplate, WorkflowStep — workflow orchestration model
- **Does NOT:** Execute workflow steps
- **Works with:** Workflow use cases, Agent Engine
- **Independent from:** Execution environment

#### `entities/knowledge.py`
- **Does:** Defines KnowledgeItem, KnowledgeQuery — knowledge base data model
- **Does NOT:** Index or search knowledge
- **Works with:** Knowledge Engine, Search use cases
- **Independent from:** Vector database technology

#### `entities/proposals.py`
- **Does:** Defines Proposal, ProposalType, ProposalStatus — improvement proposal model
- **Does NOT:** Generate or apply improvements
- **Works with:** Self-improvement use cases
- **Independent from:** Analysis tools

### 1.2 events/

#### `events/event_bus.py`
- **Does:** In-process pub/sub event bus with subscribe, publish, unsubscribe
- **Does NOT:** Provide inter-process messaging, guarantee delivery, persist events
- **Works with:** All layers (publish and subscribe)
- **Independent from:** Message broker technology

#### `events/agent_events.py`
- **Does:** Defines AgentStarted, AgentCompleted, AgentFailed, AgentDelegated events
- **Does NOT:** Start or stop agents
- **Works with:** Agent Engine, Monitoring
- **Independent from:** Agent implementations

#### `events/chat_events.py`
- **Does:** Defines ChatStarted, ChatCompleted, MessageReceived events
- **Does NOT:** Handle chat messages
- **Works with:** Chat use cases, Monitoring
- **Independent from:** Transport layer

#### `events/tool_events.py`
- **Does:** Defines ToolExecuted, ToolFailed events
- **Does NOT:** Execute tools
- **Works with:** Tool Engine, Audit
- **Independent from:** Tool implementations

### 1.3 exceptions/

#### `exceptions/base.py`
- **Does:** Defines AIDAError root exception with code, status_code, message, details
- **Does NOT:** Handle errors, log errors
- **Works with:** All layers (base class for all exceptions)
- **Independent from:** Everything

#### `exceptions/agent_errors.py`
- **Does:** Agent-specific exceptions (AgentNotFoundError, AgentExecutionError)
- **Does:** Inherit from AIDAError
- **Independent from:** Agent implementations

#### `exceptions/tool_errors.py`
- **Does:** Tool-specific exceptions (ToolNotFoundError, ToolPermissionError, ToolTimeoutError)
- **Independent from:** Tool implementations

#### `exceptions/model_errors.py`
- **Does:** Provider-specific exceptions (ProviderOfflineError, ProviderAuthError, ProviderRateLimitError)
- **Independent from:** LLM provider implementations

#### `exceptions/security_errors.py`
- **Does:** Security exceptions (AuthenticationError, AuthorizationError)
- **Independent from:** Auth mechanism

### 1.4 value_objects/

#### `value_objects/permissions.py`
- **Does:** Permission, PermissionLevel value objects
- **Does NOT:** Enforce permissions
- **Works with:** Security layer, Tool Engine, Agent Engine

#### `value_objects/identifiers.py`
- **Does:** Strongly-typed ID values (AgentID, SessionID, ToolID, TaskID)
- **Does NOT:** Generate IDs
- **Works with:** All entities

### 1.5 interfaces/ (Ports)

#### `interfaces/agent_repository.py`
- **Does:** Defines contract for agent storage and execution
- **Methods:** register(), get(), list(), execute(), get_status()
- **Works with:** Infrastructure implementation, Application use cases

#### `interfaces/tool_repository.py`
- **Does:** Defines contract for tool storage and execution
- **Methods:** register(), get(), list(), execute()
- **Works with:** Infrastructure implementation, Application use cases

#### `interfaces/model_repository.py`
- **Does:** Defines contract for LLM provider management
- **Methods:** register(), get(), list(), chat(), chat_stream(), check_health()
- **Works with:** Infrastructure implementation, Model Gateway

#### `interfaces/memory_repository.py`
- **Does:** Defines contract for memory persistence
- **Methods:** store(), get(), search(), update(), delete(), count(), clear(), get_stats()
- **Works with:** Infrastructure implementation, Memory Engine

#### `interfaces/session_repository.py`
- **Does:** Defines contract for session persistence
- **Methods:** create(), get(), list(), update(), delete(), add_message(), get_messages()
- **Works with:** Infrastructure implementation, Chat use cases

---

## 2. Application Layer

### 2.1 use_cases/chat/

#### `chat/chat_use_case.py`
- **Does:** Orchestrates chat completion: validates input, retrieves context, calls model, stores history
- **Does NOT:** Access database directly, call LLM providers directly
- **Depends on:** ModelGateway, MemoryEngine, SessionRepository (via container)

#### `chat/stream_use_case.py`
- **Does:** Streaming version of chat use case using async generators
- **Does NOT:** Block on LLM response
- **Depends on:** ModelGateway (streaming interface), MemoryEngine

### 2.2 use_cases/agents/

#### `agents/execute_agent.py`
- **Does:** Routes task to appropriate agent, manages execution lifecycle
- **Does NOT:** Implement agent logic
- **Depends on:** AgentEngine, ModelGateway, MemoryEngine

#### `agents/manage_agents.py`
- **Does:** Lists, registers, configures agents
- **Does NOT:** Execute agents
- **Depends on:** AgentRegistry interface

### 2.3 use_cases/tools/

#### `tools/execute_tool.py`
- **Does:** Validates, executes, and returns tool results
- **Does NOT:** Implement tool logic
- **Depends on:** ToolEngine, PermissionService

### 2.4 use_cases/memory/

#### `memory/store_memory.py`
- **Does:** Stores to appropriate memory tier with importance scoring
- **Does NOT:** Manage database connections
- **Depends on:** MemoryEngine, RankingService

#### `memory/search_memory.py`
- **Does:** Cross-tier semantic search with ranking fusion
- **Does NOT:** Embed text or query vector databases
- **Depends on:** MemoryEngine, EmbeddingService

### 2.5 use_cases/models/

#### `models/chat_model.py`
- **Does:** Routes to appropriate provider, handles fallback, tracks usage
- **Does NOT:** Make HTTP calls to LLM APIs
- **Depends on:** ModelGateway, MetricsCollector

### 2.6 use_cases/knowledge/

#### `knowledge/add_knowledge.py`
- **Does:** Extracts facts, embeds, indexes into knowledge base
- **Does NOT:** Implement embedding or indexing algorithms
- **Depends on:** KnowledgeEngine, EmbeddingService

### 2.7 use_cases/codebase/

#### `codebase/analyze_code.py`
- **Does:** Analyzes code quality, complexity, dependencies
- **Does NOT:** Parse AST directly
- **Depends on:** CodebaseIndexer

### 2.8 use_cases/workflow/

#### `workflow/execute_workflow.py`
- **Does:** Executes multi-step workflow with error handling and state persistence
- **Does NOT:** Implement step logic
- **Depends on:** AgentEngine, ToolEngine, MemoryEngine

### 2.9 use_cases/search/

#### `search/search_all.py`
- **Does:** Unified search across memory, knowledge, codebase
- **Does:** Fuses and ranks results from multiple sources
- **Depends on:** MemoryEngine, KnowledgeEngine, CodebaseIndexer

---

## 3. AI Kernel

### 3.1 Agent Engine

#### `agents/orchestrator.py`
- **Does:** Manages agent lifecycle, task routing, delegation, parallel execution
- **Does NOT:** Implement agent-specific logic
- **Depends on:** Agent registry, Memory, Model Gateway, Tools
- **Independent from:** Specific agent implementations

#### `agents/router.py`
- **Does:** Intent classification, task type detection, agent selection
- **Does NOT:** Execute tasks
- **Depends on:** Model Gateway (for intent analysis)
- **Independent from:** Agent implementations

#### `agents/scheduler.py`
- **Does:** Background task scheduling, priority queue, cron-like execution
- **Does NOT:** Execute agent logic
- **Depends on:** Agent registry
- **Independent from:** Scheduling backend (in-memory → Redis → Celery)

#### `agents/builtin/*.py`
- **Does:** Each agent implements domain-specific logic (code, debug, plan, etc.)
- **Does NOT:** Manage their own lifecycle, routing, or memory
- **Depends on:** BaseAgent interface, Tool Engine, Model Gateway

### 3.2 Memory Engine

#### `memory/manager.py`
- **Does:** Coordinates memory tiers, determines storage strategy, manages pruning
- **Does NOT:** Access database directly
- **Depends on:** Memory tier interfaces, Compression, Ranking

#### `memory/tiers/session_memory.py`
- **Does:** Ephemeral in-memory session context (FIFO with token budget)
- **Does NOT:** Persist data across sessions
- **Independent from:** Database

#### `memory/tiers/conversation_memory.py`
- **Does:** Per-user persistent chat history with summarization
- **Does NOT:** Embed or vector search
- **Depends on:** MemoryRepository interface

#### `memory/tiers/vector_memory.py`
- **Does:** Vector-based semantic storage and retrieval
- **Does NOT:** Choose embedding model
- **Depends on:** MemoryRepository interface, EmbeddingService

#### `memory/compression.py`
- **Does:** LLM-based conversation summarization
- **Does NOT:** Store summaries
- **Depends on:** Model Gateway

#### `memory/retrieval.py`
- **Does:** Cross-tier retrieval with importance-based ranking
- **Does NOT:** Implement individual tier storage
- **Depends on:** All memory tier interfaces

#### `memory/pruning.py`
- **Does:** Memory maintenance (delete old items, consolidate, deduplicate)
- **Does NOT:** Make retention decisions
- **Depends on:** MemoryRepository interface

### 3.3 Tool Engine

#### `tools/registry.py`
- **Does:** Tool registration, discovery, metadata management
- **Does NOT:** Execute tools
- **Independent from:** Tool implementations

#### `tools/executor.py`
- **Does:** Tool execution with sandboxing, timeout, resource limits
- **Does NOT:** Implement tool logic
- **Depends on:** Sandbox plugin, Permission service

#### `tools/builtin/file_tool.py`
- **Does:** File read/write within project scope
- **Does NOT:** Execute shell commands
- **Depends on:** Storage adapter

#### `tools/builtin/shell_tool.py`
- **Does:** Shell command execution in sandbox
- **Does NOT:** Access files outside sandbox
- **Depends on:** Sandbox, Network client

#### `tools/builtin/git_tool.py`
- **Does:** Git operations (clone, commit, push, status, diff)
- **Does NOT:** Access other VCS systems
- **Depends on:** Git executable (via infrastructure)

### 3.4 Knowledge Engine

#### `knowledge/extractor.py`
- **Does:** Fact extraction from text using LLM
- **Does NOT:** Store facts
- **Depends on:** Model Gateway

#### `knowledge/embedder.py`
- **Does:** Text-to-vector conversion
- **Does NOT:** Store vectors
- **Depends on:** Embedding model adapter

#### `knowledge/indexer.py`
- **Does:** Build and maintain knowledge index
- **Does NOT:** Search the index
- **Depends on:** Embedder, KnowledgeRepository

#### `knowledge/searcher.py`
- **Does:** Semantic + keyword hybrid search
- **Does NOT:** Index new content
- **Depends on:** KnowledgeIndex, Embedder

### 3.5 Model Gateway

#### `models/gateway.py`
- **Does:** Provider registry, capability-based routing, automatic fallback, health monitoring
- **Does NOT:** Make HTTP calls directly
- **Depends on:** ModelProvider interface, Health checker, Cache

#### `models/router.py`
- **Does:** Selects best provider based on task requirements, cost, latency, availability
- **Does NOT:** Execute model calls
- **Depends on:** Provider specs, Usage metrics

#### `models/providers/*.py`
- **Does:** Each provider implements LLM API integration
- **Does NOT:** Route between providers
- **Depends on:** BaseProvider interface, HTTP client

### 3.6 Codebase Engine

#### `codebase/indexer.py`
- **Does:** AST-based code indexing (symbols, dependencies, references)
- **Does NOT:** Analyze code quality
- **Depends on:** Language parsers

#### `codebase/analyzer.py`
- **Does:** Code quality analysis (complexity, coupling, bugs)
- **Does NOT:** Modify code
- **Depends on:** CodebaseIndexer, Model Gateway

#### `codebase/search.py`
- **Does:** Symbol search, cross-reference, find usages
- **Does NOT:** Index new code
- **Depends on:** CodebaseIndexer

---

## 4. Infrastructure Layer

### 4.1 Persistence

#### `persistence/repositories/*.py`
- **Does:** Implements domain repository interfaces against database (SQLite/PostgreSQL)
- **Does NOT:** Contain business logic
- **Depends on:** Domain interfaces, Database connection

#### `persistence/cache/redis_cache.py`
- **Does:** Redis-backed caching for sessions, provider health, rate limiting
- **Does NOT:** Act as primary storage
- **Independent from:** Business logic

### 4.2 Security

#### `security/auth.py`
- **Does:** API key validation, JWT token creation/validation, session auth
- **Does NOT:** Make authorization decisions
- **Depends on:** Domain entities (AccessKey)

#### `security/audit.py`
- **Does:** Audit logging for all security-relevant operations
- **Does NOT:** Make access decisions
- **Depends on:** Domain events

### 4.3 Network

#### `network/http_client.py`
- **Does:** HTTP client with retry, timeout, circuit breaker
- **Does NOT:** Implement business logic
- **Independent from:** Application layer

---

## 5. Presentation Layer

### 5.1 API v2 Endpoints

- **Does:** Handle HTTP requests, validate input, call use cases, format responses
- **Does NOT:** Contain business logic, access infrastructure directly
- **Depends on:** Application use cases, DTOs, Security middleware

### 5.2 CLI

- **Does:** Provide command-line interface for all platform functions
- **Does NOT:** Implement platform logic
- **Depends on:** Application use cases, DTOs

---

## 6. Plugin Layer

- **Does:** Discover, load, validate, register, sandbox, and manage plugins
- **Does NOT:** Implement plugin functionality
- **Depends on:** Kernel interfaces (BaseAgent, BaseTool, BaseModelProvider, etc.)

---

## 7. Cross-Cutting

### 7.1 Monitoring

- **Does:** Collect metrics, format logs, run health checks, trace requests
- **Does NOT:** Make business decisions
- **Independent from:** Business logic (observes, does not control)

### 7.2 Configuration

- **Does:** Load, merge, validate, and expose configuration
- **Does NOT:** Contain business logic
- **Independent from:** All layers (read-only)

### 7.3 Security

- **Does:** Authenticate, authorize, validate input, audit access
- **Does NOT:** Make business decisions
- **Depends on:** Domain entities (for permission models)
