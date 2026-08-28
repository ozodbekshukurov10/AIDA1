# AIDA — Interface Design

## 1. Interface Principles

1. Every module exposes exactly one public interface
2. Interfaces are defined in the `domain/interfaces/` or `kernel/*/interfaces/` directories
3. All interface methods are async (future-proof for distributed execution)
4. All interface methods have complete type hints
5. Interfaces use domain entities as parameters and return types (never raw dicts)
6. Every interface has a corresponding test with a mock implementation

## 2. Domain Repository Interfaces

### AgentRepository
```python
class AgentRepository(ABC):
    """Contract for agent storage and execution."""

    @abstractmethod
    async def register(self, spec: AgentSpec) -> AgentSpec:
        """Register a new agent type. Returns registered spec with ID."""

    @abstractmethod
    async def get(self, agent_id: AgentID) -> AgentSpec:
        """Get agent spec by ID. Raises AgentNotFoundError."""

    @abstractmethod
    async def list(self) -> list[AgentSpec]:
        """List all registered agents."""

    @abstractmethod
    async def execute(self, spec: AgentSpec, context: AgentContext) -> AgentResult:
        """Execute an agent with given context. Returns result."""

    @abstractmethod
    async def get_status(self, agent_id: AgentID) -> AgentStatus:
        """Get current status of an agent."""
```

### ToolRepository
```python
class ToolRepository(ABC):
    """Contract for tool storage and execution."""

    @abstractmethod
    async def register(self, spec: ToolSpec) -> ToolSpec:
        """Register a new tool. Returns registered spec with ID."""

    @abstractmethod
    async def get(self, tool_id: ToolID) -> ToolSpec:
        """Get tool spec by ID. Raises ToolNotFoundError."""

    @abstractmethod
    async def list(self) -> list[ToolSpec]:
        """List all registered tools."""

    @abstractmethod
    async def execute(self, spec: ToolSpec, args: dict) -> ToolResult:
        """Execute a tool with given arguments. Returns result."""
```

### ModelRepository (was ProviderRepository)
```python
class ModelRepository(ABC):
    """Contract for LLM provider management."""

    @abstractmethod
    async def register(self, spec: ModelSpec) -> ModelSpec:
        """Register a model provider. Returns registered spec."""

    @abstractmethod
    async def get(self, model_id: str) -> ModelSpec:
        """Get model spec by ID. Raises ProviderNotFoundError."""

    @abstractmethod
    async def list(self) -> list[ModelSpec]:
        """List all registered model providers."""

    @abstractmethod
    async def chat(self, model_id: str, messages: list[Message], **kwargs) -> Completion:
        """Send chat messages to a model. Returns completion."""

    @abstractmethod
    async def chat_stream(self, model_id: str, messages: list[Message], **kwargs) -> AsyncIterator[StreamingChunk]:
        """Streaming chat completion."""

    @abstractmethod
    async def check_health(self, model_id: str) -> ProviderStatus:
        """Check if a provider is healthy and responsive."""
```

### MemoryRepository
```python
class MemoryRepository(ABC):
    """Contract for memory persistence."""

    @abstractmethod
    async def store(self, item: MemoryItem) -> MemoryItem:
        """Store a memory item. Returns stored item with ID."""

    @abstractmethod
    async def get(self, memory_id: str) -> MemoryItem:
        """Get memory item by ID. Raises MemoryNotFoundError."""

    @abstractmethod
    async def search(self, query: MemoryQuery) -> list[MemoryItem]:
        """Search memory items by query."""

    @abstractmethod
    async def update(self, item: MemoryItem) -> MemoryItem:
        """Update an existing memory item."""

    @abstractmethod
    async def delete(self, memory_id: str) -> None:
        """Delete a memory item."""

    @abstractmethod
    async def count(self, memory_type: MemoryType | None = None) -> int:
        """Count memory items, optionally filtered by type."""

    @abstractmethod
    async def clear(self, memory_type: MemoryType | None = None) -> None:
        """Clear memory items, optionally filtered by type."""

    @abstractmethod
    async def get_stats(self) -> dict:
        """Get memory storage statistics."""
```

