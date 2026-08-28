# AIDA — Import Guidelines

## 1. Import Philosophy

AIDA uses **absolute imports** exclusively. Relative imports are forbidden. This ensures:
- Every import path is unambiguous
- Refactoring (moving files) does not break sibling imports
- IDEs and static analysis tools can resolve all imports
- Circular imports are immediately obvious during code review

## 2. Absolute Import Path Pattern

```
from aida.<layer>.<module>.<submodule> import <symbol>
```

### Examples

```python
# Domain layer
from aida.domain.entities.agent import AgentSpec, AgentContext
from aida.domain.events.event_bus import EventBus, DomainEvent
from aida.domain.exceptions.agent_errors import AgentNotFoundError
from aida.domain.interfaces.agent_repo import AgentRepository

# Application layer
from aida.application.dtos.chat_dtos import ChatRequest, ChatResponse
from aida.application.use_cases.chat.send_message import SendMessageUseCase

# Kernel layer
from aida.kernel.agents.interfaces import BaseAgent
from aida.kernel.memory.interfaces import MemoryStore
from aida.kernel.tools.interfaces import BaseTool
from aida.kernel.models.interfaces import ModelProvider, ModelGateway
from aida.kernel.codebase.interfaces import CodebaseIndexer

# Infrastructure layer
from aida.infrastructure.persistence.repositories.session_repo import SessionRepoAdapter
from aida.infrastructure.cache.redis import RedisCache
from aida.infrastructure.network.http_client import HTTPClient

# Presentation layer
from aida.presentation.api.v2.responses import APIResponse
from aida.presentation.cli.formatter import OutputFormatter
```

## 3. Forbidden Import Patterns

### 3.1 Relative Imports

```python
# ❌ FORBIDDEN
from . import sibling_module
from ..domain import entity
from ...kernel import interfaces
from .service import SomeClass

# ✅ CORRECT
from aida.domain.entities.agent import AgentSpec
from aida.kernel.agents.interfaces import BaseAgent
```

### 3.2 Wildcard Imports

```python
# ❌ FORBIDDEN — pollutes namespace, hides dependencies
from aida.domain.entities import *
from aida.kernel.agents import *

# ✅ CORRECT — explicit symbols
from aida.domain.entities.agent import AgentSpec, AgentResult
from aida.kernel.agents.registry import AgentRegistry
```

### 3.3 Circular Imports

```python
# ❌ FORBIDDEN
# Module A imports Module B, Module B imports Module A

# ✅ CORRECT — restructure to eliminate cycle
# Option 1: Extract shared interface to separate module
# Option 2: Move one import to method level (lazy import)
# Option 3: Use dependency injection to break compile-time dependency
```

### 3.4 Layer Violation Imports

```python
# ❌ FORBIDDEN — Application importing Infrastructure
from aida.infrastructure.persistence import SQLiteDatabase

# ❌ FORBIDDEN — Domain importing anything outside domain
from aida.infrastructure.logging import setup_logging

# ❌ FORBIDDEN — Infrastructure importing Application
from aida.application.use_cases.workflow import WorkflowUseCase

# ✅ CORRECT
# Application → uses interfaces from domain
from aida.domain.interfaces.memory_repo import MemoryRepository

# Infrastructure → implements domain interfaces
from aida.domain.interfaces.session_repo import SessionRepository

# Presentation → calls application use cases
from aida.application.use_cases.chat.send_message import SendMessageUseCase
```

### 3.5 Import Inside Function Body (except for rare cases)

```python
# ❌ FORBIDDEN — unless absolutely necessary for circular dependency resolution
def my_function():
    from aida.kernel.agents import AgentRegistry  # BAD
    ...

# ✅ ACCEPTABLE — only for TYPE_CHECKING or circular dep resolution
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from aida.kernel.agents.interfaces import BaseAgent
```

## 4. Import Order (Enforced by `ruff`)

