from __future__ import annotations

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Callable

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


def _run(command: str, timeout: int = 30) -> str:
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
    info.append(f"Git branch: {_run('git rev-parse --abbrev-ref HEAD', 5).strip()}")
    info.append(f"Git status:\n{_run('git status --short', 10)}")
    return "\n".join(info)


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
        name="run",
        description="Terminal buyrug'ini bajarish.",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Bajariladigan buyruq"},
                "timeout": {"type": "integer", "description": "Timeout (soniya)", "default": 30},
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
]


TOOL_MAP: Dict[str, Tool] = {t.name: t for t in TOOLS}


def get_schemas() -> List[Dict]:
    return [t.to_schema() for t in TOOLS]


def execute(name: str, **kwargs) -> str:
    tool = TOOL_MAP.get(name)
    if not tool:
        return f"[ERROR] Tool topilmadi: {name}"
    return tool(**kwargs)
