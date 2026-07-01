from __future__ import annotations
import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import httpx

from .base import BaseTool, ToolSpec, ToolResult
from .permission import Permission, PermissionLevel

logger = logging.getLogger("webapp.tools.professional")

BASE_DIR = Path(".").resolve()
ALLOWED_DIRS = [BASE_DIR]


def _is_path_allowed(path: str) -> bool:
    try:
        resolved = Path(path).resolve()
        return any(str(resolved).startswith(str(ad)) for ad in ALLOWED_DIRS)
    except Exception:
        return False


GIT_ACTIONS = {"init", "clone", "add", "commit", "push", "pull", "status",
               "log", "diff", "branch", "checkout", "stash", "tag", "remote",
               "fetch", "merge", "reset", "show", "config"}

FILE_ACTIONS = {"read", "write", "append", "delete", "copy", "move",
                "list", "search", "mkdir", "info", "exists"}

BROWSER_ACTIONS = {"search", "fetch", "get", "post", "head"}

PYTHON_ACTIONS = {"run", "eval", "check", "pip", "format"}

DOCKER_ACTIONS = {"ps", "images", "pull", "run", "stop", "rm", "logs",
                  "exec", "build", "info", "stats", "prune"}

SHELL_ACTIONS = {"run", "exec", "script"}

DATABASE_ACTIONS = {"query", "execute", "tables", "describe", "backup",
                    "import", "export", "stats", "list"}

API_ACTIONS = {"get", "post", "put", "patch", "delete", "head", "options"}

MEMORY_ACTIONS = {"store", "recall", "search", "forget", "list",
                  "stats", "clear", "export"}


class GitTool(BaseTool):
    def __init__(self):
        super().__init__(ToolSpec(
            name="git",
            description="Git repository management (clone, commit, push, pull, status, log, branch, diff, etc.)",
            category="development",
            version="1.0.0",
            timeout=120,
            permission=Permission(level=PermissionLevel.ADMIN, require_confirmation=True),
            parameters={
                "action": {"type": "string", "description": f"Git action: {', '.join(GIT_ACTIONS)}"},
                "path": {"type": "string", "description": "Repository path", "default": "."},
                "args": {"type": "object", "description": "Action arguments", "default": {}},
            },
        ))

    async def execute(self, action: str = "", path: str = ".", args: dict | None = None,
                       **kwargs) -> ToolResult:
        if action not in GIT_ACTIONS:
            return ToolResult(success=False, error=f"Unsupported action: {action}")
        args = args or {}
        work_dir = Path(path).resolve() if path else Path.cwd()
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", action, *self._build_args(action, args),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(work_dir),
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
            out = stdout.decode("utf-8", errors="replace")
            err = stderr.decode("utf-8", errors="replace")
            if proc.returncode != 0:
                return ToolResult(success=False, output=out[:2000], error=err[:1000])
            return ToolResult(success=True, output=out[:5000])
        except asyncio.TimeoutError:
            return ToolResult(success=False, error="Git operation timed out")
        except FileNotFoundError:
            return ToolResult(success=False, error="Git not found on system")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _build_args(self, action: str, args: dict) -> list[str]:
        if action == "clone":
            url = args.get("url", "")
            dest = args.get("dest", "")
            return [url] + ([dest] if dest else [])
        elif action == "commit":
            msg = args.get("message", args.get("m", "update"))
            return ["-m", msg]
        elif action == "log":
            count = str(args.get("count", args.get("n", 10)))
            return [f"--max-count={count}", "--oneline"]
        elif action == "branch":
            name = args.get("name", "")
            if args.get("delete"):
                return ["-d", name]
            if args.get("all"):
                return ["-a"]
            return [name] if name else []
        elif action == "remote":
            op = args.get("op", "")
            name = args.get("name", "origin")
            url = args.get("url", "")
            if op == "add" and url:
                return ["add", name, url]
            return [op] if op else []
        elif action == "reset":
            target = args.get("target", args.get("commit", "HEAD"))
            mode = args.get("mode", "--soft")
            return [mode, target]
        elif action == "config":
            key = args.get("key", "")
            value = args.get("value", "")
            if key and value:
                return [key, value]
            return []
        return []


