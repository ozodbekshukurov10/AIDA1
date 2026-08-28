"""Dependency Injection Container — wires the entire system together.

All dependencies are registered once and resolved automatically via lazy initialization.
Supports services, repositories, use cases, and provider plugins.
"""

from __future__ import annotations
from typing import Any, Callable
from aidaos.infrastructure.logging import get_logger

logger = get_logger("container")


class ServiceLifetime:
    SINGLETON = "singleton"
    TRANSIENT = "transient"


class ServiceDescriptor:
    def __init__(self, factory: Callable[[], Any], lifetime: str = ServiceLifetime.SINGLETON):
        self.factory = factory
        self.lifetime = lifetime
        self._instance: Any = None

    def resolve(self) -> Any:
        if self.lifetime == ServiceLifetime.SINGLETON:
            if self._instance is None:
                self._instance = self.factory()
            return self._instance
        return self.factory()


class AIDAContainer:
    """Central DI container. Register dependencies once, resolve everywhere."""

    def __init__(self):
        self._services: dict[str, ServiceDescriptor] = {}
        self._repos: dict[str, Any] = {}
        self._initialized = False

    # ─── Service Registration ──────────────────────────────────

    def register(
        self,
        name: str,
        factory: Callable[[], Any],
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        self._services[name] = ServiceDescriptor(factory, lifetime)
        logger.debug(f"Service registered: {name} ({lifetime})")

    def register_instance(self, name: str, instance: Any) -> None:
        self._services[name] = ServiceDescriptor(lambda: instance, ServiceLifetime.SINGLETON)
        self._services[name]._instance = instance
        logger.debug(f"Instance registered: {name}")

    def resolve(self, name: str) -> Any:
        desc = self._services.get(name)
        if desc is None:
            logger.warning(f"Service not found: {name}")
            return None
        return desc.resolve()

    # ─── Repository Registration ───────────────────────────────

    def register_repo(self, name: str, repo: Any) -> None:
        self._repos[name] = repo
        logger.info(f"Repository registered: {name}")

    def get_repo(self, name: str) -> Any:
        return self._repos.get(name)

    # ─── Convenience Accessors ─────────────────────────────────

    @property
    def initialized(self) -> bool:
        return self._initialized

    def initialize(self) -> dict[str, Any]:
        if self._initialized:
            return {"status": "already_initialized"}
        required_repos = ["session", "memory"]
        missing = [r for r in required_repos if r not in self._repos]
        if missing:
            logger.warning(f"Missing repositories: {missing}")
        self._initialized = True
        logger.info("Container initialized")
        return {"status": "ok", "missing_repos": missing}

    # ─── Convenience Repository Registrations ──────────────────

    def register_agent_repo(self, repo: Any) -> None:
        self.register_repo("agent", repo)

    def register_tool_repo(self, repo: Any) -> None:
        self.register_repo("tool", repo)

    def register_provider_repo(self, repo: Any) -> None:
        self._prov = repo
        self.register_repo("provider", repo)

    def register_memory_repo(self, repo: Any) -> None:
        self.register_repo("memory", repo)

    def register_session_repo(self, repo: Any) -> None:
        self.register_repo("session", repo)

    def register_knowledge_repo(self, repo: Any) -> None:
        self.register_repo("knowledge", repo)

    def register_metrics_repo(self, repo: Any) -> None:
        self.register_repo("metrics", repo)

    def register_project_repo(self, repo: Any) -> None:
        self.register_repo("project", repo)

    def register_workflow_repo(self, repo: Any) -> None:
        self.register_repo("workflow", repo)

    def register_provider_plugin(self, name: str, chat_fn, stream_fn=None, spec=None) -> None:
        logger.info(f"Provider plugin registered: {name}")

    # ─── Use Case Resolvers ────────────────────────────────────

    def chat_use_case(self):
        from aidaos.application.use_cases.chat import ChatUseCase
        return ChatUseCase(
            provider_repo=self._repos.get("provider"),
            session_repo=self._repos.get("session"),
            metrics_repo=self._repos.get("metrics"),
        )

    def agent_execute_use_case(self):
        from aidaos.application.use_cases.agent import AgentExecuteUseCase
        return AgentExecuteUseCase(
            agent_repo=self._repos.get("agent"),
            metrics_repo=self._repos.get("metrics"),
        )

    def agent_manage_use_case(self):
        from aidaos.application.use_cases.agent import AgentManageUseCase
        tmp = AgentManageUseCase(agent_repo=self._repos.get("agent"))
        return tmp

    def tool_execute_use_case(self):
        from aidaos.application.use_cases.tool import ToolExecuteUseCase
        return ToolExecuteUseCase(tool_repo=self._repos.get("tool"))

    def tool_manage_use_case(self):
        from aidaos.application.use_cases.tool import ToolManageUseCase
        return ToolManageUseCase(tool_repo=self._repos.get("tool"))

    def memory_use_case(self):
        from aidaos.application.use_cases.memory import MemoryUseCase
        return MemoryUseCase(
            memory_repo=self._repos.get("memory"),
            metrics_repo=self._repos.get("metrics"),
        )

    def improvement_use_case(self):
        from aidaos.application.use_cases.improvement import SelfImprovementUseCase
        return SelfImprovementUseCase(
            agent_repo=self._repos.get("agent"),
            metrics_repo=self._repos.get("metrics"),
        )

    def list_services(self) -> list[str]:
        return list(self._services.keys())

    def list_repos(self) -> list[str]:
        return list(self._repos.keys())


_container: AIDAContainer | None = None


def get_container() -> AIDAContainer:
    global _container
    if _container is None:
        _container = AIDAContainer()
        _container.initialize()
    return _container
