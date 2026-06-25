import json
import logging
import math
import os
import threading
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("webapp.knowledge")

BASE_DIR = Path(__file__).resolve().parent.parent
STORE_DIR = BASE_DIR / ".aida_knowledge"
STORE_DIR.mkdir(exist_ok=True)
VECTORS_FILE = STORE_DIR / "vectors.json"
DOCS_FILE = STORE_DIR / "docs.json"


# ── Simple TF-IDF Vectorizer (no dependencies) ───────────────────────────

class TfidfVectorizer:
    def __init__(self):
        self.vocab: dict[str, int] = {}
        self.idf: dict[int, float] = {}
        self._fitted = False

    def fit(self, texts: list[str]):
        n_docs = len(texts)
        df: dict[str, int] = {}
        for text in texts:
            tokens = set(self._tokenize(text))
            for t in tokens:
                df[t] = df.get(t, 0) + 1
        self.vocab = {t: i for i, t in enumerate(sorted(df.keys()))}
        self.idf = {i: math.log((n_docs + 1) / (df[t] + 1)) + 1 for t, i in self.vocab.items()}
        self._fitted = True

    def transform(self, text: str) -> list[float]:
        if not self._fitted:
            return []
        tokens = self._tokenize(text)
        tf: dict[int, float] = {}
        max_freq = 0
        for t in tokens:
            if t in self.vocab:
                idx = self.vocab[t]
                tf[idx] = tf.get(idx, 0) + 1
                max_freq = max(max_freq, tf[idx])
        vec = [0.0] * len(self.vocab)
        for idx, count in tf.items():
            tf_val = count / max_freq if max_freq else 0
            vec[idx] = tf_val * self.idf.get(idx, 1)
        return vec

    def _tokenize(self, text: str) -> list[str]:
        import re
        text = text.lower()
        tokens = re.findall(r"[a-z0-9_]+", text)
        min_len = 2
        return [t for t in tokens if len(t) >= min_len]


# ── Embedding Provider (Ollama) ──────────────────────────────────────────

