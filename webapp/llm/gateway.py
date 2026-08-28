from __future__ import annotations
import asyncio
import logging
import os
import time
from typing import AsyncIterator

from .base import (
    BaseProvider, ProviderConfig, Message, MessageRole, Completion,
    StreamingChunk, ProviderStatus,
)
from .plugin import ModelPlugin, PluginRegistry

logger = logging.getLogger("webapp.llm.gateway")


class ProfessionalModelGateway:
    _instance: ProfessionalModelGateway | None = None

    def __init__(self):
        self._providers: dict[str, ModelPlugin] = {}
        self._active_provider: str | None = None
        self._fallback_order: list[str] = []
        self._health_cache: dict[str, tuple[bool, float]] = {}
        self._health_ttl = 30.0
        self._load_providers()

    def _load_providers(self):
        instances = PluginRegistry.init_from_env()

        priority_env = os.environ.get("AIDA_PROVIDER", "")
        if priority_env in instances:
            self._providers[priority_env] = instances[priority_env]
            self._active_provider = priority_env

        for name, inst in instances.items():
            if name not in self._providers:
                self._providers[name] = inst

        priority = ["collab", "ollama", "openai", "anthropic", "gemini",
                     "deepseek", "lm_studio", "vllm", "tensorrt-llm", "aida_model"]
        self._fallback_order = [p for p in priority if p in self._providers]
        self._fallback_order.extend(
            [p for p in self._providers if p not in self._fallback_order]
        )

        if not self._active_provider and self._fallback_order:
            self._active_provider = self._fallback_order[0]

        if not self._active_provider:
            logger.warning("No providers available, creating local fallback")
            from .local import LocalProvider
            local = LocalProvider(ProviderConfig(name="local", model="local-rule-based"))
            self._providers["local"] = local
            self._active_provider = "local"
            self._fallback_order = ["local"]

        logger.info(f"Gateway initialized: {len(self._providers)} providers, active={self._active_provider}")

    @property
    def active_provider(self) -> ModelPlugin | BaseProvider:
        return self._providers.get(self._active_provider or "local", self._providers.get("local"))

    def get_provider(self, name: str) -> BaseProvider | None:
        return self._providers.get(name)

    def list_providers(self) -> dict[str, dict]:
        return {name: p.to_dict() for name, p in self._providers.items()}

    def switch_provider(self, name: str) -> bool:
        if name in self._providers:
            self._active_provider = name
            logger.info(f"Switched to provider: {name}")
            return True
        return False

    def get_status(self) -> dict:
        return {
            "active_provider": self._active_provider,
            "providers": {n: p.to_dict() for n, p in self._providers.items()},
            "fallback_order": self._fallback_order,
            "total_providers": len(self._providers),
        }

    def _prepare_messages(self, messages: list[Message]) -> list[Message]:
        system_instruction = (
            "You are AIDA, a highly intelligent agentic AI assistant.\n"
            "IMPORTANT LANGUAGE RULE: Always detect the language of the user's message (Uzbek, Russian, English, etc.) and respond in that exact same language.\n"
            "If the user writes in Uzbek, reply in natural Uzbek. If the user writes in Russian, reply in Russian. If the user writes in English, reply in English.\n"
            "Keep your tone warm, professional, helpful, and concise."
        )
        has_system = False
        prepared = []
        for m in messages:
            if m.role == MessageRole.SYSTEM:
                has_system = True
                content = m.content
                if "IMPORTANT LANGUAGE RULE" not in content:
                    content = f"{content.strip()}\n\n{system_instruction}"
                prepared.append(Message(role=MessageRole.SYSTEM, content=content))
            else:
                prepared.append(m)
        if not has_system:
            prepared.insert(0, Message(role=MessageRole.SYSTEM, content=system_instruction))
        return prepared

    async def chat(self, messages: list[Message], provider: str | None = None,
                    fallback: bool = True, **kwargs) -> Completion:
        messages = self._prepare_messages(messages)
        provider_name = provider or self._active_provider
        if not provider_name and self._fallback_order:
            provider_name = self._fallback_order[0]

        if not fallback:
            prov = self._providers.get(provider_name or "")
            if not prov:
                raise ValueError(f"Provider '{provider_name}' not found")
            return await prov.chat(messages, **kwargs)

        candidates = self._fallback_order
        if provider_name and provider_name in candidates:
            candidates = [provider_name] + [p for p in candidates if p != provider_name]

        last_error = ""
        for name in candidates:
            prov = self._providers.get(name)
            if not prov:
                continue
            try:
                return await prov.chat(messages, **kwargs)
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Provider '{name}' failed: {e}")
                continue

        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    async def chat_stream(self, messages: list[Message], provider: str | None = None,
                            **kwargs) -> AsyncIterator[StreamingChunk]:
        messages = self._prepare_messages(messages)
        provider_name = provider or self._active_provider
        if not provider_name and self._fallback_order:
            provider_name = self._fallback_order[0]

        prov = self._providers.get(provider_name or "")
        if not prov:
            yield StreamingChunk(content=f"Provider '{provider_name}' not available", done=True)
            return

        try:
            async for chunk in prov.chat_stream(messages, **kwargs):
                yield chunk
            return
        except Exception:
            for fallback in self._fallback_order:
                if fallback == provider_name:
                    continue
                fb = self._providers.get(fallback)
                if not fb:
                    continue
                try:
                    async for chunk in fb.chat_stream(messages, **kwargs):
                        yield chunk
                    return
                except Exception:
                    continue
            yield StreamingChunk(content="All providers failed for streaming", done=True)

    async def check_all_health(self) -> dict[str, bool]:
        results = {}
        for name, prov in self._providers.items():
            cached = self._health_cache.get(name)
            if cached and (time.time() - cached[1]) < self._health_ttl:
                results[name] = cached[0]
                continue
            try:
                ok = await prov.check_health()
            except Exception:
                ok = False
            self._health_cache[name] = (ok, time.time())
            results[name] = ok
        return results

    async def get_healthy_providers(self) -> list[str]:
        health = await self.check_all_health()
        return [name for name, ok in health.items() if ok]

    def discover_plugins(self) -> list[dict]:
        return [
            {"name": name, "metadata": meta}
            for name, meta in PluginRegistry.list_plugins().items()
        ]

    def register_plugin(self, plugin_name: str, **config_kwargs) -> bool:
        instance = PluginRegistry.create(plugin_name, **config_kwargs)
        if instance:
            self._providers[plugin_name] = instance
            if plugin_name not in self._fallback_order:
                self._fallback_order.append(plugin_name)
            if not self._active_provider:
                self._active_provider = plugin_name
            logger.info(f"Registered plugin instance: {plugin_name}")
            return True
        return False


_gateway_instance: ProfessionalModelGateway | None = None


def get_gateway() -> ProfessionalModelGateway:
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = ProfessionalModelGateway()
    return _gateway_instance
