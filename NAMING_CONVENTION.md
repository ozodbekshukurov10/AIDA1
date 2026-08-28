# AIDA — Naming Convention

## 1. Directory Names

| Rule | Example | Rationale |
|---|---|---|
| **lowercase only** | `agents/`, `tools/`, `memory/` | Python convention, case-sensitive filesystems |
| **singular nouns** | `entity/`, `event/`, `exception/` | Each directory is a category |
| **no underscores** | `dto/` not `dtos/`, `cli/` not `command_line/` | Short, no separators |
| **no abbreviations** | `application/` not `app/`, `configuration/` not `config/` | Except widely known: `api/`, `cli/`, `sdk/`, `dto/` |
| **no numbers** | `v2/` (allowed for API versions), NOT `module2/` | Versioning only for API |

### Directory Naming Exceptions

| Allowed Abbreviation | Full Form | Reason |
|---|---|---|
| `api/` | Application Programming Interface | Universal standard |
| `cli/` | Command Line Interface | Universal standard |
| `sdk/` | Software Development Kit | Universal standard |
| `dto/` | Data Transfer Object | Industry standard |
| `rag/` | Retrieval-Augmented Generation | AI industry standard |
| `v1/`, `v2/`, `v3/` | Version 1, 2, 3 | API versioning only |

### Parent → Child Directory Pattern

```
aida/
  domain/
    entities/         # Entity definitions
    events/           # Event definitions
    exceptions/       # Exception definitions
    interfaces/       # Interface definitions
    value_objects/    # Value object definitions

  kernel/
    agents/
      builtin/        # Built-in implementations
    memory/
      tiers/          # Memory tier implementations
    tools/
      builtin/        # Built-in tool implementations
    models/
      providers/      # Provider implementations
    codebase/
      parsers/        # Language parser implementations

  application/
    use_cases/
      chat/           # One directory per use case group
      agents/
      tools/
      memory/
      models/
      knowledge/
      codebase/
      workflow/
      projects/
      improvement/
      search/

  infrastructure/
    persistence/
      repositories/   # Repository implementations
      models/         # ORM models
      migrations/     # Schema migrations

  presentation/
    api/
      v2/
        endpoints/    # One file per endpoint group
```

## 2. File Names

| Element | Convention | Example |
|---|---|---|
| Python modules | `snake_case.py` | `agent_executor.py`, `chat_service.py` |
| TypeScript modules | `PascalCase.tsx` (components), `camelCase.ts` (services) | `ChatBubble.tsx`, `apiClient.ts` |
| Configuration | `snake_case.yaml` | `development.yaml`, `production.yaml` |
| Documentation | `UPPER_CASE.md` | `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md` |
| Test files | `test_<module>.py` | `test_chat_use_case.py` |
| Migration files | `<version>_<description>.py` | `0001_add_access_key.py` |
| Docker files | `Dockerfile` (exact), `docker-compose.yml` | Standard convention |
| Environment | `.env` (active), `.env.example` (template) | Standard convention |

### Python File Naming Patterns

| Pattern | Example | Use Case |
|---|---|---|
| `<noun>.py` | `agent.py`, `tool.py`, `session.py` | Entity definition |
| `<noun>_service.py` | `chat_service.py`, `memory_service.py` | Service implementation |
| `<noun>_use_case.py` | `execute_agent.py`, `search_memory.py` | Single use case |
| `<noun>_repository.py` | `session_repository.py` | Repository interface |
| `<noun>_repo.py` | `session_repo.py`, `memory_repo.py` | Repository implementation |
| `<noun>_provider.py` | `ollama_provider.py`, `gemini_provider.py` | Provider implementation |
| `<noun>_parser.py` | `python_parser.py`, `js_parser.py` | Parser implementation |
| `base_<noun>.py` | `base_agent.py`, `base_tool.py` | Abstract base class |

### TypeScript File Naming Patterns

| Pattern | Example | Use Case |
|---|---|---|
| `<Component>.tsx` | `ChatBubble.tsx`, `ModelSelector.tsx` | React components |
| `<service>.ts` | `chatService.ts`, `apiClient.ts` | Service layer |
| `<hook>.ts` | `useApi.ts`, `useSession.ts` | Custom hooks |
| `<store>.ts` | `sessionStore.ts`, `chatStore.ts` | State stores |
| `<type>.ts` | `chatTypes.ts`, `apiTypes.ts` | Type definitions |

## 3. Class Names

