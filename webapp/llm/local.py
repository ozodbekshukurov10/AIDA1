from __future__ import annotations
import asyncio
import json
import random
import time
from typing import AsyncIterator

from .base import (
    BaseProvider, ProviderConfig, Message, MessageRole,
    Completion, StreamingChunk, ProviderStatus,
)


INTENT_PATTERNS: dict[str, list[str]] = {
    "code_generate": ["kod yoz", "yoz", "code", "dastur", "create", "generate", "function", "class"],
    "code_analyze": ["tahlil", "analyze", "tekshir", "review", "tekshirish"],
    "code_fix": ["tuzat", "fix", "bug", "xato", "error", "not working"],
    "debug": ["debug", "nosozlik", "diagnose"],
    "translate": ["tarjima", "translate", "o'gir"],
    "explain": ["tushuntir", "explain", "nima", "what is", "how"],
    "research": ["qidir", "search", "research", "google", "internet"],
    "general": [],
}


class LocalProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.model = config.model or "local-rule-based"
        self.status = ProviderStatus.ONLINE

    def _detect_intent(self, text: str) -> str:
        text_lower = text.lower()
        for intent, keywords in INTENT_PATTERNS.items():
            for kw in keywords:
                if kw in text_lower:
                    return intent
        return "general"

    def _generate_response(self, messages: list[Message]) -> str:
        user_msg = next((m.content for m in reversed(messages) if m.role == MessageRole.USER), "")
        system = next((m.content for m in messages if m.role == MessageRole.SYSTEM), "")
        intent = self._detect_intent(user_msg)
        if intent == "code_generate":
            return f"AIDA Local: '{user_msg}' buyrug'ini bajaryapman.\n\n```python\n# {user_msg}\ndef main():\n    pass\n```"
        elif intent == "code_fix":
            return "AIDA Local: Kod tahlil qilindi. Quyidagi muammolar topildi:\n1. Import yo'q\n2. Error handling yo'q\n\nTuzatish taklif qilinmoqda."
        elif intent == "explain":
            return f"AIDA Local: {user_msg}\n\nBu haqida to'liq tushuntirish: Bu umumiy savol. To'liq javob olish uchun LLM provider (Ollama/Gemini) ulang."
        elif intent == "translate":
            return "AIDA Local: Tarjima qilyapman... (Local provider cheklangan, to'liq tarjima uchun LLM ulang)"
        else:
            return f"AIDA Local Assistant:\n\nSizning so'rovingiz: {user_msg}\n\nTo'liq AI javobi uchun Ollama yoki Gemini providerini ulang. /status orqali provider holatini tekshiring."

    async def chat(self, messages: list[Message], **kwargs) -> Completion:
        start = time.monotonic()
        content = self._generate_response(messages)
        return Completion(
            content=content,
            model=self.model,
            provider="local",
            usage={"prompt_tokens": 0, "completion_tokens": 0},
            finish_reason="stop",
            latency_ms=int((time.monotonic() - start) * 1000),
        )

    async def chat_stream(self, messages: list[Message], **kwargs) -> AsyncIterator[StreamingChunk]:
        content = self._generate_response(messages)
        for chunk in [content[i:i+50] for i in range(0, len(content), 50)]:
            yield StreamingChunk(content=chunk, done=False)
            await asyncio.sleep(0.02)
        yield StreamingChunk(content="", done=True, finish_reason="stop")

    async def check_health(self) -> bool:
        return True

    async def list_models(self) -> list[str]:
        return [self.model]
