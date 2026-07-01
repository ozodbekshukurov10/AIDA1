"""Chat use case — orchestrates message-based conversations with LLM providers."""

from __future__ import annotations
import time
import logging
from typing import Any

from ...domain.entities import Message, Completion, MessageRole, ProviderStatus
from ...domain.exceptions import ProviderOfflineError, ProviderFallbackError, ValidationError
from ...domain.interfaces import ProviderRepository, SessionRepository, MetricsRepository
from ..dtos import ChatRequest, ChatResponse

logger = logging.getLogger("aidaos.application.chat")


class ChatUseCase:
    def __init__(
        self,
        provider_repo: ProviderRepository,
        session_repo: SessionRepository,
        metrics_repo: MetricsRepository,
    ):
        self._providers = provider_repo
        self._sessions = session_repo
        self._metrics = metrics_repo

    async def execute(self, request: ChatRequest) -> ChatResponse:
        errors = request.validate()
        if errors:
            raise ValidationError("; ".join(errors))

        start = time.monotonic()
        provider = request.provider or ""
        messages = self._build_messages(request)

        try:
            completion = await self._providers.chat(
                messages, provider=provider,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
        except ProviderFallbackError as e:
            raise
        except Exception as e:
            raise ProviderOfflineError(f"Chat failed: {e}")

        latency = int((time.monotonic() - start) * 1000)

        if request.session_id:
            try:
                session = await self._sessions.get(request.session_id)
                if session:
                    await self._sessions.add_message(request.session_id, {
                        "role": "user", "content": request.message,
                    })
                    await self._sessions.add_message(request.session_id, {
                        "role": "assistant", "content": completion.content,
                    })
            except Exception:
                logger.warning("Failed to persist chat messages", exc_info=True)

        try:
            await self._metrics.record_request(
                endpoint="/chat", method="POST",
                status=200, latency_ms=latency,
                provider=completion.provider, model=completion.model,
            )
        except Exception:
            pass

        return ChatResponse(
            content=completion.content,
            session_id=request.session_id,
            model=completion.model,
            provider=completion.provider,
            latency_ms=latency,
            usage=completion.usage,
            finish_reason=completion.finish_reason,
        )

    async def stream(self, request: ChatRequest):
        errors = request.validate()
        if errors:
            raise ValidationError("; ".join(errors))

        provider = request.provider or ""
        messages = self._build_messages(request)

        async for chunk in self._providers.chat_stream(
            messages, provider=provider,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        ):
            yield chunk

    def _build_messages(self, request: ChatRequest) -> list[Message]:
        msgs = []
        if request.system_prompt:
            msgs.append(Message.system(request.system_prompt))
        if request.session_id:
            try:
                session_msgs = self._get_session_history(request.session_id)
                for m in session_msgs:
                    role = MessageRole(m.get("role", "user"))
                    msgs.append(Message(role=role, content=m.get("content", "")))
            except Exception:
                pass
        msgs.append(Message.user(request.message))
        return msgs

    def _get_session_history(self, session_id: str) -> list[dict]:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return []
            return asyncio.run(self._sessions.get_messages(session_id, limit=50))
        except Exception:
            return []
