import json
import logging
import threading
import time
import urllib.request
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger("webapp.agents")

# ── Task Types ────────────────────────────────────────────────────────────

class TaskType(Enum):
    CODE = "code"
    PLAN = "plan"
    DEBUG = "debug"
    TEST = "test"
    GENERAL = "general"
    FAST = "fast"


TASK_MODEL_MAP = {
    TaskType.CODE: {
        "primary": "qwen2.5:3b",
        "fallbacks": ["codellama:34b", "qwen2.5-coder:7b", "deepseek-coder:6.7b"],
        "description": "Kod generatsiyasi va dasturlash",
    },
    TaskType.PLAN: {
        "primary": "qwen2.5:3b",
        "fallbacks": ["llama2:13b", "mistral:7b", "llama3:8b"],
        "description": "Rejalashtirish va strategiya",
    },
    TaskType.DEBUG: {
        "primary": "qwen2.5:3b",
        "fallbacks": ["codellama:13b", "deepseek-coder:6.7b"],
        "description": "Xatolik tahlili va tuzatish",
    },
    TaskType.TEST: {
        "primary": "qwen2.5:3b",
        "fallbacks": ["codellama:13b", "qwen2.5-coder:7b"],
        "description": "Test yozish va sifat tekshiruvi",
    },
    TaskType.GENERAL: {
        "primary": "qwen2.5:3b",
        "fallbacks": ["llama3:8b", "mistral:7b"],
        "description": "Umumiy savol-javob",
    },
    TaskType.FAST: {
        "primary": "qwen2.5:3b",
        "fallbacks": ["gemma:7b", "phi3:mini"],
        "description": "Tez javob va oddiy so'rovlar",
    },
}


@dataclass
class Task:
    id: str
    prompt: str
    task_type: TaskType
    priority: int  # 1=HIGH, 2=MEDIUM, 3=LOW
    memory: list = field(default_factory=list)
    system_prompt: str = ""
    status: str = "pending"
    result: str = ""
    error: str = ""
    created_at: float = 0.0
    started_at: float = 0.0
    completed_at: float = 0.0

    @property
    def duration(self) -> float:
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        return 0.0


# ── Task Router ───────────────────────────────────────────────────────────

CODE_KEYWORDS = [
    "kod", "code", "funksiya", "function", "dastur", "program",
    "yoz", "create", "generate", "build", "implement", "python",
    "javascript", "typescript", "html", "css", "sql", "api",
    "backend", "frontend", "react", "django", "class", "oop",
    "algorithm", "algoritm", "script", "snippet",
]

PLAN_KEYWORDS = [
    "reja", "plan", "strategiya", "strategy", "bosqich", "step",
    "roadmap", "yo'l xarita", "qanday boshlash", "tahil qil",
    "qilish kerak", "nima qil", "loyiha", "project plan",
    "schedule", "jadval", "vazifa", "task list",
]

DEBUG_KEYWORDS = [
    "xato", "bug", "error", "exception", "traceback", "tuzat",
    "fix", "debug", "noto'g'ri", "ishlamayapti", "failed",
    "crash", "stack trace", "log", "hatolik", "muammo",
]

TEST_KEYWORDS = [
    "test", "unit test", "integration test", "pytest", "unittest",
    "sinov", "tekshir", "quality", "coverage", "assert",
    "mock", "testing", "ci/cd", "continuous integration",
]


class TaskRouter:
    def __init__(self):
        self.task_counter = 0
        self._lock = threading.Lock()

    def detect_task_type(self, prompt: str) -> TaskType:
        norm = prompt.lower()
        scores = {tt: 0 for tt in TaskType}

        for kw in CODE_KEYWORDS:
            if kw in norm:
                scores[TaskType.CODE] += 1
        for kw in PLAN_KEYWORDS:
            if kw in norm:
                scores[TaskType.PLAN] += 1
        for kw in DEBUG_KEYWORDS:
            if kw in norm:
                scores[TaskType.DEBUG] += 1
        for kw in TEST_KEYWORDS:
            if kw in norm:
                scores[TaskType.TEST] += 1

        max_type = max(scores, key=scores.get)
        max_score = scores[max_type]

        if max_score >= 2:
            return max_type
        if max_score == 1:
            if len(norm.split()) <= 5:
                return TaskType.FAST
            return max_type

        if len(norm.split()) <= 3:
            return TaskType.FAST
        return TaskType.GENERAL

    def assess_priority(self, prompt: str, task_type: TaskType) -> int:
        norm = prompt.lower()
        urgent = ["tez", "urgent", "zudlik", "shoshilinch", "critical",
                   "darhol", "hozir", "tezda", "quick", "asap"]
        if any(u in norm for u in urgent):
            return 1
        if task_type in (TaskType.DEBUG, TaskType.TEST):
            return 1 if any(u in norm for u in ["critical", "crash", "failed"]) else 2
        if task_type in (TaskType.CODE, TaskType.PLAN):
            return 2
        return 3

    def create_task(self, prompt: str, memory: list = None,
                    system_prompt: str = "") -> Task:
        task_type = self.detect_task_type(prompt)
        priority = self.assess_priority(prompt, task_type)
        with self._lock:
            self.task_counter += 1
            task_id = f"task-{int(time.time())}-{self.task_counter}"
        return Task(
            id=task_id,
            prompt=prompt,
            task_type=task_type,
            priority=priority,
            memory=memory or [],
            system_prompt=system_prompt,
            created_at=time.time(),
        )

    def route(self, task: Task, agents: dict[TaskType, Any]) -> Any | None:
        agent = agents.get(task.task_type)
        if agent and agent.is_available():
            return agent
        for tt in [TaskType.GENERAL]:
            fallback = agents.get(tt)
            if fallback and fallback.is_available():
                return fallback
        return None


