from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    id: str = ""
    name: str = ""
    arguments: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "arguments": self.arguments}


@dataclass
class ToolResult:
    success: bool = False
    output: str = ""
    data: Any = None
    error: str | None = None


@dataclass
class ToolDef:
    name: str = ""
    description: str = ""
    parameters: dict = field(default_factory=dict)
    required: list[str] = field(default_factory=list)
    category: str = "general"


class BaseToolCallingLayer(ABC):
    @abstractmethod
    async def select_tool(self, task: str, available_tools: list[ToolDef] | None = None) -> ToolDef | None:
        ...

    @abstractmethod
    async def execute_tool(self, tool_name: str, params: dict) -> ToolResult:
        ...

    @abstractmethod
    async def parse_tool_call(self, text: str) -> ToolCall | None:
        ...

    @abstractmethod
    async def format_tool_result(self, result: ToolResult) -> str:
        ...


class AidaToolCallingLayer(BaseToolCallingLayer):
    def __init__(self):
        self._builtin_tools: dict[str, ToolDef] = {
            "code_generate": ToolDef("code_generate", "Generate source code",
                                     {"language": "string", "task": "string"}, ["task"]),
            "web_search": ToolDef("web_search", "Search the web",
                                  {"query": "string"}, ["query"]),
            "file_read": ToolDef("file_read", "Read file contents",
                                 {"path": "string"}, ["path"]),
            "file_write": ToolDef("file_write", "Write to file",
                                  {"path": "string", "content": "string"}, ["path", "content"]),
            "shell_exec": ToolDef("shell_exec", "Execute shell command",
                                  {"command": "string"}, ["command"]),
            "database_query": ToolDef("database_query", "Query database",
                                      {"query": "string"}, ["query"]),
            "memory_store": ToolDef("memory_store", "Store in long-term memory",
                                    {"content": "string", "key": "string"}, ["content"]),
            "memory_recall": ToolDef("memory_recall", "Recall from memory",
                                     {"query": "string"}, ["query"]),
        }

    async def select_tool(self, task: str, available_tools: list[ToolDef] | None = None) -> ToolDef | None:
        tools = available_tools or list(self._builtin_tools.values())
        task_lower = task.lower()
        for tool in tools:
            if tool.name in task_lower:
                return tool
        return None

    async def execute_tool(self, tool_name: str, params: dict) -> ToolResult:
        return ToolResult(
            success=True,
            output=f"Executed tool '{tool_name}' with params: {params}",
            data={"tool": tool_name, "params": params},
        )

    async def parse_tool_call(self, text: str) -> ToolCall | None:
        import re
        pattern = r"<tool_call>\s*(\w+)\s*(.*?)\s*</tool_call>"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            name = match.group(1)
            args_str = match.group(2)
            args = {}
            for kv in re.findall(r"(\w+)=[\"']([^\"']*)[\"']", args_str):
                args[kv[0]] = kv[1]
            return ToolCall(name=name, arguments=args)
        return None

    async def format_tool_result(self, result: ToolResult) -> str:
        if result.success:
            return f"<tool_result>{result.output}</tool_result>"
        return f"<tool_error>{result.error}</tool_error>"
