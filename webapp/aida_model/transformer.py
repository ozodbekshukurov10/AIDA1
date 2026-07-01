from __future__ import annotations
import math
import random
from abc import ABC, abstractmethod
from typing import Any


class BaseAttention(ABC):
    @abstractmethod
    def forward(self, q: list[float], k: list[float], v: list[float],
                mask: list[list[float]] | None = None) -> tuple[list[float], list[list[float]]]:
        ...

    @property
    @abstractmethod
    def num_heads(self) -> int:
        ...

    @property
    @abstractmethod
    def head_dim(self) -> int:
        ...


class MultiHeadAttention(BaseAttention):
    def __init__(self, dim: int = 4096, num_heads: int = 32,
                 num_kv_heads: int = 8, max_seq_len: int = 131072):
        self._dim = dim
        self._num_heads = num_heads
        self._num_kv_heads = num_kv_heads
        self._head_dim = dim // num_heads
        self._max_seq_len = max_seq_len
        self._rng = random.Random(0)
        self.wq = self._rand(dim, dim)
        self.wk = self._rand(dim, num_kv_heads * self._head_dim)
        self.wv = self._rand(dim, num_kv_heads * self._head_dim)
        self.wo = self._rand(dim, dim)

    def _rand(self, rows: int, cols: int) -> list[list[float]]:
        return [[self._rng.gauss(0, 0.02) for _ in range(cols)] for _ in range(rows)]

    def _dot(self, a: list[float], b: list[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    def _mat_vec(self, mat: list[list[float]], vec: list[float]) -> list[float]:
        return [self._dot(row, vec) for row in mat]

    def _softmax(self, scores: list[float]) -> list[float]:
        m = max(scores)
        exps = [math.exp(s - m) for s in scores]
        s = sum(exps) or 1.0
        return [e / s for e in exps]

    def forward(self, q: list[float], k: list[float], v: list[float],
                mask: list[list[float]] | None = None) -> tuple[list[float], list[list[float]]]:
        q = self._mat_vec(self.wq, q)
        k = self._mat_vec(self.wk, k)
        v = self._mat_vec(self.wv, v)
        scale = math.sqrt(self._head_dim)
        scores = [qi * ki / scale for qi, ki in zip(q, k)]
        attn = self._softmax(scores)
        out = [a * vi for a, vi in zip(attn, v)]
        out = self._mat_vec(self.wo, out)
        return out, [attn]

    @property
    def num_heads(self) -> int:
        return self._num_heads

    @property
    def head_dim(self) -> int:
        return self._head_dim


class BaseTransformer(ABC):
    @abstractmethod
    def forward(self, x: list[float], mask: list[list[float]] | None = None) -> list[float]:
        ...

    @abstractmethod
    def generate(self, prompt: list[int], max_tokens: int = 256,
                 temperature: float = 0.7, top_p: float = 0.9) -> list[int]:
        ...

    @property
    @abstractmethod
    def num_layers(self) -> int:
        ...

    @property
    @abstractmethod
    def hidden_dim(self) -> int:
        ...


class TransformerBlock:
    def __init__(self, dim: int, num_heads: int, num_kv_heads: int,
                 max_seq_len: int, norm_eps: float = 1e-5):
        self.attention = MultiHeadAttention(dim, num_heads, num_kv_heads, max_seq_len)
        self.ffn_gate = [random.gauss(0, 0.02) for _ in range(dim * 4)]
        self.ffn_up = [random.gauss(0, 0.02) for _ in range(dim * 4)]
        self.ffn_down = [random.gauss(0, 0.02) for _ in range(dim * 4)]
        self.dim = dim
        self.norm_eps = norm_eps

    def _rms_norm(self, x: list[float]) -> list[float]:
        s = sum(v * v for v in x) / len(x) + self.norm_eps
        scale = 1.0 / math.sqrt(s)
        return [v * scale for v in x]

    def _silu(self, x: float) -> float:
        return x / (1.0 + math.exp(-x))

    def forward(self, x: list[float], mask: list[list[float]] | None = None) -> list[float]:
        attn_out, _ = self.attention.forward(x, x, x, mask)
        x = [a + b for a, b in zip(x, attn_out)]
        x = self._rms_norm(x)
        gate = [self._silu(g) for g in [sum(x[i] * w for i, w in enumerate(self.ffn_gate[j::self.dim])) for j in range(self.dim)]]
        up = [sum(x[i] * w for i, w in enumerate(self.ffn_up[j::self.dim])) for j in range(self.dim)]
        ffn_out = [g * u for g, u in zip(gate, up)]
        down = [sum(ffn_out[i] * w for i, w in enumerate(self.ffn_down[j::self.dim])) for j in range(self.dim)]
        x = [a + b for a, b in zip(x, down)]
        x = self._rms_norm(x)
        return x


class AidaTransformer(BaseTransformer):
    def __init__(self, config: Any = None):
        from .config import AidaArchitectureConfig
        cfg = config or AidaArchitectureConfig()
        self._num_layers = cfg.num_layers
        self._hidden_dim = cfg.hidden_dim
        self._max_seq_len = cfg.max_seq_len
        self._vocab_size = cfg.vocab_size
        self._layers = [
            TransformerBlock(cfg.hidden_dim, cfg.num_heads,
                             cfg.num_kv_heads, cfg.max_seq_len, cfg.norm_eps)
            for _ in range(cfg.num_layers)
        ]
        self._rng = random.Random(1)
        self.output_proj = [[self._rng.gauss(0, 0.02) for _ in range(cfg.hidden_dim)] for _ in range(cfg.vocab_size)]

    def forward(self, x: list[float], mask: list[list[float]] | None = None) -> list[float]:
        for layer in self._layers:
            x = layer.forward(x, mask)
        logits = [sum(x[i] * w[i] for i in range(len(x))) for w in self.output_proj]
        return logits

    def generate(self, prompt: list[int], max_tokens: int = 256,
                 temperature: float = 0.7, top_p: float = 0.9) -> list[int]:
        from .tokenizer import AidaTokenizer
        tok = AidaTokenizer(self._vocab_size)
        x = [0.0] * self._hidden_dim
        generated = list(prompt)
        for _ in range(max_tokens):
            logits = self.forward(x)
            m = max(logits)
            probs = [math.exp((l - m) / temperature) for l in logits]
            s = sum(probs) or 1.0
            probs = [p / s for p in probs]
            r = random.random()
            cum = 0.0
            next_id = 0
            for i, p in enumerate(probs):
                cum += p
                if r < cum:
                    next_id = i
                    break
            generated.append(next_id)
            if next_id == tok.eos_token_id:
                break
        return generated

    @property
    def num_layers(self) -> int:
        return self._num_layers

    @property
    def hidden_dim(self) -> int:
        return self._hidden_dim