### SessionRepository
```python
class SessionRepository(ABC):
    """Contract for session persistence."""

    @abstractmethod
    async def create(self, session: Session) -> Session:
        """Create a new session."""

    @abstractmethod
    async def get(self, session_id: SessionID) -> Session:
        """Get session by ID. Raises SessionNotFoundError."""

    @abstractmethod
    async def list(self, limit: int = 50, offset: int = 0) -> list[Session]:
        """List sessions with pagination."""

    @abstractmethod
    async def update(self, session: Session) -> Session:
        """Update session metadata."""

    @abstractmethod
    async def delete(self, session_id: SessionID) -> None:
        """Delete a session."""

    @abstractmethod
    async def add_message(self, session_id: SessionID, message: Message) -> None:
        """Add a message to session history."""

    @abstractmethod
    async def get_messages(self, session_id: SessionID, limit: int = 100) -> list[Message]:
        """Get messages for a session."""
```

### KnowledgeRepository
```python
class KnowledgeRepository(ABC):
    """Contract for knowledge base persistence."""

    @abstractmethod
    async def add(self, item: KnowledgeItem) -> KnowledgeItem:
        """Add an item to knowledge base."""

    @abstractmethod
    async def search(self, query: KnowledgeQuery) -> list[KnowledgeItem]:
        """Search knowledge base."""

    @abstractmethod
    async def get(self, knowledge_id: str) -> KnowledgeItem:
        """Get knowledge item by ID."""

    @abstractmethod
    async def delete(self, knowledge_id: str) -> None:
        """Delete a knowledge item."""

    @abstractmethod
    async def get_stats(self) -> dict:
        """Get knowledge base statistics."""
```

### MetricsRepository
```python
class MetricsRepository(ABC):
    """Contract for metrics persistence."""

    @abstractmethod
    async def record_request(self, endpoint: str, latency_ms: float, status_code: int, user_id: str | None = None) -> None:
        """Record an API request metric."""

    @abstractmethod
    async def record_agent_call(self, agent_id: AgentID, latency_ms: float, tokens_used: int, success: bool) -> None:
        """Record an agent execution metric."""

    @abstractmethod
    async def get_stats(self, since: datetime | None = None) -> PerformanceReport:
        """Get aggregated performance stats."""

    @abstractmethod
    async def get_agent_stats(self, agent_id: AgentID, since: datetime | None = None) -> dict:
        """Get per-agent performance stats."""

    @abstractmethod
    async def get_health_score(self) -> float:
        """Get overall system health score (0.0 - 1.0)."""
```

### ProjectRepository
```python
class ProjectRepository(ABC):
    """Contract for project workspace management."""

    @abstractmethod
    async def open(self, path: str) -> Project:
        """Open a project at given path."""

    @abstractmethod
    async def close(self, project_id: str) -> None:
        """Close a project."""

    @abstractmethod
    async def get(self, project_id: str) -> Project:
        """Get project info."""

    @abstractmethod
    async def list(self) -> list[Project]:
        """List all open projects."""

    @abstractmethod
    async def get_files(self, project_id: str, pattern: str | None = None) -> list[str]:
        """Get files in a project, optionally filtered by glob pattern."""

    @abstractmethod
    async def read_file(self, project_id: str, path: str) -> str:
        """Read a file's contents."""

    @abstractmethod
    async def write_file(self, project_id: str, path: str, content: str) -> None:
        """Write content to a file."""
```

### WorkspaceRepository
```python
class WorkspaceRepository(ABC):
    """Contract for multi-tenant workspace management (future)."""

    @abstractmethod
    async def create(self, workspace: Workspace) -> Workspace:
        """Create a new workspace."""

    @abstractmethod
    async def get(self, workspace_id: WorkspaceID) -> Workspace:
        """Get workspace by ID."""

    @abstractmethod
    async def list(self) -> list[Workspace]:
        """List all workspaces."""

    @abstractmethod
    async def add_member(self, workspace_id: WorkspaceID, user_id: str, role: str) -> None:
        """Add a member to workspace with role."""

    @abstractmethod
    async def remove_member(self, workspace_id: WorkspaceID, user_id: str) -> None:
        """Remove a member from workspace."""

    @abstractmethod
    async def get_members(self, workspace_id: WorkspaceID) -> list[MemberInfo]:
        """Get all workspace members with roles."""
```

---

## 3. AI Kernel Interfaces

