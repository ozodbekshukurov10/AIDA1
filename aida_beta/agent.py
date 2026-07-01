"""AIDA Beta Agent — fully integrated from all webapp agent patterns."""
from __future__ import annotations

import sys, json, time, ast, re, uuid, threading
from typing import List, Dict, Optional, Tuple, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from io import StringIO

sys.stdout.reconfigure(encoding='utf-8', errors='replace') if hasattr(sys.stdout, 'reconfigure') else None

try:
    from .tools import execute, get_schemas, set_work_dir, TOOLS, Tool
    from .memory import AidaBetaMemory
except ImportError:
    from tools import execute, get_schemas, set_work_dir, TOOLS, Tool
    from memory import AidaBetaMemory

OLLAMA_URL = "http://localhost:11434"
LM_STUDIO_URL = "http://localhost:1234"
MODEL_NAME = "aida-beta:latest"
LM_MODEL_NAME = "qwen/qwen2.5-coder-14b"
MAX_ITERATIONS = 25
MAX_TOOL_RETRIES = 2

# ─── Task Type System ────────────────────────────────────────────────────

class TaskType(Enum):
    CODE = "code"
    PLAN = "plan"
    DEBUG = "debug"
    TEST = "test"
    GENERAL = "general"
    FAST = "fast"
    OPTIMIZE = "optimize"
    EXPLAIN = "explain"

TASK_MODEL_MAP: Dict[TaskType, Dict] = {
    TaskType.CODE: {"primary": "qwen2.5:3b", "desc": "Kod generatsiyasi"},
    TaskType.PLAN: {"primary": "qwen2.5:3b", "desc": "Rejalashtirish"},
    TaskType.DEBUG: {"primary": "qwen2.5:3b", "desc": "Xatolik tahlili"},
    TaskType.TEST: {"primary": "qwen2.5:3b", "desc": "Test yozish"},
    TaskType.GENERAL: {"primary": "qwen2.5:3b", "desc": "Umumiy savol"},
    TaskType.FAST: {"primary": "qwen2.5:3b", "desc": "Tez javob"},
    TaskType.OPTIMIZE: {"primary": "qwen2.5:3b", "desc": "Optimizatsiya"},
    TaskType.EXPLAIN: {"primary": "qwen2.5:3b", "desc": "Tushuntirish"},
}

TASK_KEYWORDS: Dict[str, List[str]] = {
    "code": ["kod yoz", "code", "function", "class", "yoz", "create", "implement",
             "funksiya", "dastur", "api", "backend", "frontend", "python", "javascript",
             "typescript", "django", "react", "script", "snippet", "algorithm"],
    "debug": ["xato", "bug", "error", "exception", "traceback", "tuzat", "fix",
              "debug", "notogri", "ishlamayapti", "failed", "crash", "stack trace"],
    "plan": ["reja", "plan", "strategiya", "bosqich", "roadmap", "loyiha",
             "vazifa", "strategy", "schedule", "milestone", "task list"],
    "test": ["test", "unit test", "pytest", "unittest", "sinov", "tekshir",
             "coverage", "assert", "mock", "testing", "ci/cd"],
    "optimize": ["optimize", "tez", "fast", "performance", "optimallashtir",
                 "tezlik", "refactor", "cache", "refactoring"],
    "explain": ["tushuntir", "explain", "nima", "qanday ishlaydi", "what is",
                "how does", "nimaga", "sabab"],
}

# ─── Permission System ──────────────────────────────────────────────────

class PermissionLevel(Enum):
    ALWAYS_ASK = "always_ask"
    ALWAYS_ALLOW = "always_allow"
    NEVER_ALLOW = "never_allow"
    GROUP = "group"
    CHAT = "chat"

class ExecutionMode(Enum):
    PLAN = "plan"
    AUTO = "auto"
    APPROVE = "approve"

MODIFY_TOOLS = {"write", "edit", "patch", "apply_patch"}
DANGEROUS_TOOLS = {"run", "python_exec", "mcp_call"}

class PermissionManager:
    def __init__(self, mode: ExecutionMode = ExecutionMode.AUTO,
                 permission_callback: Optional[Callable] = None):
        self.mode = mode
        self._permission_callback = permission_callback
        self._tool_rules: Dict[str, PermissionLevel] = {}
        self._always_allow_tools: set = set()
        self._never_allow_tools: set = set()

    def set_rule(self, tool_name: str, level: PermissionLevel):
        self._tool_rules[tool_name] = level

    def set_mode(self, mode: ExecutionMode):
        self.mode = mode

    def check(self, tool_name: str, args: Dict) -> bool:
        rule = self._tool_rules.get(tool_name)
        if rule == PermissionLevel.NEVER_ALLOW:
            return False
        if rule == PermissionLevel.ALWAYS_ALLOW:
            return True
        if self.mode == ExecutionMode.AUTO:
            if tool_name in MODIFY_TOOLS:
                return self._ask(f"{tool_name} ({json.dumps(args)[:100]}) ruxsat?")
            return True
        if self.mode == ExecutionMode.PLAN:
            return False
        if self.mode == ExecutionMode.APPROVE:
            return self._ask(f"{tool_name} ({json.dumps(args)[:100]}) ruxsat?")
        return True

    def _ask(self, question: str) -> bool:
        if self._permission_callback:
            return self._permission_callback(question)
        return True

# ─── Hook System (Claude Code pattern: event + matcher) ──────────────────

