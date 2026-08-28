# AIDA — Engineering Principles

## 1. Core Principles (In Order of Priority)

### 1.1 Clean Architecture First
Every module respects the dependency rule: **Domain → Application → Infrastructure → Presentation**. No outer layer knows about inner layer implementations. Dependencies point inward.

**Practical rule**: If you're writing code in `aidaos/application/` and find yourself importing from `django.db`, stop. You are violating the architecture.

### 1.2 SOLID

| Principle | AIDA Application |
|---|---|
| **S**ingle Responsibility | Each class has exactly one reason to change. Use cases have one method. Entities are pure data + behavior. |
| **O**pen/Closed | Modules are open for extension (plugin registration), closed for modification (interface-based). |
| **L**iskov Substitution | All adapter implementations satisfy their interface contract exactly. Mock repos in tests are drop-in replacements for real adapters. |
| **I**nterface Segregation | Repository interfaces are narrow (ProviderRepo: 3 methods, MemoryRepo: 5 methods). No interface has more than 8 methods. |
| **D**ependency Inversion | High-level modules (use cases) do not depend on low-level modules (SQLite, HTTP). Both depend on abstractions (repository interfaces). |

### 1.3 DRY (Don't Repeat Yourself)
If you write the same logic twice, **extract it**. If you see a pattern repeated three times, **abstract it**.

**Allowed exceptions**:
- Test fixtures (duplication in tests is acceptable for readability)
- DTO boilerplate (DTOs duplicate domain fields by design — they are separate concerns)

### 1.4 KISS (Keep It Simple, Stupid)
Before adding a new abstraction, ask:
- Does this abstraction remove a real pain point, or is it speculative?
- Can I solve this with a function instead of a class?
- Is there a standard library solution?

**Default to**:
- Functions over classes (unless state is needed)
- Simple data structures over complex patterns
- Synchronous over async (unless concurrency is required)
- Composition over inheritance

### 1.5 Separation of Concerns
Every module has a clearly defined responsibility:

| Module | Responsibility | Does NOT Do |
|---|---|---|
| `domain/entities.py` | Pure data + behavior | Persistence, serialization, networking |
| `domain/events.py` | Event definitions + bus | Event processing, side effects |
| `domain/interfaces/` | Contract definitions | Implementations |
| `application/use_cases/` | Business logic orchestration | I/O, framework calls |
| `application/dtos.py` | Data transfer validation | Business logic |
| `infrastructure/` | I/O, frameworks, adapters | Business decisions |
| `presentation/` | User-facing interfaces | Business logic, I/O |

### 1.6 Dependency Injection
- No `from django.conf import settings` in application or domain code
- No `import aidaos.infrastructure.*` in use cases
- All dependencies are injected through the constructor
- The DI Container (`container.py`) is the sole wiring point

### 1.7 Testing First
- All bug fixes start with a failing test
- All new features include tests before or with implementation
- Use cases must be testable without real infrastructure (mock repos)
- Tests are part of the codebase — same review, same standards

## 2. Coding Standards

### 2.1 Python
- **Python version**: 3.10+ (use `str \| None` over `Optional[str]`)
- **Formatter**: `ruff format` (line length: 100)
- **Linter**: `ruff check` with `--fix`
- **Type checker**: `mypy --strict`
- **Sort imports**: `ruff check --select I`
- **No wildcard imports**: `from os import *` is forbidden
- **No relative imports**: Use absolute imports from package root

### 2.2 Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Packages | lowercase, no underscore | `aidaos/`, `infrastructure/` |
| Modules | lowercase, snake_case | `chat_service.py`, `agent_executor.py` |
| Classes | PascalCase | `ChatUseCase`, `AgentSpec` |
| Functions/Methods | lowercase, snake_case | `execute_chat()`, `get_container()` |
| Variables | lowercase, snake_case | `task_type`, `agent_result` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Private members | prefix with `_` | `_validate_input()`, `_cache` |
| Dunder methods | limited to `__init__`, `__str__`, `__repr__` | |
| Type variables | single uppercase | `T`, `R`, `E` |

### 2.3 File Organization

```
aidaos/
  domain/
    entities.py        # All entities for this bounded context
    events.py          # Event definitions + EventBus
    exceptions.py      # All exception types
    interfaces/
      __init__.py      # All repository ABCs
  application/
    dtos.py            # All DTOs
    use_cases/
      chat.py          # One use case per file
      agent.py
      tool.py
      ...
  infrastructure/
    persistence/
      __init__.py      # All persistence adapters
    llm/
      __init__.py      # Provider adapter + gateway wrapper
    codebase/
      indexer.py       # CodebaseIndexer
  presentation/
    api/
      __init__.py      # API response format
    cli/
      __init__.py      # CLI commands
```

### 2.4 Maximum File Sizes

| Category | Limit | Action |
|---|---|---|
| Use case file | < 200 lines | Extract helper functions |
| Domain entities file | < 300 lines | Split into sub-modules |
| Infrastructure adapter | < 400 lines | Extract private methods |
| Test file | < 500 lines | Split by domain concept |