### BaseAgent (Agent Plugin Interface)
```python
class BaseAgent(ABC):
    """Interface for all agents — built-in and plugins."""

    @property
    @abstractmethod
    def spec(self) -> AgentSpec:
        """Return agent specification (name, description, capabilities, tools)."""

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute agent task with given context. Returns result."""

    @abstractmethod
    async def can_handle(self, task_type: str, context: AgentContext) -> float:
        """Return confidence score (0.0-1.0) for handling this task. Used by router."""
```

### AgentRegistry
```python
class AgentRegistry(ABC):
    """Interface for agent registration and lookup."""

    @abstractmethod
    async def register(self, agent: BaseAgent) -> None:
        """Register an agent instance."""

    @abstractmethod
    async def unregister(self, agent_id: AgentID) -> None:
        """Unregister an agent."""

    @abstractmethod
    async def get(self, agent_id: AgentID) -> BaseAgent:
        """Get agent by ID. Raises AgentNotFoundError."""

    @abstractmethod
    async def list(self) -> list[BaseAgent]:
        """List all registered agents."""

    @abstractmethod
    async def find_best(self, task_type: str, context: AgentContext) -> BaseAgent:
        """Find the best agent for a task based on confidence scores."""
```

### MemoryStore
```python
class MemoryStore(ABC):
    """Interface for individual memory tier storage."""

    @abstractmethod
    async def store(self, item: MemoryItem) -> MemoryItem:
        """Store a memory item."""

    @abstractmethod
    async def get(self, memory_id: str) -> MemoryItem:
        """Get memory item by ID."""

    @abstractmethod
    async def search(self, query: MemoryQuery) -> list[MemoryItem]:
        """Search items in this tier."""

    @abstractmethod
    async def delete(self, memory_id: str) -> None:
        """Delete an item."""

    @abstractmethod
    async def clear(self) -> None:
        """Clear all items in this tier."""
```

### MemoryRetriever
```python
class MemoryRetriever(ABC):
    """Interface for cross-tier memory retrieval."""

    @abstractmethod
    async def retrieve(self, query: MemoryQuery, tiers: list[MemoryType] | None = None) -> list[MemoryItem]:
        """Retrieve items across specified tiers, fused and ranked."""

    @abstractmethod
    async def retrieve_context(self, session_id: SessionID, token_budget: int = 4096) -> str:
        """Retrieve compressed context for a session within token budget."""
```

### BaseTool (Tool Plugin Interface)
```python
class BaseTool(ABC):
    """Interface for all tools — built-in and plugins."""

    @property
    @abstractmethod
    def spec(self) -> ToolSpec:
        """Return tool specification (name, description, parameters, permissions)."""

    @abstractmethod
    async def execute(self, args: dict, context: ToolContext | None = None) -> ToolResult:
        """Execute tool with arguments. Returns result."""

    @abstractmethod
    async def validate(self, args: dict) -> list[str]:
        """Validate arguments. Returns list of validation errors (empty = valid)."""
```

### ToolRegistry
```python
class ToolRegistry(ABC):
    """Interface for tool registration and lookup."""

    @abstractmethod
    async def register(self, tool: BaseTool) -> None:
        """Register a tool."""

    @abstractmethod
    async def unregister(self, tool_id: ToolID) -> None:
        """Unregister a tool."""

    @abstractmethod
    async def get(self, tool_id: ToolID) -> BaseTool:
        """Get tool by ID."""

    @abstractmethod
    async def list(self) -> list[BaseTool]:
        """List all registered tools."""

    @abstractmethod
    async def list_by_permission(self, permission_level: PermissionLevel) -> list[BaseTool]:
        """List tools accessible at a given permission level."""
```

### KnowledgeStore
```python
class KnowledgeStore(ABC):
    """Interface for knowledge base storage."""

    @abstractmethod
    async def add(self, item: KnowledgeItem) -> KnowledgeItem:
        """Add an item to the knowledge base."""

    @abstractmethod
    async def add_batch(self, items: list[KnowledgeItem]) -> list[KnowledgeItem]:
        """Add multiple items efficiently."""

    @abstractmethod
    async def search(self, query: KnowledgeQuery) -> list[KnowledgeItem]:
        """Search knowledge base with semantic + keyword hybrid."""

    @abstractmethod
    async def delete(self, knowledge_id: str) -> None:
        """Delete an item."""

    @abstractmethod
    async def get_stats(self) -> KnowledgeStats:
        """Get knowledge base statistics."""
```

