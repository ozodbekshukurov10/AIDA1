from __future__ import annotations
import logging
import time
from typing import Any

from .base import MemoryItem, MemoryType, MemoryImportance, MemoryQuery, MemoryResult, BaseMemory
from .storage import SQLiteMemoryBackend

logger = logging.getLogger("webapp.memory.conversation")


class ConversationMemory(BaseMemory):
    def __init__(self, backend: SQLiteMemoryBackend | None = None):
        self._backend = backend or SQLiteMemoryBackend()

    async def store(self, item: MemoryItem) -> str:
        item.memory_type = MemoryType.CONVERSATION
        item.importance = MemoryImportance.MEDIUM
        return await self._backend.store(item)

    async def store_exchange(self, session_id: str, role: str, content: str, **metadata) -> str:
        item = MemoryItem(
            content=content,
            memory_type=MemoryType.CONVERSATION,
            tags=[session_id, role],
            metadata={"session_id": session_id, "role": role, **metadata},
        )
        return await self._backend.store(item)

    async def get_conversation(self, session_id: str, limit: int = 50) -> list[MemoryItem]:
        query = MemoryQuery(
            query="",
            tags=[session_id],
            limit=limit,
            sort_by="timestamp",
        )
        result = await self._backend.search(query)
        result.items.sort(key=lambda x: x.timestamp)
        return result.items

    async def get(self, item_id: str) -> MemoryItem | None:
        return await self._backend.get(item_id)

    async def search(self, query: MemoryQuery) -> MemoryResult:
        query.memory_type = MemoryType.CONVERSATION
        return await self._backend.search(query)

    async def update(self, item: MemoryItem) -> bool:
        return await self._backend.update(item)

    async def delete(self, item_id: str) -> bool:
        return await self._backend.delete(item_id)

    async def count(self) -> int:
        return await self._backend.count(MemoryType.CONVERSATION)

    async def clear(self) -> int:
        return await self._backend.clear()
