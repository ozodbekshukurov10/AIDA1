"""Code analysis and generation use cases."""

from __future__ import annotations
import logging
from typing import Any

from ...domain.entities import ToolSpec, Permission
from ...domain.exceptions import ValidationError
from ...domain.interfaces import CodebaseRepository, ProviderRepository
from ..dtos import CodeAnalysisRequest, CodeGenerationRequest

logger = logging.getLogger("aidaos.application.code")


class CodeAnalysisUseCase:
    def __init__(self, codebase_repo: CodebaseRepository):
        self._codebase = codebase_repo

    async def analyze_file(self, request: CodeAnalysisRequest) -> dict:
        if not request.file_path and not request.source_code:
            raise ValidationError("Either file_path or source_code is required")
        return await self._codebase.index_file(request.file_path or "")

    async def search_symbol(self, query: str, language: str = "") -> list[dict]:
        return await self._codebase.search(query, language)

    async def get_dependencies(self, file_path: str) -> list[str]:
        return await self._codebase.get_dependencies(file_path)

    async def get_file_structure(self, project_path: str) -> dict:
        return await self._codebase.index_project(project_path)

    async def analyze_complexity(self, source_code: str, language: str = "python") -> dict:
        try:
            if language == "python":
                import ast
                tree = ast.parse(source_code)
                complexity = 1
                for node in ast.walk(tree):
                    if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                         ast.With, ast.FunctionDef)):
                        complexity += 1
                    if isinstance(node, ast.BoolOp):
                        complexity += len(node.values) - 1
                return {"cyclomatic_complexity": complexity, "language": language}
            return {"cyclomatic_complexity": 0, "language": language}
        except Exception as e:
            return {"error": str(e)}


class CodeGenerationUseCase:
    def __init__(self, provider_repo: ProviderRepository):
        self._providers = provider_repo

    async def generate(self, request: CodeGenerationRequest) -> dict:
        errors = request.validate()
        if errors:
            raise ValidationError("; ".join(errors))

        prompt = self._build_prompt(request)
        from ...domain.entities import Message, MessageRole
        messages = [Message.system(self._system_prompt()), Message.user(prompt)]
        try:
            completion = await self._providers.chat(messages)
            return {"code": completion.content, "model": completion.model}
        except Exception as e:
            return {"error": str(e), "code": ""}

    def _build_prompt(self, request: CodeGenerationRequest) -> str:
        prompt = f"Generate {request.language} code:\n{request.description}"
        if request.context:
            prompt += f"\n\nContext:\n{request.context}"
        if request.include_tests:
            prompt += f"\n\nInclude {request.test_framework} tests."
        if request.include_docs:
            prompt += "\n\nInclude documentation."
        return prompt

    def _system_prompt(self) -> str:
        return "You are an expert software engineer. Generate production-quality, well-documented code."
