import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("webapp.orchestrator")


class TaskType(Enum):
    CODE_GENERATION = "code_generation"
    CODE_ANALYSIS = "code_analysis"
    PLANNING = "planning"
    DEBUGGING = "debugging"
    TESTING = "testing"
    OPTIMIZATION = "optimization"


@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: TaskType = TaskType.CODE_GENERATION
    prompt: str = ""
    priority: int = 5
    timeout: int = 120
    retry_count: int = 3
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


KEYWORDS_MAP: Dict[TaskType, List[str]] = {
    TaskType.CODE_GENERATION: [
        "kod yoz", "code", "function", "script", "class",
        "yoz", "create", "generate", "implement", "funksiya",
        "dastur", "program", "build", "api", "backend", "frontend",
    ],
    TaskType.CODE_ANALYSIS: [
        "tahlil", "analyze", "review", "check", "bug",
        "tekshir", "kod tahlil", "code review", "inspect",
        "audit", "security", "vulnerability", "quality",
    ],
    TaskType.PLANNING: [
        "reja", "plan", "strategiya", "bosqich", "qanday boshlash",
        "strategy", "roadmap", "schedule", "loyiha", "vazifa",
        "task list", "milestone", "sprint",
    ],
    TaskType.DEBUGGING: [
        "xato", "debug", "error", "fix", "tuzat",
        "exception", "traceback", "crash", "noto'g'ri",
        "ishlamayapti", "failed", "stack trace", "muammo",
    ],
    TaskType.TESTING: [
        "test", "unit test", "integration", "tekshir",
        "pytest", "unittest", "sinov", "coverage",
        "assert", "mock", "testing", "ci/cd",
    ],
    TaskType.OPTIMIZATION: [
        "optimize", "tez", "fast", "performance", "efficient",
        "optimallashtir", "tezlik", "optimization", "refactor",
        "scalability", "cache", "memory", "latency", "throughput",
    ],
}


class Orchestrator:
    def __init__(self):
        self._agents: Dict[str, Any] = {}
        self._active_tasks: Dict[str, Task] = {}
        self._completed_tasks: Dict[str, Task] = {}
        self._task_counter = 0

    def register_agent(self, agent_type: str, agent: Any) -> None:
        self._agents[agent_type] = agent
        logger.info(f"[Orchestrator] Agent registered: {agent_type}")

    def _detect_task_type(self, prompt: str) -> TaskType:
        norm = prompt.lower()
        scores = {tt: 0 for tt in TaskType}
        total_matches = 0

        for tt, kws in KEYWORDS_MAP.items():
            for kw in kws:
                if kw in norm:
                    scores[tt] += 1
                    total_matches += 1

        if total_matches == 0:
            return TaskType.CODE_GENERATION

        best = max(scores, key=lambda t: (scores[t], list(TaskType).index(t)))
        return best

    def route_task(self, task: Task) -> Dict[str, Any]:
        start = time.time()
        task_type_name = task.type.value

        if task_type_name in self._agents:
            agent = self._agents[task_type_name]
        else:
            fallback_order = [
                TaskType.CODE_GENERATION,
                TaskType.CODE_ANALYSIS,
                TaskType.PLANNING,
            ]
            agent = None
            for fb in fallback_order:
                if fb.value in self._agents:
                    agent = self._agents[fb.value]
                    break
            if not agent and self._agents:
                agent = list(self._agents.values())[0]

        if agent is None:
            return {
                "task_id": task.id,
                "status": "error",
                "agent": None,
                "result": {"error": "No available agents"},
                "execution_time": round(time.time() - start, 2),
            }

        elapsed = 0.0
        last_error = None
        for attempt in range(max(1, task.retry_count + 1)):
            try:
                if hasattr(agent, "process"):
                    result = agent.process(task)
                else:
                    result = agent(task)

                self._completed_tasks[task.id] = task
                self._active_tasks.pop(task.id, None)
                elapsed = round(time.time() - start, 2)
                return {
                    "task_id": task.id,
                    "status": "success",
                    "agent": type(agent).__name__,
                    "result": result,
                    "execution_time": elapsed,
                }
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"[Orchestrator] Attempt {attempt + 1} failed for {task.id}: {e}"
                )
                if attempt < task.retry_count:
                    time.sleep(1)

        self._active_tasks.pop(task.id, None)
        elapsed = round(time.time() - start, 2)
        return {
            "task_id": task.id,
            "status": "error",
            "agent": type(agent).__name__ if agent else None,
            "result": {"error": last_error or "Unknown error"},
            "execution_time": elapsed,
        }

    def execute_with_fallback(self, task: Task) -> Dict[str, Any]:
        return self.route_task(task)

    async def async_route_task(self, task: Task) -> Dict[str, Any]:
        """Async wrapper — agent layer bilan birga ishlash uchun."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.route_task, task)

    def get_status(self) -> Dict[str, Any]:
        return {
            "active_tasks": len(self._active_tasks),
            "completed_tasks": len(self._completed_tasks),
            "queue_size": 0,
            "agents_registered": len(self._agents),
            "agents": list(self._agents.keys()),
        }
