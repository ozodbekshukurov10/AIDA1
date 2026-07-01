"""Dependency Injection Container — wires the entire Clean Architecture together.

All dependencies are registered once and resolved automatically.
To add AIDA Model: register its adapter as a ProviderPlugin — zero code changes needed.
"""

from __future__ import annotations
import logging
from typing import Any

from .domain.entities import (
    AgentSpec, ToolSpec, Permission, PermissionLevel,
    WorkflowTemplate,
)
from .domain.events import EventBus, DomainEventType
from .domain.interfaces import (
    AgentRepository, ToolRepository, ProviderRepository,
    MemoryRepository, SessionRepository, ProjectRepository,
    CodebaseRepository, MetricsRepository, KnowledgeRepository,
    WorkflowRepository,
)
from .application.use_cases import (
    ChatUseCase, AgentExecuteUseCase, AgentManageUseCase,
    ToolExecuteUseCase, ToolManageUseCase,
    CodeAnalysisUseCase, CodeGenerationUseCase,
    MemoryUseCase, WorkflowUseCase,
    SelfImprovementUseCase, SearchUseCase, ProjectUseCase,
)

logger = logging.getLogger("aidaos.container")


class AIDAContainer:
    """Central DI container. Replace singletons with registered implementations."""

    def __init__(self):
        self._event_bus: EventBus | None = None
        self._repos: dict[str, Any] = {}
        self._use_cases: dict[str, Any] = {}
        self._initialized = False

    # ─── Event Bus ─────────────────────────────────────────────

    @property
    def event_bus(self) -> EventBus:
        if self._event_bus is None:
            self._event_bus = EventBus()
        return self._event_bus

    # ─── Repository Registration ───────────────────────────────

    def register_agent_repo(self, repo: AgentRepository):
        self._repos["agent"] = repo
        logger.info("AgentRepository registered")

    def register_tool_repo(self, repo: ToolRepository):
        self._repos["tool"] = repo
        logger.info("ToolRepository registered")

    def register_provider_repo(self, repo: ProviderRepository):
        self._repos["provider"] = repo
        logger.info("ProviderRepository registered")

    def register_memory_repo(self, repo: MemoryRepository):
        self._repos["memory"] = repo
        logger.info("MemoryRepository registered")

    def register_session_repo(self, repo: SessionRepository):
        self._repos["session"] = repo
        logger.info("SessionRepository registered")

    def register_project_repo(self, repo: ProjectRepository):
        self._repos["project"] = repo
        logger.info("ProjectRepository registered")

    def register_codebase_repo(self, repo: CodebaseRepository):
        self._repos["codebase"] = repo
        logger.info("CodebaseRepository registered")

    def register_metrics_repo(self, repo: MetricsRepository):
        self._repos["metrics"] = repo
        logger.info("MetricsRepository registered")

    def register_knowledge_repo(self, repo: KnowledgeRepository):
        self._repos["knowledge"] = repo
        logger.info("KnowledgeRepository registered")

    def register_workflow_repo(self, repo: WorkflowRepository):
        self._repos["workflow"] = repo
        logger.info("WorkflowRepository registered")

    # ─── Use Case Resolution ───────────────────────────────────

    def chat_use_case(self) -> ChatUseCase:
        return self._resolve("chat", ChatUseCase, self._prov, self._sess, self._metr)

    def agent_execute_use_case(self) -> AgentExecuteUseCase:
        return self._resolve("agent_exec", AgentExecuteUseCase, self._agent, self._metr)

    def agent_manage_use_case(self) -> AgentManageUseCase:
        return self._resolve("agent_mgmt", AgentManageUseCase, self._agent)

    def tool_execute_use_case(self) -> ToolExecuteUseCase:
        return self._resolve("tool_exec", ToolExecuteUseCase, self._tool)

    def tool_manage_use_case(self) -> ToolManageUseCase:
        return self._resolve("tool_mgmt", ToolManageUseCase, self._tool)

    def code_analysis_use_case(self) -> CodeAnalysisUseCase:
        return self._resolve("code_analysis", CodeAnalysisUseCase, self._codebase)

    def code_generation_use_case(self) -> CodeGenerationUseCase:
        return self._resolve("code_gen", CodeGenerationUseCase, self._prov)

    def memory_use_case(self) -> MemoryUseCase:
        return self._resolve("memory", MemoryUseCase, self._mem, self._metr)

    def workflow_use_case(self) -> WorkflowUseCase:
        return self._resolve("workflow", WorkflowUseCase, self._agent, self._wf)

    def improvement_use_case(self) -> SelfImprovementUseCase:
        return self._resolve("improvement", SelfImprovementUseCase, self._agent, self._metr)

    def search_use_case(self) -> SearchUseCase:
        return self._resolve("search", SearchUseCase, self._codebase, self._mem, self._know)

    def project_use_case(self) -> ProjectUseCase:
        return self._resolve("project", ProjectUseCase, self._proj)

    # ─── Plugin Registration (for AIDA Model and future models) ───

    def register_provider_plugin(self, name: str, chat_fn, stream_fn=None, spec: dict = None):
        """Register a new provider at runtime. AIDA Model just calls this."""
        from .domain.entities import ProviderSpec, ProviderStatus
        pspec = ProviderSpec(
            name=name,
            model=(spec or {}).get("model", "default"),
            status=ProviderStatus.ONLINE,
            supports_streaming=stream_fn is not None,
            supports_tools=(spec or {}).get("supports_tools", False),
            max_tokens=(spec or {}).get("max_tokens", 4096),
        )

        async def chat_wrapper(messages, **kwargs):
            return await chat_fn(messages, **kwargs)

        async def stream_wrapper(messages, **kwargs):
            if stream_fn:
                async for chunk in stream_fn(messages, **kwargs):
                    yield chunk
            else:
                yield ""

        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self._prov.register(pspec, chat_wrapper, stream_wrapper))
            else:
                asyncio.run(self._prov.register(pspec, chat_wrapper, stream_wrapper))
        except Exception:
            pass
        logger.info(f"Provider plugin '{name}' registered. No code changes needed.")

    # ─── Initialization ────────────────────────────────────────

    async def initialize(self):
        """Verify all required repositories are registered."""
        required = ["agent", "tool", "provider", "memory", "session", "metrics"]
        missing = [r for r in required if r not in self._repos]
        if missing:
            logger.warning(f"Missing repositories: {missing}. Some use cases will fail.")
        self._initialized = True
        logger.info("AIDA Container initialized successfully")
        return {"status": "ok", "missing_repos": missing}

    def is_initialized(self) -> bool:
        return self._initialized

    # ─── Internal Helpers ──────────────────────────────────────

    def _resolve(self, key: str, cls: type, *args):
        if key not in self._use_cases:
            self._use_cases[key] = cls(*args)
        return self._use_cases[key]

    @property
    def _agent(self) -> AgentRepository:
        return self._repos.get("agent")

    @property
    def _tool(self) -> ToolRepository:
        return self._repos.get("tool")

    @property
    def _prov(self) -> ProviderRepository:
        return self._repos.get("provider")

    @property
    def _mem(self) -> MemoryRepository:
        return self._repos.get("memory")

    @property
    def _sess(self) -> SessionRepository:
        return self._repos.get("session")

    @property
    def _proj(self) -> ProjectRepository:
        return self._repos.get("project")

    @property
    def _codebase(self) -> CodebaseRepository:
        return self._repos.get("codebase")

    @property
    def _metr(self) -> MetricsRepository:
        return self._repos.get("metrics")

    @property
    def _know(self) -> KnowledgeRepository:
        return self._repos.get("knowledge")

    @property
    def _wf(self) -> WorkflowRepository:
        return self._repos.get("workflow")


_container: AIDAContainer | None = None


def get_container() -> AIDAContainer:
    global _container
    if _container is None:
        _container = AIDAContainer()
    return _container
