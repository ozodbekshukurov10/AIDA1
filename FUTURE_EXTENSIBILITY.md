# AIDA — Future Extensibility Design

## 1. Extensibility Principles

Every component in AIDA is designed to be **replaced, extended, or augmented** without modifying core code. The system uses three mechanisms for extensibility:

1. **Interface-Based Plugins** — new implementations via defined contracts
2. **Event-Driven Hooks** — custom behavior triggered by domain events
3. **Configuration Overrides** — behavior changes without code changes

```
New Feature
    │
    ├── Is it a new TYPE of component?  →  Add new interface, implement in plugin
    ├── Is it a new IMPLEMENTATION?     →  Implement existing interface, register
    ├── Is it behavior on an EVENT?     →  Subscribe to event, add handler
    └── Is it a behavior CHANGE?        →  Configuration override
```

## 2. Adding New Components

### 2.1 Adding a New Agent (Zero Core Changes)

```python
# 1. Create a class that implements BaseAgent
from aida.kernel.agents.interfaces import BaseAgent
from aida.domain.entities import AgentSpec, AgentContext, AgentResult, AgentCapability

class DocumentationReviewerAgent(BaseAgent):
    @property
    def spec(self) -> AgentSpec:
        return AgentSpec(
            name="doc_reviewer",
            description="Reviews documentation for completeness and accuracy",
            capabilities=[AgentCapability.DOCUMENTATION, AgentCapability.CODE_REVIEW],
            tools=["files:read", "files:write", "search:code"],
        )

    async def execute(self, context: AgentContext) -> AgentResult:
        # Implementation here
        return AgentResult(success=True, output="Documentation reviewed")

    async def can_handle(self, task_type: str, context: AgentContext) -> float:
        return 0.9 if "documentation" in task_type.lower() else 0.1

# 2. Register with the container
container = get_container()
container.register_agent(DocumentationReviewerAgent())
```

**What did NOT change:** AgentEngine, Orchestrator, Router, Memory, Tools, API, CLI, Database, Configuration.

### 2.2 Adding a New Tool (Zero Core Changes)

```python
from aida.kernel.tools.interfaces import BaseTool
from aida.domain.entities import ToolSpec, ToolResult

class JiraTicketTool(BaseTool):
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="jira_create_ticket",
            description="Creates a Jira ticket from description",
            parameters={
                "project": {"type": "string", "required": True},
                "summary": {"type": "string", "required": True},
                "description": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
            },
        )

    async def execute(self, args: dict, context=None) -> ToolResult:
        # Jira API call here
        return ToolResult(success=True, output={"ticket_id": "PROJ-123", "url": "https://jira.example.com/PROJ-123"})

# Register
container.register_tool(JiraTicketTool())
```

**What did NOT change:** ToolEngine, Executor, Sandbox, Permission system, API, CLI, Database.

### 2.3 Adding a New Model Provider (Zero Core Changes)

```python
from aida.kernel.models.interfaces import ModelProvider
from aida.domain.entities import ModelSpec, Message, Completion, StreamingChunk, ProviderStatus

class GroqProvider(ModelProvider):
    @property
    def spec(self) -> ModelSpec:
        return ModelSpec(
            name="groq",
            models=["llama3-70b", "mixtral-8x7b"],
            capabilities={"streaming": True, "tools": True, "max_tokens": 32768},
        )

    async def chat(self, messages: list[Message], **kwargs) -> Completion:
        # Groq API call
        return Completion(content="...", model="llama3-70b", provider="groq")

    async def chat_stream(self, messages, **kwargs):
        yield StreamingChunk(content="...", done=False)
        # ...
        yield StreamingChunk(content="", done=True)

    async def check_health(self) -> ProviderStatus:
        return ProviderStatus.ONLINE

# Register with gateway
gateway = container.get(ModelGateway)
gateway.register_provider(GroqProvider())
```

**What did NOT change:** Gateway routing, fallback logic, health monitoring, caching, API, CLI, Chat use cases.

### 2.4 Adding a New Memory Tier (Zero Core Changes)

