from __future__ import annotations
import ast
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .graph_analyzers import walk_ast

logger = logging.getLogger("webapp.repo_analyzer.quality")


class BugPredictor:
    def __init__(self):
        self.issues: list[dict] = []
        self.risk_score: float = 0.0

    def add_file(self, file_path: str, source: str, language: str):
        if language == "Python":
            self._analyze_python(file_path, source)
        self._analyze_common(file_path, source, language)

    def _analyze_python(self, file_path: str, source: str):
        try:
            tree = ast.parse(source)
        except SyntaxError:
            self.issues.append({
                "file": file_path,
                "line": 1,
                "type": "syntax_error",
                "severity": "high",
                "message": "File contains syntax errors",
            })
            return

        for node in ast.walk(tree):
            line = getattr(node, "lineno", 0)

            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    self.issues.append({
                        "file": file_path, "line": line, "type": "bare_except",
                        "severity": "medium",
                        "message": "Bare except clause catches all exceptions",
                    })
                elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                    pass

            if isinstance(node, ast.FunctionDef):
                for d in node.decorator_list:
                    if isinstance(d, ast.Call) and isinstance(d.func, ast.Name):
                        if d.func.id in ("app.route", "blueprint.route"):
                            if node.args.args and node.args.args[0].arg not in ("self", "cls"):
                                self.issues.append({
                                    "file": file_path, "line": line,
                                    "type": "missing_self",
                                    "severity": "low",
                                    "message": f"Route handler '{node.name}' missing 'self' parameter",
                                })

            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == "execute" and isinstance(node.func.value, ast.Name):
                        if node.func.value.id.lower() in ("cursor", "db", "conn"):
                            self.issues.append({
                                "file": file_path, "line": line,
                                "type": "sql_injection_risk",
                                "severity": "high",
                                "message": "Possible SQL injection: execute() called without parameterization check",
                            })

            if isinstance(node, ast.FunctionDef):
                has_return = any(
                    isinstance(n, ast.Return) and n.value is not None
                    for n in ast.walk(node)
                )
                if not has_return and not any(
                    isinstance(n, ast.Yield)
                    for n in ast.walk(node)
                ):
                    for d in node.decorator_list:
                        if isinstance(d, ast.Name) and d.id in ("abstractmethod", "abc.abstractmethod"):
                            break
                    else:
                        pass

        if source.count("except:") > 3:
            self.issues.append({
                "file": file_path, "line": 1, "type": "many_bare_excepts",
                "severity": "low",
                "message": f"Multiple bare excepts ({source.count('except:')}) found",
            })

    def _analyze_common(self, file_path: str, source: str, language: str):
        line_count = source.count("\n") + 1

        for i, line in enumerate(source.split("\n"), 1):
            stripped = line.strip()

            if "TODO" in stripped.upper():
                self.issues.append({
                    "file": file_path, "line": i, "type": "todo",
                    "severity": "info",
                    "message": stripped[:120],
                })

            if "FIXME" in stripped.upper():
                self.issues.append({
                    "file": file_path, "line": i, "type": "fixme",
                    "severity": "low",
                    "message": stripped[:120],
                })

            if "HACK" in stripped.upper():
                self.issues.append({
                    "file": file_path, "line": i, "type": "hack",
                    "severity": "low",
                    "message": stripped[:120],
                })

            if stripped.count("(") > 5 and len(stripped) > 200:
                self.issues.append({
                    "file": file_path, "line": i, "type": "complex_expression",
                    "severity": "low",
                    "message": "Overly complex expression on single line",
                })

        if language == "Python":
            nesting_depth = self._nesting_depth(source)
            if nesting_depth > 4:
                self.issues.append({
                    "file": file_path, "line": 1, "type": "high_nesting",
                    "severity": "medium",
                    "message": f"Maximum nesting depth is {nesting_depth} (recommended <= 4)",
                })

    def _nesting_depth(self, source: str) -> int:
        max_depth = depth = 0
        for char in source:
            if char == "{":
                depth += 1
                max_depth = max(max_depth, depth)
            elif char == "}":
                depth = max(0, depth - 1)
        if max_depth > 0:
            return max_depth
        depth = 0
        for line in source.split("\n"):
            stripped = line.strip()
            if stripped.endswith(":"):
                depth += 1
                max_depth = max(max_depth, depth)
            elif stripped == "" or stripped.startswith("#"):
                continue
            else:
                depth = 0
        return max_depth

    def finalize(self):
        severity_weights = {"high": 3, "medium": 2, "low": 1, "info": 0.5}
        total = sum(severity_weights.get(i["severity"], 0) for i in self.issues)
        count = len(self.issues)
        self.risk_score = round(min(total / max(count, 1), 10), 2)

    def to_dict(self) -> dict:
        self.finalize()
        by_severity = Counter(i["severity"] for i in self.issues)
        return {
            "risk_score": self.risk_score,
            "total_issues": len(self.issues),
            "by_severity": dict(by_severity),
            "issues": sorted(self.issues, key=lambda x: {"high": 0, "medium": 1, "low": 2, "info": 3}.get(x["severity"], 4))[:100],
        }