| Element | Convention | Example |
|---|---|---|
| Entities | `PascalCase` — singular noun | `AgentSpec`, `ToolResult`, `MemoryItem` |
| Use Cases | `PascalCase` — verb phrase | `ExecuteAgent`, `SearchMemory`, `AnalyzeCode` |
| Services | `PascalCase` — noun + Service | `ChatService`, `MemoryService`, `GatewayService` |
| Repositories | `PascalCase` — noun + Repository | `SessionRepository`, `MemoryRepository` |
| Adapters | `PascalCase` — noun + Adapter | `SQLiteSessionAdapter`, `RedisCacheAdapter` |
| Providers | `PascalCase` — brand + Provider | `OllamaProvider`, `GeminiProvider` |
| Agents | `PascalCase` — domain + Agent | `CodeAgent`, `SecurityAgent`, `ResearchAgent` |
| Tools | `PascalCase` — domain + Tool | `FileTool`, `GitTool`, `DockerTool` |
| DTOs | `PascalCase` — noun + Request/Response | `ChatRequest`, `ChatResponse` |
| Configs | `PascalCase` — noun + Config | `ModelConfig`, `MemoryConfig` |
| Exceptions | `PascalCase` — noun + Error | `AgentNotFoundError`, `ToolPermissionError` |
| Events | `PascalCase` — past tense verb | `AgentStarted`, `TaskCompleted`, `MemoryStored` |
| Managers | `PascalCase` — noun + Manager | `PluginManager`, `MemoryManager` |
| Factories | `PascalCase` — noun + Factory | `AgentFactory`, `ToolFactory` |
| Builders | `PascalCase` — noun + Builder | `WorkflowBuilder`, `ContextBuilder` |
| Validators | `PascalCase` — noun + Validator | `InputValidator`, `PluginValidator` |
| Utilities | `PascalCase` — noun + Utils | `FormatUtils`, `FileUtils` |

### Class Naming Rules

```python
# Good examples
class AgentSpec: ...          # Entity — singular noun
class ExecuteTask: ...        # Use case — verb phrase
class OllamaProvider: ...     # Provider — brand + type
class SessionNotFoundError: ... # Exception — descriptive error
class ChatRequest: ...        # DTO — noun + Request/Response

# Bad examples — NEVER use these patterns
class Agent: ...              # Too generic — AgentSpec or BaseAgent
class DoTask: ...             # Poor verb — ExecuteTask or RunTask
class AIDAProvider: ...       # Redundant — just OllamaProvider
class Error: ...              # Too generic — SessionNotFoundError
class Req: ...                # Abbreviation — ChatRequest
```

## 4. Function & Method Names

| Element | Convention | Example |
|---|---|---|
| Functions | `snake_case` — verb phrase | `execute_agent()`, `search_memory()`, `get_session()` |
| Methods | `snake_case` — verb phrase | `async def execute()`, `async def get_by_id()` |
| Private methods | `snake_case` — `_` prefix | `_validate_input()`, `_build_context()` |
| Properties | `snake_case` — noun | `@property def spec(self)` |
| Class methods | `snake_case` — `cls` first param | `@classmethod def from_config(cls, config)` |
| Static methods | `snake_case` | `@staticmethod def create_id()` |
| Async methods | `snake_case` — `async def` | `async def execute(self)` |
| Event handlers | `handle_<event>()` | `handle_agent_completed()`, `handle_task_failed()` |

### CRUD Method Naming

| Operation | Repository Method | Service Method | Endpoint |
|---|---|---|---|
| Create | `create()` | `create_<entity>()` | `POST /<entities>/` |
| Read | `get()`, `list()` | `get_<entity>()`, `list_<entities>()` | `GET /<entities>/`, `GET /<entities>/:id/` |
| Update | `update()` | `update_<entity>()` | `PUT /<entities>/:id/` |
| Delete | `delete()` | `delete_<entity>()` | `DELETE /<entities>/:id/` |

### Function Naming Rules

```python
# Good
async def execute_task(request: AgentExecuteRequest) -> AgentExecuteResponse: ...
async def find_best_agent(task_type: str, context: AgentContext) -> BaseAgent: ...
async def _validate_permissions(user: Identity, resource: str) -> bool: ...
def _build_context(messages: list[Message], token_budget: int) -> str: ...

# Bad — NEVER
def do_stuff(a, b): ...           # Vague
def process(): ...                # Too generic
def handle(x): ...                # Not descriptive
def _(): ...                      # No name
def check_it(data): ...           # Poor naming
```

## 5. API Endpoint Names

### URL Pattern

```
METHOD /api/v<version>/<resource>/[<id>]/[<action>]/
```

