from __future__ import annotations
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ModelStatus(Enum):
    REGISTERED = "registered"
    DOWNLOADING = "downloading"
    READY = "ready"
    ACTIVE = "active"
    ERROR = "error"
    ARCHIVED = "archived"


@dataclass
class ModelEntry:
    name: str = ""
    version: str = "1.0.0"
    path: str = ""
    status: ModelStatus = ModelStatus.REGISTERED
    description: str = ""
    architecture: str = "transformer"
    params_count: str = "7B"
    quant: str = "fp16"
    created_at: float = 0.0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "path": self.path,
            "status": self.status.value,
            "description": self.description,
            "architecture": self.architecture,
            "params": self.params_count,
            "quant": self.quant,
            "created_at": self.created_at,
        }


class ModelRegistry(ABC):
    @abstractmethod
    def register(self, entry: ModelEntry) -> bool:
        ...

    @abstractmethod
    def get(self, name: str) -> ModelEntry | None:
        ...

    @abstractmethod
    def list_models(self, status: ModelStatus | None = None) -> list[ModelEntry]:
        ...

    @abstractmethod
    def set_active(self, name: str) -> bool:
        ...

    @abstractmethod
    def get_active(self) -> ModelEntry | None:
        ...

    @abstractmethod
    def remove(self, name: str) -> bool:
        ...

    @abstractmethod
    def save(self, path: str) -> None:
        ...

    @abstractmethod
    def load(self, path: str) -> None:
        ...


class AidaModelRegistry(ModelRegistry):
    def __init__(self):
        self._models: dict[str, ModelEntry] = {}
        self._active_name: str | None = None
        self._init_defaults()

    def _init_defaults(self):
        defaults = [
            ModelEntry("aida-core", "1.0.0", status=ModelStatus.REGISTERED,
                       description="AIDA flagship model", params_count="70B", quant="fp16"),
            ModelEntry("aida-code", "1.0.0", status=ModelStatus.REGISTERED,
                       description="AIDA code-specialized model", params_count="7B", quant="fp16"),
            ModelEntry("aida-chat", "1.0.0", status=ModelStatus.REGISTERED,
                       description="AIDA chat-optimized model", params_count="7B", quant="q4_k_m"),
            ModelEntry("aida-light", "1.0.0", status=ModelStatus.REGISTERED,
                       description="AIDA lightweight model for edge", params_count="1.5B", quant="q4_k_m"),
        ]
        for m in defaults:
            self._models[m.name] = m

    def register(self, entry: ModelEntry) -> bool:
        self._models[entry.name] = entry
        return True

    def get(self, name: str) -> ModelEntry | None:
        return self._models.get(name)

    def list_models(self, status: ModelStatus | None = None) -> list[ModelEntry]:
        if status:
            return [m for m in self._models.values() if m.status == status]
        return list(self._models.values())

    def set_active(self, name: str) -> bool:
        entry = self._models.get(name)
        if entry:
            if self._active_name:
                old = self._models.get(self._active_name)
                if old:
                    old.status = ModelStatus.READY
            entry.status = ModelStatus.ACTIVE
            self._active_name = name
            return True
        return False

    def get_active(self) -> ModelEntry | None:
        if self._active_name:
            return self._models.get(self._active_name)
        return None

    def remove(self, name: str) -> bool:
        if name in self._models:
            del self._models[name]
            if self._active_name == name:
                self._active_name = None
            return True
        return False

    def save(self, path: str) -> None:
        data = {
            "models": [m.to_dict() for m in self._models.values()],
            "active": self._active_name,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._models = {}
        for m_data in data.get("models", []):
            entry = ModelEntry(
                name=m_data["name"], version=m_data.get("version", "1.0.0"),
                path=m_data.get("path", ""), status=ModelStatus(m_data["status"]),
                description=m_data.get("description", ""),
                architecture=m_data.get("architecture", "transformer"),
                params_count=m_data.get("params", "7B"),
                quant=m_data.get("quant", "fp16"),
                created_at=m_data.get("created_at", time.time()),
            )
            self._models[entry.name] = entry
        self._active_name = data.get("active")
