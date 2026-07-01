"""AIDA OS — Professional AI Operating System.

Clean Architecture: Domain → Application → Infrastructure → Presentation.
All dependencies point INWARD (toward Domain). No outer layer depends on an inner layer.

Domain:     Entities, value objects, repository interfaces (no dependencies)
Application: Use cases, DTOs, services (depends only on Domain)
Infrastructure: Adapters, persistence, external integrations (implements Domain interfaces)
Presentation: API, CLI (uses Application use cases)
"""

from .container import AIDAContainer, get_container

__all__ = ["AIDAContainer", "get_container"]