### Examples

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v2/status/` | GET | System status |
| `/api/v2/chat/` | POST | Send chat message |
| `/api/v2/chat/stream/` | POST | Streaming chat |
| `/api/v2/agents/` | GET | List agents |
| `/api/v2/agents/execute/` | POST | Execute agent task |
| `/api/v2/agents/:id/status/` | GET | Agent status |
| `/api/v2/tools/` | GET | List tools |
| `/api/v2/tools/execute/` | POST | Execute tool |
| `/api/v2/models/` | GET | List models |
| `/api/v2/providers/` | GET | List providers |
| `/api/v2/providers/:id/health/` | GET | Provider health |
| `/api/v2/memory/` | GET/POST | Memory CRUD |
| `/api/v2/memory/search/` | POST | Semantic search |
| `/api/v2/knowledge/` | GET/POST | Knowledge CRUD |
| `/api/v2/sessions/` | GET/POST | Session management |
| `/api/v2/projects/` | GET/POST | Project management |
| `/api/v2/keys/` | GET/POST | Access key management |
| `/api/v2/plugins/` | GET/POST | Plugin management |
| `/api/v2/monitoring/metrics/` | GET | Metrics |
| `/api/v2/monitoring/health/` | GET | Health check |

### URL Naming Rules

- **Lowercase** — always
- **Plural nouns** for resources — `/agents/`, `/tools/`, `/models/`
- **Hyphens** for multi-word — not underscores (e.g., `/api-keys/` not `/api_keys/`)
- **No file extensions** — never `.json`, `.xml` in URL
- **Actions as last segment** — `/agents/execute/`, `/memory/search/`
- **IDs as path parameters** — `/agents/:id/status/`

## 6. Environment Variable Names

### Pattern

```
AIDA_<CATEGORY>_<NAME>
```

### Examples

| Variable | Purpose |
|---|---|
| `AIDA_PROVIDER` | Default LLM provider |
| `AIDA_MODEL` | Default model name |
| `AIDA_OLLAMA_URL` | Ollama endpoint |
| `AIDA_GEMINI_KEY` | Gemini API key |
| `AIDA_OPENAI_KEY` | OpenAI API key |
| `AIDA_ANTHROPIC_KEY` | Anthropic API key |
| `AIDA_DEEPSEEK_KEY` | DeepSeek API key |
| `AIDA_DB_ENGINE` | Database engine (sqlite/postgres) |
| `AIDA_DB_NAME` | Database name |
| `AIDA_DB_HOST` | Database host |
| `AIDA_DB_PORT` | Database port |
| `AIDA_DB_USER` | Database user |
| `AIDA_DB_PASSWORD` | Database password |
| `AIDA_REDIS_URL` | Redis connection string |
| `AIDA_LOG_LEVEL` | Logging level |
| `AIDA_LOG_FORMAT` | Log format (json/text) |
| `AIDA_SECRET_KEY` | Django secret key |
| `AIDA_DEBUG` | Debug mode (true/false) |
| `AIDA_ALLOWED_HOSTS` | Django allowed hosts |
| `AIDA_CORS_ORIGINS` | CORS allowed origins |
| `AIDA_RATE_LIMIT` | API rate limit (req/min) |
| `AIDA_MAX_CONCURRENT` | Max concurrent LLM calls |
| `AIDA_PLUGINS_DIR` | Plugin directory path |
| `AIDA_DATA_DIR` | Data directory path |

### Environment Variable Rules

- **Prefix all AIDA-specific vars** with `AIDA_`
- **UPPER_SNAKE_CASE**
- Use underscores, not hyphens
- No spaces in values
- Boolean values: `true` / `false` (lowercase, not True/False)
- API keys end with `_KEY`
- Database variables grouped under `AIDA_DB_*`

## 7. Configuration File Names

| File | Environment | Purpose |
|---|---|---|
| `defaults.py` | All | Default configuration values |
| `development.yaml` | Dev | Development overrides |
| `testing.yaml` | Test | Testing overrides |
| `staging.yaml` | Staging | Staging environment |
| `production.yaml` | Prod | Production overrides |
| `docker.yaml` | Docker | Docker container overrides |
| `cloud.yaml` | Cloud | Cloud provider overrides |
| `enterprise.yaml` | Enterprise | Enterprise deployment |

## 8. Git Branch Names

| Branch | Pattern | Example |
|---|---|---|
| Main | `main` | `main` |
| Develop | `develop` | `develop` |
| Feature | `feature/<description>` | `feature/add-groq-provider` |
| Bugfix | `fix/<issue-id>-<description>` | `fix/123-session-timeout` |
| Release | `release/<version>` | `release/v2.1.0` |
| Hotfix | `hotfix/<description>` | `hotfix/critical-security-fix` |
| Docs | `docs/<description>` | `docs/api-reference-update` |

## 9. Git Commit Messages

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | When to Use |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code change that neither fixes nor adds |
| `test` | Adding or fixing tests |
| `docs` | Documentation only |
| `chore` | Build, config, dependencies |
| `perf` | Performance improvement |
| `security` | Security fix |
| `style` | Formatting, linting (no code change) |

### Scopes

| Scope | Module |
|---|---|
| `core` | Domain layer, kernel |
| `agents` | Agent engine |
| `tools` | Tool engine |
| `memory` | Memory engine |
| `models` | Model gateway |
| `api` | API endpoints |
| `ui` | Frontend |
| `cli` | Command line |
| `plugins` | Plugin system |
| `deploy` | Deployment, Docker |
| `config` | Configuration |
| `security` | Security |
| `monitoring` | Monitoring, logging |
| `tests` | Tests |

## 10. Summary: The 10 Naming Commandments

1. **Directories**: lowercase, singular, no underscores
2. **Python files**: snake_case, descriptive
3. **TypeScript files**: PascalCase for components, camelCase for services
4. **Classes**: PascalCase, noun phrase
5. **Functions**: snake_case, verb phrase
6. **API endpoints**: lowercase, plural nouns, hyphens for multi-word
7. **Environment variables**: `AIDA_CATEGORY_NAME`, UPPER_SNAKE_CASE
8. **Config files**: environment.yaml, snake_case
9. **Git branches**: type/description, kebab-case
10. **Commit messages**: type(scope): subject, imperative mood
