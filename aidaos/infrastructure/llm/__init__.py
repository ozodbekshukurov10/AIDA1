"""Provider repository adapter — wraps the existing ProfessionalModelGateway.

This is the KEY adapter for future AIDA Model integration.
When a new model is added, only a new plugin is needed — no infrastructure changes.
"""

from __future__ import annotations
import logging
import time
from typing import Any, AsyncGenerator

from ...domain.entities import Message, Completion, MessageRole, ProviderSpec, ProviderStatus
from ...domain.interfaces import ProviderRepository
from ...domain.exceptions import ProviderNotFoundError, ProviderOfflineError, ProviderFallbackError

logger = logging.getLogger("aidaos.infrastructure.llm")


class ProviderRepoAdapter(ProviderRepository):
    def __init__(self):
        self._gateway = None

    def _get_gateway(self):
        if self._gateway is None:
            from webapp.llm.gateway import get_gateway
            self._gateway = get_gateway()
        return self._gateway

    async def register(self, spec: ProviderSpec, chat_fn, stream_fn=None) -> None:
        logger.info(f"Provider '{spec.name}' registered via plugin system")

    async def get(self, name: str) -> ProviderSpec | None:
        gw = self._get_gateway()
        try:
            status = gw.get_status()
            providers = status.get("providers", status)
            if isinstance(providers, dict) and name in providers:
                p = providers[name]
                return ProviderSpec(
                    name=name,
                    model=p.get("model", ""),
                    status=ProviderStatus(p.get("status", "unknown").lower()),
                    supports_streaming=p.get("supports_streaming", False),
                )
        except Exception:
            pass
        return None

    async def list(self) -> list[ProviderSpec]:
        gw = self._get_gateway()
        specs = []
        try:
            status = gw.get_status()
            providers = status.get("providers", {}) if isinstance(status, dict) else {}
            for name, info in providers.items():
                specs.append(ProviderSpec(
                    name=name,
                    model=info.get("model", ""),
                    status=ProviderStatus(info.get("status", "unknown").lower()),
                    priority=info.get("priority", 100),
                    supports_streaming=info.get("supports_streaming", False),
                ))
        except Exception:
            pass
        return specs

    async def chat(self, messages: list[Message], provider: str = "", **kwargs) -> Completion:
        gw = self._get_gateway()
        raw_messages = [m.to_dict() for m in messages]

        try:
            start = time.monotonic()
            result = await gw.chat(raw_messages, provider_priority=provider or None)
            latency = int((time.monotonic() - start) * 1000)

            return Completion(
                content=result.content if hasattr(result, 'content') else str(result),
                role=MessageRole.ASSISTANT,
                usage=result.usage if hasattr(result, 'usage') else {},
                model=result.model if hasattr(result, 'model') else provider,
                provider=result.provider if hasattr(result, 'provider') else provider,
                latency_ms=latency,
                finish_reason=result.finish_reason if hasattr(result, 'finish_reason') else "",
            )
        except ProviderFallbackError:
            raise
        except Exception as e:
            raise ProviderOfflineError(f"Provider chat failed: {e}")

    async def chat_stream(self, messages: list[Message], provider: str = "", **kwargs):
        gw = self._get_gateway()
        raw_messages = [m.to_dict() for m in messages]
        try:
            async for chunk in gw.chat_stream(raw_messages, provider_priority=provider or None):
                yield chunk
        except Exception as e:
            raise ProviderOfflineError(f"Stream failed: {e}")

    async def check_health(self, provider: str = "") -> bool:
        gw = self._get_gateway()
        try:
            status = gw.get_status()
            if provider:
                providers = status.get("providers", {}) if isinstance(status, dict) else {}
                p = providers.get(provider, {})
                if isinstance(p, dict):
                    return p.get("status", "").lower() == "online"
                return True
            return True
        except Exception:
            return False
