from __future__ import annotations
import logging
import time
from typing import Any

from .base import MemoryItem, MemoryType, MemoryImportance, MemoryQuery, MemoryResult
from .storage import SQLiteMemoryBackend
from .conversation_memory import ConversationMemory
from .project_memory import ProjectMemory
from .code_memory import CodeMemory
from .user_memory import UserMemory
from .vector_memory import VectorMemory, KnowledgeBase, SemanticSearch
from .compression import MemoryCompression
from .ranking import MemoryRanking
from .retrieval import MemoryRetrieval

logger = logging.getLogger("webapp.memory.manager")


class ProfessionalMemoryManager:
    def __init__(self, db_path: str | None = None):
        self._backend = SQLiteMemoryBackend(db_path) if db_path else SQLiteMemoryBackend()

        self.conversation = ConversationMemory(self._backend)
        self.project = ProjectMemory(self._backend)
        self.code = CodeMemory(self._backend)
        self.user = UserMemory(self._backend)
        self.vector = VectorMemory(self._backend)
        self.knowledge_base = KnowledgeBase(self._backend)
        self.semantic_search = SemanticSearch(self._backend)
        self.compression = MemoryCompression(self._backend)
        self.ranking = MemoryRanking(self._backend)
        self.retrieval = MemoryRetrieval(self._backend)

        self._stores = {
            "conversation": self.conversation,
            "project": self.project,
            "code": self.code,
            "user": self.user,
            "vector": self.vector,
            "knowledge": self.knowledge_base,
        }

    def get_store(self, memory_type: str) -> Any:
        return self._stores.get(memory_type)

    async def store(self, content: str, memory_type: str = "conversation",
                     importance: str = "medium", tags: list[str] | None = None,
                     metadata: dict | None = None) -> str:
        store = self.get_store(memory_type)
        if not store:
            raise ValueError(f"Unknown memory type: {memory_type}")

        imp_map = {"low": MemoryImportance.LOW, "medium": MemoryImportance.MEDIUM,
                   "high": MemoryImportance.HIGH, "critical": MemoryImportance.CRITICAL}

        item = MemoryItem(
            content=content,
            memory_type=MemoryType(memory_type),
            importance=imp_map.get(importance, MemoryImportance.MEDIUM),
            tags=tags or [],
            metadata=metadata or {},
        )
        return await store.store(item)

    async def search(self, query: str, memory_type: str | None = None,
                      tags: list[str] | None = None, limit: int = 10) -> MemoryResult:
        mt = MemoryType(memory_type) if memory_type else None
        q = MemoryQuery(query=query, memory_type=mt, tags=tags, limit=limit)
        return await self.retrieval.retrieve(q)

    async def semantic_search_all(self, query: str, limit: int = 10) -> MemoryResult:
        return await self.semantic_search.search_all(query, limit)

    async def get(self, item_id: str) -> MemoryItem | None:
        return await self._backend.get(item_id)

    async def delete(self, item_id: str) -> bool:
        return await self._backend.delete(item_id)

    async def get_stats(self) -> dict:
        return {
            "total": await self._backend.count(),
            "conversation": await self.conversation.count(),
            "project": await self.project.count(),
            "code": await self.code.count(),
            "user": await self.user.count(),
            "knowledge": await self.knowledge_base.count(),
            "vector": await self.vector.count(),
        }

    async def run_maintenance(self) -> dict:
        stats = {}
        compressed = await self.compression.compress_old_memories(days_old=7)
        stats["compressed_old"] = compressed
        by_imp = await self.compression.compress_by_importance(MemoryImportance.LOW)
        stats["compressed_low_importance"] = by_imp
        return stats

    async def clear(self) -> int:
        return await self._backend.clear()


_manager_instance: ProfessionalMemoryManager | None = None


def get_memory_manager() -> ProfessionalMemoryManager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ProfessionalMemoryManager()
    return _manager_instance