class HookEvent(Enum):
    PRE_TOOL = "pre_tool"
    POST_TOOL = "post_tool"
    PRE_TASK = "pre_task"
    POST_TASK = "post_task"
    ON_ERROR = "on_error"
    ON_REFLECTION = "on_reflection"
    ON_COMPACT = "on_compact"
    SESSION_START = "session_start"
    USER_PROMPT = "user_prompt"
    STOP = "stop"

HookFunc = Callable[..., None]

@dataclass
class HookHandler:
    func: HookFunc
    matcher: str = "*"
    async_rewake: bool = False
    rewake_message: str = ""

class HookManager:
    def __init__(self):
        self._hooks: Dict[HookEvent, List[HookHandler]] = {e: [] for e in HookEvent}

    def register(self, event: HookEvent, func: HookFunc,
                 matcher: str = "*", async_rewake: bool = False,
                 rewake_message: str = ""):
        self._hooks[event].append(HookHandler(
            func=func, matcher=matcher,
            async_rewake=async_rewake, rewake_message=rewake_message
        ))

    def trigger(self, event: HookEvent, matcher_context: str = "", **kwargs):
        for handler in self._hooks[event]:
            if handler.matcher == "*":
                matched = True
            elif handler.matcher.startswith("!"):
                matched = matcher_context != handler.matcher[1:]
            else:
                import fnmatch
                matched = any(
                    fnmatch.fnmatch(matcher_context, p)
                    for p in handler.matcher.split("|")
                )
            if not matched:
                continue
            try:
                handler.func(**kwargs)
            except Exception:
                pass

# ─── Security Patterns (Claude Code security-guidance pattern) ──────────

SECURITY_PATTERNS = [
    {
        "name": "hardcoded-secret",
        "regex": r'(?i)(password|secret|api[-_]?key|token|auth)[\s]*[:=][\s]*["\'][^"\']+["\']',
        "reminder": "Hardcoded credentials aniqlendi. Environment variable yoki .env faylidan o'qishni tavsiya etamiz."
    },
    {
        "name": "sql-injection",
        "regex": r'(?i)(execute|exec|query)\([^)]*\+[^)]*\)',
        "reminder": "SQL injection xavfi. Parametrized query yoki ORM ishlating."
    },
    {
        "name": "command-injection",
        "regex": r'(?i)(subprocess\.call|os\.system|os\.popen)\s*\(',
        "reminder": "Command injection xavfi. subprocess.run() ni shell=False bilan ishlating."
    },
    {
        "name": "eval-usage",
        "regex": r'(?i)\b(eval|exec)\s*\(',
        "reminder": "eval/exec xavfsiz emas. Xavfsiz alternativ ishlating."
    },
    {
        "name": "pickle-unsafe",
        "regex": r'(?i)pickle\.(loads?|load)',
        "reminder": "pickle deserialization xavfli. JSON yoki saf format ishlating."
    },
]

def check_security(content: str, file_path: str = "") -> List[Dict]:
    results = []
    for p in SECURITY_PATTERNS:
        try:
            if re.search(p["regex"], content):
                results.append({"name": p["name"], "reminder": p["reminder"]})
        except Exception:
            pass
    return results

# ─── Data Classes ────────────────────────────────────────────────────────

@dataclass
class ToolResult:
    success: bool
    output: str
    error: str = ""
    data: Any = None

@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str = ""
    task_type: TaskType = TaskType.CODE
    priority: int = 5
    timeout: int = 120
    retry_count: int = 3
    memory: List[Dict] = field(default_factory=list)
    system_prompt: str = ""
    status: str = "pending"
    result: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0

    @property
    def duration(self) -> float:
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        return 0.0

# ─── Task Router ─────────────────────────────────────────────────────────

def detect_task_type(prompt: str) -> str:
    norm = prompt.lower()
    scores = {t: 0 for t in TASK_KEYWORDS}
    for ttype, kws in TASK_KEYWORDS.items():
        for kw in kws:
            if kw in norm:
                scores[ttype] += 1
    if max(scores.values()) == 0:
        if len(norm.split()) <= 3:
            return "fast"
        return "general"
    return max(scores, key=scores.__getitem__)

def assess_priority(prompt: str, task_type: str) -> int:
    norm = prompt.lower()
    urgent = ["tez", "urgent", "zudlik", "shoshilinch", "critical",
              "darhol", "hozir", "tezda", "quick", "asap"]
    if any(u in norm for u in urgent):
        return 1
    if task_type in ("debug", "test"):
        return 2
    return 3

def create_task(prompt: str, task_type: TaskType = None) -> Task:
    ttype_str = detect_task_type(prompt)
    ttype = task_type or TaskType(ttype_str)
    priority = assess_priority(prompt, ttype_str)
    return Task(prompt=prompt, task_type=ttype, priority=priority)

# ─── Priority Queue ──────────────────────────────────────────────────────

class PriorityQueue:
    def __init__(self):
        self._tasks: List[Task] = []
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)

    def push(self, task: Task):
        with self._lock:
            self._tasks.append(task)
            self._tasks.sort(key=lambda t: (t.priority, t.created_at))
            self._cond.notify()

    def pop(self, timeout: float = 5.0) -> Optional[Task]:
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

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._tasks)

    def all(self) -> List[Dict]:
        with self._lock:
            return [{"id": t.id, "type": t.task_type.value, "status": t.status,
                     "priority": t.priority} for t in self._tasks]

# ─── LLM Client ──────────────────────────────────────────────────────────

