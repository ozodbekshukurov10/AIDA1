from __future__ import annotations
import json
import time
from typing import AsyncIterator

import httpx

from ..base import (
    BaseProvider, ProviderConfig, Message, MessageRole,
    Completion, StreamingChunk, ProviderStatus,
)


class OpenAICompatibleProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url.rstrip("/")
        self.api_key = config.api_key or ""
        self.client = httpx.AsyncClient(timeout=config.timeout)

    async def chat(self, messages: list[Message], **kwargs) -> Completion:
        start = time.monotonic()
        payload = {
            "model": kwargs.get("model") or self.config.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": False,
        }
        headers = self._build_headers()

        try:
            resp = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload, headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]
            self.status = ProviderStatus.ONLINE
            return Completion(
                content=choice["message"].get("content", "") or "",
                model=data.get("model", self.config.model),
                provider=self.config.name,
                usage=data.get("usage"),
                finish_reason=choice.get("finish_reason", "stop"),
                latency_ms=int((time.monotonic() - start) * 1000),
            )
        except httpx.TimeoutException:
            self.status = ProviderStatus.ERROR
            self._last_error = f"Request timed out after {self.config.timeout}s"
            raise
        except Exception as e:
            self.status = ProviderStatus.ERROR
            self._last_error = str(e)
            raise

    async def chat_stream(self, messages: list[Message], **kwargs) -> AsyncIterator[StreamingChunk]:
        payload = {
            "model": kwargs.get("model") or self.config.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": True,
        }
        headers = self._build_headers()

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            async with client.stream(
                "POST", f"{self.base_url}/v1/chat/completions",
                json=payload, headers=headers,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        yield StreamingChunk(content="", done=True)
                        break
                    data = json.loads(data_str)
                    choices = data.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    if delta.get("content"):
                        yield StreamingChunk(content=delta["content"], done=False)
                    finish = choices[0].get("finish_reason")
                    if finish:
                        yield StreamingChunk(content="", done=True, finish_reason=finish)

    async def check_health(self) -> bool:
        try:
            resp = await self.client.get(f"{self.base_url}/v1/models", timeout=5)
            if resp.status_code == 200:
                self.status = ProviderStatus.ONLINE
                return True
        except Exception:
            pass
        self.status = ProviderStatus.OFFLINE
        return False

    async def list_models(self) -> list[str]:
        try:
            resp = await self.client.get(f"{self.base_url}/v1/models", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return [m["id"] for m in data.get("data", [])]
        except Exception:
            return []

    def _build_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
