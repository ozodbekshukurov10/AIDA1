"""AIDA Beta v2 — Standalone Code Assistant.

Full integration of all webapp agent patterns:
  - base_agent.py: analyze_input, self_evaluate, record_performance
  - code_agent.py: AST analysis, auto-fix, code quality
  - orchestrator.py: Task type detection, keyword routing, fallback
  - agents.py (legacy): TaskType enum, PriorityQueue, Task dataclass
  - agents/__init__.py: AgentOrchestrator singleton, task queue
  - tool_hub.py: Web search, Python exec, HTTP request, Knowledge tools
  - react_provider.py: ReAct loop pattern
  - code_assistants.py: CodeReviewBot, DebugAssistant, ArchitectureAssistant
  - framework_assistants.py: Language, Framework, VersionControl assistants
  - infrastructure_assistants.py: Docker, Kubernetes, Performance tuning
  - learning_assistants.py: FeedbackLoop, ModelFineTuning, KnowledgeUpdater
  - knowledge_store.py: TF-IDF vectorizer, embeddings, KnowledgeStore

## Arxitektura:
  Foydalanuvchi -> TaskType detect -> Reja -> Tools -> Tekshirish -> Natija
"""

from .provider import AidaBetaProvider
from .memory import AidaBetaMemory
from .agent import (
    Agent, LLMClient, SubAgent, AgentOrchestrator, get_orchestrator,
    detect_task_type, TaskType, TASK_KEYWORDS, TASK_MODEL_MAP,
    Task, PriorityQueue, BaseAgent, CodeAgent, PlanAgent, DebugAgent, TestAgent,
    ExecutionMode, PermissionLevel, PermissionManager, HookManager, HookEvent, MemoryMD,
)
from .tools import Tool, execute, TOOLS, set_work_dir
from .knowledge import KnowledgeStore, get_knowledge_store
from .assistants import (
    CodeReviewBot, DebugAssistant, ArchitectureAssistant,
    LanguageAssistant, FrameworkAssistant, VersionControlAssistant,
    DockerAssistant, KubernetesAssistant, PerformanceTuningAssistant,
)
from .learning import FeedbackLoop, ModelFineTuning, KnowledgeUpdater

__version__ = "2.1.0"
__all__ = [
    "AidaBetaProvider", "AidaBetaMemory",
    "Agent", "LLMClient", "SubAgent", "AgentOrchestrator", "get_orchestrator",
    "detect_task_type", "TaskType", "TASK_KEYWORDS", "TASK_MODEL_MAP",
    "Task", "PriorityQueue", "BaseAgent", "CodeAgent", "PlanAgent", "DebugAgent", "TestAgent",
    "Tool", "execute", "TOOLS", "set_work_dir",
    "KnowledgeStore", "get_knowledge_store",
    "CodeReviewBot", "DebugAssistant", "ArchitectureAssistant",
    "LanguageAssistant", "FrameworkAssistant", "VersionControlAssistant",
    "DockerAssistant", "KubernetesAssistant", "PerformanceTuningAssistant",
    "FeedbackLoop", "ModelFineTuning", "KnowledgeUpdater",
    "ExecutionMode", "PermissionLevel", "PermissionManager", "HookManager", "HookEvent", "MemoryMD",
]
