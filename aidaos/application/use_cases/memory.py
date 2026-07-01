"""Memory use case — unified memory operations."""

from __future__ import annotations
import logging
import time
from typing import Any

from ...domain.entities import MemoryItem, MemoryQuery, MemoryType, MemoryImportance
from ...domain.exceptions import MemoryNotFoundError, ValidationError
from ...domain.interfaces import MemoryRepository, MetricsRepository
from ..dtos import MemorySearchRequest

logger = logging.getLogger("aidaos.application.memory")


class MemoryUseCase:
    def __init__(self, memory_repo: MemoryRepository, metrics_repo: MetricsRepository):
        self._memory = memory_repo
        self._metrics = metrics_repo

    async def store(self, content: str, memory_type: str = "conversation",
                    tags: list[str] = None, importance: str = "medium",
                    metadata: dict = None) -> dict:
        if not content:
            raise ValidationError("Content is required")

        item = MemoryItem(
            content=content,
            memory_type=MemoryType(memory_type) if memory_type else MemoryType.CONVERSATION,
            importance=MemoryImportance[importance.upper()] if importance else MemoryImportance.MEDIUM,
            tags=tags or [],
            metadata=metadata or {},
            timestamp=time.time(),
        )

        try:
            mem_id = await self._memory.store(item)
            return {"success": True, "id": mem_id}
        except Exception as e:
            logger.error(f"Memory store failed: {e}")
            return {"success": False, "error": str(e)}

    async def search(self, request: MemorySearchRequest) -> list[dict]:
        query = MemoryQuery(
            query=request.query,
            limit=request.limit,
            tags=request.tags,
        )
        if request.memory_type:
            try:
                query.memory_type = MemoryType(request.memory_type)
            except ValueError:
                pass
        if request.min_importance:
            try:
                query.min_importance = MemoryImportance[request.min_importance.upper()]
            except (ValueError, KeyError):
                pass

        results = await self._memory.search(query)
        return [r.to_dict() for r in results]

    async def get(self, memory_id: str) -> dict:
        item = await self._memory.get(memory_id)
        if not item:
            raise MemoryNotFoundError(f"Memory '{memory_id}' not found")
        return item.to_dict()

    async def delete(self, memory_id: str) -> bool:
        return await self._memory.delete(memory_id)

    async def get_stats(self) -> dict:
        return await self._memory.get_stats()

    async def clear(self, memory_type: str = "") -> int:
        mt = MemoryType(memory_type) if memory_type else None
        return await self._memory.clear(mt)
