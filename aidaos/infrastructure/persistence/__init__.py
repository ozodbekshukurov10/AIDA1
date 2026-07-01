"""Persistence adapters — implement domain interfaces using existing SQLite stores."""

from __future__ import annotations
import logging
import time
from typing import Any

from ...domain.entities import MemoryItem, MemoryQuery, MemoryType, MemoryImportance
from ...domain.interfaces import MemoryRepository, SessionRepository, KnowledgeRepository, MetricsRepository

logger = logging.getLogger("aidaos.infrastructure.persistence")


class MemoryRepoAdapter(MemoryRepository):
    def __init__(self):
        self._store = None

    def _get_store(self):
        if self._store is None:
            from webapp.memory.storage import SQLiteMemoryBackend
            self._store = SQLiteMemoryBackend()
        return self._store

    async def store(self, item: MemoryItem) -> str:
        store = self._get_store()
        mem_id = store.store(
            content=item.content,
            memory_type=item.memory_type.value,
            importance=item.importance.value,
            tags=item.tags,
            metadata=item.metadata,
        )
        return mem_id

    async def get(self, memory_id: str) -> MemoryItem | None:
        store = self._get_store()
        result = store.get(memory_id)
        if not result:
            return None
        return MemoryItem(
            id=result["id"], content=result["content"],
            memory_type=MemoryType(result["memory_type"]) if "memory_type" in result else MemoryType.CONVERSATION,
            importance=MemoryImportance(result.get("importance", 1)),
            tags=result.get("tags", []), metadata=result.get("metadata", {}),
            timestamp=result.get("timestamp", 0),
        )

    async def search(self, query: MemoryQuery) -> list[MemoryItem]:
        store = self._get_store()
        results = store.search(
            query=query.query, limit=query.limit,
            memory_type=query.memory_type.value if query.memory_type else None,
            tags=query.tags,
        )
        items = []
        for r in results:
            try:
                mt = MemoryType(r.get("memory_type", "conversation"))
            except ValueError:
                mt = MemoryType.CONVERSATION
            try:
                imp = MemoryImportance(r.get("importance", 1))
            except ValueError:
                imp = MemoryImportance.MEDIUM
            items.append(MemoryItem(
                id=r["id"], content=r["content"],
                memory_type=mt, importance=imp,
                tags=r.get("tags", []), metadata=r.get("metadata", {}),
                timestamp=r.get("timestamp", 0),
                access_count=r.get("access_count", 0),
                relevance_score=r.get("relevance_score", 0),
            ))
        return items

    async def update(self, item: MemoryItem) -> bool:
        store = self._get_store()
        return store.update(item.id, item.to_dict())

    async def delete(self, memory_id: str) -> bool:
        store = self._get_store()
        return store.delete(memory_id)

    async def count(self, memory_type: MemoryType | None = None) -> int:
        store = self._get_store()
        return store.count(memory_type.value if memory_type else None)

    async def clear(self, memory_type: MemoryType | None = None) -> int:
        store = self._get_store()
        return store.clear(memory_type.value if memory_type else None)

    async def get_stats(self) -> dict:
        store = self._get_store()
        return store.get_stats()


class SessionRepoAdapter(SessionRepository):
    def __init__(self):
        self._store = None

    def _get_store(self):
        if self._store is None:
            from webapp.memory.session import get_session_store
            self._store = get_session_store()
        return self._store

    async def create(self, session) -> str:
        store = self._get_store()
        return store.create_session(session.title)

    async def get(self, session_id: str):
        store = self._get_store()
        data = store.get_session(session_id)
        if not data:
            return None
        from ...domain.entities import Session
        return Session(id=data["id"], title=data.get("title", ""),
                       created_at=data.get("created_at", 0),
                       updated_at=data.get("updated_at", 0),
                       message_count=data.get("message_count", 0))

    async def list(self, limit=50, offset=0):
        store = self._get_store()
        sessions = store.list_sessions(limit=limit, offset=offset)
        from ...domain.entities import Session
        return [Session(id=s["id"], title=s.get("title", "")) for s in sessions]

    async def update(self, session) -> bool:
        store = self._get_store()
        store.update_session(session.id, {"title": session.title})
        return True

    async def delete(self, session_id: str) -> bool:
        store = self._get_store()
        return store.delete_session(session_id)

    async def add_message(self, session_id: str, message: dict) -> bool:
        store = self._get_store()
        store.add_message(session_id, message)
        return True

    async def get_messages(self, session_id: str, limit=100) -> list[dict]:
        store = self._get_store()
        return store.get_messages(session_id, limit=limit)


class KnowledgeRepoAdapter(KnowledgeRepository):
    def __init__(self):
        self._store = None

    def _get_store(self):
        if self._store is None:
            from webapp.memory.knowledge import get_knowledge_store
            self._store = get_knowledge_store()
        return self._store

    async def add(self, content, tags=None, source=""):
        store = self._get_store()
        return store.add(content, tags or [], source)

    async def search(self, query, limit=10):
        store = self._get_store()
        return store.search(query, limit=limit)

    async def get(self, knowledge_id):
        store = self._get_store()
        return store.get(knowledge_id)

    async def delete(self, knowledge_id):
        store = self._get_store()
        return store.delete(knowledge_id)

    async def get_stats(self):
        store = self._get_store()
        return {"total": store.count()}


class MetricsRepoAdapter(MetricsRepository):
    def __init__(self):
        self._collector = None

    def _get_collector(self):
        if self._collector is None:
            from webapp.memory.metrics import get_metrics_collector
            self._collector = get_metrics_collector()
        return self._collector

    async def record_request(self, endpoint, method, status, latency_ms, **kwargs):
        c = self._get_collector()
        c.record_request(endpoint, method, status, latency_ms,
                         provider=kwargs.get("provider", ""), model=kwargs.get("model", ""))

    async def record_agent_call(self, agent, task, success, latency_ms, **kwargs):
        c = self._get_collector()
        c.record_agent_call(agent, task, success, latency_ms,
                            tokens_used=kwargs.get("tokens_used", 0))

    async def get_stats(self, hours=24):
        c = self._get_collector()
        return c.get_stats(hours=hours)

    async def get_agent_stats(self, hours=24):
        c = self._get_collector()
        stats = c.get_stats(hours=hours)
        return [{
            "agent_name": "system",
            "avg_latency_ms": stats.get("avg_latency_ms", 0),
            "error_rate": stats.get("error_rate", 0),
            "call_count": stats.get("total_agent_calls", 0),
        }]

    async def get_health_score(self) -> float:
        try:
            stats = await self.get_stats(hours=24)
            err = stats.get("error_rate", 0)
            return max(0, 100 - err * 5)
        except Exception:
            return 50.0