```python
# 1. Future imports
from __future__ import annotations

# 2. Standard library
import abc
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Optional, Protocol

# 3. Third-party libraries
import httpx

# 4. AIDA framework imports (alphabetical by path)
from aida.domain.entities.agent import AgentSpec, AgentResult
from aida.domain.exceptions.base import AIDAError

# 5. Same-layer module imports (within same module)
from .interfaces import SomeInterface  # ONLY in same package
from .config import ModuleConfig

# 6. Test utilities (only in test files)
import pytest
```

### Groups (separated by blank line):

| Group | Contents |
|---|---|
| 1 | `from __future__ import annotations` |
| 2 | Standard library (`os`, `sys`, `typing`, `abc`, `dataclasses`, etc.) |
| 3 | Third-party (`django`, `httpx`, `pydantic`, etc.) |
| 4 | AIDA domain (`aida.domain.*`) |
| 5 | AIDA application (`aida.application.*`) |
| 6 | AIDA kernel (`aida.kernel.*`) |
| 7 | AIDA infrastructure (`aida.infrastructure.*`) |
| 8 | AIDA presentation (`aida.presentation.*`) |
| 9 | AIDA plugins (`aida.plugins.*`) |
| 10 | Same-module relative imports (only for `interfaces.py`, `config.py`) |

## 5. Allowed Dependencies by Layer

### Domain Layer

```python
# ✅ ALLOWED
from __future__ import annotations
import abc
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional, Protocol, runtime_checkable
from uuid import uuid4

# ❌ FORBIDDEN
from django.db import models
import httpx
import sqlite3
import json  # Except in event serialization
```

### Application Layer

```python
# ✅ ALLOWED
from aida.domain.entities.* import ...      # Domain entities
from aida.domain.interfaces.* import ...    # Domain interfaces
from aida.domain.exceptions.* import ...    # Domain exceptions
from aida.domain.events.event_bus import ...  # Event bus
from aida.application.dtos.* import ...     # DTOs
from aida.kernel.agents.interfaces import BaseAgent  # Kernel interfaces
from aida.kernel.memory.interfaces import MemoryStore  # Kernel interfaces
from aida.kernel.tools.interfaces import BaseTool  # Kernel interfaces
from aida.kernel.models.interfaces import ModelGateway  # Kernel interfaces

# ❌ FORBIDDEN
from aida.infrastructure.* import ...     # Infrastructure
from aida.presentation.* import ...      # Presentation
from django.db import connection          # Framework
from aida.plugins.* import ...           # Plugins
```

### Kernel Layer

```python
# ✅ ALLOWED
from aida.domain.entities.* import ...      # Domain entities
from aida.domain.interfaces.* import ...    # Domain interfaces
from aida.domain.exceptions.* import ...    # Domain exceptions
from aida.domain.events.event_bus import ...  # Event bus
from aida.kernel.*.interfaces import ...    # Other kernel module interfaces

# ❌ FORBIDDEN
from aida.infrastructure.* import ...     # Infrastructure
from aida.application.* import ...        # Application
from aida.presentation.* import ...       # Presentation
from aida.plugins.* import ...           # Plugins
```

### Infrastructure Layer

```python
# ✅ ALLOWED
from aida.domain.interfaces.* import ...  # Domain interfaces (to implement them)
from aida.domain.entities.* import ...    # Domain entities
from aida.domain.exceptions.* import ...  # Domain exceptions
from aida.kernel.*.interfaces import ...  # Kernel interfaces
import httpx                              # HTTP client
import sqlite3                            # Database

# ❌ FORBIDDEN
from aida.application.* import ...       # Application use cases
from aida.presentation.* import ...      # Presentation
```

### Presentation Layer

```python
# ✅ ALLOWED
from aida.application.use_cases.* import ...  # Use cases
from aida.application.dtos.* import ...       # DTOs
from aida.domain.exceptions.* import ...      # Domain exceptions (for error mapping)
from aida.security.auth.api_keys import ...   # Authentication

# ❌ FORBIDDEN
from aida.infrastructure.* import ...     # Infrastructure
from aida.kernel.* import ...            # Kernel (except through use cases)
```

## 6. Circular Import Prevention

### Detection

```bash
# CI check
pip install import-linter
import-linter check --layers aida/
```

### Prevention Patterns

