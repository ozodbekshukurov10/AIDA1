from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator
from enum import Enum


@dataclass
class GenerationResult:
    text: str
    tokens: list[int] | None = None
    model: str = ""
    provider: str = "aida"
    finish_reason: str = "stop"
    usage: dict | None = None
    latency_ms: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "model": self.model,
            "provider": self.provider,
            "finish_reason": self.finish_reason,
            "usage": self.usage or {},
            "latency_ms": self.latency_ms,
        }


@dataclass
class GenerationChunk:
    text: str = ""
    done: bool = False
    finish_reason: str | None = None
    usage: dict | None = None


class InferenceAPI(ABC):
    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int = 4096,
                       temperature: float = 0.7, **kwargs) -> GenerationResult:
        ...

    @abstractmethod
    async def generate_stream(self, prompt: str, max_tokens: int = 4096,
                               temperature: float = 0.7, **kwargs) -> AsyncIterator[GenerationChunk]:
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        ...

    @abstractmethod
    async def tokenize(self, text: str) -> list[int]:
        ...

    @abstractmethod
    async def detokenize(self, tokens: list[int]) -> str:
        ...

    @abstractmethod
    def get_info(self) -> dict:
        ...


class AidaInferenceEngine(InferenceAPI):
    def __init__(self, model_name: str = "aida-core", config: Any = None):
        self._model_name = model_name
        self._config = config
        self._initialized = False

    async def _lazy_init(self):
        if not self._initialized:
            from .tokenizer import AidaTokenizer
            from .embedding import AidaEmbedding
            from .transformer import AidaTransformer
            from .reasoning import AidaReasoningLayer
            from .planning import AidaPlanningLayer
            from .tool_calling import AidaToolCallingLayer
            from .memory_layer import AidaMemoryLayer
            cfg = self._config
            vocab = cfg.vocab_size if cfg else 32768
            dim = cfg.hidden_dim if cfg else 4096
            self._tokenizer = AidaTokenizer(vocab)
            self._embedding = AidaEmbedding(vocab, dim)
            self._transformer = AidaTransformer(cfg) if cfg else AidaTransformer()
            self._reasoning = AidaReasoningLayer()
            self._planning = AidaPlanningLayer()
            self._tool_calling = AidaToolCallingLayer()
            self._memory = AidaMemoryLayer()
            self._initialized = True

    async def generate(self, prompt: str, max_tokens: int = 4096,
                       temperature: float = 0.7, **kwargs) -> GenerationResult:
        import time
        start = time.monotonic()
        await self._lazy_init()
        tokens = self._tokenizer.encode(prompt)
        output_ids = self._transformer.generate(tokens, max_tokens, temperature)
        text = self._tokenizer.decode(output_ids)
        return GenerationResult(
            text=text,
            tokens=output_ids,
            model=self._model_name,
            finish_reason="stop",
            latency_ms=int((time.monotonic() - start) * 1000),
        )

    async def generate_stream(self, prompt: str, max_tokens: int = 4096,
                               temperature: float = 0.7, **kwargs) -> AsyncIterator[GenerationChunk]:
        await self._lazy_init()
        tokens = self._tokenizer.encode(prompt)
        for i in range(min(max_tokens, 50)):
            output_ids = self._transformer.generate(tokens, 1, temperature)
            chunk_text = self._tokenizer.decode(output_ids[-1:])
            tokens.append(output_ids[-1])
            yield GenerationChunk(text=chunk_text, done=False)
            if output_ids[-1] == self._tokenizer.eos_token_id:
                break
        yield GenerationChunk(text="", done=True, finish_reason="stop")

    async def embed(self, text: str) -> list[float]:
        await self._lazy_init()
        vec = self._embedding.embed_text(text)
        return vec.tolist()

    async def tokenize(self, text: str) -> list[int]:
        await self._lazy_init()
        return self._tokenizer.encode(text)

    async def detokenize(self, tokens: list[int]) -> str:
        await self._lazy_init()
        return self._tokenizer.decode(tokens)

    def get_info(self) -> dict:
        return {
            "model": self._model_name,
            "version": "1.0.0",
            "initialized": self._initialized,
            "capabilities": [
                "chat", "streaming", "embedding", "tokenization",
                "reasoning", "planning", "tool_calling", "memory",
            ],
        }
