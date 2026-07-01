from __future__ import annotations
import ast
import logging
import re
from collections import defaultdict
from typing import Any

from .graph_analyzers import walk_ast

logger = logging.getLogger("webapp.repo_analyzer.structure")


class ASTAnalyzer:
    def __init__(self):
        self.ast_data: list[dict] = []

    def add_file(self, file_path: str, source: str, language: str):
        if language == "Python":
            self._add_python_ast(file_path, source)
        else:
            self._add_fallback_ast(file_path, source, language)

    def _add_python_ast(self, file_path: str, source: str):
        walker = walk_ast(source)
        if not walker:
            return
        funcs = []
        for fn in walker.functions:
            funcs.append({
                "type": "function",
                "name": fn["name"],
                "line": fn["line"],
            })
        classes = []
        for cls in walker.classes:
            classes.append({
                "type": "class",
                "name": cls["name"],
                "line": cls["line"],
                "methods": cls["methods"],
            })
        imports = []
        for imp in walker.imports:
            imports.append({
                "type": "import",
                "name": imp["module"],
                "line": imp["line"],
            })
        self.ast_data.append({
            "file": file_path,
            "language": "Python",
            "nodes": funcs + classes + imports,
            "node_count": len(funcs) + len(classes) + len(imports),
        })

    def _add_fallback_ast(self, file_path: str, source: str, language: str):
        nodes = []
        patterns = {
            "function": [
                r'(?:async\s+)?function\s+(\w+)',
                r'(\w+)\s*=\s*(?:async\s+)?\((?:[^)]*)\)\s*(?::[^=])?=>',
                r'def\s+(\w+)\s*\(',
                r'func\s+(\w+)\s*\(',
                r'fun\s+(\w+)\s*\(',
                r'fn\s+(\w+)\s*\(',
                r'sub\s+(\w+)',
            ],
            "class": [
                r'class\s+(\w+)',
                r'class\s+(\w+)\s*(?:extends|implements)',
                r'type\s+(\w+)\s*=\s*(?:struct|class)',
                r'interface\s+(\w+)',
            ],
            "import": [
                r'import\s+(?:\w+\s*,?\s*)?\{?[^}]*\}?\s*from\s+[\'"]([^\'"]+)[\'"]',
                r'require\([\'"]([^\'"]+)[\'"]\)',
                r'import\s+[\'"]([^\'"]+)[\'"]',
                r'use\s+(\w+(?:::\w+)*)',
                r'#include\s+[<"]([^>"]+)[>"]',
            ],
        }
        for node_type, pats in patterns.items():
            for pat in pats:
                for m in re.finditer(pat, source):
                    line = source[:m.start()].count("\n") + 1
                    nodes.append({
                        "type": node_type,
                        "name": m.group(1),
                        "line": line,
                    })

        self.ast_data.append({
            "file": file_path,
            "language": language,
            "nodes": nodes,
            "node_count": len(nodes),
        })

    def to_dict(self) -> dict:
        return {
            "files": self.ast_data,
            "total_nodes": sum(f["node_count"] for f in self.ast_data),
        }


