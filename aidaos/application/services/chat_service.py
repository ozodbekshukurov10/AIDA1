"""Chat service — handles response generation with context, memory, and research.

Encapsulates the chat logic previously spread across AIDAController and views.
Provides both sync (blocking) and async interfaces.
"""

from __future__ import annotations
from typing import Any, Iterable
from aidaos.infrastructure.logging import get_logger, set_context

logger = get_logger("services.chat")


class ChatService:
    """Generates responses using configured providers with memory and research context."""

    def __init__(self, provider_service: Any = None, memory_service: Any = None):
        self._provider_service = provider_service
        self._memory_service = memory_service
        self._system_prompt = (
            "Sen AIDA — aqlli, ko'p qobiliyatli sun'iy intellektsan. "
            "Kod yozish, tahlil, tarjima, reja tuzish, yozish — barchasini bajara olasan. "
            "Har doim O'zbek tilida javob ber. Texnik atamalar inglizcha bo'lishi mumkin. "
            "Aniq, lo'nda va foydali javob ber."
        )

    def chat(
        self,
        prompt: str,
        memory: Iterable[dict[str, str]] | None = None,
        provider: Any = None,
        system_prompt: str = "",
        session_id: str = "",
        research: list[Any] | None = None,
        mode: str = "",
        **kwargs,
    ) -> str:
        """Send a chat prompt and return the response.

        Args:
            prompt: User message
            memory: Conversation history as list of {role, content} dicts
            provider: Specific provider to use (default: primary)
            system_prompt: Override system prompt
            session_id: Session identifier for logging
            research: Research results to include as context
            mode: Provider mode (pro, flash, low)
        """
        set_context(session_id=session_id or "chat")
        prov = provider or (self._provider_service.get_primary() if self._provider_service else None)
        if not prov:
            logger.error("No provider available for chat")
            return "Hech qanday provider mavjud emas. Iltimos, provider sozlamalarini tekshiring."

        sys = system_prompt or self._system_prompt
        mem = memory or []

        try:
            response = prov.respond(
                prompt=prompt,
                memory=mem,
                system_prompt=sys,
                research=research or [],
                mode=mode,
            )
            logger.info(f"Chat response: session={session_id} prompt_len={len(prompt)} resp_len={len(response)}")
            return response
        except Exception as e:
            logger.exception(f"Chat failed: {e}")
            return f"Xatolik yuz berdi: {e}"

    def chat_with_fallback(
        self,
        prompt: str,
        memory: Iterable[dict[str, str]] | None = None,
        providers: list[Any] | None = None,
        system_prompt: str = "",
        session_id: str = "",
        research: list[Any] | None = None,
    ) -> str:
        """Try providers in order until one succeeds."""
        provs = providers or []
        if not provs and self._provider_service:
            provs = [
                self._provider_service.get_primary(),
                *self._provider_service.get_all().values(),
            ]

        last_error = ""
        for prov in provs:
            if not prov or getattr(prov, "name", "") == "local":
                continue
            try:
                return self.chat(
                    prompt=prompt, memory=memory, provider=prov,
                    system_prompt=system_prompt, session_id=session_id,
                    research=research,
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Fallback provider '{getattr(prov, 'name', '?')}' failed: {e}")
                continue

        logger.error(f"All providers failed: {last_error}")
        return f"Barcha providerlar muvaffaqiyatsiz: {last_error}"

    def set_system_prompt(self, prompt: str) -> None:
        self._system_prompt = prompt
