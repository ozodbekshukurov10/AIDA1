from __future__ import annotations
import ast
import logging
import re
import time
import uuid
from pathlib import Path
from typing import Any

from .config import Proposal, ProposalType, Severity

logger = logging.getLogger("webapp.self_improvement.refactorer")


class Refactorer:
    def __init__(self):
        self._refactored_files: list[str] = []

    def propose_refactors(self, file_path: str, source: str) -> list[Proposal]:
        proposals = []
        ext = Path(file_path).suffix.lower()
        if ext == ".py":
            proposals.extend(self._propose_python_refactors(file_path, source))
        return proposals

    def _propose_python_refactors(self, file_path: str, source: str) -> list[Proposal]:
        proposals = []
        lines = source.split("\n")

        for_loops = re.findall(r"for\s+(\w+)\s+in\s+(\w+)\s*:", source)
        for var, collection in for_loops:
            append_pattern = rf"for\s+{re.escape(var)}\s+in\s+{re.escape(collection)}\s*:\s*\n\s+{re.escape(var)}\w*\.append\("
            if re.search(append_pattern, source, re.DOTALL):
                proposals.append(Proposal(
                    id=str(uuid.uuid4())[:8],
                    type=ProposalType.REFACTOR,
                    title=f"Replace for-loop with list comprehension ({file_path})",
                    description=f"Loop building a list via .append() can be replaced with a list comprehension for clarity.",
                    severity=Severity.INFO,
                    target_file=file_path,
                    impact="Improved readability, minor performance gain",
                    effort="~2 min",
                    created_at=time.time(),
                    agent_recommendations=["Use list comprehension instead of for+append pattern"],
                ))

        for i, line in enumerate(lines, 1):
            if line.strip().startswith("if ") and line.strip().endswith(":"):
                if i + 2 < len(lines):
                    next_line = lines[i]
                    next_next = lines[i + 1]
                    if next_line.strip().startswith("return ") and next_next.strip().startswith("return "):
                        proposals.append(Proposal(
                            id=str(uuid.uuid4())[:8],
                            type=ProposalType.REFACTOR,
                            title=f"Simplify if/return at {Path(file_path).name}:{i}",
                            description="Multiple sequential if/return blocks. Consider using a dict lookup or ternary.",
                            severity=Severity.LOW,
                            target_file=file_path,
                            created_at=time.time(),
                        ))

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return proposals

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith("get_") or node.name.startswith("fetch_"):
                    returns = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
                    if len(returns) <= 1:
                        body = node.body
                        if (len(body) == 2 and isinstance(body[0], ast.Expr) and
                            isinstance(body[0].value, ast.Call)):
                            pname = body[0].value.func
                            if isinstance(pname, ast.Attribute) and pname.attr == "get":
                                proposals.append(Proposal(
                                    id=str(uuid.uuid4())[:8],
                                    type=ProposalType.REFACTOR,
                                    title=f"Simplify property-like function: {node.name}",
                                    description=f"Function '{node.name}' just wraps a return. Consider replacing with @property or direct attribute access.",
                                    severity=Severity.LOW,
                                    target_file=file_path,
                                    created_at=time.time(),
                                ))

            if isinstance(node, ast.ClassDef):
                if len(node.body) <= 2:
                    all_pass = all(
                        isinstance(item, ast.Pass) or
                        (isinstance(item, ast.FunctionDef) and len(item.body) == 1 and isinstance(item.body[0], ast.Pass))
                        for item in node.body
                    )
                    if all_pass:
                        proposals.append(Proposal(
                            id=str(uuid.uuid4())[:8],
                            type=ProposalType.REFACTOR,
                            title=f"Empty class: {node.name}",
                            description=f"Class '{node.name}' is empty or only has pass statements. Consider removing if unused.",
                            severity=Severity.INFO,
                            target_file=file_path,
                            created_at=time.time(),
                        ))

        return proposals
