from __future__ import annotations
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any
import math

from .base import MemoryItem, MemoryType, MemoryImportance, MemoryQuery, MemoryResult, BaseMemory

logger = logging.getLogger("webapp.memory.storage")

DB_DIR = Path("data")
DB_PATH = DB_DIR / "aida_long_term_memory.db"


class TfidfVectorizer:
    def __init__(self):
        self.idf: dict[str, float] = {}
        self.doc_count = 0
        self._token_cache: dict[str, list[str]] = {}

    def _tokenize(self, text: str) -> list[str]:
        if text in self._token_cache:
            return self._token_cache[text]
        import re
        tokens = re.findall(r"\b[a-z]{2,}\b", text.lower())
        self._token_cache[text] = tokens
        return tokens

    def fit(self, documents: list[str]):
        import math
        self.doc_count = len(documents)
        df: dict[str, int] = {}
        for doc in documents:
            tokens = set(self._tokenize(doc))
            for t in tokens:
                df[t] = df.get(t, 0) + 1
        self.idf = {t: math.log((self.doc_count + 1) / (f + 1)) + 1 for t, f in df.items()}

    def transform(self, text: str) -> dict[str, float]:
        tokens = self._tokenize(text)
        tf: dict[str, float] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        max_tf = max(tf.values()) if tf else 1
        vector: dict[str, float] = {}
        for t, f in tf.items():
            if t in self.idf:
                vector[t] = (f / max_tf) * self.idf[t]
        return vector

    def similarity(self, v1: dict[str, float], v2: dict[str, float]) -> float:
        dot = sum(v1.get(t, 0) * v2.get(t, 0) for t in set(v1) | set(v2))
        n1 = math.sqrt(sum(v * v for v in v1.values())) or 1
        n2 = math.sqrt(sum(v * v for v in v2.values())) or 1
        return dot / (n1 * n2)


class SQLiteMemoryBackend(BaseMemory):
    def __init__(self, db_path: str | Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._vectorizer = TfidfVectorizer()
        self._init_db()
        self._load_vectorizer()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=OFF")
        return conn

    def _init_db(self):
        conn = self._get_conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    importance INTEGER DEFAULT 1,
                    timestamp REAL NOT NULL,
                    tags TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}',
                    compressed INTEGER DEFAULT 0,
                    access_count INTEGER DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
                CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance);
                CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp);
            """)
            conn.commit()
        finally:
            conn.close()

    def _load_vectorizer(self):
        conn = self._get_conn()
        try:
            docs = [row["content"] for row in conn.execute("SELECT content FROM memories").fetchall()]
            if docs:
                self._vectorizer.fit(docs)
        finally:
            conn.close()

    def _row_to_item(self, row: sqlite3.Row) -> MemoryItem:
        return MemoryItem(
            id=row["id"],
            content=row["content"],
            memory_type=MemoryType(row["memory_type"]),
            importance=MemoryImportance(row["importance"]),
            timestamp=row["timestamp"],
            tags=json.loads(row["tags"]),
            metadata=json.loads(row["metadata"]),
            compressed=bool(row["compressed"]),
            access_count=row["access_count"],
        )

    async def store(self, item: MemoryItem) -> str:
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO memories
                   (id, content, memory_type, importance, timestamp, tags, metadata, compressed, access_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (item.id, item.content, item.memory_type.value, item.importance.value,
                 item.timestamp, json.dumps(item.tags), json.dumps(item.metadata),
                 int(item.compressed), item.access_count),
            )
            conn.commit()
            self._vectorizer.fit([item.content])
            return item.id
        finally:
            conn.close()

    async def get(self, item_id: str) -> MemoryItem | None:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM memories WHERE id=?", (item_id,)).fetchone()
            if row:
                conn.execute("UPDATE memories SET access_count = access_count + 1 WHERE id=?", (item_id,))
                conn.commit()
                return self._row_to_item(row)
            return None
        finally:
            conn.close()

    async def search(self, query: MemoryQuery) -> MemoryResult:
        start = time.monotonic()
        conn = self._get_conn()
        try:
            conditions = []
            params = []

            if query.memory_type:
                conditions.append("memory_type = ?")
                params.append(query.memory_type.value)
            if query.min_importance and query.min_importance != MemoryImportance.LOW:
                conditions.append("importance >= ?")
                params.append(query.min_importance.value)
            if query.time_range:
                conditions.append("timestamp BETWEEN ? AND ?")
                params.extend(query.time_range)
            if query.tags:
                for tag in query.tags:
                    conditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")

            where = " AND ".join(conditions) if conditions else "1=1"

            rows = conn.execute(f"SELECT * FROM memories WHERE {where} ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                               params + [query.limit, query.offset]).fetchall()
            total = conn.execute(f"SELECT COUNT(*) as cnt FROM memories WHERE {where}", params).fetchone()["cnt"]

            items = [self._row_to_item(r) for r in rows]

            if query.query:
                query_vec = self._vectorizer.transform(query.query)
                for item in items:
                    doc_vec = self._vectorizer.transform(item.content)
                    item.relevance_score = self._vectorizer.similarity(query_vec, doc_vec)
                items.sort(key=lambda x: x.relevance_score, reverse=True)

            return MemoryResult(
                items=items[:query.limit],
                total=total,
                query_time_ms=int((time.monotonic() - start) * 1000),
            )
        finally:
            conn.close()

    async def update(self, item: MemoryItem) -> bool:
        conn = self._get_conn()
        try:
            cur = conn.execute(
                """UPDATE memories SET content=?, memory_type=?, importance=?, timestamp=?,
                   tags=?, metadata=?, compressed=?, access_count=? WHERE id=?""",
                (item.content, item.memory_type.value, item.importance.value,
                 item.timestamp, json.dumps(item.tags), json.dumps(item.metadata),
                 int(item.compressed), item.access_count, item.id),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    async def delete(self, item_id: str) -> bool:
        conn = self._get_conn()
        try:
            cur = conn.execute("DELETE FROM memories WHERE id=?", (item_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    async def count(self, memory_type: MemoryType | None = None) -> int:
        conn = self._get_conn()
        try:
            if memory_type:
                row = conn.execute("SELECT COUNT(*) as cnt FROM memories WHERE memory_type=?", (memory_type.value,)).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) as cnt FROM memories").fetchone()
            return row["cnt"]
        finally:
            conn.close()

    async def clear(self) -> int:
        conn = self._get_conn()
        try:
            cnt = conn.execute("SELECT COUNT(*) as cnt FROM memories").fetchone()["cnt"]
            conn.execute("DELETE FROM memories")
            conn.commit()
            return cnt
        finally:
            conn.close()
