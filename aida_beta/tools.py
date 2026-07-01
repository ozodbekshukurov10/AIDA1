from __future__ import annotations

import os
import sys
import json
import subprocess
import difflib
import re as regex
import urllib.request, urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional

sys.stdout.reconfigure(encoding='utf-8', errors='replace') if hasattr(sys.stdout, 'reconfigure') else None

ToolFunc = Callable[..., str]


class Tool:
    def __init__(self, name: str, description: str, parameters: Dict, fn: ToolFunc):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.fn = fn

    def to_schema(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }

    def __call__(self, **kwargs) -> str:
        try:
            return self.fn(**kwargs)
        except Exception as e:
            return f"[TOOL ERROR] {self.name}: {e}"


_work_dir = Path.cwd()


def set_work_dir(path: Path):
    global _work_dir
    _work_dir = path


def _read(path: str, offset: int = 0, limit: int = 2000) -> str:
    p = (_work_dir / path).resolve()
    if not p.exists():
        return f"[ERROR] Fayl topilmadi: {path}"
    if p.is_dir():
        items = sorted(p.iterdir())
        lines = []
        for item in items:
            suffix = "/" if item.is_dir() else ""
            lines.append(f"{item.name}{suffix}")
        return "\n".join(lines)
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
        if offset > 0 or limit < len(text.splitlines()):
            lines = text.splitlines()
            selected = lines[offset:offset + limit]
            result = "\n".join(selected)
            if offset > 0:
                result = f"(lines {offset+1}-{offset+len(selected)})\n" + result
            elif limit < len(lines):
                result = result + f"\n... ({len(lines) - limit} more lines)"
            return result
        return text
    except Exception as e:
        return f"[ERROR] {e}"


