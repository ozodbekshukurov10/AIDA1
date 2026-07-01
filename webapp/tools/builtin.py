from __future__ import annotations
import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

from .base import BaseTool, ToolSpec, ToolResult


class WebSearchTool(BaseTool):
    def __init__(self):
        super().__init__(ToolSpec(
            name="web_search",
            description="Search the web for information",
            parameters={
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results", "default": 5},
            },
        ))

    async def execute(self, query: str = "", max_results: int = 5, **kwargs) -> ToolResult:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_html": 1},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    if data.get("AbstractText"):
                        results.append(f"[{data.get('Heading', 'Result')}] {data['AbstractText']}")
                    for topic in data.get("RelatedTopics", [])[:max_results]:
                        if "Text" in topic:
                            results.append(topic["Text"])
                    return ToolResult(
                        success=True,
                        output="\n\n".join(results) if results else "No results found",
                        data={"results": results},
                    )
            return ToolResult(success=False, error="Search failed")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class FileReadTool(BaseTool):
    def __init__(self):
        super().__init__(ToolSpec(
            name="file_read",
            description="Read a file from the filesystem",
            parameters={
                "path": {"type": "string", "description": "Absolute file path"},
                "max_length": {"type": "integer", "description": "Max characters", "default": 10000},
            },
        ))

    async def execute(self, path: str = "", max_length: int = 10000, **kwargs) -> ToolResult:
        try:
            p = Path(path).resolve()
            if not p.exists():
                return ToolResult(success=False, error=f"File not found: {path}")
            content = p.read_text(encoding="utf-8", errors="replace")
            if len(content) > max_length:
                content = content[:max_length] + f"\n... (truncated, {len(content)} total chars)"
            return ToolResult(success=True, output=content, data={"size": len(content), "path": str(p)})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class PythonExecTool(BaseTool):
    def __init__(self):
        super().__init__(ToolSpec(
            name="python_exec",
            description="Execute Python code in a sandboxed environment",
            parameters={
                "code": {"type": "string", "description": "Python code to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 10},
            },
        ))

    async def execute(self, code: str = "", timeout: int = 10, **kwargs) -> ToolResult:
        blocked = ["import os", "import subprocess", "import shutil", "__import__"]
        for b in blocked:
            if b in code:
                return ToolResult(success=False, error=f"Security: '{b}' is blocked")
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                script = Path(tmpdir) / "script.py"
                script.write_text(code, encoding="utf-8")
                proc = await asyncio.create_subprocess_exec(
                    sys.executable, str(script),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=tmpdir,
                    timeout=timeout,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                if proc.returncode == 0:
                    return ToolResult(success=True, output=stdout.decode("utf-8", errors="replace"))
                else:
                    return ToolResult(success=False, error=stderr.decode("utf-8", errors="replace"))
        except asyncio.TimeoutError:
            return ToolResult(success=False, error=f"Execution timed out after {timeout}s")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ShellTool(BaseTool):
    def __init__(self):
        super().__init__(ToolSpec(
            name="shell",
            description="Execute a shell command (read-only commands only)",
            parameters={
                "command": {"type": "string", "description": "Shell command"},
                "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 10},
            },
        ))

    BLOCKED_CMDS = ["rm ", "mkfs", "dd ", "format", "chmod", "chown", ">", "|"]

    async def execute(self, command: str = "", timeout: int = 10, **kwargs) -> ToolResult:
        for b in self.BLOCKED_CMDS:
            if b in command:
                return ToolResult(success=False, error=f"Security: '{b}' not allowed")
        try:
            proc = await asyncio.create_subprocess_exec(
                "cmd.exe" if sys.platform == "win32" else "/bin/sh",
                "/c" if sys.platform == "win32" else "-c",
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                timeout=timeout,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            output = stdout.decode("utf-8", errors="replace")
            if proc.returncode != 0:
                error = stderr.decode("utf-8", errors="replace")
                return ToolResult(success=False, output=output, error=error)
            return ToolResult(success=True, output=output)
        except asyncio.TimeoutError:
            return ToolResult(success=False, error=f"Command timed out after {timeout}s")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class KnowledgeAddTool(BaseTool):
    def __init__(self):
        super().__init__(ToolSpec(
            name="knowledge_add",
            description="Add a document to the knowledge base",
            parameters={
                "content": {"type": "string", "description": "Document content"},
                "tags": {"type": "string", "description": "Comma-separated tags"},
            },
        ))

    async def execute(self, content: str = "", tags: str = "", **kwargs) -> ToolResult:
        try:
            from ..memory.knowledge import get_knowledge_store
            store = get_knowledge_store()
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            doc_id = store.add(content, tags=tag_list)
            return ToolResult(success=True, output=f"Added to knowledge base (id: {doc_id})")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class KnowledgeSearchTool(BaseTool):
    def __init__(self):
        super().__init__(ToolSpec(
            name="knowledge_search",
            description="Search the knowledge base",
            parameters={
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results", "default": 5},
            },
        ))

    async def execute(self, query: str = "", limit: int = 5, **kwargs) -> ToolResult:
        try:
            from ..memory.knowledge import get_knowledge_store
            store = get_knowledge_store()
            results = store.search(query, top_k=limit)
            output = "\n\n".join(
                f"[{r.get('score', 0):.2f}] {r.get('content', '')[:500]}"
                for r in results
            ) if results else "No results found"
            return ToolResult(success=True, output=output, data={"results": results})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
