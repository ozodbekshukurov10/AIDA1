from __future__ import annotations

import asyncio
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ..orchestrator import Orchestrator, Task, TaskType

logger = logging.getLogger("webapp.agents")

# Public re-exports from agents
from .base_agent import BaseAgent
from .code_agent import CodeAgent
from .planning_agent import PlanningAgent
from .general_agent import GeneralAgent

# Task type → model mapping
TASK_MODEL_MAP: Dict[TaskType, str] = {
    TaskType.CODE_GENERATION: "codellama:34b",
    TaskType.CODE_ANALYSIS: "codellama:34b",
    TaskType.PLANNING: "qwen2.5:3b",
    TaskType.DEBUGGING: "codellama:34b",
    TaskType.TESTING: "codellama:34b",
    TaskType.OPTIMIZATION: "codellama:34b",
}


@dataclass
class QueuedTask:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType = TaskType.CODE_GENERATION
    prompt: str = ""
    priority: int = 5
    status: str = "queued"  # queued | running | done | error
    result: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)


class TaskQueue:
    def __init__(self):
        self._items: List[QueuedTask] = []
        self._lock = threading.Lock()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._items)

    def push(self, task: QueuedTask) -> None:
        with self._lock:
            self._items.append(task)
            self._items.sort(key=lambda t: -t.priority)

    def pop(self) -> Optional[QueuedTask]:
        with self._lock:
            if not self._items:
                return None
            return self._items.pop(0)

    def all_tasks(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                {"id": t.id, "type": t.task_type.value, "status": t.status, "priority": t.priority}
                for t in self._items
            ]


class TaskRouter:
    """Prompt'dan task type aniqlash."""

    def __init__(self):
        self._orch = Orchestrator()

    def detect(self, prompt: str) -> TaskType:
        return self._orch._detect_task_type(prompt)


def _run_async(coro):
    """Sync kontekstda async coroutine ni ishlatish."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=120)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


class AgentOrchestrator:
    """Global persistent orchestrator — barcha agentlarni boshqaradi."""

    def __init__(
        self,
        respond_func: Optional[Callable] = None,
        tool_hub: Optional[Any] = None,
    ):
        self.queue = TaskQueue()
        self._router = TaskRouter()
        self._completed: Dict[str, QueuedTask] = {}
        self._respond_func = respond_func

        call_fn = self._make_async_call(respond_func) if respond_func else None

        self._agents: Dict[str, BaseAgent] = {
            TaskType.CODE_GENERATION.value: CodeAgent(call_model_func=call_fn),
            TaskType.CODE_ANALYSIS.value: CodeAgent(call_model_func=call_fn),
            TaskType.DEBUGGING.value: CodeAgent(call_model_func=call_fn),
            TaskType.TESTING.value: CodeAgent(call_model_func=call_fn),
            TaskType.OPTIMIZATION.value: CodeAgent(call_model_func=call_fn),
            TaskType.PLANNING.value: PlanningAgent(call_model_func=call_fn),
        }
        self._general = GeneralAgent(call_model_func=call_fn)

    @staticmethod
    def _make_async_call(sync_fn: Callable) -> Callable:
        """Sync respond_func ni async'ga o'rash."""
        async def async_call(prompt: str) -> str:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, sync_fn, prompt)
        return async_call

    def submit(self, prompt: str, priority: int = 5) -> QueuedTask:
        task_type = self._router.detect(prompt)
        qt = QueuedTask(task_type=task_type, prompt=prompt, priority=priority)
        self.queue.push(qt)
        return qt

    def execute(self, prompt: str) -> Dict[str, Any]:
        """Sync: prompt → agent → javob."""
        qt = self.submit(prompt)
        qt.status = "running"

        task_type = qt.task_type
        agent = self._agents.get(task_type.value, self._general)

        orch_task = Task(id=qt.id, type=task_type, prompt=prompt)

        try:
            result = _run_async(agent.execute(orch_task))
            qt.status = "done"
            qt.result = result
        except Exception as e:
            qt.status = "error"
            qt.result = {"status": "error", "error": str(e)}
            logger.exception(f"[AgentOrchestrator] execute failed: {e}")

        self._completed[qt.id] = qt
        return qt.result or {}

    def get_agent_stats(self) -> List[Dict[str, Any]]:
        stats = []
        for key, agent in self._agents.items():
            stats.append({
                "name": agent.name,
                "task_type": key,
                "model": agent.model_name,
                "metrics": agent.performance_metrics,
            })
        stats.append({
            "name": self._general.name,
            "task_type": "general",
            "model": self._general.model_name,
            "metrics": self._general.performance_metrics,
        })
        return stats

    def get_queue_stats(self) -> Dict[str, Any]:
        return {
            "queued": self.queue.size,
            "completed": len(self._completed),
            "tasks": self.queue.all_tasks(),
        }


# ---------- Global singleton ----------
_orchestrator_instance: Optional[AgentOrchestrator] = None
_orch_lock = threading.Lock()


def get_orchestrator(
    respond_func: Optional[Callable] = None,
    tool_hub: Optional[Any] = None,
) -> AgentOrchestrator:
    global _orchestrator_instance
    with _orch_lock:
        if _orchestrator_instance is None:
            _orchestrator_instance = AgentOrchestrator(respond_func=respond_func, tool_hub=tool_hub)
        elif respond_func and _orchestrator_instance._respond_func is None:
            _orchestrator_instance._respond_func = respond_func
    return _orchestrator_instance


__all__ = [
    "BaseAgent",
    "CodeAgent",
    "PlanningAgent",
    "GeneralAgent",
    "TaskQueue",
    "TaskRouter",
    "AgentOrchestrator",
    "QueuedTask",
    "TASK_MODEL_MAP",
    "get_orchestrator",
]