# ── Priority Queue ────────────────────────────────────────────────────────

class PriorityQueue:
    def __init__(self):
        self._tasks: list[Task] = []
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)

    def push(self, task: Task):
        with self._lock:
            self._tasks.append(task)
            self._tasks.sort(key=lambda t: (t.priority, t.created_at))
            self._cond.notify()

    def pop(self, timeout: float = 5.0) -> Task | None:
        deadline = time.time() + timeout
        with self._lock:
            while not self._tasks:
                remaining = deadline - time.time()
                if remaining <= 0:
                    return None
                self._cond.wait(timeout=remaining)
            if not self._tasks:
                return None
            task = self._tasks.pop(0)
            task.status = "processing"
            task.started_at = time.time()
            return task

    def peek(self) -> Task | None:
        with self._lock:
            return self._tasks[0] if self._tasks else None

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._tasks)

    def remove(self, task_id: str) -> bool:
        with self._lock:
            for i, t in enumerate(self._tasks):
                if t.id == task_id:
                    self._tasks.pop(i)
                    return True
        return False


# ── Base Agent ────────────────────────────────────────────────────────────

class BaseAgent:
    name = "base"
    task_type = TaskType.GENERAL

    def __init__(self, respond_func: Callable = None,
                 model_name: str = "qwen2.5:3b"):
        self.respond_func = respond_func
        self.model_name = model_name
        self._busy = False
        self.task_count = 0
        self.error_count = 0
        self.total_duration = 0.0

    def is_available(self) -> bool:
        return not self._busy

    def _call_llm(self, prompt: str, memory: list,
                  system_prompt: str) -> str:
        if self.respond_func:
            try:
                return self.respond_func(prompt, memory, system_prompt)
            except Exception as e:
                logger.warning(f"[{self.name}] LLM xatosi: {e}")
                raise
        raise RuntimeError("respond_func mavjud emas")

    def process(self, task: Task) -> str:
        self._busy = True
        self.task_count += 1
        try:
            system = task.system_prompt or self._build_system_prompt(task)
            result = self._call_llm(task.prompt, task.memory, system)
            task.result = result
            task.status = "completed"
            task.completed_at = time.time()
            self.total_duration += task.duration
            return result
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            self.error_count += 1
            raise
        finally:
            self._busy = False

    def _build_system_prompt(self, task: Task) -> str:
        return (
            f"Sen {self.name} agentsan. {TASK_MODEL_MAP.get(self.task_type, {}).get('description', '')} "
            "O'zbek tilida javob ber. Aniq va foydali bo'l."
        )

    def stats(self) -> dict:
        return {
            "name": self.name,
            "task_type": self.task_type.value,
            "busy": self._busy,
            "task_count": self.task_count,
            "error_count": self.error_count,
            "total_duration_sec": round(self.total_duration, 2),
            "model": self.model_name,
        }


class CodeAgent(BaseAgent):
    name = "code"
    task_type = TaskType.CODE

    def _build_system_prompt(self, task: Task) -> str:
        return (
            "Sen professional dasturchi agentsan. "
            "Vazifa: foydalanuvchi so'ragan kodni to'liq va ishlaydigan holatda yozish. "
            "Multi-language support: Python, JS, TS, HTML, CSS, SQL, Go, Rust, Java, C++. "
            "Error handling, input validation, va eng yaxshi amaliyotlarni qo'lla. "
            "Kodni ```lang ... ``` blokiga o'rab ber. "
            "O'zbek tilida tushuntir, kod esa ingliz tilida bo'lsin."
        )


class PlanAgent(BaseAgent):
    name = "plan"
    task_type = TaskType.PLAN

    def _build_system_prompt(self, task: Task) -> str:
        return (
            "Sen strategik rejalashtirish agentsan. "
            "Vazifa: bosqichma-bosqich reja tuzish, resurslarni baholash, "
            "xavflarni aniqlash, vaqt jadvalini belgilash. "
            "Har bir bosqichni aniq va batafsil tushuntir. "
            "O'zbek tilida javob ber."
        )


