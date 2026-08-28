"""AIDA OS — Professional AI Operating System.

Clean Architecture: Domain → Application → Infrastructure → Presentation.
All dependencies point INWARD (toward Domain). No outer layer depends on an inner layer.

Domain:       Entities, value objects, repository interfaces (no dependencies)
Application:  Use cases, DTOs, services (depends only on Domain)
Infrastructure: Adapters, persistence, external integrations (implements Domain interfaces)
Presentation: API, CLI (uses Application use cases)
"""

from .container import AIDAContainer, get_container
from .infrastructure.config.settings import AIDASettings, get_settings
from .infrastructure.logging import setup_logging, get_logger, set_context, clear_context

__all__ = [
    "AIDAContainer", "get_container",
    "AIDASettings", "get_settings",
    "setup_logging", "get_logger", "set_context", "clear_context",
]