```python
# Pattern 1: Type-checking only imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aida.kernel.agents.interfaces import BaseAgent
    # These imports are only used for type hints, never at runtime

# Pattern 2: Lazy imports (only when absolutely necessary)
class SomeService:
    async def execute(self):
        from aida.kernel.agents.registry import AgentRegistry  # Lazy import
        registry = AgentRegistry()
        ...

# Pattern 3: Extract shared interface to separate module
# Before: module_a.py imports module_b.py imports module_a.py
# After:  module_a.py imports interfaces.py imports module_b.py (no cycle)

# Pattern 4: Dependency injection
# Instead of importing the concrete class, import the interface and inject the implementation
class MyUseCase:
    def __init__(self, agent_repo: AgentRepository):  # Interface, not concrete
        self._agent_repo = agent_repo
```

## 7. `__init__.py` Export Policy

### Domain Entities

```python
# aida/domain/entities/__init__.py
"""Domain entities."""

from .agent import AgentSpec, AgentContext, AgentResult, AgentCapability
from .tool import ToolSpec, ToolResult
from .message import Message, Completion, StreamingChunk, MessageRole
from .session import Session, SessionConfig

__all__ = [
    "AgentSpec", "AgentContext", "AgentResult", "AgentCapability",
    "ToolSpec", "ToolResult",
    "Message", "Completion", "StreamingChunk", "MessageRole",
    "Session", "SessionConfig",
]
```

### Rules

- Export only frequently-used symbols
- Never export internal implementation classes
- Keep `__init__.py` under 20 lines
- Always use explicit `__all__`
- Group related exports with comments

## 8. Type Import Policy

```python
# ✅ PREFERRED — import types directly
from aida.domain.entities.agent import AgentSpec

def process(spec: AgentSpec) -> None: ...

# ✅ ACCEPTABLE — TYPE_CHECKING for circular import prevention
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aida.kernel.agents.interfaces import BaseAgent

class MyService:
    def __init__(self, agent: "BaseAgent") -> None:  # String annotation
        self._agent = agent
```

## 9. Import Linting Configuration

```toml
# pyproject.toml
[tool.ruff.lint]
select = ["I"]  # Import ordering

[tool.ruff.lint.isort]
known-first-party = ["aida"]
lines-after-imports = 2

[tool.import-linter]
root_package = "aida"
include_extensions = "py"

[[tool.import-linter.layers]]
name = "Domain"
contain = "aida.domain"

[[tool.import-linter.layers]]
name = "Application"
contain = "aida.application"
import_allow = ["aida.domain", "aida.kernel"]

[[tool.import-linter.layers]]
name = "Kernel"
contain = "aida.kernel"
import_allow = ["aida.domain"]

[[tool.import-linter.layers]]
name = "Infrastructure"
contain = "aida.infrastructure"
import_allow = ["aida.domain", "aida.kernel"]

[[tool.import-linter.layers]]
name = "Presentation"
contain = "aida.presentation"
import_allow = ["aida.application"]

[[tool.import-linter.layers]]
name = "Plugins"
contain = "aida.plugins"
import_allow = ["aida.domain", "aida.kernel"]

[[tool.import-linter.layers]]
name = "Security"
contain = "aida.security"
import_allow = ["aida.domain"]

[[tool.import-linter.layers]]
name = "Monitoring"
contain = "aida.monitoring"
```

## 10. Import Guidelines Summary

| Rule | Severity | Enforcement |
|---|---|---|
| Absolute imports only | BLOCKER | `ruff` + code review |
| No wildcard imports | BLOCKER | `ruff` (lint rule) |
| No circular imports | BLOCKER | `import-linter` CI check |
| No layer violations | BLOCKER | `import-linter` CI check |
| Correct import order | ERROR | `ruff check --select I` |
| No imports inside function bodies | WARNING | Code review |
| `TYPE_CHECKING` for type-only imports | WARNING | Code review |
| `__init__.py` exports explicit `__all__` | WARNING | Code review |
| Third-party imports after stdlib | ERROR | `ruff` auto-fix |
| AIDA imports after third-party | ERROR | `ruff` auto-fix |
