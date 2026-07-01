from __future__ import annotations
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import uuid


@dataclass
class MemoryItem:
    id: str = ""
    key: str = ""
    content: str = ""
    importance: float = 1.0
    timestamp: float = 0.0
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    access_count: int = 0

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "id": self.id, "key": self.key,
            "content": self.content[:200],
            "importance": self.importance,
            "timestamp": self.timestamp,
            "tags": self.tags, "access_count": self.access_count,
        }


class BaseMemoryLayer(ABC):
    @abstractmethod
    async def store(self, key: str, content: Any, importance: float = 1.0,
                    tags: list[str] | None = None) -> str:
        ...

    @abstractmethod
    async def recall(self, query: str, limit: int = 10) -> list[MemoryItem]:
        ...

    @abstractmethod
    async def get(self, key: str) -> MemoryItem | None:
        ...

    @abstractmethod
    async def forget(self, key: str) -> bool:
        ...

    @abstractmethod
    async def consolidate(self) -> int:
        ...

    @abstractmethod
    async def clear(self) -> int:
        ...


class AidaMemoryLayer(BaseMemoryLayer):
    def __init__(self, capacity: int = 100000):
        self._capacity = capacity
        self._store: dict[str, MemoryItem] = {}
        self._index: dict[str, list[str]] = {}

    async def store(self, key: str, content: Any, importance: float = 1.0,
                    tags: list[str] | None = None) -> str:
        if len(self._store) >= self._capacity:
            oldest = min(self._store.values(), key=lambda x: (x.importance, x.timestamp))
            del self._store[oldest.key]
        item = MemoryItem(key=key, content=str(content), importance=importance, tags=tags or [])
        self._store[key] = item
        for tag in (tags or []):
            if tag not in self._index:
                self._index[tag] = []
            self._index[tag].append(key)
        return item.id

    async def recall(self, query: str, limit: int = 10) -> list[MemoryItem]:
        query_lower = query.lower()
        scored = []
        for item in self._store.values():
            score = 0.0
            if query_lower in item.content.lower():
                score += item.importance * 0.5
            if query_lower in item.key.lower():
                score += item.importance * 0.3
            for tag in item.tags:
                if query_lower in tag.lower():
                    score += 0.2
            if score > 0:
                scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    async def get(self, key: str) -> MemoryItem | None:
        item = self._store.get(key)
        if item:
            item.access_count += 1
        return item

    async def forget(self, key: str) -> bool:
        if key in self._store:
            item = self._store.pop(key)
            for tag in item.tags:
                if tag in self._index and key in self._index[tag]:
                    self._index[tag].remove(key)
            return True
        return False

    async def consolidate(self) -> int:
        threshold = time.time() - 86400 * 30
        to_remove = [
            k for k, v in self._store.items()
            if v.importance < 0.3 and v.timestamp < threshold
        ]
        for k in to_remove:
            await self.forget(k)
        return len(to_remove)

    async def clear(self) -> int:
        count = len(self._store)
        self._store.clear()
        self._index.clear()
        return count