```python
from aida.kernel.memory.interfaces import MemoryStore
from aida.domain.entities import MemoryItem, MemoryQuery, MemoryType

class EpisodicMemory(MemoryStore):
    """Remembers past problem-solving patterns."""

    @property
    def memory_type(self) -> MemoryType:
        return MemoryType.EPISODIC

    async def store(self, item: MemoryItem) -> MemoryItem:
        # Store episodic memory
        return item

    async def search(self, query: MemoryQuery) -> list[MemoryItem]:
        # Retrieve similar past episodes
        return []

# Register with memory manager
memory_manager = container.get(MemoryManager)
memory_manager.register_tier(EpisodicMemory())
```

**What did NOT change:** MemoryManager, Retriever, Ranking, Compression, Other tiers, API, Use cases.

### 2.5 Adding a New API Endpoint (Minimal Core Changes)

```python
# In presentation/api/v2/endpoints/
from aida.application.dtos import ChatRequest, ChatResponse
from aida.application.use_cases.chat import ChatUseCase
from aida.presentation.api.v2.responses import APIResponse

async def chat_endpoint(request):
    dto = ChatRequest.from_request(request)
    result = await container.resolve(ChatUseCase).execute(dto)
    return APIResponse.ok(result)
```

**What did NOT change:** Domain, Application (unless new use case needed), Kernel, Infrastructure.

---

## 3. Event-Driven Extensibility

### 3.1 Available Hook Points

Every significant action in AIDA publishes a domain event. Custom behavior can be added by subscribing to events:

```python
# Subscribe to events from anywhere
from aida.domain.events import EventBus, DomainEventType

bus = container.get(EventBus)

# Before execution hooks
bus.subscribe(DomainEventType.TASK_CREATED, notify_slack)
bus.subscribe(DomainEventType.AGENT_STARTED, log_to_custom_db)

# After execution hooks
bus.subscribe(DomainEventType.TASK_COMPLETED, send_webhook)
bus.subscribe(DomainEventType.TOOL_EXECUTED, audit_tool_usage)

# Error hooks
bus.subscribe(DomainEventType.AGENT_ERROR, pagerduty_alert)
bus.subscribe(DomainEventType.PROVIDER_FAILED, fallback_to_backup)

# System hooks
bus.subscribe(DomainEventType.SYSTEM_STARTUP, warm_caches)
bus.subscribe(DomainEventType.SYSTEM_SHUTDOWN, save_state)
```

### 3.2 Custom Event Definitions

```python
# Define custom events without modifying core
from aida.domain.events import DomainEvent, DomainEventType

# New event type
CUSTOM_EVENT = DomainEventType("CUSTOM_DEPLOYMENT_STARTED")

# Publish custom event
bus.publish(DomainEvent(
    type=CUSTOM_EVENT,
    payload={"project": "my-project", "env": "production"},
    metadata={"correlation_id": "abc-123"},
))

# Subscribe
bus.subscribe(CUSTOM_EVENT, handle_deployment)
```

---

## 4. Configuration-Driven Extensibility

### 4.1 Feature Flags

```python
# Enable/disable features without code changes
config:
  features:
    streaming: true
    autonomous_mode: false
    multi_tenant: false
    voice_interface: false
    vision_analysis: false
    collaborative_agents: true
```

### 4.2 Provider Configuration

```yaml
# Add new providers without code changes (if they use standard protocol)
providers:
  - name: groq
    type: openai_compatible
    base_url: https://api.groq.com/openai/v1
    api_key: ${GROQ_API_KEY}
    models:
      - llama3-70b-8192
      - mixtral-8x7b-32768
    capabilities:
      streaming: true
      tools: true
```

### 4.3 Agent Configuration

```yaml
# Configure agent behavior without code changes
agents:
  code_agent:
    enabled: true
    model: gpt-4
    temperature: 0.2
    max_tokens: 4096
    tools:
      - files:read
      - files:write
      - search:code
      - git:diff
  research_agent:
    enabled: true
    model: claude-3-opus
    temperature: 0.7
    tools:
      - web:search
      - web:fetch
```

---

## 5. Future Component Integration Points

### 5.1 Voice AI

