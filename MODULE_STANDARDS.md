# AIDA — Module Standards

## 1. Every Module Must Contain

Every module (directory with `__init__.py`) in the `aida/` package must include the following standardized files:

```
module_name/
+-- __init__.py          # Public API exports
+-- interfaces.py        # Module interfaces (contracts)
+-- config.py            # Module-specific configuration
+-- exceptions.py        # Module-specific exceptions
+-- models.py            # Internal data models (not exposed)
+-- service.py           # Main service implementation
+-- README.md            # Module documentation
+-- tests/               # Module-specific tests
|   +-- __init__.py
|   +-- test_service.py
|   +-- test_interfaces.py
+-- docs/                # Module-specific documentation
    +-- DESIGN.md
```

### Exceptions by Module Type

| Module Type | Required Files | Optional |
|---|---|---|
| `domain/entities/` | `__init__.py`, entity files | — |
| `domain/events/` | `__init__.py`, event files, `event_bus.py` | — |
| `domain/exceptions/` | `__init__.py`, exception files | — |
| `domain/interfaces/` | `__init__.py`, interface files | — |
| `application/dtos/` | `__init__.py`, DTO files | — |
| `application/use_cases/*/` | `__init__.py`, use case files | `config.py`, `exceptions.py` |
| `kernel/*/` | `__init__.py`, `interfaces.py`, `service.py`, `config.py`, `exceptions.py` | `models.py` |
| `kernel/*/builtin/` | `__init__.py`, implementation files | — |
| `infrastructure/*/` | `__init__.py`, adapter files, `config.py` | `exceptions.py` |
| `presentation/api/*/endpoints/` | `__init__.py`, endpoint files | — |
| `presentation/cli/` | `__init__.py`, `app.py`, `parser.py` | `commands/*` |
| `security/` | `__init__.py`, module files | — |
| `plugins/` | `__init__.py`, `interfaces.py`, `manager.py` | All sub-modules |

## 2. File Content Standards

### 2.1 `__init__.py` — Public API

Exports only what should be public. Never exports internal implementation details.

```python
"""module_name — brief description of module responsibility."""

from .interfaces import ConcreteInterface
from .service import MainService

__all__ = ["ConcreteInterface", "MainService"]
```

**Rules:**
- Maximum 5 exported symbols per module
- Never export private classes (prefixed with `_`)
- Never `from .service import *`
- Always use explicit `__all__`

### 2.2 `interfaces.py` — Module Contracts

```python
"""Interfaces for module_name module."""

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable
from dataclasses import dataclass


class ModuleInterface(ABC):
    """Contract for module_name functionality."""

    @abstractmethod
    async def execute(self, param: str) -> Result:
        """Execute the primary operation."""
        raise NotImplementedError
```

**Rules:**
- All interfaces use `ABC` or `Protocol`
- All methods are `@abstractmethod`
- All methods have complete type hints
- All methods are async (future-proof)
- Maximum 8 methods per interface (Interface Segregation)
- Interface parameters and returns use domain entities or primitives
- Never use `dict` or `Any` in interface signatures

### 2.3 `config.py` — Module Configuration

```python
"""Configuration for module_name module."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModuleConfig:
    """Typed configuration for module_name."""

    enabled: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3
    allowed_domains: list[str] = field(default_factory=list)
    api_key: Optional[str] = None  # Loaded from secrets, never hardcoded
```

**Rules:**
- Always a `@dataclass` with default values
- No business logic in config
- Secrets (API keys, passwords) are `Optional[str] = None` — loaded from environment
- All timeouts in seconds as `int`
- All limits as positive `int`

### 2.4 `exceptions.py` — Module Errors

```python
"""Exceptions for module_name module."""

from aida.domain.exceptions.base import AIDAError


class ModuleError(AIDAError):
    """Base exception for module_name."""


class ModuleNotFoundError(ModuleError):
    """Raised when a resource is not found."""


class ModuleExecutionError(ModuleError):
    """Raised when operation fails."""
```

