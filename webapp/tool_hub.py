import json
import logging
import os
import subprocess
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger("webapp.toolhub")


@dataclass
class ToolResult:
    success: bool
    output: str
    error: str = ""
    data: Any = None


class BaseTool:
    name = "base"
    description = "Asosiy tool"
    parameters: dict = field(default_factory=dict)

    def execute(self, **kwargs) -> ToolResult:
        raise NotImplementedError


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Internetdan ma'lumot qidirish"

    def execute(self, query: str = "", max_results: int = 3, **kwargs) -> ToolResult:
        if not query:
            return ToolResult(False, "", error="Query kerak")
        try:
            from .aida_controller import WebResearchService
            service = WebResearchService()
            results = service.search(query, limit=max_results)
            if not results:
                return ToolResult(True, "Hech qanday natija topilmadi")
            lines = [f"{i+1}. {r.title} — {r.summary[:200]}\n   Link: {r.url}"
                     for i, r in enumerate(results)]
            return ToolResult(True, "\n\n".join(lines), data=[r.__dict__ for r in results])
        except Exception as e:
            return ToolResult(False, "", error=str(e))


class FileReadTool(BaseTool):
    name = "file_read"
    description = "Fayl tarkibini o'qish"

    def execute(self, path: str = "", encoding: str = "utf-8", **kwargs) -> ToolResult:
        if not path:
            return ToolResult(False, "", error="Path kerak")
        try:
            p = os.path.abspath(path)
            if not os.path.exists(p):
                return ToolResult(False, "", error=f"Fayl topilmadi: {path}")
            if not p.startswith(os.path.abspath(".")):
                return ToolResult(False, "", error="Faqat loyiha ichidagi fayllar")
            content = open(p, "r", encoding=encoding).read()
            return ToolResult(True, content[:10000])
        except Exception as e:
            return ToolResult(False, "", error=str(e))


class FileWriteTool(BaseTool):
    name = "file_write"
    description = "Faylga yozish (yaratish/yangilash)"

    def execute(self, path: str = "", content: str = "", **kwargs) -> ToolResult:
        if not path:
            return ToolResult(False, "", error="Path kerak")
        try:
            p = os.path.abspath(path)
            base = os.path.abspath(".")
            if not p.startswith(base):
                return ToolResult(False, "", error="Faqat loyiha ichidagi fayllar")
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(True, f"Fayl saqlandi: {path} ({len(content)} bayt)")
        except Exception as e:
            return ToolResult(False, "", error=str(e))


class ShellTool(BaseTool):
    name = "shell"
    description = "Shell buyruqlarini bajarish"
    parameters = {
        "command": {"type": "string", "description": "Bajariladigan buyruq"},
    }

    def execute(self, command: str = "", timeout: int = 15, **kwargs) -> ToolResult:
        if not command:
            return ToolResult(False, "", error="Command kerak")
        blocked = ["rm -rf", "del /f", "format", "shutdown", "taskkill /f"]
        if any(b in command.lower() for b in blocked):
            return ToolResult(False, "", error="Xavfsizlik: buyruq bloklandi")
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout)
            out = (result.stdout or "")[:5000]
            err = (result.stderr or "")[:2000]
            if result.returncode != 0:
                return ToolResult(False, out or err, error=err or "Noma'lum xato")
            return ToolResult(True, out)
        except subprocess.TimeoutExpired:
            return ToolResult(False, "", error=f"Buyruq {timeout}s da tugamadi")
        except Exception as e:
            return ToolResult(False, "", error=str(e))


class PythonExecTool(BaseTool):
    name = "python_exec"
    description = "Python kodini bajarish"

    def execute(self, code: str = "", timeout: int = 10, **kwargs) -> ToolResult:
        if not code:
            return ToolResult(False, "", error="Code kerak")
        blocked = ["import os", "import subprocess", "__import__", "eval(", "exec("]
        for b in blocked:
            if b in code:
                return ToolResult(False, "", error=f"Xavfsizlik: {b} bloklandi")
        try:
            import sys
            from io import StringIO
            old_out, old_err = sys.stdout, sys.stderr
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            try:
                exec(code, {"__builtins__": __builtins__})
                out = sys.stdout.getvalue()
                err = sys.stderr.getvalue()
            finally:
                sys.stdout = old_out
                sys.stderr = old_err
            if err:
                return ToolResult(False, out, error=err)
            return ToolResult(True, out or "Kod bajarildi (chiqish yo'q)")
        except Exception as e:
            return ToolResult(False, "", error=str(e))


class HTTPRequestTool(BaseTool):
    name = "http_request"
    description = "HTTP so'rov yuborish (GET/POST)"

    def execute(self, url: str = "", method: str = "GET",
                body: str = "", headers: dict = None, timeout: int = 10, **kwargs) -> ToolResult:
        if not url:
            return ToolResult(False, "", error="URL kerak")
        try:
            req = urllib.request.Request(url, method=method.upper())
            if headers:
                for k, v in headers.items():
                    req.add_header(k, v)
            if body and method.upper() == "POST":
                data = body.encode("utf-8") if isinstance(body, str) else body
                req.data = data
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                content = resp.read().decode("utf-8", errors="replace")[:10000]
                return ToolResult(True, content, data={"status": resp.status})
        except Exception as e:
            return ToolResult(False, "", error=str(e))


class KnowledgeAddTool(BaseTool):
    name = "knowledge_add"
    description = "Bilimlar bazasiga ma'lumot qo'shish"

    def execute(self, content: str = "", tags: str = "", **kwargs) -> ToolResult:
        if not content:
            return ToolResult(False, "", error="Content kerak")
        try:
            from .knowledge_store import get_knowledge_store
            store = get_knowledge_store()
            doc_id = store.add(content, metadata={"tags": tags.split(",") if tags else []})
            return ToolResult(True, f"Bilim qo'shildi (id: {doc_id})")
        except Exception as e:
            return ToolResult(False, "", error=str(e))


class KnowledgeSearchTool(BaseTool):
    name = "knowledge_search"
    description = "Bilimlar bazasidan qidirish"

    def execute(self, query: str = "", top_k: int = 5, **kwargs) -> ToolResult:
        if not query:
            return ToolResult(False, "", error="Query kerak")
        try:
            from .knowledge_store import get_knowledge_store
            store = get_knowledge_store()
            results = store.search(query, top_k=top_k)
            if not results:
                return ToolResult(True, "Hech narsa topilmadi")
            lines = [f"{i+1}. [{r['score']}] {r['content'][:200]}"
                     for i, r in enumerate(results)]
            return ToolResult(True, "\n\n".join(lines), data=results)
        except Exception as e:
            return ToolResult(False, "", error=str(e))


# ── Tool Hub ──────────────────────────────────────────────────────────────

class ToolHub:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._register_defaults()

    def _register_defaults(self):
        for tool_cls in [WebSearchTool, FileReadTool, FileWriteTool,
                         ShellTool, PythonExecTool, HTTPRequestTool,
                         KnowledgeAddTool, KnowledgeSearchTool]:
            tool = tool_cls()
            self._tools[tool.name] = tool

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        return [
            {"name": t.name, "description": t.description}
            for t in self._tools.values()
        ]

    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolResult(False, "", error=f"Tool topilmadi: {tool_name}")
        return tool.execute(**kwargs)


_tool_hub: ToolHub | None = None


def get_tool_hub() -> ToolHub:
    global _tool_hub
    if _tool_hub is None:
        _tool_hub = ToolHub()
    return _tool_hub