def _write(path: str, content: str) -> str:
    p = (_work_dir / path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"[OK] Fayl saqlandi: {path} ({len(content)} bytes)"


def _edit(path: str, old_string: str, new_string: str) -> str:
    p = (_work_dir / path).resolve()
    if not p.exists():
        return f"[ERROR] Fayl topilmadi: {path}"
    text = p.read_text(encoding="utf-8")
    if old_string not in text:
        return f"[ERROR] Matn topilmadi: '{old_string[:50]}...'"
    count = text.count(old_string)
    if count > 1:
        return f"[ERROR] '{old_string[:50]}...' {count} marta topildi. Aniqroq matn kiriting."
    text = text.replace(old_string, new_string)
    p.write_text(text, encoding="utf-8")
    return f"[OK] Fayl tahrirlandi: {path}"


def _patch(path: str, old_string: str, new_string: str) -> str:
    p = (_work_dir / path).resolve()
    if not p.exists():
        return f"[ERROR] Fayl topilmadi: {path}"
    text = p.read_text(encoding="utf-8")
    if old_string not in text:
        close = difflib.get_close_matches(old_string, text.splitlines(), n=3, cutoff=0.6)
        hint = f"\nYaqin satrlar: {close}" if close else ""
        return f"[ERROR] Matn topilmadi: '{old_string[:50]}...'{hint}"
    count = text.count(old_string)
    if count > 1:
        return f"[ERROR] '{old_string[:50]}...' {count} marta topildi. Aniqroq matn kiriting."
    text = text.replace(old_string, new_string)
    p.write_text(text, encoding="utf-8")
    return f"[OK] Patch qo'llandi: {path}"


def _apply_patch(path: str, diff_text: str) -> str:
    p = (_work_dir / path).resolve()
    if not p.exists():
        return f"[ERROR] Fayl topilmadi: {path}"
    original = p.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    hunks = []
    current_hunk = []
    for line in diff_text.splitlines(keepends=True):
        if line.startswith('@@'):
            if current_hunk:
                hunks.append(current_hunk)
            current_hunk = [line]
        elif current_hunk:
            current_hunk.append(line)
    if current_hunk:
        hunks.append(current_hunk)
    if not hunks:
        return _patch(path=path, old_string=diff_text, new_string="")
    for hunk in hunks:
        header = hunk[0] if hunk[0].startswith('@@') else None
        if not header:
            continue
        m = regex.search(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', header)
        if not m:
            continue
        old_start = int(m.group(1))
        old_lines = []
        new_lines = []
        for l in hunk[1:]:
            if l.startswith('-'):
                old_lines.append(l[1:])
            elif l.startswith('+'):
                new_lines.append(l[1:])
            elif l.startswith(' '):
                old_lines.append(l[1:])
                new_lines.append(l[1:])
        if not old_lines:
            continue
        old_text = ''.join(old_lines)
        new_text = ''.join(new_lines)
        idx = original.find(old_text)
        if idx == -1:
            return f"[ERROR] Hunk '{old_text[:40]}...' topilmadi"
        original = original[:idx] + new_text + original[idx + len(old_text):]
    p.write_text(original, encoding="utf-8")
    return f"[OK] Diff qo'llandi: {path}"


def _run(command: str, timeout: int = 30, sandbox: str = "none") -> str:
    if sandbox != "none":
        return f"[SANDBOX] Sandbox ({sandbox}) hali qollab-quvvatlanmaydi. 'none' bilan ishlat."
    try:
        r = subprocess.run(
            command,
            capture_output=True,
            text=True,
            shell=True,
            timeout=timeout,
            cwd=str(_work_dir),
        )
        out = r.stdout or ""
        err = r.stderr or ""
        result = out + ("\n[STDERR]\n" + err if err else "")
        if len(result) > 4000:
            result = result[:4000] + f"\n... (output truncated, {len(result)} chars total)"
        return result or "(bo'sh output)"
    except subprocess.TimeoutExpired:
        return f"[TIMEOUT] Buyruq {timeout}s ichida tugamadi."
    except Exception as e:
        return f"[ERROR] {e}"


def _grep(pattern: str, path: str = ".", include: str = "") -> str:
    p = (_work_dir / path).resolve()
    if not p.exists():
        return f"[ERROR] Yo'l topilmadi: {path}"
    cmd = ["rg", "-n", pattern, str(p)]
    if include:
        cmd.extend(["-g", include])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15, cwd=str(_work_dir))
        out = r.stdout or ""
        if not out:
            return f"Hech narsa topilmadi: '{pattern}'"
        lines = out.splitlines()
        if len(lines) > 50:
            lines = lines[:50]
            out = "\n".join(lines) + f"\n... ({len(out.splitlines()) - 50} more matches)"
        return out
    except FileNotFoundError:
        return "[ERROR] rg (ripgrep) topilmadi. 'pip install ripgrep' yoki grep ishlating."
    except Exception as e:
        return f"[ERROR] {e}"


def _glob(pattern: str, path: str = ".") -> str:
    p = (_work_dir / path).resolve()
    if not p.exists():
        return f"[ERROR] Yo'l topilmadi: {path}"
    try:
        import glob as glob_module
        matches = glob_module.glob(str(p / pattern), recursive=True)
        if not matches:
            return f"Hech narsa topilmadi: '{pattern}'"
        rel = [os.path.relpath(m, _work_dir) for m in matches[:100]]
        if len(matches) > 100:
            rel.append(f"... ({len(matches) - 100} more)")
        return "\n".join(rel)
    except Exception as e:
        return f"[ERROR] {e}"


def _context() -> str:
    info = []
    info.append(f"Joriy papka: {_work_dir}")
    info.append(f"Platforma: {sys.platform}")
    info.append(f"Python: {sys.version.split()[0]}")
    info.append(f"Node: {_run('node --version', 5).strip()}")
    git_branch = _run('git rev-parse --abbrev-ref HEAD', 5).strip()
    info.append(f"Git branch: {git_branch}" if git_branch else "Git: topilmadi")
    git_status = _run('git status --short', 10)
    if git_status:
        info.append(f"Git status:\n{git_status}")
    return "\n".join(info)


def _search(query: str, path: str = ".") -> str:
    p = (_work_dir / path).resolve()
    if not p.exists():
        return f"[ERROR] Yo'l topilmadi: {path}"
    results = []
    try:
        for filepath in p.rglob("*"):
            if filepath.is_file() and filepath.suffix in {'.py', '.js', '.ts', '.tsx', '.jsx', '.html', '.css', '.json', '.md', '.txt'}:
                try:
                    text = filepath.read_text(encoding="utf-8", errors="replace")
                    if query.lower() in text.lower():
                        rel = os.path.relpath(filepath, _work_dir)
                        lines = text.splitlines()
                        for i, line in enumerate(lines, 1):
                            if query.lower() in line.lower():
                                results.append(f"{rel}:{i}: {line.strip()[:150]}")
                                if len(results) >= 30:
                                    break
                        if len(results) >= 30:
                            break
                except Exception:
                    pass
    except Exception as e:
        return f"[ERROR] {e}"
    if not results:
        return f"Hech narsa topilmadi: '{query}'"
    return "\n".join(results[:30]) + (f"\n... ({len(results) - 30} more)" if len(results) > 30 else "")


def _web_search(query: str) -> str:
    try:
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1"
        req = urllib.request.Request(url, headers={"User-Agent": "AIDA-Beta/2.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        results = []
        if data.get("AbstractText"):
            results.append(f"[Abstract] {data['AbstractText'][:500]}")
        if data.get("RelatedTopics"):
            for topic in data["RelatedTopics"][:5]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append(f"- {topic['Text'][:200]}")
        return "\n".join(results) if results else "Hech narsa topilmadi."
    except Exception as e:
        return f"[ERROR] Web search: {e}"


def _web_fetch(url: str, format: str = "text") -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AIDA-Beta/2.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="replace")
        if format == "markdown":
            content = _html_to_markdown(content)
        return content[:5000] + ("\n... (truncated)" if len(content) > 5000 else "")
    except Exception as e:
        return f"[ERROR] Web fetch: {e}"


def _html_to_markdown(html: str) -> str:
    import html as html_mod
    text = html_mod.unescape(html)
    text = regex.sub(r'<script[^>]*>.*?</script>', '', text, flags=regex.DOTALL)
    text = regex.sub(r'<style[^>]*>.*?</style>', '', text, flags=regex.DOTALL)
    text = regex.sub(r'<[^>]+>', ' ', text)
    text = regex.sub(r'\n\s*\n', '\n\n', text)
    text = regex.sub(r' {2,}', ' ', text)
    return text.strip()


def _python_exec(code: str) -> str:
    blocked = ["import os", "import subprocess", "__import__", "eval(", "exec(", "open(", "shutil"]
    for b in blocked:
        if b in code:
            return f"[SECURITY] {b} bloklandi"
    try:
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
            return f"[STDERR]\n{err}\n[STDOUT]\n{out}"
        return out or "Kod bajarildi (chiqish yo'q)"
    except Exception as e:
        return f"[ERROR] {e}"


def _http_request(url: str, method: str = "GET", body: str = "") -> str:
    try:
        req = urllib.request.Request(url, method=method.upper())
        if body and method.upper() == "POST":
            req.data = body.encode("utf-8")
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="replace")[:5000]
            return f"[{resp.status}]\n{content}"
    except Exception as e:
        return f"[ERROR] HTTP {method} {url}: {e}"


def _knowledge_add(fact: str) -> str:
    try:
        from .memory import AidaBetaMemory
        mem = AidaBetaMemory()
        mem.remember_fact(fact)
        return f"[OK] Xotirada saqlandi: {fact[:100]}"
    except ImportError:
        from memory import AidaBetaMemory
        mem = AidaBetaMemory()
        mem.remember_fact(fact)
        return f"[OK] Xotirada saqlandi: {fact[:100]}"


def _knowledge_search(query: str) -> str:
    try:
        from .memory import AidaBetaMemory
        from .agent import detect_task_type
        mem = AidaBetaMemory()
        facts = mem.learned_facts(limit=20)
        if not facts:
            return "Xotirada ma'lumot yo'q."
        matching = [f for f in facts if query.lower() in f.lower()]
        if not matching:
            return f"'{query}' bo'yicha hech narsa topilmadi.\nBarcha faktlar:\n" + "\n".join(f"- {f}" for f in facts)
        return "\n".join(f"- {f}" for f in matching)
    except ImportError:
        return "[ERROR] Xotira tizimi topilmadi."


def _mcp_call(server: str, tool: str, args: str = "{}") -> str:
    try:
        import subprocess
        cmd = ["npx", "-y", server, "call", tool]
        if args and args != "{}":
            cmd.append("--args")
            cmd.append(args)
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return r.stdout or r.stderr or "[MCP] Bo'sh javob"
    except FileNotFoundError:
        return "[ERROR] npx topilmadi. Node.js o'rnatilganligini tekshiring."
    except Exception as e:
        return f"[ERROR] MCP: {e}"


def _lint(path: str = "") -> str:
    if path:
        p = (_work_dir / path).resolve()
        if not p.exists():
            return f"[ERROR] Yo'l topilmadi: {path}"
        target = str(p)
    else:
        target = str(_work_dir)
    results = []
    for runner, cmd in [("ruff", f"ruff check {target}"), ("flake8", f"flake8 {target}")]:
        r = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=15)
        out = r.stdout.strip()
        if out:
            results.append(f"[{runner}]\n{out[:2000]}")
    if not results:
        return "[OK] Lint xatoliklari topilmadi."
    return "\n".join(results)


