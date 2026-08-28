"""Provider service — manages LLM provider selection, connection, and health.

Unified interface over both legacy providers (OllamaProvider, GeminiProvider, etc.)
and the new plugin-based LLM gateway.
"""

from __future__ import annotations
import os
from typing import Any, Callable
from aidaos.infrastructure.logging import get_logger

logger = get_logger("services.provider")


class ProviderService:
    """Manages provider lifecycle: selection, connection, health checks."""

    def __init__(self, settings: Any = None):
        self._settings = settings
        self._primary_provider: Any = None
        self._providers: dict[str, Any] = {}
        self._local_provider: Any = None

    def build_provider(self, config: Any) -> Any:
        """Build primary provider from config (legacy path)."""
        p = config.provider
        url = getattr(config, "api_url", "")

        if p == "collab":
            return self._build_collab(config, url)

        if p == "aida-beta":
            return self._build_aida_beta(config, url)

        if p in ("local", "ollama"):
            return self._build_ollama(config, url)

        if p == "lmstudio":
            return self._build_lmstudio(config, url)

        if p == "remote" and getattr(config, "api_key", ""):
            return self._build_gemini(config)

        return self._get_local()

    def build_all_providers(self, config: Any, build_fn: Callable) -> dict[str, Any]:
        """Build all available providers (legacy path)."""
        providers = {}
        for name in ("ollama", "lmstudio", "gemini", "local"):
            try:
                cfg_copy = config
                cfg_copy.provider = name
                prov = build_fn(cfg_copy)
                if prov:
                    providers[name] = prov
            except Exception as e:
                logger.debug(f"Provider '{name}' build failed: {e}")
        return providers

    def _build_collab(self, config, url):
        from webapp.aida_controller import CollaborationProvider
        lmstudio_url = os.getenv("LMSTUDIO_API_URL", "http://localhost:1234")
        import threading
        threading.Thread(target=self._try_connect_lmstudio, args=(lmstudio_url,), daemon=True).start()
        return CollaborationProvider(
            ollama_url=url or "http://localhost:11434",
            ollama_model=config.model or "qwen2.5:3b",
            lmstudio_url=lmstudio_url,
            mode=config.mode,
        )

    def _build_aida_beta(self, config, url):
        from webapp.llm.gateway import get_gateway
        gw = get_gateway()
        plugin = gw.get_provider("ollama")
        if plugin:
            return plugin
        return self._try_connect_ollama(url or "http://localhost:11434", "aida-beta:latest") or self._get_local()

    def _build_ollama(self, config, url):
        preferred = None if (not config.model or config.model == "AIDA Local Core") else config.model
        provider = self._try_connect_ollama(url or "http://localhost:11434", preferred)
        return provider or self._get_local()

    def _build_lmstudio(self, config, url, model=""):
        from webapp.aida_controller import LMStudioProvider
        import threading
        threading.Thread(target=self._try_connect_lmstudio, args=(url or "http://localhost:1234",), daemon=True).start()
        return LMStudioProvider(url=url or "http://localhost:1234", model=model or config.model, mode=config.mode)

    def _build_gemini(self, config):
        from webapp.aida_controller import GeminiProvider
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        return GeminiProvider(config.api_key, model=gemini_model)

    def _try_connect_ollama(self, url: str = "http://localhost:11434", preferred_model: str = None):
        from webapp.aida_controller import OllamaProvider
        mode = getattr(self._settings, "mode", "pro") if self._settings else "pro"
        try:
            return OllamaProvider(url=url, model=preferred_model or "llama3.2", mode=mode)
        except Exception as e:
            logger.warning(f"Ollama connection failed: {e}")
            return None

    def _try_connect_lmstudio(self, url: str = "http://localhost:1234"):
        try:
            import urllib.request
            with urllib.request.urlopen(f"{url}/v1/models", timeout=5):
                logger.info(f"LM Studio available at {url}")
        except Exception:
            logger.debug(f"LM Studio not available at {url}")

    def _get_local(self):
        if self._local_provider is None:
            from webapp.aida_controller import LocalProvider
            self._local_provider = LocalProvider()
        return self._local_provider

    def get_primary(self) -> Any:
        return self._primary_provider

    def get_all(self) -> dict[str, Any]:
        return self._providers

    def set_primary(self, provider: Any) -> None:
        self._primary_provider = provider

    def register(self, name: str, provider: Any) -> None:
        self._providers[name] = provider
