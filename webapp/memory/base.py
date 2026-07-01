from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import time
import uuid


class MemoryType(Enum):
    CONVERSATION = "conversation"
    PROJECT = "project"
    CODE = "code"
    USER = "user"
    KNOWLEDGE = "knowledge"
    VECTOR = "vector"


class MemoryImportance(Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class MemoryItem:
    id: str = ""
    content: str = ""
    memory_type: MemoryType = MemoryType.CONVERSATION
    importance: MemoryImportance = MemoryImportance.MEDIUM
    timestamp: float = 0.0
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    embedding: list[float] | None = None
    compressed: bool = False
    access_count: int = 0
    relevance_score: float = 0.0

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content[:500],
            "memory_type": self.memory_type.value,
            "importance": self.importance.name.lower(),
            "timestamp": self.timestamp,
            "tags": self.tags,
            "metadata": self.metadata,
            "compressed": self.compressed,
            "access_count": self.access_count,
            "relevance_score": self.relevance_score,
        }


@dataclass
class MemoryQuery:
    query: str = ""
    memory_type: MemoryType | None = None
    tags: list[str] | None = None
    limit: int = 10
    min_importance: MemoryImportance = MemoryImportance.LOW
    time_range: tuple[float, float] | None = None
    offset: int = 0
    sort_by: str = "relevance"


@dataclass
class MemoryResult:
    items: list[MemoryItem] = field(default_factory=list)
    total: int = 0
    query_time_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "items": [i.to_dict() for i in self.items],
            "total": self.total,
            "query_time_ms": self.query_time_ms,
        }


class BaseMemory(ABC):
    @abstractmethod
    async def store(self, item: MemoryItem) -> str:
        ...

    @abstractmethod
    async def get(self, item_id: str) -> MemoryItem | None:
        ...

    @abstractmethod
    async def search(self, query: MemoryQuery) -> MemoryResult:
        ...

    @abstractmethod
    async def update(self, item: MemoryItem) -> bool:
        ...

    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        ...

    @abstractmethod
    async def count(self) -> int:
        ...

    @abstractmethod
    async def clear(self) -> int:
        ...