class ClassDiagram:
    def __init__(self):
        self.classes: list[dict] = []
        self.relationships: list[dict] = []

    def add_file(self, file_path: str, source: str, language: str):
        if language == "Python":
            self._add_python_classes(file_path, source)
        else:
            self._add_fallback_classes(file_path, source, language)

    def _add_python_classes(self, file_path: str, source: str):
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(f"{self._get_name(base.value)}.{base.attr}")
                methods = []
                attributes = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append({
                            "name": item.name,
                            "line": getattr(item, "lineno", 0),
                            "decorators": [d.id for d in item.decorator_list if isinstance(d, ast.Name)],
                            "args": [a.arg for a in item.args.args],
                        })
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                attributes.append({
                                    "name": target.id,
                                    "line": getattr(item, "lineno", 0),
                                })
                cls_info = {
                    "name": node.name,
                    "file": file_path,
                    "line": getattr(node, "lineno", 0),
                    "bases": bases,
                    "methods": methods,
                    "attributes": attributes,
                    "is_abstract": any(
                        isinstance(d, ast.Name) and d.id == "abstractmethod"
                        for item in node.body
                        if isinstance(item, ast.FunctionDef)
                        for d in item.decorator_list
                    ),
                }
                self.classes.append(cls_info)

                for base in bases:
                    if base != "object":
                        self.relationships.append({
                            "from": node.name,
                            "to": base,
                            "type": "inheritance",
                        })

    def _add_fallback_classes(self, file_path: str, source: str, language: str):
        patterns = [
            (r'class\s+(\w+)(?:\s+extends\s+(\w+))?', "extends"),
            (r'class\s+(\w+)(?:\s+implements\s+(\w+))?', "implements"),
            (r'interface\s+(\w+)(?:\s+extends\s+(\w+))?', "extends"),
            (r'type\s+(\w+)\s*=\s*struct\s*\{', "struct"),
        ]
        for pat, rel_type in patterns:
            for m in re.finditer(pat, source):
                cls_name = m.group(1)
                self.classes.append({
                    "name": cls_name,
                    "file": file_path,
                    "line": source[:m.start()].count("\n") + 1,
                    "bases": [m.group(2)] if m.lastindex >= 2 and m.group(2) else [],
                    "methods": [],
                    "attributes": [],
                    "is_abstract": False,
                })
                if m.lastindex >= 2 and m.group(2):
                    self.relationships.append({
                        "from": cls_name,
                        "to": m.group(2),
                        "type": rel_type,
                    })

    def to_dict(self) -> dict:
        return {
            "classes": self.classes,
            "relationships": self.relationships,
        }

    def _get_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return "?"


class FunctionDiagram:
    def __init__(self):
        self.functions: list[dict] = []

    def add_file(self, file_path: str, source: str, language: str):
        if language == "Python":
            self._add_python_functions(file_path, source)
        else:
            self._add_fallback_functions(file_path, source, language)

    def _add_python_functions(self, file_path: str, source: str):
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                decorators = [
                    d.id for d in node.decorator_list
                    if isinstance(d, ast.Name)
                ]
                docstring = ast.get_docstring(node) or ""
                returns = ""
                if node.returns:
                    if isinstance(node.returns, ast.Name):
                        returns = node.returns.id
                    elif isinstance(node.returns, ast.Subscript):
                        returns = "Generic"
                    else:
                        returns = ast.dump(node.returns)[:30]

                self.functions.append({
                    "name": node.name,
                    "file": file_path,
                    "line": getattr(node, "lineno", 0),
                    "end_line": getattr(node, "end_lineno", 0),
                    "args": [a.arg for a in node.args.args],
                    "defaults_count": len(node.args.defaults),
                    "returns": returns,
                    "decorators": decorators,
                    "docstring": docstring[:200] if docstring else "",
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "is_method": False,
                })

    def _add_fallback_functions(self, file_path: str, source: str, language: str):
        patterns = [
            (r'(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)', "js"),
            (r'(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*(?::[^=])?=>', "arrow"),
            (r'(\w+)\s*\(([^)]*)\)\s*\{', "c_style"),
            (r'def\s+(\w+)\s*\(([^)]*)\)', "python"),
            (r'fn\s+(\w+)\s*\(([^)]*)\)', "rust"),
            (r'func\s+(\w+)\s*\(([^)]*)\)', "go"),
            (r'sub\s+(\w+)\s*\{', "perl"),
        ]
        for pat, style in patterns:
            for m in re.finditer(pat, source):
                args_str = m.group(2) if m.lastindex >= 2 else ""
                args = [a.strip().split(":")[0].strip() for a in args_str.split(",") if a.strip()]
                self.functions.append({
                    "name": m.group(1),
                    "file": file_path,
                    "line": source[:m.start()].count("\n") + 1,
                    "args": args,
                    "defaults_count": 0,
                    "returns": "",
                    "decorators": [],
                    "docstring": "",
                    "is_async": "async" in pat,
                    "is_method": False,
                })

    def to_dict(self) -> dict:
        return {"functions": self.functions}
