from __future__ import annotations
import logging
import time
from typing import Any

from .base import MemoryItem, MemoryType, MemoryImportance, MemoryQuery, MemoryResult, BaseMemory
from .storage import SQLiteMemoryBackend

logger = logging.getLogger("webapp.memory.project")


class ProjectMemory(BaseMemory):
    def __init__(self, backend: SQLiteMemoryBackend | None = None):
        self._backend = backend or SQLiteMemoryBackend()

    async def store(self, item: MemoryItem) -> str:
        item.memory_type = MemoryType.PROJECT
        return await self._backend.store(item)

    async def store_project_info(self, project_name: str, key: str, value: Any, importance: MemoryImportance = MemoryImportance.MEDIUM) -> str:
        item = MemoryItem(
            content=str(value),
            memory_type=MemoryType.PROJECT,
            importance=importance,
            tags=[project_name, key],
            metadata={"project": project_name, "key": key},
        )
        return await self._backend.store(item)

    async def get_project_info(self, project_name: str, key: str | None = None) -> list[MemoryItem]:
        tags = [project_name]
        if key:
            tags.append(key)
        query = MemoryQuery(query="", tags=tags, limit=50, sort_by="timestamp")
        result = await self._backend.search(query)
        return result.items

    async def store_structure(self, project_name: str, structure: dict) -> str:
        import json
        item = MemoryItem(
            content=json.dumps(structure, indent=2),
            memory_type=MemoryType.PROJECT,
            importance=MemoryImportance.HIGH,
            tags=[project_name, "structure"],
            metadata={"project": project_name, "type": "structure"},
        )
        return await self._backend.store(item)

    async def get(self, item_id: str) -> MemoryItem | None:
        return await self._backend.get(item_id)

    async def search(self, query: MemoryQuery) -> MemoryResult:
        query.memory_type = MemoryType.PROJECT
        return await self._backend.search(query)

    async def update(self, item: MemoryItem) -> bool:
        return await self._backend.update(item)

    async def delete(self, item_id: str) -> bool:
        return await self._backend.delete(item_id)

    async def count(self) -> int:
        return await self._backend.count(MemoryType.PROJECT)

    async def clear(self) -> int:
        return await self._backend.clear()
