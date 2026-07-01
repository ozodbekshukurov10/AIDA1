from __future__ import annotations
import json
import os
import time
from typing import AsyncIterator

import httpx

from ..base import (
    ProviderConfig, Message, MessageRole, Completion,
    StreamingChunk, ProviderStatus,
)
from ..plugin import ModelPlugin, PluginMetadata, ProviderCapability


class AnthropicPlugin(ModelPlugin):
    metadata = PluginMetadata(
        name="Anthropic",
        version="1.0.0",
        description="Anthropic Claude API (Claude 3 Opus, Sonnet, Haiku)",
        website="https://anthropic.com",
        capabilities=[
            ProviderCapability.CHAT, ProviderCapability.STREAMING,
            ProviderCapability.TOOL_USE, ProviderCapability.VISION,
        ],
        requires_api_key=True,
        env_prefix="ANTHROPIC_",
        config_schema={
            "model": {"type": "string", "default": "claude-3-5-sonnet-20241022"},
            "api_key": {"type": "string", "required": True},
            "base_url": {"type": "string", "default": "https://api.anthropic.com"},
            "timeout": {"type": "integer", "default": 120},
        },
    )

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.base_url = (config.base_url or "https://api.anthropic.com").rstrip("/")
        self.client = httpx.AsyncClient(timeout=config.timeout)

    def _build_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

    def _convert_messages(self, messages: list[Message]) -> tuple[str | None, list[dict]]:
        system = None
        converted = []
        for m in messages:
            if m.role == MessageRole.SYSTEM:
                system = m.content
            else:
                converted.append({"role": m.role.value, "content": m.content})
        return system, converted

    async def chat(self, messages: list[Message], **kwargs) -> Completion:
        start = time.monotonic()
        system, converted = self._convert_messages(messages)
        payload = {
            "model": kwargs.get("model") or self.config.model,
            "messages": converted,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }
        if system:
            payload["system"] = system

        try:
            resp = await self.client.post(
                f"{self.base_url}/v1/messages",
                json=payload, headers=self._build_headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            self.status = ProviderStatus.ONLINE
            content = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    content += block.get("text", "")
            return Completion(
                content=content,
                model=data.get("model", self.config.model),
                provider="anthropic",
                usage={
                    "input_tokens": data.get("usage", {}).get("input_tokens"),
                    "output_tokens": data.get("usage", {}).get("output_tokens"),
                },
                finish_reason=data.get("stop_reason", "stop"),
                latency_ms=int((time.monotonic() - start) * 1000),
            )
        except Exception as e:
            self.status = ProviderStatus.ERROR
            self._last_error = str(e)
            raise

    async def chat_stream(self, messages: list[Message], **kwargs) -> AsyncIterator[StreamingChunk]:
        system, converted = self._convert_messages(messages)
        payload = {
            "model": kwargs.get("model") or self.config.model,
            "messages": converted,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "stream": True,
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            async with client.stream(
                "POST", f"{self.base_url}/v1/messages",
                json=payload, headers=self._build_headers(),
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if not data_str or data_str == "[DONE]":
                        yield StreamingChunk(content="", done=True)
                        break
                    data = json.loads(data_str)
                    if data.get("type") == "content_block_delta":
                        delta = data.get("delta", {})
                        if delta.get("type") == "text_delta":
                            yield StreamingChunk(content=delta.get("text", ""), done=False)
                    if data.get("type") == "message_stop":
                        yield StreamingChunk(content="", done=True, finish_reason="stop")

    async def check_health(self) -> bool:
        try:
            resp = await self.client.get(
                f"{self.base_url}/v1/models",
                headers=self._build_headers(), timeout=5,
            )
            if resp.status_code == 200:
                self.status = ProviderStatus.ONLINE
                return True
        except Exception:
            pass
        self.status = ProviderStatus.OFFLINE
        return False

    async def list_models(self) -> list[str]:
        return [
            "claude-3-opus-20240229", "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307", "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ]

    @classmethod
    def from_env(cls) -> AnthropicPlugin | None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        return cls(ProviderConfig(
            name="anthropic",
            model=os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            api_key=api_key,
            base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
            timeout=int(os.environ.get("ANTHROPIC_TIMEOUT", "120")),
        ))
