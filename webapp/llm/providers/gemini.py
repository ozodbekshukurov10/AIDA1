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


class GeminiPlugin(ModelPlugin):
    metadata = PluginMetadata(
        name="Gemini",
        version="1.1.0",
        description="Google Gemini API (Gemini 2.0 Flash, Gemini 1.5 Pro, etc.)",
        website="https://ai.google.dev",
        capabilities=[
            ProviderCapability.CHAT, ProviderCapability.STREAMING,
            ProviderCapability.VISION, ProviderCapability.FUNCTION_CALLING,
        ],
        requires_api_key=True,
        env_prefix="GEMINI_",
        config_schema={
            "model": {"type": "string", "default": "gemini-2.0-flash"},
            "api_key": {"type": "string", "required": True},
            "timeout": {"type": "integer", "default": 60},
        },
    )

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key or os.environ.get("GEMINI_API_KEY", "")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.client = httpx.AsyncClient(timeout=config.timeout)
        self._sys_patched = False

    def _convert_messages(self, messages: list[Message]) -> tuple[str, list[dict]]:
        system = ""
        contents = []
        for m in messages:
            if m.role == MessageRole.SYSTEM:
                system = m.content
            elif m.role == MessageRole.USER:
                contents.append({"role": "user", "parts": [{"text": m.content}]})
            elif m.role == MessageRole.ASSISTANT:
                contents.append({"role": "model", "parts": [{"text": m.content}]})
        return system, contents

    async def chat(self, messages: list[Message], **kwargs) -> Completion:
        start = time.monotonic()
        model = kwargs.get("model") or self.config.model
        system, contents = self._convert_messages(messages)
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "maxOutputTokens": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        try:
            resp = await self.client.post(
                f"{self.base_url}/models/{model}:generateContent",
                params={"key": self.api_key}, json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            candidate = data.get("candidates", [{}])[0]
            parts = candidate.get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)
            self.status = ProviderStatus.ONLINE
            return Completion(
                content=text, model=model, provider="gemini",
                finish_reason=candidate.get("finishReason", "stop"),
                latency_ms=int((time.monotonic() - start) * 1000),
            )
        except Exception as e:
            self.status = ProviderStatus.ERROR
            self._last_error = str(e)
            raise

    async def chat_stream(self, messages: list[Message], **kwargs) -> AsyncIterator[StreamingChunk]:
        model = kwargs.get("model") or self.config.model
        system, contents = self._convert_messages(messages)
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "maxOutputTokens": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/models/{model}:streamGenerateContent",
                params={"key": self.api_key, "alt": "sse"},
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if not data_str:
                        continue
                    data = json.loads(data_str)
                    candidates = data.get("candidates", [])
                    if not candidates:
                        continue
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts)
                    finish = candidates[0].get("finishReason")
                    if text:
                        yield StreamingChunk(content=text, done=False)
                    if finish:
                        yield StreamingChunk(content="", done=True, finish_reason=finish)

    async def check_health(self) -> bool:
        try:
            resp = await self.client.get(
                f"{self.base_url}/models", params={"key": self.api_key}, timeout=5,
            )
            if resp.status_code == 200:
                self.status = ProviderStatus.ONLINE
                return True
        except Exception:
            pass
        self.status = ProviderStatus.OFFLINE
        return False

    async def list_models(self) -> list[str]:
        try:
            resp = await self.client.get(
                f"{self.base_url}/models", params={"key": self.api_key}, timeout=10,
            )
            resp.raise_for_status()
            return [m["name"].replace("models/", "") for m in resp.json().get("models", [])]
        except Exception:
            return ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]

    @classmethod
    def from_env(cls) -> GeminiPlugin | None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        return cls(ProviderConfig(
            name="gemini",
            model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
            api_key=api_key,
            timeout=int(os.environ.get("GEMINI_TIMEOUT", "60")),
        ))
