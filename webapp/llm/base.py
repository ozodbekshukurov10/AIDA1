from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import AsyncIterator, Optional
from enum import Enum
import json
import time


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    role: MessageRole
    content: str
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
    name: str | None = None

    def to_dict(self) -> dict:
        d = {"role": self.role.value, "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        if self.name:
            d["name"] = self.name
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Message:
        return cls(
            role=MessageRole(d["role"]),
            content=d.get("content", ""),
            tool_calls=[ToolCall.from_dict(tc) for tc in d.get("tool_calls", [])],
            tool_call_id=d.get("tool_call_id"),
            name=d.get("name"),
        )


@dataclass
class ToolCall:
    id: str
    type: str = "function"
    function: dict | None = None

    def to_dict(self) -> dict:
        return {"id": self.id, "type": self.type, "function": self.function or {}}


@dataclass
class Completion:
    content: str
    model: str
    provider: str
    usage: dict | None = None
    finish_reason: str | None = None
    latency_ms: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class StreamingChunk:
    content: str
    done: bool = False
    finish_reason: str | None = None
    usage: dict | None = None


@dataclass
class ProviderConfig:
    name: str
    model: str = ""
    base_url: str = ""
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60
    extra: dict = field(default_factory=dict)


class ProviderStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    LOADING = "loading"


class BaseProvider(ABC):
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.status = ProviderStatus.OFFLINE
        self._last_error: str | None = None

    @abstractmethod
    async def chat(self, messages: list[Message], **kwargs) -> Completion:
        ...

    @abstractmethod
    async def chat_stream(self, messages: list[Message], **kwargs) -> AsyncIterator[StreamingChunk]:
        ...
        if False:
            yield StreamingChunk(content="")

    @abstractmethod
    async def check_health(self) -> bool:
        ...

    @abstractmethod
    async def list_models(self) -> list[str]:
        ...

    def to_dict(self) -> dict:
        return {
            "name": self.config.name,
            "model": self.config.model,
            "status": self.status.value,
            "last_error": self._last_error,
        }
