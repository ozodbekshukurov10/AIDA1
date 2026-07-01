from __future__ import annotations
import ast
import logging
import re
from typing import Any

from .graph_analyzers import walk_ast

logger = logging.getLogger("webapp.repo_analyzer.documentation")


class DocumentationGenerator:
    def __init__(self):
        self.docs: dict[str, Any] = {
            "modules": [],
            "overview": "",
            "api": [],
            "readme": "",
        }

    def add_file(self, file_path: str, source: str, language: str):
        if language == "Python":
            self._add_python_docs(file_path, source)
        else:
            self._add_fallback_docs(file_path, source, language)

    def _add_python_docs(self, file_path: str, source: str):
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return

        module_doc = ast.get_docstring(tree) or ""
        classes = []
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                cls_doc = ast.get_docstring(node) or ""
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        m_doc = ast.get_docstring(item) or ""
                        methods.append({
                            "name": item.name,
                            "doc": m_doc[:500] if m_doc else "",
                            "line": getattr(item, "lineno", 0),
                            "args": [a.arg for a in item.args.args],
                        })
                classes.append({
                    "name": node.name,
                    "doc": cls_doc[:500] if cls_doc else "",
                    "line": getattr(node, "lineno", 0),
                    "methods": methods,
                })
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn_doc = ast.get_docstring(node) or ""
                functions.append({
                    "name": node.name,
                    "doc": fn_doc[:500] if fn_doc else "",
                    "line": getattr(node, "lineno", 0),
                    "args": [a.arg for a in node.args.args],
                })

        self.docs["modules"].append({
            "file": file_path,
            "module_doc": module_doc[:500] if module_doc else "",
            "classes": classes,
            "functions": functions,
            "doc_coverage": self._calc_coverage(classes, functions),
        })

    def _add_fallback_docs(self, file_path: str, source: str, language: str):
        comments = []
        jsdoc_patterns = [
            r'/\*\*([^*]|\*[^/])*\*/',
            r'//\s*(.*)',
            r'#\s*(.*)',
            r'--\s*(.*)',
            r'/\*\s*(.*?)\s*\*/',
        ]
        for pat in jsdoc_patterns:
            for m in re.finditer(pat, source, re.DOTALL):
                text = m.group(0).strip()
                if len(text) > 10:
                    comments.append({
                        "text": text[:300],
                        "line": source[:m.start()].count("\n") + 1,
                    })

        if comments:
            self.docs["modules"].append({
                "file": file_path,
                "comments_count": len(comments),
                "comments": comments[:20],
            })

    def _calc_coverage(self, classes: list, functions: list) -> float:
        total = len(classes) + len(functions)
        if total == 0:
            return 0.0
        documented = sum(1 for c in classes if c["doc"]) + sum(1 for f in functions if f["doc"])
        return round(documented / total * 100, 1)

    def generate_readme(self, repo_name: str = "", description: str = "") -> str:
        lines = []
        if repo_name:
            lines.append(f"# {repo_name}\n")
            if description:
                lines.append(f"{description}\n")
        if self.docs["modules"]:
            lines.append("## Module Overview\n")
            for mod in self.docs["modules"]:
                fname = mod.get("file", "unknown")
                doc = mod.get("module_doc", "")
                if doc:
                    lines.append(f"- **{fname}**: {doc[:100]}")
                else:
                    lines.append(f"- **{fname}")

            lines.append("\n## Documentation Coverage\n")
            coverages = [m.get("doc_coverage", 0) for m in self.docs["modules"] if "doc_coverage" in m]
            if coverages:
                avg = sum(coverages) / len(coverages)
                lines.append(f"- Average doc coverage: {avg:.1f}%\n")

            lines.append("## API Reference\n")
            for mod in self.docs["modules"]:
                fname = mod.get("file", "unknown")
                for cls in mod.get("classes", []):
                    lines.append(f"### `{cls['name']}`\n")
                    if cls["doc"]:
                        lines.append(f"{cls['doc']}\n")
                    for m in cls.get("methods", []):
                        args_s = ", ".join(m["args"])
                        lines.append(f"- `{m['name']}({args_s})`")
                        if m["doc"]:
                            lines.append(f"  - {m['doc'][:100]}")
                for fn in mod.get("functions", []):
                    args_s = ", ".join(fn["args"])
                    lines.append(f"### `{fn['name']}({args_s})`\n")
                    if fn["doc"]:
                        lines.append(f"{fn['doc']}\n")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "modules": self.docs["modules"],
            "overview": self.generate_readme(),
        }