class DebugAgent(BaseAgent):
    name = "debug"
    task_type = TaskType.DEBUG

    def _build_system_prompt(self, task: Task) -> str:
        return (
            "Sen debug agentsan. "
            "Vazifa: xatolikni tahlil qilish, sababini aniqlash va tuzatish yo'lini ko'rsatish. "
            "Stack trace, error message, va kod kontekstini tahlil qil. "
            "Muammo sababi, yechim, va oldini olish choralarini ko'rsat. "
            "O'zbek tilida javob ber."
        )


class TestAgent(BaseAgent):
    name = "test"
    task_type = TaskType.TEST

    def _build_system_prompt(self, task: Task) -> str:
        return (
            "Sen test agentsan. "
            "Vazifa: unit testlar, integration testlar, edge-case testlar yozish. "
            "pytest, unittest, jest, mocha kabi frameworklardan foydalan. "
            "Test coverage, mock, assertionlarni to'liq qamrab ol. "
            "Kodni ```lang ... ``` blokiga o'rab ber. "
            "O'zbek tilida tushuntir."
        )


# ── Agent Orchestrator ────────────────────────────────────────────────────

class AgentOrchestrator:
    def __init__(self, respond_func: Callable = None):
        self.respond_func = respond_func
        self.router = TaskRouter()
        self.queue = PriorityQueue()

        self._agents: dict[TaskType, BaseAgent] = {
            TaskType.CODE: CodeAgent(respond_func, model_name="qwen2.5:3b"),
            TaskType.PLAN: PlanAgent(respond_func, model_name="qwen2.5:3b"),
            TaskType.DEBUG: DebugAgent(respond_func, model_name="qwen2.5:3b"),
            TaskType.TEST: TestAgent(respond_func, model_name="qwen2.5:3b"),
            TaskType.GENERAL: BaseAgent(respond_func, model_name="qwen2.5:3b"),
            TaskType.FAST: BaseAgent(respond_func, model_name="qwen2.5:3b"),
        }

        self._auto_assign_model_names()
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._running = True
        self._worker_thread.start()
        logger.info("[AgentOrchestrator] ishga tushdi — 6 agent, priority queue")

    def _auto_assign_model_names(self):
        try:
            req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                available = [m["name"] for m in data.get("models", [])]
        except Exception:
            available = []

        for tt, cfg in TASK_MODEL_MAP.items():
            agent = self._agents.get(tt)
            if not agent:
                continue
            for candidate in [cfg["primary"]] + cfg["fallbacks"]:
                if any(candidate in av for av in available):
                    agent.model_name = candidate
                    break
            if available and not any(candidate in str(available) for candidate in [cfg["primary"]] + cfg["fallbacks"]):
                agent.model_name = available[0]

    def submit(self, prompt: str, memory: list = None,
               system_prompt: str = "") -> Task:
        task = self.router.create_task(prompt, memory, system_prompt)
        self.queue.push(task)
        logger.info(f"[Orchestrator] +{task.id} ({task.task_type.value}, pri={task.priority})")
        return task

    def submit_and_wait(self, prompt: str, memory: list = None,
                        system_prompt: str = "", timeout: float = 120.0) -> str:
        task = self.submit(prompt, memory, system_prompt)
        deadline = time.time() + timeout
        while time.time() < deadline:
            if task.status in ("completed", "failed"):
                if task.status == "completed":
                    return task.result
                raise RuntimeError(f"Agent xatosi: {task.error}")
            time.sleep(0.1)
        raise TimeoutError(f"Task {task.id} {timeout}s da tugamadi")

    def process_sync(self, prompt: str, memory: list = None,
                     system_prompt: str = "", task_type: TaskType = None) -> str:
        task = self.router.create_task(prompt, memory, system_prompt)
        if task_type:
            task.task_type = task_type
        agent = self.router.route(task, self._agents)
        if not agent:
            agent = self._agents[TaskType.GENERAL]
        return agent.process(task)

    def _worker_loop(self):
        while self._running:
            try:
                task = self.queue.pop(timeout=2.0)
                if not task:
                    continue
                agent = self.router.route(task, self._agents)
                if not agent:
                    agent = self._agents[TaskType.GENERAL]
                agent.process(task)
            except Exception as e:
                logger.error(f"[Orchestrator] worker xatosi: {e}")

    def get_agent_stats(self) -> dict:
        return {tt.value: agent.stats() for tt, agent in self._agents.items()}

    def get_queue_stats(self) -> dict:
        return {"queue_size": self.queue.size}

    def stop(self):
        self._running = False


_orchestrator_instance = None

def get_orchestrator(respond_func: Callable = None) -> AgentOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AgentOrchestrator(respond_func)
    return _orchestrator_instance