class FileTool(BaseTool):
    def __init__(self):
        super().__init__(ToolSpec(
            name="file",
            description="File system operations (read, write, delete, copy, move, list, search, mkdir, info)",
            category="system",
            version="1.0.0",
            timeout=30,
            permission=Permission(level=PermissionLevel.USER),
            parameters={
                "action": {"type": "string", "description": f"File action: {', '.join(FILE_ACTIONS)}"},
                "path": {"type": "string", "description": "File or directory path"},
                "content": {"type": "string", "description": "Content for write/append", "default": ""},
                "dest": {"type": "string", "description": "Destination for copy/move", "default": ""},
                "pattern": {"type": "string", "description": "Search pattern (glob)", "default": ""},
                "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"},
            },
        ))

    async def execute(self, action: str = "", path: str = "", content: str = "",
                       dest: str = "", pattern: str = "", encoding: str = "utf-8",
                       **kwargs) -> ToolResult:
        if action not in FILE_ACTIONS:
            return ToolResult(success=False, error=f"Unsupported action: {action}")

        try:
            p = Path(path).resolve() if path else None

            if action == "read":
                if not p or not p.exists():
                    return ToolResult(success=False, error=f"File not found: {path}")
                text = p.read_text(encoding=encoding, errors="replace")
                return ToolResult(success=True, output=text[:10000], data={"size": len(text)})

            elif action == "write":
                if not p:
                    return ToolResult(success=False, error="Path required")
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding=encoding)
                return ToolResult(success=True, output=f"Written {len(content)} bytes to {path}")

            elif action == "append":
                if not p:
                    return ToolResult(success=False, error="Path required")
                with p.open("a", encoding=encoding) as f:
                    f.write(content)
                return ToolResult(success=True, output=f"Appended {len(content)} bytes to {path}")

            elif action == "delete":
                if not p or not p.exists():
                    return ToolResult(success=False, error=f"Not found: {path}")
                if p.is_dir():
                    import shutil
                    shutil.rmtree(p)
                    return ToolResult(success=True, output=f"Deleted directory: {path}")
                p.unlink()
                return ToolResult(success=True, output=f"Deleted file: {path}")

            elif action == "copy":
                if not p or not p.exists():
                    return ToolResult(success=False, error=f"Source not found: {path}")
                dst = Path(dest).resolve()
                dst.parent.mkdir(parents=True, exist_ok=True)
                if p.is_dir():
                    import shutil
                    shutil.copytree(p, dst)
                else:
                    import shutil
                    shutil.copy2(p, dst)
                return ToolResult(success=True, output=f"Copied to: {dest}")

            elif action == "move":
                if not p or not p.exists():
                    return ToolResult(success=False, error=f"Source not found: {path}")
                dst = Path(dest).resolve()
                dst.parent.mkdir(parents=True, exist_ok=True)
                p.rename(dst)
                return ToolResult(success=True, output=f"Moved to: {dest}")

            elif action == "list":
                if not p or not p.is_dir():
                    return ToolResult(success=False, error=f"Directory not found: {path}")
                entries = []
                for entry in sorted(p.iterdir()):
                    suffix = "/" if entry.is_dir() else ""
                    entries.append(f"{entry.name}{suffix}")
                return ToolResult(success=True, output="\n".join(entries) or "(empty)")

            elif action == "search":
                if not path:
                    return ToolResult(success=False, error="Path required")
                base = Path(path).resolve()
                if not base.is_dir():
                    return ToolResult(success=False, error=f"Not a directory: {path}")
                matches = list(base.rglob(pattern)) if pattern else []
                lines = [str(m.relative_to(base)) for m in matches[:200]]
                return ToolResult(success=True, output="\n".join(lines) or "No matches",
                                  data={"count": len(matches)})

            elif action == "mkdir":
                if not p:
                    return ToolResult(success=False, error="Path required")
                p.mkdir(parents=True, exist_ok=True)
                return ToolResult(success=True, output=f"Created directory: {path}")

            elif action == "info":
                if not p or not p.exists():
                    return ToolResult(success=False, error=f"Not found: {path}")
                stat = p.stat()
                info = {
                    "size": stat.st_size,
                    "is_dir": p.is_dir(),
                    "is_file": p.is_file(),
                    "modified": stat.st_mtime,
                    "created": getattr(stat, "st_ctime", 0),
                    "suffix": p.suffix,
                    "name": p.name,
                }
                return ToolResult(success=True, output=json.dumps(info, indent=2), data=info)

            elif action == "exists":
                exists = p.exists() if p else False
                return ToolResult(success=True, output=str(exists), data={"exists": exists})

            return ToolResult(success=False, error=f"Unhandled action: {action}")
        except PermissionError:
            return ToolResult(success=False, error="Permission denied: outside allowed directory")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserTool(BaseTool):
    def __init__(self):
        super().__init__(ToolSpec(
            name="browser",
            description="Web browser operations (search, fetch pages, make HTTP requests)",
            category="network",
            version="1.0.0",
            timeout=30,
            permission=Permission(level=PermissionLevel.PUBLIC),
            parameters={
                "action": {"type": "string", "description": f"Browser action: {', '.join(BROWSER_ACTIONS)}"},
                "url": {"type": "string", "description": "URL to fetch", "default": ""},
                "query": {"type": "string", "description": "Search query", "default": ""},
                "headers": {"type": "object", "description": "Custom HTTP headers", "default": {}},
                "timeout": {"type": "integer", "description": "Request timeout in seconds", "default": 15},
            },
        ))

    async def execute(self, action: str = "", url: str = "", query: str = "",
                       headers: dict | None = None, timeout: int = 15,
                       **kwargs) -> ToolResult:
        if action not in BROWSER_ACTIONS:
            return ToolResult(success=False, error=f"Unsupported action: {action}")

        headers = headers or {}
        headers.setdefault("User-Agent", "Mozilla/5.0 (compatible; AIDA-Bot/1.0)")

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                if action == "search":
                    if not query:
                        return ToolResult(success=False, error="Query required")
                    resp = await client.get(
                        "https://api.duckduckgo.com/",
                        params={"q": query, "format": "json", "no_html": 1},
                    )
                    if resp.status_code != 200:
                        return ToolResult(success=False, error=f"Search failed: HTTP {resp.status_code}")
                    data = resp.json()
                    results = []
                    abstract = data.get("AbstractText", "")
                    if abstract:
                        results.append(f"[{data.get('Heading', 'Result')}] {abstract}")
                    for topic in data.get("RelatedTopics", [])[:5]:
                        if "Text" in topic:
                            results.append(topic["Text"])
                        if "Topics" in topic:
                            for sub in topic["Topics"][:3]:
                                if "Text" in sub:
                                    results.append(sub["Text"])
                    return ToolResult(
                        success=True,
                        output="\n\n".join(results) if results else "No results found",
                        data={"results": results},
                    )

                elif action in ("fetch", "get"):
                    if not url:
                        return ToolResult(success=False, error="URL required")
                    resp = await client.get(url, headers=headers)
                    text = resp.text[:15000]
                    return ToolResult(
                        success=True,
                        output=text,
                        data={"status": resp.status_code, "headers": dict(resp.headers)},
                    )

                elif action == "post":
                    if not url:
                        return ToolResult(success=False, error="URL required")
                    resp = await client.post(url, headers=headers)
                    return ToolResult(
                        success=True,
                        output=resp.text[:15000],
                        data={"status": resp.status_code},
                    )

                elif action == "head":
                    if not url:
                        return ToolResult(success=False, error="URL required")
                    resp = await client.head(url, headers=headers)
                    return ToolResult(
                        success=True,
                        output=json.dumps(dict(resp.headers), indent=2),
                        data={"status": resp.status_code, "headers": dict(resp.headers)},
                    )

            return ToolResult(success=False, error=f"Unhandled action: {action}")
        except httpx.TimeoutException:
            return ToolResult(success=False, error=f"Request timed out after {timeout}s")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class PythonTool(BaseTool):
    def __init__(self):
        super().__init__(ToolSpec(
            name="python",
            description="Python code execution and analysis (run, eval, check syntax, pip install, format)",
            category="development",
            version="1.0.0",
            timeout=30,
            permission=Permission(level=PermissionLevel.ADMIN, require_confirmation=True),
            parameters={
                "action": {"type": "string", "description": f"Python action: {', '.join(PYTHON_ACTIONS)}"},
                "code": {"type": "string", "description": "Python code to run/eval/check"},
                "timeout": {"type": "integer", "description": "Execution timeout", "default": 10},
                "packages": {"type": "string", "description": "Packages for pip install (comma-separated)", "default": ""},
            },
        ))

    async def execute(self, action: str = "", code: str = "", timeout: int = 10,
                       packages: str = "", **kwargs) -> ToolResult:
        if action not in PYTHON_ACTIONS:
            return ToolResult(success=False, error=f"Unsupported action: {action}")

        if action == "check":
            try:
                compile(code, "<string>", "exec")
                return ToolResult(success=True, output="Syntax OK")
            except SyntaxError as e:
                return ToolResult(success=False, error=f"Syntax error: {e}")

        if action == "eval":
            try:
                result = eval(code, {"__builtins__": {}}, {})
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, error=str(e))

        if action == "pip":
            if not packages:
                return ToolResult(success=False, error="No packages specified")
            pkg_list = [p.strip() for p in packages.split(",") if p.strip()]
            results = []
            for pkg in pkg_list:
                try:
                    proc = await asyncio.create_subprocess_exec(
                        sys.executable, "-m", "pip", "install", pkg,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
                    if proc.returncode == 0:
                        results.append(f"Installed: {pkg}")
                    else:
                        results.append(f"Failed: {pkg} - {stderr.decode('utf-8', errors='replace')[:200]}")
                except Exception as e:
                    results.append(f"Error: {pkg} - {e}")
            return ToolResult(success=True, output="\n".join(results))

        if action == "format":
            try:
                import ast
                tree = ast.parse(code)
                import astor
                formatted = astor.to_source(tree)
                return ToolResult(success=True, output=formatted)
            except ImportError:
                try:
                    import black
                    mode = black.Mode()
                    formatted = black.format_str(code, mode=mode)
                    return ToolResult(success=True, output=formatted)
                except ImportError:
                    return ToolResult(success=False, error="No formatter available (install black or astor)")

        if action == "run":
            blocked = ["import os", "import subprocess", "import shutil", "__import__", "eval(", "exec("]
            import_line = next((b for b in blocked if b in code), None)
            if import_line:
                return ToolResult(success=False, error=f"Security: '{import_line}' is blocked")

            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    script = Path(tmpdir) / "script.py"
                    script.write_text(code, encoding="utf-8")
                    proc = await asyncio.create_subprocess_exec(
                        sys.executable, "-c", code,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=tmpdir,
                    )
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                    out = stdout.decode("utf-8", errors="replace")
                    err = stderr.decode("utf-8", errors="replace")
                    if proc.returncode == 0:
                        return ToolResult(success=True, output=out or "(no output)")
                    return ToolResult(success=False, output=out, error=err or "Execution failed")
            except asyncio.TimeoutError:
                return ToolResult(success=False, error=f"Execution timed out after {timeout}s")
            except Exception as e:
                return ToolResult(success=False, error=str(e))

        return ToolResult(success=False, error=f"Unhandled action: {action}")


class DockerTool(BaseTool):
    def __init__(self):
        super().__init__(ToolSpec(
            name="docker",
            description="Docker container and image management (ps, images, pull, run, stop, logs, build, exec)",
            category="infrastructure",
            version="1.0.0",
            timeout=120,
            permission=Permission(level=PermissionLevel.SYSTEM, require_confirmation=True),
            parameters={
                "action": {"type": "string", "description": f"Docker action: {', '.join(DOCKER_ACTIONS)}"},
                "args": {"type": "object", "description": "Action arguments", "default": {}},
            },
        ))

    async def execute(self, action: str = "", args: dict | None = None,
                       **kwargs) -> ToolResult:
        if action not in DOCKER_ACTIONS:
            return ToolResult(success=False, error=f"Unsupported action: {action}")

        args = args or {}
        cmd_parts = ["docker", action]

        if action == "ps":
            if args.get("all"):
                cmd_parts.append("--all")
            cmd_parts.extend(["--format", "{{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}"])

        elif action == "images":
            cmd_parts.extend(["--format", "{{.Repository}}:{{.Tag}}\t{{.Size}}"])

        elif action == "pull":
            image = args.get("image", "")
            if not image:
                return ToolResult(success=False, error="Image name required")
            cmd_parts.append(image)

        elif action == "run":
            image = args.get("image", "")
            if not image:
                return ToolResult(success=False, error="Image name required")
            cmd_parts.append("-d" if args.get("detach") else "-it")
            cmd_parts.append("--rm")
            cmd_parts.append(image)

        elif action == "stop":
            container = args.get("container", "")
            if not container:
                return ToolResult(success=False, error="Container ID required")
            cmd_parts.append(container)

        elif action == "rm":
            target = args.get("container", args.get("target", ""))
            if not target:
                return ToolResult(success=False, error="Container/image ID required")
            if args.get("force"):
                cmd_parts.append("--force")
            cmd_parts.append(target)

        elif action == "logs":
            container = args.get("container", "")
            if not container:
                return ToolResult(success=False, error="Container ID required")
            if args.get("tail"):
                cmd_parts.extend(["--tail", str(args["tail"])])
            cmd_parts.append(container)

        elif action == "exec":
            container = args.get("container", "")
            command = args.get("command", "")
            if not container or not command:
                return ToolResult(success=False, error="Container and command required")
            cmd_parts.extend(["-it", container, *command.split()])

        elif action == "build":
            tag = args.get("tag", "")
            dockerfile = args.get("file", "Dockerfile")
            context = args.get("context", ".")
            if tag:
                cmd_parts.extend(["-t", tag])
            cmd_parts.extend(["-f", dockerfile, context])

        elif action == "info":
            pass

        elif action == "stats":
            cmd_parts.append("--no-stream")

        elif action == "prune":
            cmd_parts = ["docker", "system", "prune", "-f"]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
            out = stdout.decode("utf-8", errors="replace")
            err = stderr.decode("utf-8", errors="replace")
            if proc.returncode != 0:
                return ToolResult(success=False, output=out[:1000], error=err[:1000])
            return ToolResult(success=True, output=out[:5000])
        except FileNotFoundError:
            return ToolResult(success=False, error="Docker not found on system")
        except asyncio.TimeoutError:
            return ToolResult(success=False, error="Docker operation timed out")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ShellTool(BaseTool):
    def __init__(self):
        super().__init__(ToolSpec(
            name="shell",
            description="Shell command execution with security filtering",
            category="system",
            version="1.0.0",
            timeout=30,
            permission=Permission(level=PermissionLevel.ADMIN, require_confirmation=True),
            parameters={
                "action": {"type": "string", "description": f"Shell action: {', '.join(SHELL_ACTIONS)}"},
                "command": {"type": "string", "description": "Shell command to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 15},
                "workdir": {"type": "string", "description": "Working directory", "default": "."},
            },
        ))

    BLOCKED_PATTERNS = [
        "rm -rf /", "rm -rf ~", "mkfs", "dd if=", "format",
        ":(){ :|:& };:", "chmod 777", "chown ", "sudo ",
        "> /dev/sda", "| bash", "| sh", "wget ", "curl ",
    ]

    def _is_safe(self, command: str) -> bool:
        cmd_lower = command.lower()
        for pattern in self.BLOCKED_PATTERNS:
            if pattern.lower() in cmd_lower:
                return False
        return True

    async def execute(self, action: str = "run", command: str = "", timeout: int = 15,
                       workdir: str = ".", **kwargs) -> ToolResult:
        if action not in SHELL_ACTIONS:
            return ToolResult(success=False, error=f"Unsupported action: {action}")

        if not command:
            return ToolResult(success=False, error="Command required")

        if not self._is_safe(command):
            return ToolResult(success=False, error="Security: command blocked")

        shell = "cmd.exe" if sys.platform == "win32" else "/bin/sh"
        shell_arg = "/c" if sys.platform == "win32" else "-c"

        try:
            proc = await asyncio.create_subprocess_exec(
                shell, shell_arg, command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            out = stdout.decode("utf-8", errors="replace")[:10000]
            err = stderr.decode("utf-8", errors="replace")[:2000]
            if proc.returncode != 0:
                return ToolResult(success=False, output=out, error=err or f"Exit code: {proc.returncode}")
            return ToolResult(success=True, output=out or "(no output)")
        except asyncio.TimeoutError:
            return ToolResult(success=False, error=f"Command timed out after {timeout}s")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DatabaseTool(BaseTool):
    def __init__(self):
        super().__init__(ToolSpec(
            name="database",
            description="SQL database operations (query, execute, tables, describe, backup, import, export)",
            category="data",
            version="1.0.0",
            timeout=60,
            permission=Permission(level=PermissionLevel.ADMIN, require_confirmation=True),
            parameters={
                "action": {"type": "string", "description": f"Database action: {', '.join(DATABASE_ACTIONS)}"},
                "query": {"type": "string", "description": "SQL query for query/execute actions", "default": ""},
                "db_path": {"type": "string", "description": "Database file path", "default": ""},
                "table": {"type": "string", "description": "Table name for describe action", "default": ""},
                "file": {"type": "string", "description": "File path for backup/import/export", "default": ""},
            },
        ))

    async def execute(self, action: str = "", query: str = "", db_path: str = "",
                       table: str = "", file: str = "", **kwargs) -> ToolResult:
        if action not in DATABASE_ACTIONS:
            return ToolResult(success=False, error=f"Unsupported action: {action}")

        import sqlite3
        db = db_path or "data/aida_long_term_memory.db"

        try:
            conn = sqlite3.connect(db)
            conn.row_factory = sqlite3.Row

            if action == "query":
                if not query:
                    return ToolResult(success=False, error="SQL query required")
                cur = conn.execute(query)
                rows = [dict(r) for r in cur.fetchall()]
                conn.close()
                output = json.dumps(rows, indent=2, default=str) if rows else "(no rows)"
                return ToolResult(success=True, output=output[:10000], data={"rows": len(rows)})

            elif action == "execute":
                if not query:
                    return ToolResult(success=False, error="SQL required")
                cur = conn.execute(query)
                conn.commit()
                output = f"Affected rows: {cur.rowcount}"
                conn.close()
                return ToolResult(success=True, output=output)

            elif action == "tables":
                cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [r["name"] for r in cur.fetchall()]
                conn.close()
                return ToolResult(success=True, output="\n".join(tables) or "(no tables)")

            elif action == "describe":
                if not table:
                    return ToolResult(success=False, error="Table name required")
                cur = conn.execute(f"PRAGMA table_info({table})")
                cols = [dict(r) for r in cur.fetchall()]
                conn.close()
                output = json.dumps(cols, indent=2) if cols else f"Table not found: {table}"
                return ToolResult(success=True, output=output)

            elif action == "backup":
                import shutil
                from pathlib import Path
                backup_path = file or f"{db}.backup"
                conn.close()
                conn2 = sqlite3.connect(db)
                backup_conn = sqlite3.connect(backup_path)
                conn2.backup(backup_conn)
                backup_conn.close()
                conn2.close()
                return ToolResult(success=True, output=f"Backup saved: {backup_path}")

            elif action == "import":
                if not file:
                    return ToolResult(success=False, error="Import file required")
                import csv
                if not table:
                    return ToolResult(success=False, error="Table name required")
                with open(file, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    headers = next(reader)
                    placeholders = ",".join("?" for _ in headers)
                    for row in reader:
                        conn.execute(f"INSERT INTO {table} VALUES ({placeholders})", row)
                conn.commit()
                conn.close()
                return ToolResult(success=True, output=f"Imported CSV to {table}")

            elif action == "export":
                if not table:
                    return ToolResult(success=False, error="Table name required")
                import csv
                export_path = file or f"{table}.csv"
                cur = conn.execute(f"SELECT * FROM {table}")
                with open(export_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([d[0] for d in cur.description])
                    writer.writerows(cur.fetchall())
                conn.close()
                return ToolResult(success=True, output=f"Exported to: {export_path}")

            elif action == "stats":
                cur = conn.execute("SELECT COUNT(*) as cnt FROM sqlite_master WHERE type='table'")
                num_tables = cur.fetchone()["cnt"]
                total_rows = 0
                cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                for r in cur.fetchall():
                    cnt = conn.execute(f"SELECT COUNT(*) as c FROM [{r['name']}]").fetchone()["c"]
                    total_rows += cnt
                conn.close()
                stats = {"tables": num_tables, "total_rows": total_rows, "db_path": db}
                return ToolResult(success=True, output=json.dumps(stats, indent=2), data=stats)

            elif action == "list":
                cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [r["name"] for r in cur.fetchall()]
                conn.close()
                return ToolResult(success=True, output=json.dumps(tables, indent=2), data={"tables": tables})

            conn.close()
            return ToolResult(success=False, error=f"Unhandled action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class APITool(BaseTool):
    def __init__(self):
        super().__init__(ToolSpec(
            name="api",
            description="HTTP API client (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS) with auth support",
            category="network",
            version="1.0.0",
            timeout=30,
            permission=Permission(level=PermissionLevel.USER),
            parameters={
                "action": {"type": "string", "description": f"HTTP method: {', '.join(API_ACTIONS)}"},
                "url": {"type": "string", "description": "Request URL"},
                "headers": {"type": "object", "description": "HTTP headers", "default": {}},
                "params": {"type": "object", "description": "Query parameters", "default": {}},
                "body": {"type": "object", "description": "Request body (JSON)", "default": {}},
                "auth": {"type": "object", "description": "Auth: {type: 'bearer'|'basic', token/username/password}", "default": {}},
                "timeout": {"type": "integer", "description": "Request timeout", "default": 15},
            },
        ))

    async def execute(self, action: str = "", url: str = "", headers: dict | None = None,
                       params: dict | None = None, body: dict | None = None,
                       auth: dict | None = None, timeout: int = 15,
                       **kwargs) -> ToolResult:
        if action not in API_ACTIONS:
            return ToolResult(success=False, error=f"Unsupported HTTP method: {action}")

        if not url:
            return ToolResult(success=False, error="URL required")

        headers = headers or {}
        params = params or {}
        body = body or {}

        if auth:
            auth_type = auth.get("type", "")
            if auth_type == "bearer":
                headers["Authorization"] = f"Bearer {auth.get('token', '')}"
            elif auth_type == "basic":
                import base64
                creds = f"{auth.get('username', '')}:{auth.get('password', '')}"
                encoded = base64.b64encode(creds.encode()).decode()
                headers["Authorization"] = f"Basic {encoded}"

        method = action.upper()

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=body if method in ("POST", "PUT", "PATCH") else None,
                )
                try:
                    data = resp.json()
                    output = json.dumps(data, indent=2, default=str)
                except Exception:
                    output = resp.text[:10000]

                return ToolResult(
                    success=resp.status_code < 400,
                    output=output,
                    data={
                        "status": resp.status_code,
                        "headers": dict(resp.headers),
                        "elapsed_ms": int(resp.elapsed.total_seconds() * 1000),
                    },
                )
        except httpx.TimeoutException:
            return ToolResult(success=False, error=f"Request timed out after {timeout}s")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class MemoryTool(BaseTool):
    def __init__(self):
        super().__init__(ToolSpec(
            name="memory",
            description="Long-term memory system (store, recall, search, forget, list, stats, clear, export memories)",
            category="ai",
            version="1.0.0",
            timeout=30,
            permission=Permission(level=PermissionLevel.USER),
            parameters={
                "action": {"type": "string", "description": f"Memory action: {', '.join(MEMORY_ACTIONS)}"},
                "content": {"type": "string", "description": "Content to store or search", "default": ""},
                "memory_type": {"type": "string", "description": "Memory type: conversation/project/code/user/knowledge/vector", "default": "conversation"},
                "tags": {"type": "string", "description": "Comma-separated tags", "default": ""},
                "limit": {"type": "integer", "description": "Max results", "default": 10},
                "item_id": {"type": "string", "description": "Memory item ID for recall/forget", "default": ""},
            },
        ))

    async def execute(self, action: str = "", content: str = "", memory_type: str = "conversation",
                       tags: str = "", limit: int = 10, item_id: str = "",
                       **kwargs) -> ToolResult:
        if action not in MEMORY_ACTIONS:
            return ToolResult(success=False, error=f"Unsupported action: {action}")

        try:
            from ..memory.manager import get_memory_manager
            mgr = get_memory_manager()

            tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

            if action == "store":
                if not content:
                    return ToolResult(success=False, error="Content required")
                mem_id = await mgr.store(content, memory_type=memory_type, tags=tag_list)
                return ToolResult(success=True, output=f"Stored as {memory_type} memory: {mem_id}",
                                  data={"id": mem_id})

            elif action == "recall":
                if item_id:
                    item = await mgr.get(item_id)
                    if item:
                        return ToolResult(success=True, output=item.content[:5000],
                                          data=item.to_dict())
                    return ToolResult(success=False, error=f"Memory not found: {item_id}")
                return ToolResult(success=False, error="item_id required for recall")

            elif action == "search":
                if not content:
                    return ToolResult(success=False, error="Search query required")
                result = await mgr.search(query=content, memory_type=memory_type,
                                           tags=tag_list or None, limit=limit)
                items = [i.to_dict() for i in result.items]
                output = "\n\n".join(
                    f"[{i['importance']}] {i['content'][:300]}"
                    for i in items
                ) if items else "No results found"
                return ToolResult(success=True, output=output, data={"items": items, "total": result.total})

            elif action == "forget":
                if item_id:
                    deleted = await mgr.delete(item_id)
                    return ToolResult(success=deleted, output=f"Deleted: {item_id}" if deleted else f"Not found: {item_id}")
                return ToolResult(success=False, error="item_id required for forget")

            elif action == "list":
                result = await mgr.search(query="", memory_type=memory_type, limit=limit)
                items = [{"id": i.id, "content": i.content[:100], "importance": i.importance.name.lower(),
                          "timestamp": i.timestamp} for i in result.items]
                output = json.dumps(items, indent=2) if items else "(empty)"
                return ToolResult(success=True, output=output, data={"items": items})

            elif action == "stats":
                stats = await mgr.get_stats()
                output = json.dumps(stats, indent=2)
                return ToolResult(success=True, output=output, data=stats)

            elif action == "clear":
                count = await mgr.clear()
                return ToolResult(success=True, output=f"Cleared {count} memories")

            elif action == "export":
                result = await mgr.search(query="", memory_type=memory_type, limit=1000)
                items = [i.to_dict() for i in result.items]
                output = json.dumps(items, indent=2, default=str)
                return ToolResult(success=True, output=output[:10000], data={"count": len(items)})

            return ToolResult(success=False, error=f"Unhandled action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
