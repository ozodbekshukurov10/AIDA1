from __future__ import annotations
import logging
import time
from typing import Any

from .base import MemoryItem, MemoryType, MemoryImportance, MemoryQuery, MemoryResult, BaseMemory
from .storage import SQLiteMemoryBackend
from .ranking import MemoryRanking
from .vector_memory import SemanticSearch

logger = logging.getLogger("webapp.memory.retrieval")


class MemoryRetrieval(BaseMemory):
    def __init__(self, backend: SQLiteMemoryBackend | None = None):
        self._backend = backend or SQLiteMemoryBackend()
        self._semantic = SemanticSearch(backend)
        self._ranker = MemoryRanking(backend)

    async def retrieve(self, query: MemoryQuery) -> MemoryResult:
        start = time.monotonic()

        if query.query:
            result = await self._semantic.hybrid_search(
                query=query.query,
                tags=query.tags,
                limit=query.limit * 2,
            )
        else:
            result = await self._backend.search(query)

        if query.memory_type and result.items:
            result.items = [i for i in result.items if i.memory_type == query.memory_type]

        if query.tags and result.items:
            result.items = [i for i in result.items if any(t in i.tags for t in query.tags)]

        if result.items:
            result.items = await self._ranker.rank(query.query, result.items)
            result.items = result.items[:query.limit]

        result.total = len(result.items)
        result.query_time_ms = int((time.monotonic() - start) * 1000)
        return result

    async def retrieve_context(self, context: str, limit: int = 5) -> str:
        result = await self.retrieve(MemoryQuery(query=context, limit=limit))

        if not result.items:
            return ""

        lines = []
        for i, item in enumerate(result.items, 1):
            type_tag = item.memory_type.value.upper()
            relevance = f"{item.relevance_score:.2f}" if item.relevance_score else "N/A"
            content = item.content[:300]
            lines.append(f"[{i}] ({type_tag} rel:{relevance}) {content}")

        return "\n\n".join(lines)

    async def store(self, item: MemoryItem) -> str:
        return await self._backend.store(item)

    async def get(self, item_id: str) -> MemoryItem | None:
        return await self._backend.get(item_id)

    async def search(self, query: MemoryQuery) -> MemoryResult:
        return await self.retrieve(query)

    async def update(self, item: MemoryItem) -> bool:
        return await self._backend.update(item)

    async def delete(self, item_id: str) -> bool:
        return await self._backend.delete(item_id)

    async def count(self) -> int:
        return await self._backend.count()

    async def clear(self) -> int:
        return await self._backend.clear()
