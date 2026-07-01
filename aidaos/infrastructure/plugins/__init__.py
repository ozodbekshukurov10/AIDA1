"""Plugin system for AIDA Model and future third-party extensions.

To add a new model provider (including AIDA Model):
  1. Create a class that has `chat()` and optionally `chat_stream()` methods
  2. Call `container.register_provider_plugin("aida_model", chat_fn, stream_fn)`
  → Zero changes to any existing code.
"""

from __future__ import annotations
import importlib
import logging
import os
from typing import Any, Callable

logger = logging.getLogger("aidaos.infrastructure.plugins")


class PluginLoader:
    """Discovers and loads plugins from the plugins directory or environment."""

    def __init__(self, plugin_dirs: list[str] | None = None):
        self._dirs = plugin_dirs or []
        self._loaded: dict[str, Any] = {}

    def discover(self) -> list[dict]:
        """Discover available plugins from registered directories."""
        plugins = []
        for d in self._dirs:
            if not os.path.isdir(d):
                continue
            for f in os.listdir(d):
                if f.endswith(".py") and not f.startswith("_"):
                    name = f[:-3]
                    plugins.append({"name": name, "path": os.path.join(d, f), "source": "directory"})
        return plugins

    def load(self, name: str) -> Any | None:
        """Load a plugin by name."""
        if name in self._loaded:
            return self._loaded[name]

        for d in self._dirs:
            path = os.path.join(d, f"{name}.py")
            if os.path.isfile(path):
                try:
                    spec = importlib.util.spec_from_file_location(name, path)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        self._loaded[name] = mod
                        logger.info(f"Loaded plugin: {name}")
                        return mod
                except Exception as e:
                    logger.error(f"Failed to load plugin '{name}': {e}")
        return None

    def get_loaded(self) -> dict[str, Any]:
        return dict(self._loaded)


class ModelPluginAdapter:
    """Adapter that wraps any model plugin into the provider repository format.

    When AIDA Model is built, it just needs to provide:
      async def chat(messages, **kwargs) -> Completion
      async def chat_stream(messages, **kwargs) -> AsyncGenerator
      def get_spec() -> ProviderSpec
    """

    def __init__(self, name: str, module: Any):
        self.name = name
        self._module = module

    def is_valid(self) -> bool:
        return hasattr(self._module, "chat") or hasattr(self._module, "get_spec")

    def create_chat_fn(self):
        if hasattr(self._module, "chat"):
            return self._module.chat
        return None

    def create_stream_fn(self):
        if hasattr(self._module, "chat_stream"):
            return self._module.chat_stream
        return None

    def get_spec(self) -> dict:
        if hasattr(self._module, "get_spec"):
            return self._module.get_spec()
        return {"name": self.name, "model": "default", "description": f"{self.name} plugin"}


def auto_register_plugins(container):
    """Auto-discover and register all available plugins into the container."""
    from ..container import get_container
    c = container or get_container()

    loader = PluginLoader(plugin_dirs=["plugins", "aidaos/infrastructure/plugins"])
    discovered = loader.discover()

    for plugin_info in discovered:
        name = plugin_info["name"]
        mod = loader.load(name)
        if mod is None:
            continue

        adapter = ModelPluginAdapter(name, mod)
        if not adapter.is_valid():
            logger.warning(f"Plugin '{name}' is missing required interfaces")
            continue

        chat_fn = adapter.create_chat_fn()
        stream_fn = adapter.create_stream_fn()
        spec = adapter.get_spec()

        if chat_fn:
            c.register_provider_plugin(name, chat_fn, stream_fn, spec)
            logger.info(f"Auto-registered plugin: {name}")

    return discovered