### ModelProvider (Provider Plugin Interface)
```python
class ModelProvider(ABC):
    """Interface for LLM provider plugins."""

    @property
    @abstractmethod
    def spec(self) -> ModelSpec:
        """Return provider specification (models, capabilities, cost)."""

    @abstractmethod
    async def chat(self, messages: list[Message], **kwargs) -> Completion:
        """Send chat messages. Returns completion."""

    @abstractmethod
    async def chat_stream(self, messages: list[Message], **kwargs) -> AsyncIterator[StreamingChunk]:
        """Streaming chat completion."""

    @abstractmethod
    async def check_health(self) -> ProviderStatus:
        """Check if provider is available."""

    @abstractmethod
    async def count_tokens(self, messages: list[Message]) -> int:
        """Count tokens for given messages."""
```

### ModelGateway
```python
class ModelGateway(ABC):
    """Interface for model routing and provider management."""

    @abstractmethod
    async def chat(self, messages: list[Message], model: str | None = None, **kwargs) -> Completion:
        """Route chat to best available provider. Handles fallback."""

    @abstractmethod
    async def chat_stream(self, messages: list[Message], model: str | None = None, **kwargs) -> AsyncIterator[StreamingChunk]:
        """Streaming chat with automatic fallback."""

    @abstractmethod
    async def register_provider(self, provider: ModelProvider) -> None:
        """Register a new provider."""

    @abstractmethod
    async def list_models(self) -> list[ModelSpec]:
        """List all available models with capabilities."""

    @abstractmethod
    async def get_health(self) -> dict[str, ProviderStatus]:
        """Get health status of all providers."""

    @abstractmethod
    async def select_model(self, task_requirements: ModelRequirements) -> str:
        """Select best model based on task requirements."""
```

### CodebaseIndexer
```python
class CodebaseIndexer(ABC):
    """Interface for codebase indexing and search."""

    @abstractmethod
    async def index_file(self, path: str) -> CodeIndex | None:
        """Index a single file. Returns index or None if unsupported."""

    @abstractmethod
    async def index_project(self, path: str) -> CodeIndex:
        """Index an entire project directory. Returns project index."""

    @abstractmethod
    async def search(self, query: str, index_id: str | None = None) -> list[CodeIndex]:
        """Search for symbols matching query."""

    @abstractmethod
    async def get_symbol(self, symbol_name: str, file_path: str) -> CodeIndex | None:
        """Get detailed info about a symbol."""

    @abstractmethod
    async def get_dependencies(self, file_path: str) -> list[str]:
        """Get dependencies of a file."""

    @abstractmethod
    async def get_impact(self, file_path: str) -> list[str]:
        """Get files affected by changes to given file."""

    @abstractmethod
    async def get_stats(self) -> dict:
        """Get indexing statistics."""
```

---

## 4. Plugin Interfaces

### Plugin
```python
class Plugin(ABC):
    """Base interface for all plugins."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique plugin identifier."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version (semver)."""

    @property
    @abstractmethod
    def dependencies(self) -> list[str]:
        """Plugin dependency IDs."""

    @abstractmethod
    async def initialize(self, container: AIDAContainer) -> None:
        """Initialize plugin. Register components with container."""

    @abstractmethod
    async def shutdown(self) -> None:
        """Clean shutdown. Release resources."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if plugin is healthy."""
```

### AgentPlugin
```python
class AgentPlugin(Plugin, BaseAgent):
    """Interface for agent plugins. Inherits both Plugin lifecycle and BaseAgent contract."""

    @property
    @abstractmethod
    def permissions(self) -> list[str]:
        """Required permissions (e.g., ['files:read', 'network:http'])."""

    @abstractmethod
    async def on_task_delegated(self, from_agent: str, context: AgentContext) -> AgentResult:
        """Handle task delegated from another agent."""
```

### ToolPlugin
```python
class ToolPlugin(Plugin, BaseTool):
    """Interface for tool plugins. Inherits both Plugin lifecycle and BaseTool contract."""

    @property
    @abstractmethod
    def permissions(self) -> list[str]:
        """Required runtime permissions."""
```

### ModelPlugin
```python
class ModelPlugin(Plugin, ModelProvider):
    """Interface for model provider plugins. Inherits both Plugin lifecycle and ModelProvider."""

    @property
    @abstractmethod
    def models(self) -> list[str]:
        """List of model names this plugin provides."""
```

