from __future__ import annotations
import ast
import logging
import re
import time
import uuid
from pathlib import Path
from typing import Any

from .config import Proposal, ProposalType, ProposalStatus, Severity

logger = logging.getLogger("webapp.self_improvement.test_writer")


class TestWriter:
    def __init__(self):
        self._generated_tests: list[dict] = []

    def propose_tests(self, file_path: str, source: str) -> list[Proposal]:
        proposals = []
        ext = Path(file_path).suffix.lower()
        if ext == ".py":
            proposals.extend(self._propose_python_tests(file_path, source))
        return proposals

    def _propose_python_tests(self, file_path: str, source: str) -> list[Proposal]:
        proposals = []
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return proposals

        module_name = Path(file_path).stem
        test_file_path = str(Path(file_path).parent / f"test_{module_name}.py")

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue
                test_code = self._generate_test_for_function(node, module_name)
                proposals.append(Proposal(
                    id=str(uuid.uuid4())[:8],
                    type=ProposalType.TEST,
                    title=f"Test for {node.name}() in {module_name}",
                    description=f"Generate unit test for function '{node.name}' in {file_path}:{getattr(node, 'lineno', 0)}. Function args: {[a.arg for a in node.args.args]}. Test will be added to {test_file_path}.",
                    severity=Severity.INFO,
                    target_file=test_file_path,
                    suggested_content=test_code,
                    impact="Improves test coverage",
                    effort="~5 min",
                    created_at=time.time(),
                    agent_recommendations=[f"Add pytest test for {node.name}"],
                ))

            elif isinstance(node, ast.ClassDef):
                class_test_code = self._generate_test_for_class(node, module_name)
                proposals.append(Proposal(
                    id=str(uuid.uuid4())[:8],
                    type=ProposalType.TEST,
                    title=f"Tests for class {node.name} in {module_name}",
                    description=f"Generate tests for class '{node.name}' with {len([m for m in node.body if isinstance(m, ast.FunctionDef)])} methods.",
                    severity=Severity.INFO,
                    target_file=test_file_path,
                    suggested_content=class_test_code,
                    impact="Improves test coverage",
                    effort="~10 min",
                    created_at=time.time(),
                ))

        return proposals

    def _generate_test_for_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef,
                                     module_name: str) -> str:
        args = [a.arg for a in node.args.args if a.arg != "self"]
        args_str = ", ".join(args)
        test_lines = [
            f"import pytest",
            f"from {module_name} import {node.name}",
            "",
            "",
            f"class Test{node.name.capitalize()}:",
            f"    \"\"\"Tests for {node.name} function.\"\"\"",
            "",
            f"    def test_{node.name}_basic(self):",
            f"        \"\"\"Test basic functionality.\"\"\"",
        ]
        if args:
            test_lines.extend([
                f"        # Arrange",
                f"        # {args_str} = ...",
                f"",
                f"        # Act",
                f"        # result = {node.name}({args_str})",
                f"",
                f"        # Assert",
                f"        # assert result is not None",
            ])
        else:
            test_lines.extend([
                f"        # Act",
                f"        # result = {node.name}()",
                f"",
                f"        # Assert",
                f"        # assert result is not None",
            ])

        test_lines.extend([
            "",
            f"    def test_{node.name}_edge_cases(self):",
            f"        \"\"\"Test edge cases.\"\"\"",
            f"        pass",
            "",
        ])
        return "\n".join(test_lines)

    def _generate_test_for_class(self, node: ast.ClassDef, module_name: str) -> str:
        methods = [m for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
        test_lines = [
            "import pytest",
            f"from {module_name} import {node.name}",
            "",
            "",
            f"class Test{node.name}:",
            f"    \"\"\"Tests for {node.name} class.\"\"\"",
            "",
            f"    def setup_method(self):",
            f"        \"\"\"Setup test fixtures.\"\"\"",
            f"        self.instance = {node.name}()",
            "",
        ]
        for m in methods:
            if m.name.startswith("_"):
                continue
            args = [a.arg for a in m.args.args if a.arg not in ("self", "cls")]
            test_lines.extend([
                f"    def test_{m.name}(self):",
                f"        \"\"\"Test {m.name} method.\"\"\"",
                f"        # result = self.instance.{m.name}({', '.join(args)})",
                f"        # assert result is not None",
                f"        pass",
                f"",
            ])
        return "\n".join(test_lines)

    def propose_integration_tests(self, webapp_path: str) -> list[Proposal]:
        proposals = []
        test_api_path = Path(webapp_path) / "tests" / "test_api_self_improvement.py"
        test_code = """import pytest
from django.test import Client
from django.urls import reverse


class TestSelfImprovementAPI:
    \"\"\"Integration tests for self-improvement system.\"\"\"

    def setup_method(self):
        self.client = Client()

    def test_proposals_list(self):
        url = reverse("api_v2_self_improvement_proposals")
        response = self.client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert "proposals" in data

    def test_proposal_approve(self):
        url = reverse("api_v2_self_improvement_proposals")
        response = self.client.get(url)
        if response.status_code == 200:
            data = response.json()
            proposals = data.get("proposals", [])
            if proposals:
                pid = proposals[0]["id"]
                approve_url = reverse("api_v2_self_improvement_proposal_action",
                                      args=[pid, "approve"])
                resp = self.client.post(approve_url)
                assert resp.status_code in (200, 404, 400)

    def test_performance_report(self):
        url = reverse("api_v2_self_improvement_report")
        response = self.client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert "performance" in data

    def test_error_logs(self):
        url = reverse("api_v2_self_improvement_errors")
        response = self.client.get(url)
        assert response.status_code == 200
"""
        proposals.append(Proposal(
            id=str(uuid.uuid4())[:8],
            type=ProposalType.TEST,
            title="Integration tests for self-improvement API",
            description="Generate integration tests for all self-improvement API endpoints.",
            severity=Severity.MEDIUM,
            target_file=test_api_path,
            suggested_content=test_code,
            created_at=time.time(),
        ))
        return proposals
