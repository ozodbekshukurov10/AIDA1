from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class BaseTokenizer(ABC):
    @abstractmethod
    def encode(self, text: str, add_special_tokens: bool = True) -> list[int]:
        ...

    @abstractmethod
    def decode(self, token_ids: list[int], skip_special_tokens: bool = True) -> str:
        ...

    @abstractmethod
    def vocab_size(self) -> int:
        ...

    @abstractmethod
    def save(self, path: str) -> None:
        ...

    @abstractmethod
    def load(self, path: str) -> None:
        ...

    @abstractmethod
    def tokenize(self, text: str) -> list[str]:
        ...

    @property
    def pad_token_id(self) -> int:
        return 0

    @property
    def bos_token_id(self) -> int:
        return 1

    @property
    def eos_token_id(self) -> int:
        return 2

    @property
    def unk_token_id(self) -> int:
        return 3


class AidaTokenizer(BaseTokenizer):
    def __init__(self, vocab_size: int = 32768):
        self._vocab_size = vocab_size
        self._vocab: dict[str, int] = {}
        self._reverse_vocab: dict[int, str] = {}
        self._init_placeholders()

    def _init_placeholders(self):
        self._vocab = {f"token_{i}": i for i in range(self._vocab_size)}
        self._vocab["<pad>"] = 0
        self._vocab["<bos>"] = 1
        self._vocab["<eos>"] = 2
        self._vocab["<unk>"] = 3
        self._reverse_vocab = {v: k for k, v in self._vocab.items()}

    def encode(self, text: str, add_special_tokens: bool = True) -> list[int]:
        tokens = [self.bos_token_id] if add_special_tokens else []
        words = text.split()
        for word in words:
            tokens.append(self._vocab.get(word, self.unk_token_id))
        if add_special_tokens:
            tokens.append(self.eos_token_id)
        return tokens

    def decode(self, token_ids: list[int], skip_special_tokens: bool = True) -> str:
        words = []
        for tid in token_ids:
            if skip_special_tokens and tid in (0, 1, 2):
                continue
            words.append(self._reverse_vocab.get(tid, "<unk>"))
        return " ".join(words)

    def tokenize(self, text: str) -> list[str]:
        return text.split()

    def vocab_size(self) -> int:
        return self._vocab_size

    def save(self, path: str) -> None:
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"vocab": self._vocab, "vocab_size": self._vocab_size}, f)

    def load(self, path: str) -> None:
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._vocab = data["vocab"]
        self._vocab_size = data["vocab_size"]
        self._reverse_vocab = {v: k for k, v in self._vocab.items()}