```python
# 1. New interface
class VoiceProvider(ABC):
    @abstractmethod
    async def speech_to_text(self, audio: bytes) -> str: ...
    @abstractmethod
    async def text_to_speech(self, text: str) -> bytes: ...

# 2. Plugin implementation
class WhisperProvider(VoiceProvider):
    async def speech_to_text(self, audio: bytes) -> str:
        # Whisper API call
        return "transcribed text"

# 3. Existing ChatUseCase gets voice input from new VoiceEndpoint
# Core change: New endpoint, same use case
```

### 5.2 Vision AI

```python
# 1. New interface
class VisionProvider(ABC):
    @abstractmethod
    async def analyze_image(self, image: bytes, prompt: str) -> str: ...
    @abstractmethod
    async def analyze_video(self, video: bytes, prompt: str) -> str: ...

# 2. Integration with existing ModelGateway
# Most providers (GPT-4V, Gemini Pro Vision, Claude 3) are already supported
# VisionProvider wraps existing provider with image support
```

### 5.3 RAG Engine

```python
# 1. New module in kernel/rag/
class RAGEngine:
    """Retrieval-Augmented Generation engine."""

    def __init__(self, embedder, vector_store, model_gateway):
        self._embedder = embedder
        self._vector_store = vector_store
        self._model_gateway = model_gateway

    async def query(self, question: str, context_docs: list[str] | None = None) -> RAGResult:
        # 1. Embed question
        # 2. Retrieve relevant documents
        # 3. Build prompt with context
        # 4. Generate answer with citations
        return RAGResult(answer="...", sources=[...], confidence=0.95)

# Integration: RAGEngine wraps existing Memory, Knowledge, Codebase engines
# No changes needed to existing components
```

### 5.4 Knowledge Graph

```python
# 1. New module in kernel/knowledge/graph.py
class KnowledgeGraph:
    """Knowledge graph for entity relationships."""

    async def build(self, source: str) -> None:
        """Build graph from text or codebase."""

    async def query(self, entity: str, relation: str | None = None) -> list[GraphResult]:
        """Query relationships."""

    async def infer(self, source: str, target: str) -> list[str]:
        """Infer relationships between entities."""

# Integration: Builds on existing KnowledgeEngine
# Uses existing extractor + new graph storage
```

### 5.5 Cloud Platform

```python
# 1. New deployment targets via plugins
class CloudProvider(ABC):
    @abstractmethod
    async def deploy(self, config: DeploymentConfig) -> DeploymentResult: ...
    @abstractmethod
    async def scale(self, service_id: str, replicas: int) -> None: ...
    @abstractmethod
    async def monitor(self, service_id: str) -> ServiceMetrics: ...

# 2. Built-in implementations
class AWSProvider(CloudProvider): ...
class GCPProvider(CloudProvider): ...
class AzureProvider(CloudProvider): ...

# 3. Existing deployment tools use these providers
```

### 5.6 Distributed Workers

```python
# 1. New execution backend (swap without API change)
class TaskQueue(ABC):
    @abstractmethod
    async def enqueue(self, task: Task) -> str: ...
    @abstractmethod
    async def dequeue(self, worker_id: str) -> Task | None: ...
    @abstractmethod
    async def ack(self, task_id: str) -> None: ...

# 2. Implementations
class RedisTaskQueue(TaskQueue): ...
class RabbitMQTaskQueue(TaskQueue): ...
class CeleryTaskQueue(TaskQueue): ...

# 3. AgentEngine uses TaskQueue interface
# Can switch from in-process → Redis → Celery without code change
```

### 5.7 Plugin Marketplace

```python
# 1. Remote plugin registry
class PluginMarketplace:
    async def search(self, query: str) -> list[PluginListing]: ...
    async def install(self, plugin_id: str) -> PluginRegistration: ...
    async def publish(self, plugin: PluginPackage) -> PluginListing: ...
    async def update(self, plugin_id: str) -> PluginRegistration: ...

# 2. The existing PluginManager handles installation
# Marketplace just provides discovery + distribution
```

### 5.8 AIDA SDK

