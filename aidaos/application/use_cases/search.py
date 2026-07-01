"""Search use case — unified search across codebase, memory, and knowledge."""

from __future__ import annotations
import logging
from typing import Any

from ...domain.interfaces import CodebaseRepository, MemoryRepository, KnowledgeRepository


logger = logging.getLogger("aidaos.application.search")


class SearchUseCase:
    def __init__(
        self,
        codebase_repo: CodebaseRepository,
        memory_repo: MemoryRepository,
        knowledge_repo: KnowledgeRepository,
    ):
        self._codebase = codebase_repo
        self._memory = memory_repo
        self._knowledge = knowledge_repo

    async def search_all(self, query: str, limit: int = 10) -> dict:
        results = {"codebase": [], "memory": [], "knowledge": []}
        try:
            results["codebase"] = await self._codebase.search(query)
        except Exception as e:
            logger.debug(f"Codebase search failed: {e}")
        try:
            from ...domain.entities import MemoryQuery
            mq = MemoryQuery(query=query, limit=limit)
            mem_results = await self._memory.search(mq)
            results["memory"] = [r.to_dict() for r in mem_results]
        except Exception as e:
            logger.debug(f"Memory search failed: {e}")
        try:
            kn_results = await self._knowledge.search(query, limit=limit)
            results["knowledge"] = kn_results
        except Exception as e:
            logger.debug(f"Knowledge search failed: {e}")
        return results

    async def search_code(self, query: str, language: str = "") -> list[dict]:
        return await self._codebase.search(query, language)

    async def search_memory(self, query: str, limit: int = 10) -> list[dict]:
        from ...domain.entities import MemoryQuery
        mq = MemoryQuery(query=query, limit=limit)
        results = await self._memory.search(mq)
        return [r.to_dict() for r in results]

    async def search_knowledge(self, query: str, limit: int = 10) -> list[dict]:
        return await self._knowledge.search(query, limit=limit)
