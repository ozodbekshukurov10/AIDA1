from __future__ import annotations
import ast
import logging
import re
from collections import defaultdict
from typing import Any

logger = logging.getLogger("webapp.repo_analyzer.graph_analyzers")


class ASTWalker(ast.NodeVisitor):
    def __init__(self):
        self.imports: list[dict] = []
        self.functions: list[dict] = []
        self.classes: list[dict] = []
        self.calls: list[dict] = []
        self.current_module = ""

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({
                "module": alias.name or "",
                "alias": alias.asname or "",
                "line": getattr(node, "lineno", 0),
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ""
        for alias in node.names:
            self.imports.append({
                "module": f"{module}.{alias.name}" if module else alias.name,
                "alias": alias.asname or "",
                "line": getattr(node, "lineno", 0),
                "from_module": module,
            })
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.functions.append({
            "name": node.name,
            "line": getattr(node, "lineno", 0),
            "end_line": getattr(node, "end_lineno", 0),
        })
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.functions.append({
            "name": node.name,
            "line": getattr(node, "lineno", 0),
            "end_line": getattr(node, "end_lineno", 0),
            "async": True,
        })
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.classes.append({
            "name": node.name,
            "line": getattr(node, "lineno", 0),
            "methods": [
                n.name for n in node.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ],
        })
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = f"{self._get_attribute_base(node.func)}.{node.func.attr}"
        else:
            name = str(node.func)
        self.calls.append({
            "name": name,
            "line": getattr(node, "lineno", 0),
        })
        self.generic_visit(node)

    def _get_attribute_base(self, node: ast.Attribute) -> str:
        if isinstance(node.value, ast.Name):
            return node.value.id
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_base(node.value)}.{node.value.attr}"
        return "?"


def walk_ast(source: str) -> ASTWalker | None:
    try:
        tree = ast.parse(source)
        walker = ASTWalker()
        walker.visit(tree)
        return walker
    except SyntaxError:
        return None


class DependencyGraph:
    def __init__(self):
        self.nodes: list[dict[str, Any]] = []
        self.edges: list[dict[str, Any]] = []
        self._node_set: set[str] = set()

    def add_file(self, file_path: str, source: str, language: str):
        if language == "Python":
            self._add_python_imports(file_path, source)
        elif language in ("JavaScript", "TypeScript", "React JSX", "React TSX", "Vue", "Svelte"):
            self._add_js_imports(file_path, source)

    def _add_python_imports(self, file_path: str, source: str):
        walker = walk_ast(source)
        if not walker:
            return
        self._ensure_node(file_path, "module")
        for imp in walker.imports:
            mod = imp["module"].split(".")[0]
            self._ensure_node(mod, "module")
            self._ensure_edge(file_path, mod, "imports")

    def _add_js_imports(self, file_path: str, source: str):
        patterns = [
            r'import\s+(?:\w+\s*,?\s*)?\{?[^}]*\}?\s*from\s+[\'"]([^\'"]+)[\'"]',
            r'require\([\'"]([^\'"]+)[\'"]\)',
            r'import\s+[\'"]([^\'"]+)[\'"]',
        ]
        self._ensure_node(file_path, "module")
        for pat in patterns:
            for m in re.finditer(pat, source):
                mod = m.group(1).split("/")[0]
                if mod.startswith(".") or mod.startswith("@"):
                    mod = m.group(1).split("/")[0:2][0] if m.group(1).startswith("@") else m.group(1).split("/")[0]
                self._ensure_node(mod, "module")
                self._ensure_edge(file_path, mod, "imports")

    def _add_html_imports(self, file_path: str, source: str):
        for m in re.finditer(r'<script[^>]*src=["\']([^"\']+)["\']', source):
            self._ensure_node(file_path, "module")
            self._ensure_node(m.group(1), "resource")
            self._ensure_edge(file_path, m.group(1), "includes")

    def add_dependency(self, source: str, target: str, dep_type: str = "depends_on"):
        self._ensure_node(source)
        self._ensure_node(target)
        self._ensure_edge(source, target, dep_type)

    def _ensure_node(self, name: str, node_type: str = "module"):
        if name not in self._node_set:
            self._node_set.add(name)
            self.nodes.append({"id": name, "type": node_type, "label": name})

    def _ensure_edge(self, source: str, target: str, label: str):
        self.edges.append({
            "source": source,
            "target": target,
            "label": label,
        })

    def to_dict(self) -> dict:
        return {"nodes": self.nodes, "edges": self.edges}


class CallGraph:
    def __init__(self):
        self.functions: list[dict] = []
        self.calls: list[dict] = []
        self._func_names: set[str] = set()
        self._func_definitions: dict[str, list[int]] = defaultdict(list)

    def add_file(self, file_path: str, source: str, language: str):
        if language == "Python":
            self._add_python_calls(file_path, source)

    def _add_python_calls(self, file_path: str, source: str):
        walker = walk_ast(source)
        if not walker:
            return
        for fn in walker.functions:
            fn_name = f"{file_path}::{fn['name']}"
            self.functions.append({
                "id": fn_name,
                "name": fn["name"],
                "file": file_path,
                "line": fn["line"],
            })
            self._func_names.add(fn["name"])

        for call in walker.calls:
            callee = call["name"].split(".")[0]
            self.calls.append({
                "caller_file": file_path,
                "caller_name": "module",
                "callee": callee,
                "line": call["line"],
                "file": file_path,
            })

    def to_dict(self) -> dict:
        return {"functions": self.functions, "calls": self.calls}


class ImportGraph:
    def __init__(self):
        self.modules: list[dict] = []
        self.imports: list[dict] = []
        self.circular_deps: list[list[str]] = []
        self._module_set: set[str] = set()
        self._import_map: dict[str, set[str]] = defaultdict(set)

    def add_file(self, file_path: str, source: str, language: str):
        if language == "Python":
            self._add_python_imports(file_path, source)
        elif language in ("JavaScript", "TypeScript", "React JSX", "React TSX"):
            self._add_js_imports(file_path, source)

    def _add_python_imports(self, file_path: str, source: str):
        walker = walk_ast(source)
        if not walker:
            return
        self._ensure_module(file_path)
        for imp in walker.imports:
            mod = imp["module"].split(".")[0]
            self._ensure_module(mod)
            self._import_map[file_path].add(mod)
            self.imports.append({
                "from_module": file_path,
                "to_module": mod,
                "line": imp["line"],
            })

    def _add_js_imports(self, file_path: str, source: str):
        patterns = [
            r'import\s+(?:\w+\s*,?\s*)?\{?[^}]*\}?\s*from\s+[\'"]([^\'"]+)[\'"]',
            r'require\([\'"]([^\'"]+)[\'"]\)',
        ]
        self._ensure_module(file_path)
        for pat in patterns:
            for m in re.finditer(pat, source):
                mod = m.group(1).split("/")[0]
                if mod.startswith("."):
                    continue
                self._ensure_module(mod)
                self._import_map[file_path].add(mod)
                self.imports.append({
                    "from_module": file_path,
                    "to_module": mod,
                    "line": source[:m.start()].count("\n") + 1,
                })

    def _ensure_module(self, name: str):
        if name not in self._module_set:
            self._module_set.add(name)
            self.modules.append({"id": name, "label": name})

    def detect_circular(self):
        visited: set[str] = set()
        path: list[str] = []
        path_set: set[str] = set()

        def dfs(node: str):
            if node in path_set:
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                self.circular_deps.append(cycle)
                return
            if node in visited:
                return
            if node not in self._import_map:
                return
            visited.add(node)
            path.append(node)
            path_set.add(node)
            for neighbor in list(self._import_map.get(node, set())):
                if neighbor in self._module_set:
                    dfs(neighbor)
            path.pop()
            path_set.discard(node)

        for mod in self.modules:
            dfs(mod["id"])

        self.circular_deps = [list(dict.fromkeys(c)) for c in self.circular_deps]

    def to_dict(self) -> dict:
        self.detect_circular()
        return {
            "modules": self.modules,
            "imports": self.imports,
            "circular_dependencies": self.circular_deps,
        }
