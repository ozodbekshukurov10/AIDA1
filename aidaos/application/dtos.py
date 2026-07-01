"""Data Transfer Objects for the Application layer."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


@dataclass
class ChatRequest:
    message: str
    session_id: str = ""
    provider: str = ""
    model: str = ""
    stream: bool = False
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors = []
        if not self.message or not self.message.strip():
            errors.append("Message is required")
        if len(self.message) > 100000:
            errors.append("Message too long (max 100k chars)")
        if self.temperature < 0 or self.temperature > 2:
            errors.append("Temperature must be 0-2")
        return errors


@dataclass
class ChatResponse:
    content: str
    session_id: str = ""
    model: str = ""
    provider: str = ""
    latency_ms: int = 0
    usage: dict[str, Any] = field(default_factory=dict)
    finish_reason: str = ""


@dataclass
class AgentExecuteRequest:
    agent_name: str
    prompt: str
    system_prompt: str = ""
    thread_id: str = ""
    max_iterations: int = 10
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors = []
        if not self.agent_name:
            errors.append("Agent name is required")
        if not self.prompt or not self.prompt.strip():
            errors.append("Prompt is required")
        return errors


@dataclass
class ToolExecuteRequest:
    tool_name: str
    params: dict[str, Any] = field(default_factory=dict)
    require_confirmation: bool = False

    def validate(self) -> list[str]:
        errors = []
        if not self.tool_name:
            errors.append("Tool name is required")
        return errors


@dataclass
class MemorySearchRequest:
    query: str = ""
    memory_type: str = ""
    tags: list[str] = field(default_factory=list)
    limit: int = 10
    min_importance: str = "low"

    def validate(self) -> list[str]:
        errors = []
        if not self.query:
            errors.append("Query is required")
        return errors


@dataclass
class CodeAnalysisRequest:
    file_path: str = ""
    source_code: str = ""
    language: str = "python"
    analysis_types: list[str] = field(default_factory=lambda: ["quality", "security", "complexity"])


@dataclass
class CodeGenerationRequest:
    description: str
    language: str = "python"
    context: str = ""
    test_framework: str = "pytest"
    include_tests: bool = True
    include_docs: bool = False

    def validate(self) -> list[str]:
        errors = []
        if not self.description:
            errors.append("Description is required")
        return errors


@dataclass
class ProjectInfo:
    id: str = ""
    name: str = ""
    path: str = ""
    language: str = ""
    file_count: int = 0
    total_lines: int = 0
    has_tests: bool = False
    has_docs: bool = False
    frameworks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "path": self.path,
            "language": self.language, "file_count": self.file_count,
            "total_lines": self.total_lines, "has_tests": self.has_tests,
            "has_docs": self.has_docs, "frameworks": self.frameworks,
        }


@dataclass
class Pagination:
    page: int = 1
    per_page: int = 20
    total: int = 0

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page

    @property
    def total_pages(self) -> int:
        return max(1, (self.total + self.per_page - 1) // self.per_page)

    def to_dict(self) -> dict:
        return {"page": self.page, "per_page": self.per_page, "total": self.total, "pages": self.total_pages}
