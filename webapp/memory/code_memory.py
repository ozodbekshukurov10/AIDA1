from __future__ import annotations
import logging
from typing import Any

from .base import MemoryItem, MemoryType, MemoryImportance, MemoryQuery, MemoryResult, BaseMemory
from .storage import SQLiteMemoryBackend

logger = logging.getLogger("webapp.memory.code")


class CodeMemory(BaseMemory):
    def __init__(self, backend: SQLiteMemoryBackend | None = None):
        self._backend = backend or SQLiteMemoryBackend()

    async def store(self, item: MemoryItem) -> str:
        item.memory_type = MemoryType.CODE
        return await self._backend.store(item)

    async def store_code(self, code: str, language: str, name: str = "",
                         description: str = "", tags: list[str] | None = None) -> str:
        item = MemoryItem(
            content=code,
            memory_type=MemoryType.CODE,
            importance=MemoryImportance.MEDIUM,
            tags=(tags or []) + [language, name],
            metadata={"language": language, "name": name, "description": description},
        )
        return await self._backend.store(item)

    async def store_pattern(self, pattern_name: str, pattern_code: str, language: str,
                            description: str = "") -> str:
        item = MemoryItem(
            content=pattern_code,
            memory_type=MemoryType.CODE,
            importance=MemoryImportance.HIGH,
            tags=[language, "pattern", pattern_name],
            metadata={"type": "pattern", "language": language, "name": pattern_name, "description": description},
        )
        return await self._backend.store(item)

    async def find_by_language(self, language: str, limit: int = 20) -> list[MemoryItem]:
        query = MemoryQuery(query="", tags=[language], memory_type=MemoryType.CODE, limit=limit)
        result = await self._backend.search(query)
        return result.items

    async def find_by_name(self, name: str, limit: int = 10) -> list[MemoryItem]:
        query = MemoryQuery(query=name, memory_type=MemoryType.CODE, limit=limit)
        result = await self._backend.search(query)
        return result.items

    async def get(self, item_id: str) -> MemoryItem | None:
        return await self._backend.get(item_id)

    async def search(self, query: MemoryQuery) -> MemoryResult:
        query.memory_type = MemoryType.CODE
        return await self._backend.search(query)

    async def update(self, item: MemoryItem) -> bool:
        return await self._backend.update(item)

    async def delete(self, item_id: str) -> bool:
        return await self._backend.delete(item_id)

    async def count(self) -> int:
        return await self._backend.count(MemoryType.CODE)

    async def clear(self) -> int:
        return await self._backend.clear()