```python
# 1. Python SDK (client library)
class AIDAClient:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8001"):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def chat(self, prompt: str, session_id: str | None = None) -> ChatResponse:
        response = await self._client.post("/api/v2/chat/", json={
            "prompt": prompt,
            "session_id": session_id,
        })
        return ChatResponse(**response.json())

    async def execute_agent(self, agent: str, task: str) -> AgentResponse:
        response = await self._client.post("/api/v2/agents/execute/", json={
            "agent": agent,
            "task": task,
        })
        return AgentResponse(**response.json())

    async def execute_tool(self, tool: str, args: dict) -> ToolResponse:
        response = await self._client.post("/api/v2/tools/execute/", json={
            "tool": tool,
            "args": args,
        })
        return ToolResponse(**response.json())

# 2. SDK uses existing v2 API — no backend changes needed
```

---

## 6. Extensibility Verification Checklist

For each new feature, verify:

| Check | Criteria |
|---|---|
| Interface exists | Feature can be implemented by implementing an existing interface |
| No core changes | Feature does not require changes to aida/domain/ or aida/kernel/interfaces/ |
| Plugin registration | Feature is registered with the container, not hardcoded |
| Event hooks | Feature can observe or extend behavior via events |
| Configuration | Feature behavior can be changed via configuration |
| Test isolation | Feature can be tested independently with mocks |
| Deployment | Feature can be enabled/disabled without restart |

## 7. Extensibility Scorecard

| Extension Point | Current | Target | Mechanism |
|---|---|---|---|
| New Agent | ✅ Interface exists | ✅ | BaseAgent plugin |
| New Tool | ✅ Interface exists | ✅ | BaseTool plugin |
| New Model Provider | ✅ Interface exists | ✅ | ModelProvider plugin |
| New Memory Tier | ⚠️ Partial | ✅ | MemoryStore plugin |
| New Knowledge Source | ⚠️ Partial | ✅ | KnowledgeStore plugin |
| New Database | ❌ Hardcoded SQLite | ✅ | Repository interface |
| New API Endpoint | ✅ Possible | ✅ | Use case + endpoint |
| New UI Component | ✅ Possible | ✅ | React component |
| New Plugin Type | ❌ No plugin system | ✅ | Plugin interface |
| New Deployment | ❌ Docker only | ✅ | CloudProvider interface |
| New Event Handler | ⚠️ EventBus defined but unused | ✅ | Event subscription |
| New Auth Provider | ⚠️ API key only | ✅ | AuthProvider interface |
| New LLM Protocol | ⚠️ Ad-hoc | ✅ | ModelProvider plugin |
| New File Storage | ⚠️ Local only | ✅ | StorageProvider interface |
| New Cache Backend | ❌ In-memory only | ✅ | CacheProvider interface |

## 8. Migration Cost Matrix

| Extension | Current Effort | Target Effort | Reduction |
|---|---|---|---|
| Add Ollama provider | 1 day (read gateway, follow pattern) | 30 min (plugin) | 94% |
| Add code agent | 2 days (understand orchestrator, agents) | 1 hour (BaseAgent plugin) | 94% |
| Add web search tool | 4 hours (understand tool system) | 20 min (BaseTool plugin) | 92% |
| Add PostgreSQL support | 1 week (find all SQLite calls) | 2 days (new Repository adapter) | 60% |
| Add new API endpoint | 1 hour (Django view pattern) | 30 min (use case + endpoint) | 50% |
| Add custom behavior on agent error | 3 days (find hook point) | 10 min (subscribe to event) | 99% |
| Add new embedding model | 2 hours (find hardcoded calls) | 15 min (ConfigStore override) | 88% |

## 9. Future-Proofing Principles

1. **Interface over Implementation** — depend on abstractions, never concretions
2. **Plugin over Fork** — extend via plugin, never fork the core
3. **Event over Callback** — observe via events, never modify core to add hooks
4. **Config over Code** — configure behavior, never modify code for environment changes
5. **Adapter over Direct** — wrap external dependencies in adapters, never use directly
6. **Version over Latest** — pin interfaces by semver, never depend on latest
7. **Test over Trust** — test plugins in isolation, never trust third-party code
