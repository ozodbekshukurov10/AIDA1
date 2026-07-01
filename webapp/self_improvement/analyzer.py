from __future__ import annotations
import ast
import logging
import os
import re
import time
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

from .config import Proposal, ProposalType, ProposalStatus, Severity
from .monitor import SystemMonitor

logger = logging.getLogger("webapp.self_improvement.analyzer")


class ImprovementAnalyzer:
    def __init__(self, monitor: SystemMonitor | None = None):
        self._monitor = monitor or SystemMonitor.get_instance()
        self._proposals: list[Proposal] = []

    def analyze_performance(self) -> list[Proposal]:
        proposals = []
        report = self._monitor.get_performance_report(hours=24)
        for b in report.bottlenecks:
            agent = b.get("agent", "unknown")
            rec = b.get("recommendation", "")
            proposals.append(Proposal(
                id=str(uuid.uuid4())[:8],
                type=ProposalType.PERFORMANCE,
                title=f"Performance bottleneck: {agent}",
                description=rec,
                severity=Severity.HIGH if b.get("type") == "error_rate" else Severity.MEDIUM,
                impact=b.get("value", ""),
                metrics_before={"avg_latency_ms": report.avg_latency_ms, "error_rate": report.error_rate},
                created_at=time.time(),
                agent_recommendations=[rec],
            ))
        if report.trends.get("latency") == "increasing":
            proposals.append(Proposal(
                id=str(uuid.uuid4())[:8],
                type=ProposalType.PERFORMANCE,
                title="Latency is trending upward",
                description="System latency has been increasing over the last 3 measurement periods. Consider provider optimization or model downgrade.",
                severity=Severity.MEDIUM,
                metrics_before={"trend": "increasing"},
                created_at=time.time(),
            ))
        return proposals

    def analyze_errors(self) -> list[Proposal]:
        proposals = []
        error_summary = self._monitor.get_error_summary(hours=24)
        if error_summary["total_errors"] > 10:
            top_source = max(error_summary["by_source"].items(), key=lambda x: x[1]) if error_summary["by_source"] else ("", 0)
            proposals.append(Proposal(
                id=str(uuid.uuid4())[:8],
                type=ProposalType.MONITORING,
                title=f"High error rate: {error_summary['total_errors']} errors in 24h",
                description=f"Source '{top_source[0]}' has {top_source[1]} errors. Investigate and fix.",
                severity=Severity.HIGH if error_summary["total_errors"] > 50 else Severity.MEDIUM,
                metrics_before=error_summary,
                created_at=time.time(),
            ))
        unresolved = self._monitor.get_errors(hours=168, unresolved=True)
        if len(unresolved) > 5:
            proposals.append(Proposal(
                id=str(uuid.uuid4())[:8],
                type=ProposalType.MONITORING,
                title=f"{len(unresolved)} unresolved errors from the past week",
                description="Review and resolve pending errors. Some may indicate systemic issues.",
                severity=Severity.LOW,
                created_at=time.time(),
            ))
        return proposals

    def analyze_code_quality(self, file_path: str, source: str) -> list[Proposal]:
        proposals = []
        ext = Path(file_path).suffix.lower()
        if ext == ".py":
            proposals.extend(self._analyze_python_file(file_path, source))
        elif ext in (".js", ".ts", ".jsx", ".tsx"):
            proposals.extend(self._analyze_js_file(file_path, source))
        return proposals

    def _analyze_python_file(self, file_path: str, source: str) -> list[Proposal]:
        proposals = []
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            proposals.append(Proposal(
                id=str(uuid.uuid4())[:8],
                type=ProposalType.REFACTOR,
                title=f"Syntax error in {Path(file_path).name}",
                description=str(e),
                severity=Severity.HIGH,
                target_file=file_path,
                created_at=time.time(),
            ))
            return proposals

        lines = source.split("\n")

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                line = getattr(node, "lineno", 0)
                func_lines = getattr(node, "end_lineno", line) - line
                if func_lines > 50:
                    proposals.append(Proposal(
                        id=str(uuid.uuid4())[:8],
                        type=ProposalType.REFACTOR,
                        title=f"Long function: {node.name} ({func_lines} lines)",
                        description=f"Function '{node.name}' in {file_path}:{line} is {func_lines} lines. Consider breaking into smaller functions.",
                        severity=Severity.LOW,
                        target_file=file_path,
                        impact="Reduced maintainability",
                        effort=f"~{func_lines // 10} min refactor",
                        created_at=time.time(),
                    ))

                complexity = sum(1 for n in ast.walk(node) if isinstance(n, (ast.If, ast.While, ast.For, ast.ExceptHandler)))
                if complexity > 10:
                    proposals.append(Proposal(
                        id=str(uuid.uuid4())[:8],
                        type=ProposalType.REFACTOR,
                        title=f"High cyclomatic complexity: {node.name} ({complexity})",
                        description=f"Function '{node.name}' has cyclomatic complexity of {complexity} (>10 recommended). Simplify conditional logic.",
                        severity=Severity.MEDIUM,
                        target_file=file_path,
                        created_at=time.time(),
                    ))

                docstring = ast.get_docstring(node)
                if docstring is None:
                    proposals.append(Proposal(
                        id=str(uuid.uuid4())[:8],
                        type=ProposalType.REFACTOR,
                        title=f"Missing docstring: {node.name}",
                        description=f"Function '{node.name}' in {file_path}:{line} has no docstring.",
                        severity=Severity.INFO,
                        target_file=file_path,
                        created_at=time.time(),
                    ))

                for d in node.decorator_list:
                    if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute):
                        if d.func.attr == "route" and node.args.args:
                            first = node.args.args[0].arg
                            if first not in ("self", "cls"):
                                proposals.append(Proposal(
                                    id=str(uuid.uuid4())[:8],
                                    type=ProposalType.REFACTOR,
                                    title=f"Route handler missing self: {node.name}",
                                    description=f"Route handler '{node.name}' first param is '{first}' instead of 'self'.",
                                    severity=Severity.MEDIUM,
                                    target_file=file_path,
                                    created_at=time.time(),
                                ))

            elif isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node)
                if docstring is None:
                    proposals.append(Proposal(
                        id=str(uuid.uuid4())[:8],
                        type=ProposalType.REFACTOR,
                        title=f"Missing docstring: class {node.name}",
                        description=f"Class '{node.name}' in {file_path}:{getattr(node, 'lineno', 0)} has no docstring.",
                        severity=Severity.INFO,
                        target_file=file_path,
                        created_at=time.time(),
                    ))

                if len(node.bases) > 3:
                    proposals.append(Proposal(
                        id=str(uuid.uuid4())[:8],
                        type=ProposalType.ARCHITECTURE,
                        title=f"Multiple inheritance: {node.name}",
                        description=f"Class '{node.name}' inherits from {len(node.bases)} base classes. Consider composition over inheritance.",
                        severity=Severity.LOW,
                        target_file=file_path,
                        created_at=time.time(),
                    ))

            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                    proposals.append(Proposal(
                        id=str(uuid.uuid4())[:8],
                        type=ProposalType.SECURITY,
                        title=f"Unsafe {node.func.id}() call",
                        description=f"'{node.func.id}()' at {file_path}:{getattr(node, 'lineno', 0)} allows arbitrary code execution.",
                        severity=Severity.HIGH,
                        target_file=file_path,
                        created_at=time.time(),
                    ))

        bare_excepts = len(re.findall(r"^\s*except\s*:", source, re.MULTILINE))
        if bare_excepts > 2:
            proposals.append(Proposal(
                id=str(uuid.uuid4())[:8],
                type=ProposalType.REFACTOR,
                title=f"{bare_excepts} bare except clauses",
                description=f"Found {bare_excepts} bare 'except:' clauses. Specify exception types to avoid catching unexpected errors.",
                severity=Severity.MEDIUM,
                target_file=file_path,
                created_at=time.time(),
            ))

        todos = len(re.findall(r"#\s*TODO", source, re.IGNORECASE))
        if todos > 0:
            proposals.append(Proposal(
                id=str(uuid.uuid4())[:8],
                type=ProposalType.REFACTOR,
                title=f"{todos} TODO(s) in {Path(file_path).name}",
                description=f"Found {todos} TODO comment(s). Review and resolve them.",
                severity=Severity.INFO,
                target_file=file_path,
                created_at=time.time(),
            ))

        return proposals

    def _analyze_js_file(self, file_path: str, source: str) -> list[Proposal]:
        proposals = []
        lines = source.split("\n")

        for i, line in enumerate(lines, 1):
            if "innerHTML" in line and "=" in line:
                proposals.append(Proposal(
                    id=str(uuid.uuid4())[:8],
                    type=ProposalType.SECURITY,
                    title=f"Potential XSS at {Path(file_path).name}:{i}",
                    description="innerHTML assignment can lead to XSS. Use textContent or sanitize input.",
                    severity=Severity.HIGH,
                    target_file=file_path,
                    created_at=time.time(),
                ))
            if "eval(" in line:
                proposals.append(Proposal(
                    id=str(uuid.uuid4())[:8],
                    type=ProposalType.SECURITY,
                    title=f"eval() at {Path(file_path).name}:{i}",
                    description="eval() executes arbitrary code. Avoid it.",
                    severity=Severity.HIGH,
                    target_file=file_path,
                    created_at=time.time(),
                ))
            if "==" in line and "===" not in line and "!==" not in line:
                if re.search(r"[^!=]==[^=]", line):
                    proposals.append(Proposal(
                        id=str(uuid.uuid4())[:8],
                        type=ProposalType.REFACTOR,
                        title=f"Loose equality at {Path(file_path).name}:{i}",
                        description="Use === instead of == for strict equality.",
                        severity=Severity.LOW,
                        target_file=file_path,
                        created_at=time.time(),
                    ))

        func_count = len(re.findall(r"(?:function\s+\w+|=>\s*\{)", source))
        if func_count > 20:
            proposals.append(Proposal(
                id=str(uuid.uuid4())[:8],
                type=ProposalType.REFACTOR,
                title=f"Large file: {Path(file_path).name} ({func_count} functions)",
                description=f"File contains {func_count} functions. Consider splitting into modules.",
                severity=Severity.LOW,
                target_file=file_path,
                created_at=time.time(),
            ))

        return proposals

    def analyze_coverage(self, files: list[dict], repo_path: str = "") -> list[Proposal]:
        proposals = []
        tested = set()
        untested = []

        for f in files:
            ext = f.get("extension", "")
            name = Path(f["path"]).stem
            if ext == ".py" and name.startswith("test_"):
                tested_file = name[5:]
                tested.add(tested_file)
                tested.add(tested_file.replace("_", ""))

        for f in files:
            ext = f.get("extension", "")
            if ext != ".py":
                continue
            name = Path(f["path"]).stem
            if name.startswith("test_") or name == "__init__":
                continue
            if name not in tested and name not in tested:
                untested.append(f["path"])

        if untested:
            batch = untested[:10]
            proposals.append(Proposal(
                id=str(uuid.uuid4())[:8],
                type=ProposalType.TEST,
                title=f"{len(untested)} module(s) without tests",
                description=f"Found {len(untested)} untested Python modules. First 10: {', '.join(batch[:5])}...",
                severity=Severity.MEDIUM,
                impact="Low test coverage increases regression risk",
                effort=f"~{len(untested) * 10} min to write tests",
                created_at=time.time(),
            ))

        return proposals

    def generate_all_proposals(self, files: list[dict] | None = None,
                                repo_path: str = "") -> list[Proposal]:
        proposals = []
        proposals.extend(self.analyze_performance())
        proposals.extend(self.analyze_errors())
        if files:
            proposals.extend(self.analyze_coverage(files, repo_path))
            for f in files:
                ext = f.get("extension", "")
                fp = f.get("abs_path", "")
                if ext in (".py", ".js", ".ts", ".jsx", ".tsx"):
                    try:
                        source = Path(fp).read_text(encoding="utf-8", errors="replace")
                    except Exception:
                        continue
                    proposals.extend(self.analyze_code_quality(f["path"], source))

        proposals.sort(key=lambda p: {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(p.severity.value, 5))
        self._proposals.extend(proposals)
        return proposals

    def add_proposals(self, proposals: list[Proposal]):
        existing_ids = {p.id for p in self._proposals}
        for p in proposals:
            if p.id not in existing_ids:
                self._proposals.append(p)
                existing_ids.add(p.id)

    def get_pending_proposals(self) -> list[Proposal]:
        return [p for p in self._proposals if p.status == ProposalStatus.PENDING]

    def get_proposal(self, proposal_id: str) -> Proposal | None:
        for p in self._proposals:
            if p.id == proposal_id:
                return p
        return None

    def get_all_proposals(self) -> list[Proposal]:
        return self._proposals

    def clear_applied(self):
        self._proposals = [p for p in self._proposals if p.status != ProposalStatus.APPLIED]