TOOLS: List[Tool] = [
    Tool(
        name="read",
        description="Fayl o'qish. Katta fayllarni offset/limit bilan qismlab o'qish mumkin.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Fayl yo'li"},
                "offset": {"type": "integer", "description": "Qatordan boshlash (0-indexed)", "default": 0},
                "limit": {"type": "integer", "description": "Nechta qator o'qish", "default": 2000},
            },
            "required": ["path"],
        },
        fn=_read,
    ),
    Tool(
        name="write",
        description="Yangi fayl yaratish yoki mavjud faylni to'liq qayta yozish.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Fayl yo'li"},
                "content": {"type": "string", "description": "Fayl kontenti"},
            },
            "required": ["path", "content"],
        },
        fn=_write,
    ),
    Tool(
        name="edit",
        description="Fayl ichida matnni almashtirish (mavjud faylni tahrirlash).",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Fayl yo'li"},
                "old_string": {"type": "string", "description": "Almashtiriladigan matn"},
                "new_string": {"type": "string", "description": "Yangi matn"},
            },
            "required": ["path", "old_string", "new_string"],
        },
        fn=_edit,
    ),
    Tool(
        name="patch",
        description="Fayl ichida matnni almashtirish (edit dan farqli - close matching bilan).",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Fayl yo'li"},
                "old_string": {"type": "string", "description": "Almashtiriladigan matn"},
                "new_string": {"type": "string", "description": "Yangi matn"},
            },
            "required": ["path", "old_string", "new_string"],
        },
        fn=_patch,
    ),
    Tool(
        name="apply_patch",
        description="Unified diff formatidagi patchni faylga qo'llash (Git diff format).",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Fayl yo'li"},
                "diff_text": {"type": "string", "description": "Unified diff text (@@ -l,c +l,c @@ format)"},
            },
            "required": ["path", "diff_text"],
        },
        fn=_apply_patch,
    ),
    Tool(
        name="run",
        description="Terminal buyrug'ini bajarish.",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Bajariladigan buyruq"},
                "timeout": {"type": "integer", "description": "Timeout (soniya)", "default": 30},
                "sandbox": {"type": "string", "description": "Xavfsizlik rejimi: none|restricted", "default": "none", "enum": ["none", "restricted"]},
            },
            "required": ["command"],
        },
        fn=_run,
    ),
    Tool(
        name="grep",
        description="Fayllar ichidan matn qidirish (ripgrep).",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Qidiruv matni (regex)"},
                "path": {"type": "string", "description": "Qidiruv papkasi", "default": "."},
                "include": {"type": "string", "description": "Fayl pattern (masalan *.py)", "default": ""},
            },
            "required": ["pattern"],
        },
        fn=_grep,
    ),
    Tool(
        name="glob",
        description="Fayllarni pattern bo'yicha qidirish (masalan **/*.py).",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern"},
                "path": {"type": "string", "description": "Qidiruv papkasi", "default": "."},
            },
            "required": ["pattern"],
        },
        fn=_glob,
    ),
    Tool(
        name="search",
        description="Fayllar ichidan matn qidirish (sekin, lekin keng qamrovli).",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Qidiruv matni"},
                "path": {"type": "string", "description": "Qidiruv papkasi", "default": "."},
            },
            "required": ["query"],
        },
        fn=_search,
    ),
    Tool(
        name="lint",
        description="Python kodini lint tekshirish (ruff / flake8).",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Fayl yoki papka yo'li", "default": ""},
            },
        },
        fn=_lint,
    ),
    Tool(
        name="context",
        description="Loyiha kontekstini olish (joriy papka, git status, platforma).",
        parameters={
            "type": "object",
            "properties": {
                "dummy": {"type": "string", "description": "Ishlatilmaydi", "default": ""},
            },
        },
        fn=lambda dummy="": _context(),
    ),
    Tool(
        name="web_search",
        description="Internetdan ma'lumot qidirish (DuckDuckGo API).",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Qidiruv so'rovi"},
            },
            "required": ["query"],
        },
        fn=_web_search,
    ),
    Tool(
        name="web_fetch",
        description="Web sahifani o'qish va matn sifatida qaytarish.",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL manzil"},
                "format": {"type": "string", "description": "Format: text|markdown", "default": "text", "enum": ["text", "markdown"]},
            },
            "required": ["url"],
        },
        fn=_web_fetch,
    ),
    Tool(
        name="python_exec",
        description="Python kodini xavfsiz muhitda bajarish.",
        parameters={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Bajariladigan Python kodi"},
            },
            "required": ["code"],
        },
        fn=_python_exec,
    ),
    Tool(
        name="http_request",
        description="HTTP so'rov yuborish (GET/POST/PUT/DELETE).",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL manzil"},
                "method": {"type": "string", "description": "HTTP method (GET/POST)", "default": "GET", "enum": ["GET", "POST", "PUT", "DELETE"]},
                "body": {"type": "string", "description": "POST body", "default": ""},
            },
            "required": ["url"],
        },
        fn=_http_request,
    ),
    Tool(
        name="knowledge_add",
        description="Xotiraga ma'lumot qo'shish (keyingi sessiyalarda eslab qoladi).",
        parameters={
            "type": "object",
            "properties": {
                "fact": {"type": "string", "description": "Eslab qolinadigan ma'lumot"},
            },
            "required": ["fact"],
        },
        fn=_knowledge_add,
    ),
    Tool(
        name="knowledge_search",
        description="Xotiradan ma'lumot qidirish.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Qidiruv matni"},
            },
            "required": ["query"],
        },
        fn=_knowledge_search,
    ),
    Tool(
        name="mcp_call",
        description="MCP server orqali tool chaqirish (Model Context Protocol).",
        parameters={
            "type": "object",
            "properties": {
                "server": {"type": "string", "description": "MCP server nomi (npm package)"},
                "tool": {"type": "string", "description": "Cha qiriladigan tool nomi"},
                "args": {"type": "string", "description": "JSON formatdagi argumentlar", "default": "{}"},
            },
            "required": ["server", "tool"],
        },
        fn=_mcp_call,
    ),
]


TOOL_MAP: Dict[str, Tool] = {t.name: t for t in TOOLS}


def get_schemas() -> List[Dict]:
    return [t.to_schema() for t in TOOLS]


def execute(name: str, **kwargs) -> str:
    tool = TOOL_MAP.get(name)
    if not tool:
        return f"[ERROR] Tool topilmadi: {name}"
    return tool(**kwargs)