class LLMClient:
    def __init__(self, use_lmstudio: Optional[bool] = None):
        if use_lmstudio is None:
            use_lmstudio = self._detect_lmstudio()
        self._use_lmstudio = use_lmstudio
        self._static_prompt_cache: Dict[str, str] = {}

    def _detect_lmstudio(self) -> bool:
        import urllib.request
        try:
            with urllib.request.urlopen(f"{LM_STUDIO_URL}/v1/models", timeout=2) as r:
                return True
        except Exception:
            return False

    def _mk_req(self, payload: dict) -> urllib.request.Request:
        import urllib.request
        return urllib.request.Request(
            payload.pop("_url"),
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )

    def _call(self, messages: List[Dict], tools: Optional[List[Dict]] = None,
              stream: bool = False) -> Any:
        import urllib.request
        if self._use_lmstudio:
            payload = {
                "_url": f"{LM_STUDIO_URL}/v1/chat/completions",
                "model": LM_MODEL_NAME,
                "messages": messages,
                "stream": stream,
                "temperature": 0.2,
                "max_tokens": 4096,
            }
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"
        else:
            payload = {
                "_url": f"{OLLAMA_URL}/api/chat",
                "model": MODEL_NAME,
                "messages": messages,
                "stream": stream,
                "options": {"temperature": 0.2, "num_predict": 4096, "num_ctx": 16384},
            }
            if tools:
                payload["tools"] = tools
        req = self._mk_req(payload)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    if stream:
                        return resp
                    data = json.loads(resp.read())
                    if self._use_lmstudio:
                        return {"_lmstudio": True, "_data": data}
                    return data
            except Exception as e:
                if attempt == 2:
                    return {"error": str(e)}
                time.sleep(1)
        return {"error": "Max retries"}

    def chat(self, messages: List[Dict]) -> str:
        result = self._call(messages)
        if "error" in result:
            return f"[LLM Error] {result['error']}"
        if result.get("_lmstudio"):
            choices = result["_data"].get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return ""
        return result.get("message", {}).get("content", "")

    def _parse_tool_calls(self, msg: dict) -> list:
        raw = msg.get("tool_calls", [])
        result = []
        for tc in raw:
            func = tc.get("function", tc)
            name = func.get("name", "")
            args_raw = func.get("arguments", {})
            if isinstance(args_raw, str):
                try:
                    args_raw = json.loads(args_raw)
                except json.JSONDecodeError:
                    args_raw = {}
            result.append({"function": {"name": name, "arguments": args_raw}})
        return result

    def chat_with_tools(self, messages: List[Dict]) -> Tuple[str, List[Dict]]:
        schemas = get_schemas()
        result = self._call(messages, schemas)
        if "error" in result:
            return f"[LLM Error] {result['error']}", []
        if result.get("_lmstudio"):
            choices = result["_data"].get("choices", [])
            if not choices:
                return "", []
            msg = choices[0].get("message", {})
            return msg.get("content", ""), self._parse_tool_calls(msg)
        msg = result.get("message", {})
        return msg.get("content", ""), msg.get("tool_calls", [])

    def chat_with_tools_stream(self, messages: List[Dict]):
        schemas = get_schemas()
        resp = self._call(messages, schemas, stream=True)
        if resp is None:
            yield ("token", "[LLM Error] Stream failed")
            return
        full_content = ""
        all_tool_calls = []
        try:
            for line in resp:
                if not line:
                    continue
                try:
                    decoded = line.decode().strip()
                    if self._use_lmstudio:
                        if decoded.startswith("data: "):
                            decoded = decoded[6:]
                        if decoded == "[DONE]":
                            break
                        chunk = json.loads(decoded)
                        choices = chunk.get("choices", [])
                        for c in choices:
                            delta = c.get("delta", {})
                            content = delta.get("content", "")
                            tc = delta.get("tool_calls", [])
                            if content:
                                full_content += content
                                yield ("token", content)
                            if tc:
                                parsed = self._parse_tool_calls({"tool_calls": tc})
                                all_tool_calls.extend(parsed)
                                yield ("tool_calls", parsed)
                    else:
                        chunk = json.loads(decoded)
                        msg = chunk.get("message", {})
                        content = msg.get("content", "")
                        tc = msg.get("tool_calls", [])
                        if content:
                            full_content += content
                            yield ("token", content)
                        if tc:
                            all_tool_calls.extend(tc)
                            yield ("tool_calls", tc)
                        if chunk.get("done"):
                            break
                except Exception:
                    pass
        except Exception:
            pass
        yield ("done", (full_content, all_tool_calls))

    def chat_stream(self, messages: List[Dict]):
        resp = self._call(messages, stream=True)
        if resp is None:
            yield "[LLM Error] Stream failed"
            return
        try:
            for line in resp:
                if not line:
                    continue
                try:
                    decoded = line.decode().strip()
                    if self._use_lmstudio:
                        if decoded.startswith("data: "):
                            decoded = decoded[6:]
                        if decoded == "[DONE]":
                            return
                        chunk = json.loads(decoded)
                        for c in chunk.get("choices", []):
                            content = c.get("delta", {}).get("content", "")
                            if content:
                                yield content
                    else:
                        chunk = json.loads(decoded)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if chunk.get("done"):
                            return
                except Exception:
                    pass
        except Exception:
            pass

    def split_prompt_cache(self, messages: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        system_msgs = [m for m in messages if m["role"] == "system"]
        dynamic_msgs = [m for m in messages if m["role"] != "system"]
        return system_msgs, dynamic_msgs

# ─── Memory MD Support ──────────────────────────────────────────────────

class MemoryMD:
    def __init__(self, work_dir: Path):
        self.work_dir = work_dir
        self._files = {}

    def load(self) -> Dict[str, str]:
        for name in ["AGENTS.md", "MEMORY.md", "CLAUDE.md", ".aida/memory.md",
                      ".aida/AGENTS.md"]:
            p = self.work_dir / name
            if p.exists():
                try:
                    self._files[name] = p.read_text(encoding="utf-8")
                except Exception:
                    pass
        return dict(self._files)

    def get_summary(self) -> str:
        parts = []
        for name, content in self.load().items():
            lines = content.strip().splitlines()
            short = "\n".join(lines[:20])
            if len(lines) > 20:
                short += f"\n... ({len(lines) - 20} more lines)"
            parts.append(f"## {name}\n{short}")
        return "\n\n".join(parts) if parts else ""

    def save(self, name: str, content: str) -> bool:
        target = self.work_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self._files[name] = content
        return True

    def ensure_dir(self):
        (self.work_dir / ".aida").mkdir(parents=True, exist_ok=True)

# ─── Base Agent ──────────────────────────────────────────────────────────

class BaseAgent:
    name = "base"
    task_type = TaskType.GENERAL
    allowed_tools: List[str] = []
    forbidden_tools: List[str] = ["mcp_call"]

    def __init__(self, respond_func: Optional[Callable] = None,
                 model_name: str = MODEL_NAME):
        self.respond_func = respond_func
        self.model_name = model_name
        self._busy = False
        self.task_count = 0
        self.error_count = 0
        self.total_duration = 0.0

    def is_available(self) -> bool:
        return not self._busy

    def _build_system_prompt(self, task: Task) -> str:
        return (
            f"Sen {self.name} agentsan. "
            f"{TASK_MODEL_MAP.get(self.task_type, {}).get('desc', '')}. "
            "O'zbek tilida javob ber. Aniq va foydali bol."
        )

    def process(self, task: Task) -> str:
        self._busy = True
        self.task_count += 1
        try:
            system = task.system_prompt or self._build_system_prompt(task)
            msgs = [{"role": "system", "content": system}]
            for m in task.memory:
                msgs.append({"role": m["role"], "content": m["content"]})
            msgs.append({"role": "user", "content": task.prompt})
            result = self._call_llm(msgs)
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

    def _call_llm(self, messages: List[Dict]) -> str:
        if self.respond_func:
            try:
                return self.respond_func(messages)
            except Exception as e:
                raise RuntimeError(f"LLM xatosi: {e}")
        if not hasattr(self, '_client'):
            self._client = LLMClient()
        return self._client.chat(messages)

    def use_tool(self, tool_name: str, **kwargs) -> str:
        if tool_name in self.forbidden_tools:
            return f"[RUXSAT YOQ] {tool_name} bloklangan"
        if self.allowed_tools and tool_name not in self.allowed_tools:
            return f"[RUXSAT YOQ] {tool_name} ruxsat etilmagan"
        result = execute(tool_name, **kwargs)
        return result

    def stats(self) -> Dict:
        return {
            "name": self.name,
            "task_type": self.task_type.value,
            "busy": self._busy,
            "task_count": self.task_count,
            "error_count": self.error_count,
            "total_duration_sec": round(self.total_duration, 2),
        }

# ─── Specialized Agents ─────────────────────────────────────────────────

class CodeAgent(BaseAgent):
    name = "code"
    task_type = TaskType.CODE
    allowed_tools = ["read", "write", "edit", "patch", "apply_patch", "run",
                     "grep", "glob", "search", "lint", "context", "web_search",
                     "web_fetch", "http_request", "python_exec"]

    def _build_system_prompt(self, task: Task) -> str:
        return (
            "Sen professional dasturchi agentsan. "
            "Vazifa: foydalanuvchi soragan kodni to'liq va ishlaydigan holatda yozish. "
            "Python, JS, TS, HTML, CSS, SQL, Go, Rust, Java, C++. "
            "Error handling, input validation, best practices. "
            "Kodni ```lang ... ``` blokiga o'rab ber. "
            "O'zbek tilida tushuntir, kod ingliz tilida."
        )

    def analyze_code(self, code: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {"valid": False, "issues": [], "complexity": 0}
        if not code.strip():
            result["issues"].append("Empty code")
            return result
        try:
            tree = ast.parse(code)
            result["valid"] = True
        except SyntaxError as e:
            result["issues"].append(f"Syntax error: {e}")
            return result
        node_count = sum(1 for _ in ast.walk(tree))
        lines = code.strip().split("\n")
        avg_line_len = sum(len(l) for l in lines) / len(lines) if lines else 0
        if avg_line_len > 100:
            result["issues"].append("Lines too long (>100 chars)")
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                result["issues"].append("Bare except clause")
        result["complexity"] = min(node_count // 10, 10)
        return result

    def generate_tests(self, code: str) -> str:
        prompt = f"Ushbu kod uchun unit tests yoz (pytest):\nKOD:\n{code}\nTEST KOD:"
        msgs = [
            {"role": "system", "content": "Sen test yozuvchi agent. Faqat kod qaytar."},
            {"role": "user", "content": prompt}
        ]
        return self._call_llm(msgs)

    def auto_fix(self, code: str, issues: List[str]) -> str:
        if not issues:
            return code
        prompt = f"Quyidagi kodni tuzat. Muammolar: {json.dumps(issues)}\nKOD:\n{code}\nTUZATILGAN KOD:"
        msgs = [
            {"role": "system", "content": "Sen kod tuzatuvchi agent. Faqat kod qaytar."},
            {"role": "user", "content": prompt}
        ]
        return self._call_llm(msgs)

class PlanAgent(BaseAgent):
    name = "plan"
    task_type = TaskType.PLAN
    allowed_tools = ["read", "grep", "glob", "search", "context", "web_search"]

    def _build_system_prompt(self, task: Task) -> str:
        return (
            "Sen strategik rejalashtirish agentsan. "
            "Vazifa: bosqichma-bosqich reja tuzish, resurslarni baholash, "
            "xavflarni aniqlash, vaqt jadvalini belgilash. O'zbek tilida javob ber."
        )

class DebugAgent(BaseAgent):
    name = "debug"
    task_type = TaskType.DEBUG
    allowed_tools = ["read", "grep", "search", "run", "context",
                     "web_search", "python_exec"]

    def _build_system_prompt(self, task: Task) -> str:
        return (
            "Sen debug agentsan. "
            "Vazifa: xatolikni tahlil qilish, sababini aniqlash va tuzatish. "
            "Stack trace, error message, kod kontekstini tahlil qil. O'zbek tilida."
        )

class TestAgent(BaseAgent):
    name = "test"
    task_type = TaskType.TEST
    allowed_tools = ["read", "write", "edit", "patch", "run", "grep",
                     "glob", "search", "lint", "context", "python_exec"]

    def _build_system_prompt(self, task: Task) -> str:
        return (
            "Sen test agentsan. "
            "Vazifa: unit testlar, integration testlar, edge-case testlar. "
            "pytest, unittest, jest, mocha. Coverage, mock, assertion. O'zbek tilida."
        )

# ─── Main Agent (ReAct Loop) ────────────────────────────────────────────

class Agent(BaseAgent):
    def __init__(self, session_id: str = "default", mode: ExecutionMode = ExecutionMode.AUTO,
                 permission_callback: Optional[Callable] = None):
        super().__init__(model_name=MODEL_NAME)
        self.llm = LLMClient()
        self.memory_store = AidaBetaMemory()
        self.session_id = session_id
        self.thread_id = str(uuid.uuid4())
        self.plan: List[Dict] = []
        self.history: List[Dict] = []
        self.iteration = 0
        self.execution_log: List[str] = []
        self.code_history: List[Dict] = []
        self.performance: Dict[str, Any] = {
            "total_calls": 0, "success_count": 0, "error_count": 0,
            "avg_response_time": 0.0, "total_response_time": 0.0,
        }
        self.permission = PermissionManager(mode=mode, permission_callback=permission_callback)
        self.hooks = HookManager()
        self.memory_md = MemoryMD(Path.cwd())
        self._register_default_hooks()

    def _register_default_hooks(self):
        def log_pre_tool(tool_name="", args=None, **kw):
            self.execution_log.append(f"[PRE] {tool_name}({json.dumps(args)[:80]})")
        def log_post_tool(tool_name="", result="", **kw):
            self.execution_log.append(f"[POST] {tool_name}: {str(result)[:80]}")
        self.hooks.register(HookEvent.PRE_TOOL, log_pre_tool)
        self.hooks.register(HookEvent.POST_TOOL, log_post_tool)
        def save_on_post_task(prompt="", result="", **kw):
            self.memory_store.save("assistant", result[:500], self.session_id)
        self.hooks.register(HookEvent.POST_TASK, save_on_post_task)

    def run(self, user_input: str, work_dir: str = ".") -> str:
        set_work_dir(Path(work_dir).resolve())
        self.memory_md = MemoryMD(Path(work_dir).resolve())
        ttype_str = detect_task_type(user_input)

        self.history = [{"role": "system", "content": self._system_prompt()}]
        md_summary = self.memory_md.get_summary()
        if md_summary:
            self.history.append({
                "role": "system",
                "content": f"## Loyiha yodnomasi (CLAUDE.md / AGENTS.md / MEMORY.md)\n{md_summary}"
            })
        learned = self.memory_store.learned_facts(session_id=self.session_id)
        if learned:
            self.history.append({
                "role": "system",
                "content": "## Xotiradagi malumotlar:\n" + "\n".join(f"- {f}" for f in learned)
            })
        self.history.append({"role": "user", "content": user_input})
        self.iteration = 0
        self.execution_log = []
        self.memory_store.save("user", user_input, self.session_id)
        self.memory_store.save_thread_message(self.thread_id, "user", user_input,
                                               session_id=self.session_id)

        print(f"\n  --- Agent [{self.session_id}] [{ttype_str}] [{self.permission.mode.value}] ---\n")

        task = create_task(user_input)
        analysis = self._analyze_input(user_input)
        if analysis.get("complexity", 0) > 5:
            plan = self._generate_plan(user_input)
            if plan:
                print(f"  === REJA ===")
                for i, step in enumerate(plan, 1):
                    print(f"   {i}. {step.get('description', step)}")
                print()

        start_time = time.time()
        try:
            result = self._execute_loop()
            elapsed = time.time() - start_time
            self._record_performance(True, elapsed)
            self.memory_store.save("assistant", result[:500], self.session_id)
            self.memory_store.save_thread_message(self.thread_id, "assistant", result[:500],
                                                   session_id=self.session_id)
            self.hooks.trigger(HookEvent.POST_TASK, prompt=user_input, result=result)
            if ttype_str == "code":
                self.code_history.append({"prompt": user_input, "result": result[:200], "time": time.time()})
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            self._record_performance(False, elapsed)
            self.hooks.trigger(HookEvent.ON_ERROR, error=str(e))
            return f"[Xato] {e}"

    def run_stream(self, user_input: str, work_dir: str = "."):
        set_work_dir(Path(work_dir).resolve())
        self.memory_md = MemoryMD(Path(work_dir).resolve())
        ttype_str = detect_task_type(user_input)

        self.history = [{"role": "system", "content": self._system_prompt()}]
        md_summary = self.memory_md.get_summary()
        if md_summary:
            self.history.append({
                "role": "system",
                "content": f"## Loyiha yodnomasi (CLAUDE.md / AGENTS.md / MEMORY.md)\n{md_summary}"
            })
        learned = self.memory_store.learned_facts(session_id=self.session_id)
        if learned:
            self.history.append({
                "role": "system",
                "content": "## Xotiradagi malumotlar:\n" + "\n".join(f"- {f}" for f in learned)
            })
        self.history.append({"role": "user", "content": user_input})
        self.iteration = 0
        self.execution_log = []
        self.memory_store.save("user", user_input, self.session_id)
        self.memory_store.save_thread_message(self.thread_id, "user", user_input,
                                               session_id=self.session_id)

        yield ("status", f"Agent [{self.session_id}] [{ttype_str}] [{self.permission.mode.value}]")

        analysis = self._analyze_input(user_input)
        if analysis.get("complexity", 0) > 5:
            plan = self._generate_plan(user_input)
            if plan:
                for i, step in enumerate(plan, 1):
                    yield ("plan_step", f"{i}. {step.get('description', step)}")

        start_time = time.time()
        try:
            content_buffer = ""

            while self.iteration < MAX_ITERATIONS:
                self.iteration += 1
                thinking_buffer = ""
                pending_tool_calls = []

                for event_type, event_data in self.llm.chat_with_tools_stream(self.history):
                    if event_type == "token":
                        thinking_buffer += event_data
                        yield ("thinking", event_data)
                    elif event_type == "tool_calls":
                        pending_tool_calls.extend(event_data)
                    elif event_type == "done":
                        full_content, tool_calls = event_data
                        if full_content:
                            content_buffer = full_content
                        if tool_calls:
                            pending_tool_calls.extend(tool_calls)

                if thinking_buffer.strip():
                    self.history.append({"role": "assistant", "content": thinking_buffer})

                if not pending_tool_calls:
                    final = self._finalize(thinking_buffer or content_buffer)
                    yield ("result", final)
                    elapsed = time.time() - start_time
                    self._record_performance(True, elapsed)
                    self.hooks.trigger(HookEvent.POST_TASK, prompt=user_input, result=final)
                    return

                for tc in pending_tool_calls:
                    fn_name = tc.get("function", {}).get("name", "")
                    fn_args = tc.get("function", {}).get("arguments", {})
                    if isinstance(fn_args, str):
                        try:
                            fn_args = json.loads(fn_args)
                        except json.JSONDecodeError:
                            fn_args = {}

                    if not self.permission.check(fn_name, fn_args):
                        denied = f"[RUXSAT YOQ] {fn_name} bloklandi"
                        yield ("tool_result", fn_name, denied)
                        self.history.append({"role": "tool", "content": denied})
                        continue

                    if fn_name in ("write", "edit", "patch", "apply_patch"):
                        content = fn_args.get("content", "") or fn_args.get("new_string", "")
                        if content:
                            sec_issues = check_security(content, fn_args.get("path", ""))
                            if sec_issues:
                                warn = "; ".join(f"{i['name']}: {i['reminder']}" for i in sec_issues)
                                yield ("security", warn)
                                self.history.append({
                                    "role": "user",
                                    "content": f"Security ogohlantirish: {warn}"
                                })

                    yield ("tool_call", fn_name, fn_args)
                    self.hooks.trigger(HookEvent.PRE_TOOL, tool_name=fn_name, args=fn_args,
                                       matcher_context=fn_name)
                    result = self._execute_with_retry(fn_name, fn_args)
                    self.hooks.trigger(HookEvent.POST_TOOL, tool_name=fn_name, args=fn_args,
                                       result=result, matcher_context=fn_name)
                    yield ("tool_result", fn_name, result)

                    self.history.append({
                        "role": "assistant",
                        "content": thinking_buffer or content_buffer,
                        "tool_calls": [{
                            "function": {"name": fn_name, "arguments": fn_args}
                        }]
                    })
                    self.history.append({"role": "tool", "content": result})
                    self.execution_log.append(f"[{self.iteration}] {fn_name}: {result[:200]}")

                    if len(self.history) > 40:
                        self._compact_history()

                if self.iteration % 5 == 0:
                    reflection = self._reflection_check()
                    if reflection:
                        yield ("reflection", reflection)
                        self.history.append({
                            "role": "user",
                            "content": f"Tekshirish: {reflection}"
                        })

                content_buffer = ""
                thinking_buffer = ""

            yield ("result", "Maksimal iteratsiyaga yetildi.")

        except Exception as e:
            elapsed = time.time() - start_time
            self._record_performance(False, elapsed)
            self.hooks.trigger(HookEvent.ON_ERROR, error=str(e))
            yield ("error", str(e))

    def _execute_loop(self) -> str:
        while self.iteration < MAX_ITERATIONS:
            self.iteration += 1
            step_label = f"[{self.iteration}/{MAX_ITERATIONS}]"

            content, tool_calls = self.llm.chat_with_tools(self.history)

            if content and content.strip():
                print(f"  {step_label} {content[:300]}")
                self.history.append({"role": "assistant", "content": content})

            if not tool_calls:
                if content and content.strip():
                    return self._finalize(content)
                final = self.llm.chat(self.history)
                return self._finalize(final)

            for tc in tool_calls:
                fn_name = tc.get("function", {}).get("name", "")
                fn_args = tc.get("function", {}).get("arguments", {})
                if isinstance(fn_args, str):
                    try:
                        fn_args = json.loads(fn_args)
                    except json.JSONDecodeError:
                        fn_args = {}

                if not self.permission.check(fn_name, fn_args):
                    denied = f"[RUXSAT YOQ] {fn_name} bloklandi"
                    print(f"  {step_label} {denied}")
                    self.history.append({"role": "tool", "content": denied})
                    continue

                print(f"  {step_label} {fn_name}({json.dumps(fn_args)[:150]})")

                if fn_name in ("write", "edit", "patch", "apply_patch"):
                    content = fn_args.get("content", "") or fn_args.get("new_string", "")
                    if content:
                        issues = check_security(content, fn_args.get("path", ""))
                        if issues:
                            warn = "; ".join(f"{i['name']}: {i['reminder']}" for i in issues)
                            print(f"  {step_label} [SECURITY] {warn[:150]}")
                            self.history.append({
                                "role": "user",
                                "content": f"Security ogohlantirish: {warn}"
                            })

                self.hooks.trigger(HookEvent.PRE_TOOL, tool_name=fn_name, args=fn_args,
                                   matcher_context=fn_name)
                result = self._execute_with_retry(fn_name, fn_args)
                self.hooks.trigger(HookEvent.POST_TOOL, tool_name=fn_name, args=fn_args,
                                   result=result, matcher_context=fn_name)
                result_preview = result[:500].replace("\n", "\\n")
                print(f"  {step_label} {fn_name} -> {result_preview}")

                self.history.append({
                    "role": "assistant",
                    "content": content or "",
                    "tool_calls": [{
                        "function": {"name": fn_name, "arguments": fn_args}
                    }]
                })
                self.history.append({
                    "role": "tool",
                    "content": result,
                })
                self.execution_log.append(f"[{self.iteration}] {fn_name}: {result[:200]}")

                if len(self.history) > 40:
                    self._compact_history()

            if self.iteration % 5 == 0:
                reflection = self._reflection_check()
                if reflection:
                    print(f"  [Reflection] {reflection[:200]}")
                    self.hooks.trigger(HookEvent.ON_REFLECTION, reflection=reflection)
                    self.history.append({
                        "role": "user",
                        "content": f"Tekshirish: {reflection}"
                    })

        return self._finalize("Maksimal iteratsiyaga yetildi.")

    def _execute_with_retry(self, fn_name: str, fn_args: Dict) -> str:
        for attempt in range(MAX_TOOL_RETRIES + 1):
            result = execute(fn_name, **fn_args)
            if not result.startswith("[TOOL ERROR]") or attempt == MAX_TOOL_RETRIES:
                return result
            print(f"  [RETRY {attempt + 1}/{MAX_TOOL_RETRIES}] {fn_name} qayta urinilmoqda...")
            self.history.append({
                "role": "user",
                "content": f"Tool {fn_name} xato berdi: {result[:200]}. Qayta urin."
            })
        return result

    def _analyze_input(self, prompt: str) -> Dict[str, Any]:
        words = len(re.findall(r"\S+", prompt.strip()))
        complexity = min(max(int(words / 10), 1), 10)
        norm = prompt.lower()
        steps = []
        if any(kw in norm for kw in ["code", "kod", "function", "class", "yoz", "create"]):
            steps = ["Analyze requirements", "Design solution", "Implement code", "Test"]
        elif any(kw in norm for kw in ["debug", "xato", "error", "bug", "fix", "tuzat"]):
            steps = ["Reproduce error", "Find root cause", "Fix", "Verify"]
        elif any(kw in norm for kw in ["plan", "reja", "strategiya"]):
            steps = ["Define objectives", "Break down tasks", "Set timeline"]
        elif any(kw in norm for kw in ["test", "sinov", "tekshir"]):
            steps = ["Understand requirements", "Write test cases", "Execute", "Report"]
        confidence = round(min(words / 20, 1.0), 2)
        return {"complexity": complexity, "steps": steps, "confidence": confidence}

    def _generate_plan(self, user_input: str) -> List[Dict]:
        plan_prompt = (
            "Foydalanuvchi sorovi asosida bajariladigan amallar rejasini tuz.\n"
            "Rejani JSON formatida chiqar (faqat JSON):\n"
            '{"steps": [{"description": "...", "tool": "...", "expected": "..."}]}'
        )
        msgs = [
            {"role": "system", "content": "Sen reja tuzuvchi agent. Faqat JSON qaytar."},
            {"role": "user", "content": f"Sorov: {user_input}\n\n{plan_prompt}"}
        ]
        result = self.llm.chat(msgs)
        try:
            data = json.loads(result)
            if "steps" in data:
                self.plan = data["steps"]
                return self.plan
        except (json.JSONDecodeError, TypeError):
            pass
        return []

    def _reflection_check(self) -> Optional[str]:
        if len(self.execution_log) < 2:
            return None
        recent = self.execution_log[-3:]
        check_prompt = (
            "Oxirgi bajarilgan amallarni tekshir:\n" +
            "\n".join(recent) +
            "\n\nXatolik bormi? Agar bolsa, tuzatish yolini yoz. "
            "Agar hammasi joyida bolsa, 'OK' deb yoz."
        )
        msgs = [
            {"role": "system", "content": "Sen tekshiruvchi agent. Qisqa javob ber."},
            {"role": "user", "content": check_prompt}
        ]
        result = self.llm.chat(msgs)
        if result.strip() != "OK" and len(result) > 5:
            return result
        return None

    def _compact_history(self):
        system = [m for m in self.history if m["role"] == "system"]
        user_msgs = [m for m in self.history if m["role"] == "user"]
        assistant_msgs = [m for m in self.history if m["role"] == "assistant"]
        summary_prompt = (
            "Quyidagi suhbatni 2-3 gapda qisqacha yakunlab ber:\n" +
            json.dumps(self.history[-6:], ensure_ascii=False)
        )
        msgs = [{"role": "user", "content": summary_prompt}]
        summary = self.llm.chat(msgs)
        self.history = (system + user_msgs[-2:] + assistant_msgs[-2:] +
                        [{"role": "system", "content": f"[Compacted] {summary}"}])
        self.hooks.trigger(HookEvent.ON_COMPACT, history_len=len(self.history))

    def _finalize(self, content: str) -> str:
        self.history.append({
            "role": "user",
            "content": "Yuqoridagi barcha amallardan song, yakuniy natijani qisqa, aniq qilib chiqar."
        })
        return self.llm.chat(self.history)

    def _record_performance(self, success: bool, response_time: float) -> None:
        m = self.performance
        m["total_calls"] += 1
        if success:
            m["success_count"] += 1
        else:
            m["error_count"] += 1
        m["total_response_time"] += response_time
        m["avg_response_time"] = round(m["total_response_time"] / m["total_calls"], 4)

    def _system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            f"  - {t.name}: {t.description}" for t in TOOLS
        )
        return f"""Sen AIDA Beta agenti — terminalda ishlaydigan kod yozish assistantisan.

## ISH JARAYONI (Agent Loop)
1. **KONTEKST** — context tool orqali loyiha holatini bil
2. **REJA** — vazifani bosqichlarga ajrat
3. **BAJARISH** — har bir bosqich uchun mos tool ni chaqir
4. **TEKSHIRISH** — natijani tekshir, xato bolsa tuzat
5. **YAKUNLASH** — qisqa aniq natija chiqar

## MAVJUD TOOLS
{tool_descriptions}

## QOIDALAR
- Tool chaqirishda barcha kerakli argumentlarni toldir
- Agar xato bolsa, tuzatib qayta urin
- Katta fayllarni offset/limit bilan qismlab oqi
- Kodni yozishdan oldin mavjud kodni oqib tahlil qil
- Natijani run/lint tool bilan tekshir
- AGENTS.md / MEMORY.md / CLAUDE.md fayllaridagi loyiha yodnomasiga amal qil
"""

    def close_thread(self):
        self.memory_store.close_thread(self.thread_id, self.session_id)

# ─── SubAgent ────────────────────────────────────────────────────────────

class SubAgent(Agent):
    def __init__(self, task: str, context: str, session_id: str = "sub",
                 mode: ExecutionMode = ExecutionMode.AUTO,
                 permission_callback: Optional[Callable] = None):
        super().__init__(session_id=session_id, mode=mode,
                         permission_callback=permission_callback)
        self.task = task
        self.context = context

    def run(self, work_dir: str = ".") -> str:
        prompt = f"## Kontekst\n{self.context}\n\n## Vazifa\n{self.task}"
        return super().run(prompt, work_dir)

# ─── Agent Orchestrator ─────────────────────────────────────────────────

class AgentOrchestrator:
    def __init__(self, respond_func: Optional[Callable] = None,
                 mode: ExecutionMode = ExecutionMode.AUTO):
        self.respond_func = respond_func
        self.mode = mode
        self.queue = PriorityQueue()

        self._agents: Dict[TaskType, BaseAgent] = {
            TaskType.CODE: CodeAgent(respond_func),
            TaskType.PLAN: PlanAgent(respond_func),
            TaskType.DEBUG: DebugAgent(respond_func),
            TaskType.TEST: TestAgent(respond_func),
            TaskType.GENERAL: BaseAgent(respond_func),
            TaskType.FAST: BaseAgent(respond_func),
            TaskType.OPTIMIZE: CodeAgent(respond_func),
            TaskType.EXPLAIN: BaseAgent(respond_func),
        }

        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._running = True
        self._worker_thread.start()

    def submit(self, prompt: str, task_type: Optional[TaskType] = None) -> Task:
        task = create_task(prompt, task_type)
        self.queue.push(task)
        return task

    def submit_and_wait(self, prompt: str, task_type: Optional[TaskType] = None,
                        timeout: float = 120.0) -> str:
        task = self.submit(prompt, task_type)
        deadline = time.time() + timeout
        while time.time() < deadline:
            if task.status in ("completed", "failed"):
                if task.status == "completed":
                    return task.result
                raise RuntimeError(f"Agent xatosi: {task.error}")
            time.sleep(0.1)
        raise TimeoutError(f"Task {timeout}s da tugamadi")

    def process_sync(self, prompt: str, task_type: Optional[TaskType] = None) -> str:
        task = create_task(prompt, task_type)
        if task_type:
            task.task_type = task_type
        agent = self._route(task)
        return agent.process(task)

    def _route(self, task: Task) -> BaseAgent:
        agent = self._agents.get(task.task_type)
        if agent:
            return agent
        return self._agents[TaskType.GENERAL]

    def _worker_loop(self):
        while self._running:
            try:
                task = self.queue.pop(timeout=2.0)
                if not task:
                    continue
                agent = self._route(task)
                agent.process(task)
            except Exception:
                pass

    def get_agent_stats(self) -> Dict:
        return {tt.value: agent.stats() for tt, agent in self._agents.items()}

    def get_queue_stats(self) -> Dict:
        return {"queue_size": self.queue.size, "tasks": self.queue.all()}

    def stop(self):
        self._running = False

_orchestrator_instance: Optional[AgentOrchestrator] = None

def get_orchestrator(respond_func: Optional[Callable] = None,
                     mode: ExecutionMode = ExecutionMode.AUTO) -> AgentOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AgentOrchestrator(respond_func, mode)
    return _orchestrator_instance