---

## 5. Cross-Cutting Interfaces

### Logger
```python
class Logger(ABC):
    """Abstract logging interface."""

    @abstractmethod
    def debug(self, msg: str, **context) -> None: ...
    @abstractmethod
    def info(self, msg: str, **context) -> None: ...
    @abstractmethod
    def warning(self, msg: str, **context) -> None: ...
    @abstractmethod
    def error(self, msg: str, **context) -> None: ...
    @abstractmethod
    def critical(self, msg: str, **context) -> None: ...
    @abstractmethod
    def set_context(self, **kwargs) -> None: ...
    @abstractmethod
    def clear_context(self) -> None: ...
```

### MetricsCollector
```python
class MetricsCollector(ABC):
    """Abstract metrics collection interface."""

    @abstractmethod
    def increment(self, metric: str, tags: dict | None = None, value: int = 1) -> None: ...
    @abstractmethod
    def gauge(self, metric: str, value: float, tags: dict | None = None) -> None: ...
    @abstractmethod
    def timing(self, metric: str, duration_ms: float, tags: dict | None = None) -> None: ...
    @abstractmethod
    def histogram(self, metric: str, value: float, tags: dict | None = None) -> None: ...
```

### ConfigStore
```python
class ConfigStore(ABC):
    """Abstract configuration interface."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any: ...
    @abstractmethod
    def get_int(self, key: str, default: int = 0) -> int: ...
    @abstractmethod
    def get_float(self, key: str, default: float = 0.0) -> float: ...
    @abstractmethod
    def get_bool(self, key: str, default: bool = False) -> bool: ...
    @abstractmethod
    def get_list(self, key: str, default: list | None = None) -> list: ...
    @abstractmethod
    def set(self, key: str, value: Any) -> None: ...
    @abstractmethod
    def reload(self) -> None: ...
```

### AuthProvider
```python
class AuthProvider(ABC):
    """Abstract authentication interface."""

    @abstractmethod
    async def authenticate(self, credentials: AuthCredentials) -> AuthResult:
        """Authenticate user. Returns result with identity or error."""

    @abstractmethod
    async def authorize(self, identity: Identity, resource: str, action: str) -> bool:
        """Check if identity is authorized for action on resource."""

    @abstractmethod
    async def create_api_key(self, identity: Identity, permissions: list[str]) -> str:
        """Create a new API key for identity with given permissions."""

    @abstractmethod
    async def revoke_api_key(self, key_id: str) -> None:
        """Revoke an API key."""

    @abstractmethod
    async def validate_api_key(self, key: str) -> Identity | None:
        """Validate an API key. Returns identity or None."""
```

---

## 6. Interface Usage Guide

### Adding a New Agent (Example)
```python
# 1. Create agent class that implements BaseAgent
class MyNewAgent(BaseAgent):
    @property
    def spec(self) -> AgentSpec:
        return AgentSpec(
            name="my_agent",
            description="Does something new",
            capabilities=[AgentCapability.RESEARCH],
        )

    async def execute(self, context: AgentContext) -> AgentResult:
        # Agent logic here
        return AgentResult(success=True, output="Done!")

    async def can_handle(self, task_type: str, context: AgentContext) -> float:
        return 0.9 if task_type == "my_specialty" else 0.1

# 2. Register with container
container.register_agent(MyNewAgent())
```

### Adding a New Model Provider (Example)
```python
# 1. Create provider that implements ModelProvider
class MyProvider(ModelProvider):
    @property
    def spec(self) -> ModelSpec:
        return ModelSpec(name="my-model", provider="my_provider")

    async def chat(self, messages, **kwargs):
        # API call here
        return Completion(content="...", model="my-model", provider="my_provider")

    async def chat_stream(self, messages, **kwargs):
        yield StreamingChunk(content="...", done=False)

# 2. Register with gateway
container.get(ModelGateway).register_provider(MyProvider())
```

### Adding a New Tool (Example)
```python
# 1. Create tool that implements BaseTool
class MyTool(BaseTool):
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="my_tool",
            description="Does something",
            parameters={"input": {"type": "string"}},
        )

    async def execute(self, args, context=None):
        return ToolResult(success=True, output=f"Processed: {args['input']}")

# 2. Register
container.register_tool(MyTool())
```
