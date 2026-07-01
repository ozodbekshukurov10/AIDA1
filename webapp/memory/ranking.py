from __future__ import annotations
import logging
import math
import time
from typing import Any

from .base import MemoryItem, MemoryType, MemoryImportance, MemoryQuery, MemoryResult, BaseMemory
from .storage import SQLiteMemoryBackend, TfidfVectorizer

logger = logging.getLogger("webapp.memory.ranking")


class MemoryRanking:
    def __init__(self, backend: SQLiteMemoryBackend | None = None):
        self._backend = backend or SQLiteMemoryBackend()
        self._vectorizer = TfidfVectorizer()

    async def rank(self, query: str, items: list[MemoryItem]) -> list[MemoryItem]:
        if not query:
            return items

        query_vec = self._vectorizer.transform(query)

        for item in items:
            doc_vec = self._vectorizer.transform(item.content)
            tfidf_score = self._vectorizer.similarity(query_vec, doc_vec)
            recency = self._recency_score(item.timestamp)
            importance = item.importance.value / 3.0
            popularity = min(item.access_count / 10.0, 1.0)

            item.relevance_score = (
                tfidf_score * 0.40 +
                recency * 0.25 +
                importance * 0.20 +
                popularity * 0.15
            )

        items.sort(key=lambda x: x.relevance_score, reverse=True)
        return items

    def _recency_score(self, timestamp: float) -> float:
        age_hours = (time.time() - timestamp) / 3600
        return math.exp(-age_hours / 24.0)

    async def rank_by_importance(self, items: list[MemoryItem]) -> list[MemoryItem]:
        for item in items:
            recency = self._recency_score(item.timestamp)
            importance = item.importance.value / 3.0
            item.relevance_score = (importance * 0.6) + (recency * 0.4)
        items.sort(key=lambda x: x.relevance_score, reverse=True)
        return items

    async def rank_by_recency(self, items: list[MemoryItem]) -> list[MemoryItem]:
        items.sort(key=lambda x: x.timestamp, reverse=True)
        return items

    async def rank_by_popularity(self, items: list[MemoryItem]) -> list[MemoryItem]:
        items.sort(key=lambda x: x.access_count, reverse=True)
        return items

    async def get_top_memories(self, memory_type: MemoryType | None = None,
                                 limit: int = 10) -> list[MemoryItem]:
        query = MemoryQuery(query="", memory_type=memory_type, limit=limit * 3)
        result = await self._backend.search(query)

        for item in result.items:
            importance = item.importance.value / 3.0
            recency = self._recency_score(item.timestamp)
            popularity = min(item.access_count / 10.0, 1.0)
            item.relevance_score = (importance * 0.5) + (recency * 0.3) + (popularity * 0.2)

        result.items.sort(key=lambda x: x.relevance_score, reverse=True)
        return result.items[:limit]
