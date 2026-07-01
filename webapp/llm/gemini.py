from __future__ import annotations
import json
import time
import httpx
from typing import AsyncIterator

from .base import (
    BaseProvider, ProviderConfig, Message, MessageRole,
    Completion, StreamingChunk, ProviderStatus,
)


GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key or ""
        self.model = config.model or "gemini-2.0-flash"
        self.client = httpx.AsyncClient(timeout=config.timeout)

    def _to_gemini_messages(self, messages: list[Message]) -> list[dict]:
        gemini_msgs = []
        system = ""
        for m in messages:
            if m.role == MessageRole.SYSTEM:
                system += m.content + "\n"
            elif m.role == MessageRole.USER:
                gemini_msgs.append({"role": "user", "parts": [{"text": m.content}]})
            elif m.role == MessageRole.ASSISTANT:
                gemini_msgs.append({"role": "model", "parts": [{"text": m.content}]})
        if system:
            if gemini_msgs:
                gemini_msgs[0]["parts"][0]["text"] = f"[System: {system}]\n{gemini_msgs[0]['parts'][0]['text']}"
        return gemini_msgs

    async def chat(self, messages: list[Message], **kwargs) -> Completion:
        start = time.monotonic()
        url = f"{GEMINI_API_BASE}/models/{kwargs.get('model', self.model)}:generateContent?key={self.api_key}"
        payload = {
            "contents": self._to_gemini_messages(messages),
            "generationConfig": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "maxOutputTokens": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }
        try:
            resp = await self.client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            usage = data.get("usageMetadata")
            self.status = ProviderStatus.ONLINE
            return Completion(
                content=text,
                model=self.model,
                provider="gemini",
                usage=usage,
                finish_reason=data.get("candidates", [{}])[0].get("finishReason", "STOP"),
                latency_ms=int((time.monotonic() - start) * 1000),
            )
        except Exception as e:
            self.status = ProviderStatus.ERROR
            self._last_error = str(e)
            raise

    async def chat_stream(self, messages: list[Message], **kwargs) -> AsyncIterator[StreamingChunk]:
        url = f"{GEMINI_API_BASE}/models/{kwargs.get('model', self.model)}:streamGenerateContent?key={self.api_key}&alt=sse"
        payload = {
            "contents": self._to_gemini_messages(messages),
            "generationConfig": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "maxOutputTokens": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            async with client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = json.loads(line[6:])
                    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts)
                    finish = data.get("candidates", [{}])[0].get("finishReason")
                    done = finish is not None
                    yield StreamingChunk(content=text, done=done, finish_reason=finish)

    async def check_health(self) -> bool:
        if not self.api_key:
            self.status = ProviderStatus.OFFLINE
            return False
        try:
            resp = await self.client.get(
                f"{GEMINI_API_BASE}/models?key={self.api_key}", timeout=5
            )
            if resp.status_code == 200:
                self.status = ProviderStatus.ONLINE
                return True
        except Exception:
            self.status = ProviderStatus.OFFLINE
        return False

    async def list_models(self) -> list[str]:
        if not self.api_key:
            return []
        try:
            resp = await self.client.get(
                f"{GEMINI_API_BASE}/models?key={self.api_key}", timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            return [m["name"].replace("models/", "") for m in data.get("models", [])]
        except Exception:
            return []
