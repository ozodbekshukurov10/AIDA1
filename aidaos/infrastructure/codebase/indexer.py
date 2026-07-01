"""Codebase indexer and searcher — infrastructure adapter."""

from __future__ import annotations
import ast
import hashlib
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger("aidaos.infrastructure.codebase")


class CodebaseIndexer:
    """Indexes code files for symbol search and dependency analysis."""

    def __init__(self):
        self._indices: dict[str, dict] = {}

    def index_file(self, file_path: str) -> dict:
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}"}

        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return {"error": str(e)}

        content_hash = hashlib.md5(source.encode()).hexdigest()
        if file_path in self._indices and self._indices[file_path].get("hash") == content_hash:
            return self._indices[file_path]

        ext = path.suffix.lower()
        if ext == ".py":
            index = self._index_python(file_path, source)
        elif ext in (".js", ".ts", ".jsx", ".tsx"):
            index = self._index_js(file_path, source)
        else:
            index = self._index_generic(file_path, source)

        index["hash"] = content_hash
        self._indices[file_path] = index
        return index

    def _index_python(self, file_path: str, source: str) -> dict:
        imports = []
        classes = []
        functions = []
        symbols = []
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return {"file": file_path, "error": "Syntax error", "imports": [], "classes": [], "functions": []}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
                    symbols.append({"name": alias.name, "type": "import", "line": getattr(node, "lineno", 0)})
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    full = f"{mod}.{alias.name}" if mod else alias.name
                    imports.append(full)
                    symbols.append({"name": full, "type": "import", "line": getattr(node, "lineno", 0)})
            elif isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                classes.append({
                    "name": node.name, "line": getattr(node, "lineno", 0),
                    "bases": [b.id if isinstance(b, ast.Name) else str(b) for b in node.bases],
                    "methods": methods,
                })
                symbols.append({"name": node.name, "type": "class", "line": getattr(node, "lineno", 0)})
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append({
                    "name": node.name, "line": getattr(node, "lineno", 0),
                    "args": [a.arg for a in node.args.args],
                })
                symbols.append({"name": node.name, "type": "function", "line": getattr(node, "lineno", 0)})

        return {
            "file": file_path, "language": "python",
            "imports": imports, "classes": classes,
            "functions": functions, "symbols": symbols,
            "line_count": source.count("\n") + 1,
        }

    def _index_js(self, file_path: str, source: str) -> dict:
        imports = re.findall(r"(?:import|require)\s*\(?['\"]([^'\"]+)['\"]", source)
        classes = [
            {"name": m.group(1), "line": source[:m.start()].count("\n") + 1}
            for m in re.finditer(r"class\s+(\w+)", source)
        ]
        functions = []
        for pat in [r"function\s+(\w+)", r"(\w+)\s*=\s*(?:async\s+)?\(", r"(\w+)\s*\([^)]*\)\s*\{"]:
            for m in re.finditer(pat, source):
                name = m.group(1)
                if name and name not in ("if", "for", "while", "switch"):
                    functions.append({"name": name, "line": source[:m.start()].count("\n") + 1})
        functions = functions[:100]
        symbols = [{"name": c["name"], "type": "class"} for c in classes] + \
                  [{"name": f["name"], "type": "function"} for f in functions]
        return {
            "file": file_path, "language": "javascript",
            "imports": list(set(imports)), "classes": classes,
            "functions": functions, "symbols": symbols,
            "line_count": source.count("\n") + 1,
        }

    def _index_generic(self, file_path: str, source: str) -> dict:
        return {
            "file": file_path,
            "language": Path(file_path).suffix.lstrip("."),
            "imports": [],
            "classes": [],
            "functions": [],
            "symbols": [],
            "line_count": source.count("\n") + 1,
        }

    def search(self, query: str, language: str = "") -> list[dict]:
        results = []
        q = query.lower()
        for file_path, index in self._indices.items():
            if language and index.get("language", "") != language.lower():
                continue
            matches = []
            for sym in index.get("symbols", []):
                if q in sym.get("name", "").lower():
                    matches.append(sym)
            if matches:
                results.append({
                    "file": file_path,
                    "language": index.get("language", ""),
                    "matches": matches[:10],
                    "match_count": len(matches),
                })
        results.sort(key=lambda x: -x["match_count"])
        return results[:50]

    def get_dependencies(self, file_path: str) -> list[str]:
        index = self._indices.get(file_path, {})
        return index.get("imports", [])

    def index_project(self, project_path: str) -> dict:
        base = Path(project_path)
        if not base.exists():
            return {"error": "Path not found", "files": 0}
        count = 0
        for ext in (".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java"):
            for f in base.rglob(f"*{ext}"):
                if "node_modules" in str(f) or "__pycache__" in str(f) or ".git" in str(f):
                    continue
                self.index_file(str(f))
                count += 1
        return {"files_indexed": count, "project": project_path}

    def get_stats(self) -> dict:
        return {
            "files_indexed": len(self._indices),
            "total_symbols": sum(len(i.get("symbols", [])) for i in self._indices.values()),
        }
