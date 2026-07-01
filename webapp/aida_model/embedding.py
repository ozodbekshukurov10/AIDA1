from __future__ import annotations
import math
import random
from abc import ABC, abstractmethod
from typing import Any


class BaseEmbedding(ABC):
    @abstractmethod
    def embed(self, token_ids: list[int]) -> list[float]:
        ...

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        ...

    @property
    @abstractmethod
    def dim(self) -> int:
        ...

    @property
    @abstractmethod
    def vocab_size(self) -> int:
        ...


class AidaEmbedding(BaseEmbedding):
    def __init__(self, vocab_size: int = 32768, dim: int = 4096):
        self._dim = dim
        self._vocab_size = vocab_size
        self._weight: dict[int, list[float]] = {}
        self._init_placeholder()

    def _init_placeholder(self):
        rng = random.Random(42)
        for i in range(min(self._vocab_size, 1000)):
            vec = [rng.gauss(0, 0.02) for _ in range(self._dim)]
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            self._weight[i] = [v / norm for v in vec]

    def _get_vec(self, idx: int) -> list[float]:
        idx = max(0, min(idx, self._vocab_size - 1))
        if idx not in self._weight:
            rng = random.Random(idx)
            vec = [rng.gauss(0, 0.02) for _ in range(self._dim)]
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            self._weight[idx] = [v / norm for v in vec]
        return self._weight[idx]

    def embed(self, token_ids: list[int]) -> list[float]:
        if not token_ids:
            return [0.0] * self._dim
        vecs = [self._get_vec(tid) for tid in token_ids]
        avg = [sum(v[i] for v in vecs) / len(vecs) for i in range(self._dim)]
        return avg

    def embed_text(self, text: str) -> list[float]:
        from .tokenizer import AidaTokenizer
        tok = AidaTokenizer(self._vocab_size)
        ids = tok.encode(text)
        return self.embed(ids)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def vocab_size(self) -> int:
        return self._vocab_size

    def save(self, path: str):
        import json
        with open(path, "w") as f:
            json.dump({str(k): v for k, v in self._weight.items()}, f)

    def load(self, path: str):
        import json
        with open(path) as f:
            self._weight = {int(k): v for k, v in json.load(f).items()}
