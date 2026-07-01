from __future__ import annotations
import json
import os
import time
from typing import AsyncIterator

import httpx

from ..base import (
    ProviderConfig, Message, Completion, StreamingChunk, ProviderStatus,
)
from ..plugin import ModelPlugin, PluginMetadata, ProviderCapability


class OllamaPlugin(ModelPlugin):
    metadata = PluginMetadata(
        name="Ollama",
        version="1.1.0",
        description="Ollama local LLM server",
        website="https://ollama.com",
        capabilities=[
            ProviderCapability.CHAT, ProviderCapability.STREAMING,
            ProviderCapability.TOOL_USE, ProviderCapability.VISION,
        ],
        env_prefix="OLLAMA_",
        config_schema={
            "model": {"type": "string", "default": "qwen2.5:3b"},
            "base_url": {"type": "string", "default": "http://127.0.0.1:11434"},
            "timeout": {"type": "integer", "default": 120},
        },
    )

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://127.0.0.1:11434"
        self.client = httpx.AsyncClient(timeout=config.timeout)

    async def chat(self, messages: list[Message], **kwargs) -> Completion:
        start = time.monotonic()
        payload = {
            "model": kwargs.get("model") or self.config.model,
            "messages": [m.to_dict() for m in messages],
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }
        try:
            resp = await self.client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            self.status = ProviderStatus.ONLINE
            return Completion(
                content=data.get("message", {}).get("content", ""),
                model=data.get("model", self.config.model),
                provider="ollama",
                usage=data.get("usage"),
                finish_reason=data.get("done_reason", "stop"),
                latency_ms=int((time.monotonic() - start) * 1000),
            )
        except Exception as e:
            self.status = ProviderStatus.ERROR
            self._last_error = str(e)
            raise

    async def chat_stream(self, messages: list[Message], **kwargs) -> AsyncIterator[StreamingChunk]:
        payload = {
            "model": kwargs.get("model") or self.config.model,
            "messages": [m.to_dict() for m in messages],
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    delta = data.get("message", {}).get("content", "")
                    done = data.get("done", False)
                    yield StreamingChunk(
                        content=delta, done=done,
                        finish_reason=data.get("done_reason") if done else None,
                    )
                    if done:
                        break

    async def check_health(self) -> bool:
        try:
            resp = await self.client.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                self.status = ProviderStatus.ONLINE
                return True
        except Exception:
            pass
        self.status = ProviderStatus.OFFLINE
        return False

    async def list_models(self) -> list[str]:
        try:
            resp = await self.client.get(f"{self.base_url}/api/tags", timeout=10)
            resp.raise_for_status()
            return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            return []

    @classmethod
    def from_env(cls) -> OllamaPlugin | None:
        if os.environ.get("OLLAMA_ENABLED", "true").lower() == "false":
            return None
        return cls(ProviderConfig(
            name="ollama",
            model=os.environ.get("OLLAMA_MODEL", "qwen2.5:3b"),
            base_url=os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434"),
            timeout=int(os.environ.get("OLLAMA_TIMEOUT", "120")),
        ))