class EmbeddingProvider:
    def __init__(self, url: str = "http://localhost:11434"):
        self.url = url.rstrip("/")
        self._cache: dict[str, list[float]] = {}

    def embed(self, text: str) -> list[float]:
        if text in self._cache:
            return self._cache[text]
        if len(text) < 10:
            return self._fallback_embed(text)
        try:
            payload = json.dumps({"model": "qwen2.5:3b", "prompt": text}).encode("utf-8")
            req = urllib.request.Request(
                f"{self.url}/api/embeddings", data=payload,
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                vec = data.get("embedding", [])
                if vec:
                    self._cache[text] = vec
                    return vec
        except Exception:
            pass
        return self._fallback_embed(text)

    def _fallback_embed(self, text: str) -> list[float]:
        n = len(text)
        return [float(ord(c) % 100) / 100.0 for c in text[:64]] + [0.0] * max(0, 64 - n)


# ── Knowledge Store ──────────────────────────────────────────────────────

@dataclass
class KnowledgeDoc:
    id: str
    content: str
    metadata: dict
    vector: list[float] | None = None
    created_at: float = 0.0


class KnowledgeStore:
    def __init__(self, store_dir: str | Path = None):
        self.store_dir = Path(store_dir) if store_dir else STORE_DIR
        self.store_dir.mkdir(exist_ok=True)
        self.vectors_file = self.store_dir / "vectors.json"
        self.docs_file = self.store_dir / "docs.json"
        self.embedder = EmbeddingProvider()
        self.vectorizer = TfidfVectorizer()
        self._lock = threading.Lock()
        self._docs: dict[str, KnowledgeDoc] = {}
        self._all_texts: list[str] = []
        self._fitted = False
        self._load()

    # ── CRUD ──────────────────────────────────────────────────────────────

    def add(self, content: str, metadata: dict = None, doc_id: str = None) -> str:
        doc_id = doc_id or f"doc-{int(time.time())}-{len(self._docs)}"
        with self._lock:
            vec = self.embedder.embed(content)
            doc = KnowledgeDoc(
                id=doc_id, content=content, metadata=metadata or {},
                vector=vec, created_at=time.time())
            self._docs[doc_id] = doc
            self._all_texts.append(content)
            self._fitted = False
            self._save()
        return doc_id

    def get(self, doc_id: str) -> KnowledgeDoc | None:
        return self._docs.get(doc_id)

    def remove(self, doc_id: str) -> bool:
        with self._lock:
            if doc_id in self._docs:
                del self._docs[doc_id]
                self._all_texts = [d.content for d in self._docs.values()]
                self._fitted = False
                self._save()
                return True
        return False

    def list_all(self) -> list[dict]:
        return [
            {"id": d.id, "content": d.content[:200],
             "metadata": d.metadata, "created_at": d.created_at}
            for d in self._docs.values()
        ]

    # ── Search ────────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        query_vec = self.embedder.embed(query)
        results = []
        with self._lock:
            for doc in self._docs.values():
                if doc.vector:
                    sim = self._cosine_sim(query_vec, doc.vector)
                    results.append((sim, doc))
        results.sort(key=lambda x: x[0], reverse=True)

        if not results or results[0][0] < 0.3:
            tfidf_results = self._search_tfidf(query, top_k)
            if tfidf_results:
                return tfidf_results

        return [
            {"id": d.id, "content": d.content, "metadata": d.metadata,
             "score": round(s, 4), "created_at": d.created_at}
            for s, d in results[:top_k]
        ]

    def _search_tfidf(self, query: str, top_k: int) -> list[dict]:
        if not self._fitted and self._all_texts:
            self.vectorizer.fit(self._all_texts)
            self._fitted = True
        if not self._fitted or not self._all_texts:
            return []
        query_vec = self.vectorizer.transform(query)
        scores = []
        for doc in self._docs.values():
            doc_vec = self.vectorizer.transform(doc.content)
            sim = self._cosine_sim(query_vec, doc_vec) if doc_vec else 0
            scores.append((sim, doc))
        scores.sort(key=lambda x: x[0], reverse=True)
        return [
            {"id": d.id, "content": d.content, "metadata": d.metadata,
             "score": round(s, 4), "created_at": d.created_at}
            for s, d in scores[:top_k] if s > 0.01
        ]

    # ── Similarity ────────────────────────────────────────────────────────

    @staticmethod
    def _cosine_sim(a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if not na or not nb:
            return 0.0
        return dot / (na * nb)

    # ── Persistence ───────────────────────────────────────────────────────

    def _save(self):
        data = {
            "docs": [
                {"id": d.id, "content": d.content, "metadata": d.metadata,
                 "vector": d.vector, "created_at": d.created_at}
                for d in self._docs.values()
            ]
        }
        try:
            self.docs_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.warning(f"KnowledgeStore save error: {e}")

    def _load(self):
        try:
            if self.docs_file.exists():
                data = json.loads(self.docs_file.read_text(encoding="utf-8"))
                for item in data.get("docs", []):
                    doc = KnowledgeDoc(
                        id=item["id"], content=item["content"],
                        metadata=item.get("metadata", {}),
                        vector=item.get("vector"),
                        created_at=item.get("created_at", 0))
                    self._docs[doc.id] = doc
                    self._all_texts.append(doc.content)
                logger.info(f"KnowledgeStore: {len(self._docs)} ta hujjat yuklandi")
        except Exception as e:
            logger.warning(f"KnowledgeStore load error: {e}")


# ── Singleton ────────────────────────────────────────────────────────────

_knowledge_store: KnowledgeStore | None = None
_knowledge_lock = threading.Lock()


def get_knowledge_store() -> KnowledgeStore:
    global _knowledge_store
    if _knowledge_store is None:
        with _knowledge_lock:
            if _knowledge_store is None:
                _knowledge_store = KnowledgeStore()
    return _knowledge_store