class SecurityAnalyzer:
    def __init__(self):
        self.vulnerabilities: list[dict] = []
        self.severity_score: float = 0.0

    PATTERNS: list[tuple[str, str, str, str]] = [
        ("hardcoded_password", r'password\s*=\s*["\'][^"\']+["\']', "medium", "Hardcoded password detected"),
        ("hardcoded_secret", r'(secret|api_key|apikey|token)\s*=\s*["\'][^"\']+["\']', "high", "Hardcoded secret/token detected"),
        ("hardcoded_jwt", r'jwt\s*=\s*["\'][^"\']+\.[^"\']+\.[^"\']+["\']', "high", "Hardcoded JWT token detected"),
        ("eval_usage", r'\beval\s*\(', "high", "eval() can execute arbitrary code"),
        ("exec_usage", r'\bexec\s*\(', "high", "exec() can execute arbitrary code"),
        ("pickle_unsafe", r'\bpickle\.loads?\b', "high", "unpickling untrusted data is insecure"),
        ("yaml_unsafe", r'yaml\.load\s*\(', "medium", "yaml.load() without Loader is unsafe"),
        ("insecure_hash", r'\b(md5|sha1)\b', "medium", "Weak cryptographic hash function"),
        ("command_injection", r'(os\.system|subprocess\.call|subprocess\.Popen|commands\.getoutput)\s*\(', "high", "Potential command injection"),
        ("file_write", r'open\([^)]*["\']w["\']', "low", "File write operation"),
        ("sql_injection", r'execute\(["\'].*\{.*["\']\)|execute\(f["\']', "high", "Possible SQL injection via f-string/format"),
        ("path_traversal", r'(open|read)\s*\(.*\.\./', "medium", "Path traversal risk"),
        ("no_https", r'http://', "low", "Uses HTTP instead of HTTPS"),
        ("debug_enabled", r'debug\s*=\s*True', "low", "Debug mode enabled in production"),
        ("cors_allow_all", r'Access-Control-Allow-Origin\s*:\s*\*', "medium", "CORS allows all origins"),
        ("xss_risk", r'innerHTML\s*=|document\.write\s*\(|\.html\s*\(', "high", "Potential XSS vulnerability"),
        ("unsafe_redirect", r'redirect\(request\.|redirect\([^)]*user[^)]*input', "medium", "Unvalidated redirect"),
    ]

    def add_file(self, file_path: str, source: str, language: str):
        for pattern_type, pattern, severity, message in self.PATTERNS:
            for m in re.finditer(pattern, source, re.IGNORECASE):
                line = source[:m.start()].count("\n") + 1
                existing = any(
                    v["file"] == file_path and v["line"] == line and v["type"] == pattern_type
                    for v in self.vulnerabilities
                )
                if not existing:
                    self.vulnerabilities.append({
                        "file": file_path,
                        "line": line,
                        "type": pattern_type,
                        "severity": severity,
                        "message": message,
                        "match": m.group()[:80],
                    })

    def finalize(self):
        weights = {"high": 10, "medium": 5, "low": 2}
        total = sum(weights.get(v["severity"], 0) for v in self.vulnerabilities)
        self.severity_score = round(min(total / max(len(self.vulnerabilities), 1), 10), 2)

    def to_dict(self) -> dict:
        self.finalize()
        by_severity = Counter(v["severity"] for v in self.vulnerabilities)
        return {
            "severity_score": self.severity_score,
            "total_vulnerabilities": len(self.vulnerabilities),
            "by_severity": dict(by_severity),
            "vulnerabilities": sorted(self.vulnerabilities, key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["severity"], 3))[:100],
        }


