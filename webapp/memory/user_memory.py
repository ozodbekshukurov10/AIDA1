from __future__ import annotations
import json
import logging
from typing import Any

from .base import MemoryItem, MemoryType, MemoryImportance, MemoryQuery, MemoryResult, BaseMemory
from .storage import SQLiteMemoryBackend

logger = logging.getLogger("webapp.memory.user")


class UserMemory(BaseMemory):
    def __init__(self, backend: SQLiteMemoryBackend | None = None):
        self._backend = backend or SQLiteMemoryBackend()

    async def store(self, item: MemoryItem) -> str:
        item.memory_type = MemoryType.USER
        return await self._backend.store(item)

    async def store_preference(self, user_id: str, key: str, value: Any) -> str:
        item = MemoryItem(
            content=json.dumps({"key": key, "value": value}),
            memory_type=MemoryType.USER,
            importance=MemoryImportance.MEDIUM,
            tags=[user_id, key, "preference"],
            metadata={"user_id": user_id, "key": key, "type": "preference"},
        )
        return await self._backend.store(item)

    async def get_preference(self, user_id: str, key: str) -> MemoryItem | None:
        query = MemoryQuery(
            query="",
            tags=[user_id, key, "preference"],
            memory_type=MemoryType.USER,
            limit=1,
        )
        result = await self._backend.search(query)
        return result.items[0] if result.items else None

    async def store_profile(self, user_id: str, profile: dict) -> str:
        item = MemoryItem(
            content=json.dumps(profile, indent=2),
            memory_type=MemoryType.USER,
            importance=MemoryImportance.HIGH,
            tags=[user_id, "profile"],
            metadata={"user_id": user_id, "type": "profile"},
        )
        return await self._backend.store(item)

    async def get_profile(self, user_id: str) -> MemoryItem | None:
        query = MemoryQuery(
            query="",
            tags=[user_id, "profile"],
            memory_type=MemoryType.USER,
            limit=1,
        )
        result = await self._backend.search(query)
        return result.items[0] if result.items else None

    async def store_behavior(self, user_id: str, action: str, context: dict) -> str:
        item = MemoryItem(
            content=json.dumps({"action": action, "context": context}),
            memory_type=MemoryType.USER,
            importance=MemoryImportance.LOW,
            tags=[user_id, "behavior", action],
            metadata={"user_id": user_id, "action": action, "type": "behavior"},
        )
        return await self._backend.store(item)

    async def get(self, item_id: str) -> MemoryItem | None:
        return await self._backend.get(item_id)

    async def search(self, query: MemoryQuery) -> MemoryResult:
        query.memory_type = MemoryType.USER
        return await self._backend.search(query)

    async def update(self, item: MemoryItem) -> bool:
        return await self._backend.update(item)

    async def delete(self, item_id: str) -> bool:
        return await self._backend.delete(item_id)

    async def count(self) -> int:
        return await self._backend.count(MemoryType.USER)

    async def clear(self) -> int:
        return await self._backend.clear()
