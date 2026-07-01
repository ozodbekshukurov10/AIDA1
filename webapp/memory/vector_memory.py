from __future__ import annotations
import json
import logging
import math
import time
from typing import Any

from .base import MemoryItem, MemoryType, MemoryImportance, MemoryQuery, MemoryResult, BaseMemory
from .storage import SQLiteMemoryBackend, TfidfVectorizer

logger = logging.getLogger("webapp.memory.vector")


class VectorMemory(BaseMemory):
    def __init__(self, backend: SQLiteMemoryBackend | None = None):
        self._backend = backend or SQLiteMemoryBackend()
        self._embeddings: dict[str, list[float]] = {}
        self._dimension = 128

    async def store(self, item: MemoryItem) -> str:
        item.memory_type = MemoryType.VECTOR
        if not item.embedding:
            item.embedding = self._compute_embedding(item.content)
        item_id = await self._backend.store(item)
        self._embeddings[item_id] = item.embedding
        return item_id

    async def store_with_vector(self, content: str, vector: list[float],
                                 tags: list[str] | None = None, **metadata) -> str:
        item = MemoryItem(
            content=content,
            memory_type=MemoryType.VECTOR,
            embedding=vector,
            tags=tags or [],
            metadata=metadata,
        )
        item_id = await self._backend.store(item)
        self._embeddings[item_id] = vector
        return item_id

    def _compute_embedding(self, text: str) -> list[float]:
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            return model.encode(text).tolist()
        except ImportError:
            pass
        try:
            import httpx
            resp = httpx.post(
                "http://localhost:11434/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text},
                timeout=5,
            )
            if resp.status_code == 200:
                return resp.json().get("embedding", self._fallback_embedding(text))
        except Exception:
            pass
        return self._fallback_embedding(text)

    def _fallback_embedding(self, text: str) -> list[float]:
        vec = [0.0] * self._dimension
        for i, ch in enumerate(text[:2000]):
            vec[i % self._dimension] += ord(ch) / 255.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1
        return [v / norm for v in vec]

    def _cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = math.sqrt(sum(a * a for a in v1)) or 1
        n2 = math.sqrt(sum(b * b for b in v2)) or 1
        return dot / (n1 * n2)

    async def search(self, query: MemoryQuery) -> MemoryResult:
        start = time.monotonic()
        query_vec = self._compute_embedding(query.query) if query.query else None

        result = await self._backend.search(query)
        if query_vec and result.items:
            for item in result.items:
                stored_emb = self._embeddings.get(item.id)
                if stored_emb:
                    item.relevance_score = self._cosine_similarity(query_vec, stored_emb)
                else:
                    text_vec = self._compute_embedding(item.content)
                    item.relevance_score = self._cosine_similarity(query_vec, text_vec)
            result.items.sort(key=lambda x: x.relevance_score, reverse=True)

        result.query_time_ms = int((time.monotonic() - start) * 1000)
        return result

    async def get(self, item_id: str) -> MemoryItem | None:
        return await self._backend.get(item_id)

    async def update(self, item: MemoryItem) -> bool:
        return await self._backend.update(item)

    async def delete(self, item_id: str) -> bool:
        self._embeddings.pop(item_id, None)
        return await self._backend.delete(item_id)

    async def count(self) -> int:
        return await self._backend.count(MemoryType.VECTOR)

    async def clear(self) -> int:
        self._embeddings.clear()
        return await self._backend.clear()


