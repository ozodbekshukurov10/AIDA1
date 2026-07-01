from __future__ import annotations
import logging
from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, ClassVar, Optional
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

from .base import BaseProvider, ProviderConfig, ProviderStatus

logger = logging.getLogger("webapp.llm.plugin")


class ProviderCapability(Enum):
    CHAT = "chat"
    STREAMING = "streaming"
    EMBEDDINGS = "embeddings"
    TOOL_USE = "tool_use"
    VISION = "vision"
    CODE = "code"
    FUNCTION_CALLING = "function_calling"
    JSON_MODE = "json_mode"


@dataclass
class PluginMetadata:
    name: str
    version: str = "1.0.0"
    description: str = ""
    website: str = ""
    models: list[str] = field(default_factory=list)
    capabilities: list[ProviderCapability] = field(default_factory=lambda: [
        ProviderCapability.CHAT, ProviderCapability.STREAMING,
    ])
    requires_api_key: bool = False
    requires_base_url: bool = False
    env_prefix: str = ""
    config_schema: dict | None = None


class ModelPlugin(BaseProvider):
    metadata: ClassVar[PluginMetadata] = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.metadata and not cls.__name__.startswith("_"):
            PluginRegistry.register(cls)

    @classmethod
    def from_env(cls) -> Self | None:
        return None

    @classmethod
    def detect(cls) -> bool:
        return cls.from_env() is not None

    def get_capabilities(self) -> list[str]:
        if self.metadata:
            return [c.value for c in self.metadata.capabilities]
        return []

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["capabilities"] = self.get_capabilities()
        d["version"] = self.metadata.version if self.metadata else "unknown"
        return d


class PluginRegistry:
    _plugins: dict[str, type[ModelPlugin]] = {}
    _instances: dict[str, ModelPlugin] = {}

    @classmethod
    def register(cls, plugin_cls: type[ModelPlugin]):
        name = plugin_cls.metadata.name.lower().replace(" ", "_") if plugin_cls.metadata else plugin_cls.__name__.lower()
        cls._plugins[name] = plugin_cls
        logger.info(f"Plugin registered: {plugin_cls.metadata.name} v{plugin_cls.metadata.version}")

    @classmethod
    def get(cls, name: str) -> type[ModelPlugin] | None:
        return cls._plugins.get(name.lower().replace(" ", "_"))

    @classmethod
    def list_plugins(cls) -> dict[str, PluginMetadata]:
        return {name: pl.metadata for name, pl in cls._plugins.items() if pl.metadata}

    @classmethod
    def create(cls, name: str, **config_kwargs) -> ModelPlugin | None:
        plugin_cls = cls.get(name)
        if not plugin_cls:
            return None
        if name in cls._instances:
            return cls._instances[name]
        try:
            cfg = ProviderConfig(name=plugin_cls.metadata.name, **config_kwargs)
            instance = plugin_cls(cfg)
            cls._instances[name] = instance
            return instance
        except Exception as e:
            logger.error(f"Failed to create plugin {name}: {e}")
            return None

    @classmethod
    def init_from_env(cls) -> dict[str, ModelPlugin]:
        instances = {}
        for name, plugin_cls in cls._plugins.items():
            try:
                instance = plugin_cls.from_env()
                if instance:
                    instances[name] = instance
                    cls._instances[name] = instance
                    logger.info(f"Loaded plugin: {plugin_cls.metadata.name}")
            except Exception as e:
                logger.debug(f"Plugin {name} not available: {e}")
        return instances

    @classmethod
    def get_instance(cls, name: str) -> ModelPlugin | None:
        return cls._instances.get(name)