**Rules:**
- Every module has a base exception inheriting from `AIDAError`
- Maximum 5 exception types per module
- Each exception carries: `code`, `status_code`, `message`, `details`
- Never raise raw `Exception` — always a domain exception

### 2.5 `models.py` — Internal Models

```python
"""Internal data models for module_name."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class InternalState(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"


@dataclass
class InternalModel:
    """Internal representation — not exposed outside this module."""
    id: str
    state: InternalState
    created_at: datetime = field(default_factory=datetime.utcnow)
```

**Rules:**
- Never import these models outside the module
- Never use in interface signatures
- Pure data containers — no business logic

### 2.6 `service.py` — Main Implementation

```python
"""Service implementation for module_name."""

import logging
from typing import Optional

from .interfaces import ModuleInterface
from .config import ModuleConfig
from .exceptions import ModuleNotFoundError


class ModuleService(ModuleInterface):
    """Implements ModuleInterface."""

    def __init__(self, config: ModuleConfig, dependency: SomeInterface):
        self._config = config
        self._dependency = dependency
        self._logger = logging.getLogger(__name__)

    async def execute(self, param: str) -> Result:
        """Primary operation implementation."""
        self._logger.debug("Executing with param=%s", param)
        if not self._config.enabled:
            raise ModuleExecutionError("Module is disabled")
        return await self._dependency.process(param)
```

**Rules:**
- One service class per module
- All dependencies injected via constructor (no global lookups)
- Log all entry and exit points at DEBUG level
- Log errors at WARNING/ERROR level with context
- Never catch `Exception` silently — always log and re-raise or handle specifically
- All public methods are async

### 2.7 `README.md` — Module Documentation

```markdown
# module_name

## Purpose
One paragraph describing what this module does.

## Responsibilities
- What this module owns
- What this module does NOT do

## Dependencies
- `dependency1` — what it provides
- `dependency2` — what it provides

## Usage
```python
from aida.module_name import MainService

service = MainService(config, dependency)
result = await service.execute("input")
```

## Configuration
| Variable | Default | Description |
|---|---|---|
| `enabled` | `true` | Enable/disable module |
| `timeout_seconds` | `30` | Operation timeout |
```

## 3. File Size Limits

| File Type | Max Lines | Action |
|---|---|---|
| `__init__.py` | 20 | Extract to separate file |
| `interfaces.py` | 100 | Split interface (ISP violation) |
| `config.py` | 30 | Extract sub-configs |
| `exceptions.py` | 50 | Split exceptions |
| `models.py` | 100 | Split models |
| `service.py` | 200 | Extract helper methods |
| Entity file | 300 | Split entities |
| Use case file | 150 | Split use case |
| Endpoint file | 150 | Split endpoint |
| Test file | 300 | Split test |

## 4. Module Quality Gates

| Check | Requirement | Enforcement |
|---|---|---|
| All required files exist | CI check | Custom script |
| `__init__.py` exports listed | Code review | Manual |
| `interfaces.py` has full type hints | `mypy --strict` | CI |
| `config.py` has defaults | Code review | Manual |
| `exceptions.py` inherits from `AIDAError` | CI check | Custom script |
| `service.py` < 200 lines | `pylint` | CI |
| All public methods have docstrings | `interrogate` | CI |
| Module has tests in `tests/` | Coverage | CI |
| No `import *` in module | `ruff` | CI |

## 5. Module Template Generator

When creating a new module:

```bash
# Command: aida-cli generate module <name>
# Creates:
aida/module_name/
+-- __init__.py          # Auto-generated with standard header
+-- interfaces.py        # Skeleton with ABC and placeholder
+-- config.py            # Standard dataclass with defaults
+-- exceptions.py        # Base exception class
+-- models.py            # Empty dataclass
+-- service.py           # Skeleton implementing interfaces
+-- README.md            # Template filled with module name
+-- tests/
|   +-- __init__.py
|   +-- test_service.py  # Skeleton with import
|   +-- test_interfaces.py # Skeleton with mock
+-- docs/
    +-- DESIGN.md        # Empty design document template
```