class CodeQualityAnalyzer:
    def __init__(self):
        self.metrics: dict[str, Any] = {
            "maintainability": 100.0,
            "complexity": 0.0,
            "duplication": 0.0,
            "documentation": 0.0,
            "testability": 0.0,
            "style_consistency": 100.0,
            "security": 100.0,
            "modularity": 0.0,
            "reliability": 100.0,
        }
        self.total_lines = 0
        self.total_files = 0
        self.file_metrics: list[dict] = []

    def add_file(self, file_path: str, source: str, language: str, file_size: int = 0):
        lines = source.count("\n") + 1
        self.total_lines += lines
        self.total_files += 1

        fm = {"file": file_path, "lines": lines}
        complexity = self._calc_complexity(source, language)
        fm["complexity"] = complexity

        if complexity > 10:
            self.metrics["complexity"] += 1
        if complexity > 20:
            self.metrics["reliability"] -= 2

        doc_ratio = self._doc_ratio(source, language)
        fm["doc_ratio"] = doc_ratio
        fm["line_length_issues"] = self._line_length_issues(source)
        fm["blank_line_ratio"] = self._blank_line_ratio(source)
        self.file_metrics.append(fm)

        self.metrics["documentation"] += doc_ratio * 100

        if fm["line_length_issues"] > lines * 0.1:
            self.metrics["style_consistency"] -= 5

    def _calc_complexity(self, source: str, language: str) -> int:
        if language == "Python":
            try:
                tree = ast.parse(source)
                complexity = 1
                for node in ast.walk(tree):
                    if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                         ast.With, ast.Assert, ast.FunctionDef)):
                        complexity += 1
                    if isinstance(node, ast.BoolOp):
                        complexity += len(node.values) - 1
                return complexity
            except SyntaxError:
                pass
        branching = len(re.findall(r'\b(if|elif|else|for|while|case|catch|except)\b', source))
        logical_ops = len(re.findall(r'\b(and|or|&&|\|\|)\b', source))
        return branching + logical_ops + 1

    def _doc_ratio(self, source: str, language: str) -> float:
        if not source.strip():
            return 0.0
        if language == "Python":
            doc_lines = len(re.findall(r'^\s*"""', source, re.MULTILINE)) * 2
            doc_lines += len(re.findall(r'^\s*#', source, re.MULTILINE))
        elif language in ("JavaScript", "TypeScript"):
            doc_lines = len(re.findall(r'^\s*/\*\*', source, re.MULTILINE)) * 2
            doc_lines += len(re.findall(r'^\s*//', source, re.MULTILINE))
        else:
            doc_lines = len(re.findall(r'^\s*(#|//|--|/\*)', source, re.MULTILINE))
        total = source.count("\n") + 1
        return min(doc_lines / max(total, 1), 1.0)

    def _line_length_issues(self, source: str) -> int:
        return sum(1 for line in source.split("\n") if len(line) > 120)

    def _blank_line_ratio(self, source: str) -> float:
        lines = source.split("\n")
        if not lines:
            return 0.0
        blanks = sum(1 for line in lines if not line.strip())
        return blanks / len(lines)

    def finalize(self):
        if self.total_files == 0:
            return
        self.metrics["documentation"] = round(self.metrics["documentation"] / self.total_files, 1)
        self.metrics["complexity"] = round(
            sum(fm.get("complexity", 0) for fm in self.file_metrics) / self.total_files, 1
        )
        self.metrics["modularity"] = round(
            min(len(set(fm["file"].split("/")[0] for fm in self.file_metrics if "/" in fm["file"])) * 15, 100), 1
        )
        self.metrics["maintainability"] = round(
            max(0, 100 - self.metrics["complexity"] * 2 - (100 - self.metrics["documentation"]) * 0.3), 1
        )
        self.metrics["security"] = round(self.metrics["security"], 1)
        self.metrics["style_consistency"] = round(max(0, self.metrics["style_consistency"]), 1)
        self.metrics["reliability"] = round(max(0, self.metrics["reliability"]), 1)

    def to_dict(self) -> dict:
        self.finalize()
        overall = round(
            sum(self.metrics.values()) / len(self.metrics), 1
        )
        return {
            "overall_score": overall,
            "metrics": self.metrics,
            "total_files": self.total_files,
            "total_lines": self.total_lines,
        }