### 2.5 Complexity Limits

| Metric | Limit | Tool |
|---|---|---|
| Cyclomatic complexity | < 10 per function | `ruff check --select C90` |
| Cognitive complexity | < 15 per function | `lizard` |
| Function lines | < 40 lines | Code review |
| Method parameters | < 5 | Consider dataclass |
| Return statements | < 3 per function | Early returns OK |
| Nested control flow | < 3 levels | Extract inner block |
| Boolean expressions | < 5 operands | Extract named variables |

## 3. Error Handling

### 3.1 Exception Hierarchy
```
AIDAError (base)
├── AgentError
│   ├── AgentNotFoundError
│   ├── AgentExecutionError
│   └── AgentTimeoutError
├── ToolError
│   ├── ToolNotFoundError
│   ├── ToolExecutionError
│   ├── ToolPermissionError
│   └── ToolTimeoutError
├── ProviderError
│   ├── ProviderNotFoundError
│   ├── ProviderConnectionError
│   ├── ProviderAuthError
│   └── ProviderRateLimitError
├── MemoryError
│   ├── MemoryStorageError
│   └── MemoryRetrievalError
├── ValidationError
├── ConfigurationError
├── SecurityError
│   ├── AuthenticationError
│   └── AuthorizationError
└── NotFoundError
```

### 3.2 Exception Rules
- Never catch `Exception` — always catch specific exception types
- Never `except: pass` — log and re-raise if truly unrecoverable
- Application layer throws domain exceptions, never infrastructure exceptions
- Wrap infrastructure exceptions in domain exceptions at the adapter boundary
- Each exception carries `code`, `status_code`, `message`, `details` for API responses

## 4. Async Patterns

### 4.1 When to Use Async
| Use Case | Pattern |
|---|---|
| LLM provider calls | `async def` in use case, `ThreadPoolExecutor` bridge |
| Database queries | Synchronous Django ORM (WSGI) |
| Agent execution | `async def` with `asyncio.gather` for parallel agents |
| Event bus dispatch | Synchronous (in-process) |
| File I/O | Synchronous (Django file handling) |
| Streaming responses | Async generator → SSE |

### 4.2 Async Bridge Pattern
```python
def run_async(coro):
    """Bridge sync WSGI to async LLM calls."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
```

## 5. Testing Standards

### 5.1 Test Structure
```
tests/
  test_domain/          # Unit tests for domain entities
  test_application/     # Use case tests with mock repos
  test_infrastructure/  # Integration tests with real adapters
  test_presentation/    # API integration tests
  conftest.py           # Shared fixtures
```

### 5.2 Test Requirements
- Every use case: one test file, all branches covered
- Every repository adapter: one test file, CRUD + edge cases
- Every public API endpoint: happy path + error path
- Every exception: at least one test that triggers it
- No test may require a real LLM provider or network

### 5.3 Mock Repository Pattern
```python
class MockProviderRepo(ProviderRepository):
    """In-memory provider repo for tests."""
    async def complete(self, messages, **kwargs):
        return Completion(
            content="Mock response",
            model="test-model",
            provider="test"
        )
```

## 6. Documentation Standards

### 6.1 What Must Be Documented
- All public APIs (endpoints, request/response schemas)
- All domain entities and value objects
- All repository interfaces
- All use case classes
- Architecture decisions (in ADR format)
- Configuration options (in README or dedicated config doc)

### 6.2 Documentation Format
- API docs: OpenAPI/Swagger (auto-generated from DRF)
- Code docs: Docstrings only where logic is non-obvious
- Architecture docs: Markdown in `docs/`
- Decision records: `docs/adr/NNN-title.md` (Architecture Decision Record)

## 7. Version Control

### 7.1 Branch Strategy
- `main` — production-ready, protected
- `develop` — integration branch
- `feature/*` — feature branches from `develop`
- `fix/*` — bug fix branches
- `release/*` — release preparation
- `docs/*` — documentation-only changes

### 7.2 Commit Messages
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `security`
Scopes: `core`, `agents`, `tools`, `memory`, `api`, `ui`, `deploy`, `docs`

### 7.3 Code Review Checklist
- [ ] Architecture: no layer violations
- [ ] Design: follows SOLID, KISS, DRY
- [ ] Security: no eval/exec, no SQL injection, input validated
- [ ] Testing: tests exist and cover new code
- [ ] Types: all functions have type hints
- [ ] Complexity: below defined limits
- [ ] Naming: clear and consistent with conventions
- [ ] Dependencies: no unnecessary new dependencies

## 8. Performance Rules

- No N+1 queries in API endpoints (use `select_related`/`prefetch_related`)
- No synchronous HTTP calls in request-response path
- No expensive computation in hot paths (cache it)
- All LLM calls must have timeouts
- All external API calls must have circuit breakers
- Profile before optimizing (measure, then act)
