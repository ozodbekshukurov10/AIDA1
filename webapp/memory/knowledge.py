from __future__ import annotations
import json
import math
import re
import sqlite3
import threading
import time
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "aida_knowledge.db"

_lock = threading.Lock()


class TfidfVectorizer:
    def __init__(self):
        self.docs: list[dict] = []
        self.idf: dict[str, float] = {}

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\b[a-z]{2,}\b", text.lower())

    def fit(self, docs: list[dict]):
        self.docs = docs
        n = len(docs)
        df: Counter = Counter()
        for doc in docs:
            tokens = set(self._tokenize(doc.get("content", "")))
            for t in tokens:
                df[t] += 1
        self.idf = {t: math.log((n + 1) / (c + 1)) + 1 for t, c in df.items()}

    def transform(self, text: str) -> dict[str, float]:
        tokens = self._tokenize(text)
        if not tokens:
            return {}
        tf = Counter(tokens)
        max_tf = max(tf.values())
        return {
            t: (tf[t] / max_tf) * self.idf.get(t, 1.0)
            for t in set(tokens)
        }

    def similarity(self, vec1: dict[str, float], vec2: dict[str, float]) -> float:
        common = set(vec1) & set(vec2)
        if not common:
            return 0.0
        dot = sum(vec1[t] * vec2[t] for t in common)
        norm1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)


class KnowledgeStore:
    _instance: KnowledgeStore | None = None

    def __init__(self, db_path: str | Path = DB_PATH):
        self.db_path = str(db_path)
        self.vectorizer = TfidfVectorizer()
        self._init_db()
        self._load()

    def _init_db(self):
        with _lock, sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    content TEXT,
                    tags TEXT DEFAULT '',
                    created_at REAL,
                    updated_at REAL
                )
            """)

    def _load(self):
        with _lock, sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT id, content, tags FROM documents").fetchall()
        docs = [{"id": r[0], "content": r[1], "tags": r[2]} for r in rows]
        if docs:
            self.vectorizer.fit(docs)

    def add(self, content: str, tags: list[str] | None = None) -> str:
        doc_id = uuid.uuid4().hex[:16]
        now = time.time()
        tags_str = ",".join(tags or [])
        with _lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO documents (id, content, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (doc_id, content, tags_str, now, now),
            )
        self.vectorizer.fit(self.list_all())
        return doc_id

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not self.vectorizer.docs:
            return []
        query_vec = self.vectorizer.transform(query)
        if not query_vec:
            return []
        scored = []
        for doc in self.vectorizer.docs:
            doc_vec = self.vectorizer.transform(doc.get("content", ""))
            score = self.vectorizer.similarity(query_vec, doc_vec)
            scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"id": d["id"], "content": d["content"][:1000], "tags": d.get("tags", ""), "score": round(s, 4)}
            for s, d in scored[:top_k]
        ]

    def list_all(self) -> list[dict]:
        with _lock, sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT id, content, tags, created_at FROM documents ORDER BY created_at DESC").fetchall()
        return [{"id": r[0], "content": r[1], "tags": r[2], "created_at": r[3]} for r in rows]

    def delete(self, doc_id: str) -> bool:
        with _lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            deleted = cur.rowcount > 0
        if deleted:
            self.vectorizer.fit(self.list_all())
        return deleted

    def count(self) -> int:
        with _lock, sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]


_store_instance: KnowledgeStore | None = None


def get_knowledge_store() -> KnowledgeStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = KnowledgeStore()
    return _store_instance