class KnowledgeBase(BaseMemory):
    def __init__(self, backend: SQLiteMemoryBackend | None = None):
        self._backend = backend or SQLiteMemoryBackend()
        self._vectorizer = TfidfVectorizer()
        self._memory_type = MemoryType.KNOWLEDGE

    async def store(self, item: MemoryItem) -> str:
        item.memory_type = MemoryType.KNOWLEDGE
        item_id = await self._backend.store(item)
        self._vectorizer.fit([item.content])
        return item_id

    async def store_knowledge(self, content: str, category: str = "general",
                               tags: list[str] | None = None, source: str = "") -> str:
        item = MemoryItem(
            content=content,
            memory_type=MemoryType.KNOWLEDGE,
            importance=MemoryImportance.HIGH,
            tags=(tags or []) + [category],
            metadata={"category": category, "source": source},
        )
        item_id = await self._backend.store(item)
        self._vectorizer.fit([content])
        return item_id

    async def search(self, query: MemoryQuery) -> MemoryResult:
        query.memory_type = MemoryType.KNOWLEDGE
        result = await self._backend.search(query)

        if query.query and result.items:
            query_vec = self._vectorizer.transform(query.query)
            for item in result.items:
                doc_vec = self._vectorizer.transform(item.content)
                item.relevance_score = self._vectorizer.similarity(query_vec, doc_vec)
            result.items.sort(key=lambda x: x.relevance_score, reverse=True)

        return result

    async def get(self, item_id: str) -> MemoryItem | None:
        return await self._backend.get(item_id)

    async def update(self, item: MemoryItem) -> bool:
        return await self._backend.update(item)

    async def delete(self, item_id: str) -> bool:
        return await self._backend.delete(item_id)

    async def count(self) -> int:
        return await self._backend.count(MemoryType.KNOWLEDGE)

    async def clear(self) -> int:
        return await self._backend.clear()

    async def get_all_categories(self) -> list[str]:
        result = await self._backend.search(MemoryQuery(query="", limit=1000))
        categories = set()
        for item in result.items:
            cat = item.metadata.get("category", "general")
            categories.add(cat)
        return sorted(categories)


class SemanticSearch:
    def __init__(self, backend: SQLiteMemoryBackend | None = None):
        self._backend = backend or SQLiteMemoryBackend()
        self._vectorizer = TfidfVectorizer()
        self._vector_memory = VectorMemory(backend)

    async def search_all(self, query: str, limit: int = 10,
                          memory_types: list[MemoryType] | None = None) -> MemoryResult:
        start = time.monotonic()

        q = MemoryQuery(query=query, limit=limit * 3)
        result = await self._backend.search(q)

        if memory_types:
            result.items = [i for i in result.items if i.memory_type in memory_types]

        if not result.items:
            return MemoryResult(query_time_ms=int((time.monotonic() - start) * 1000))

        query_vec = self._vectorizer.transform(query)
        for item in result.items:
            doc_vec = self._vectorizer.transform(item.content)
            tfidf_score = self._vectorizer.similarity(query_vec, doc_vec)
            try:
                emb = self._vector_memory._compute_embedding(item.content)
                q_emb = self._vector_memory._compute_embedding(query)
                vec_score = self._vector_memory._cosine_similarity(q_emb, emb)
                item.relevance_score = (tfidf_score * 0.4) + (vec_score * 0.6)
            except Exception:
                item.relevance_score = tfidf_score

        result.items.sort(key=lambda x: x.relevance_score, reverse=True)
        result.total = len(result.items)
        result.items = result.items[:limit]
        result.query_time_ms = int((time.monotonic() - start) * 1000)

        return result

    async def search_by_type(self, query: str, memory_type: MemoryType,
                               limit: int = 10) -> MemoryResult:
        q = MemoryQuery(query=query, memory_type=memory_type, limit=limit)
        return await self.search_all(query, limit, [memory_type])

    async def hybrid_search(self, query: str, tags: list[str] | None = None,
                              limit: int = 10) -> MemoryResult:
        q = MemoryQuery(query=query, tags=tags, limit=limit)
        result = await self._backend.search(q)

        if result.items:
            query_vec = self._vectorizer.transform(query)
            for item in result.items:
                doc_vec = self._vectorizer.transform(item.content)
                item.relevance_score = self._vectorizer.similarity(query_vec, doc_vec)
            result.items.sort(key=lambda x: x.relevance_score, reverse=True)
            result.items = result.items[:limit]

        return result
