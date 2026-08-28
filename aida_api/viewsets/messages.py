"""
AIDA Enterprise API — Message ViewSet

Xabarlarni boshqarish uchun CRUD va maxsus endpointlar.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..responses import APIResponse
from ..exceptions import ResourceNotFoundError

# ── In-Memory Storage (demo) ──────────────────────────────────────────────────
_messages_db: dict[str, dict] = {}


class MessageViewSet(viewsets.ViewSet):
    """
    Xabar boshqarish.

    - GET    /messages/            — Xabarlar ro'yxati
    - GET    /messages/{id}/       — Bitta xabar
    - POST   /messages/{id}/regenerate/ — AI javobni qayta generatsiya qilish
    - POST   /messages/{id}/feedback/   — Xabarni baholash
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Xabarlar ro'yxati (faqat foydalanuvchining chatlaridagi xabarlar)."""
        from .chats import _chats_db

        user_chat_ids = {
            chat["id"]
            for chat in _chats_db.values()
            if chat["user_id"] == str(request.user.id)
        }

        chat_id = request.query_params.get("chat_id")
        role = request.query_params.get("role")

        messages = [
            msg for msg in _messages_db.values()
            if msg["chat_id"] in user_chat_ids
        ]

        if chat_id:
            messages = [m for m in messages if m["chat_id"] == chat_id]
        if role:
            messages = [m for m in messages if m["role"] == role]

        messages.sort(key=lambda m: m["created_at"], reverse=True)

        return Response(APIResponse.success(data=messages))

    def retrieve(self, request, pk=None):
        """Bitta xabarni olish."""
        from .chats import _chats_db

        message = _get_message_or_404(pk)
        _check_message_ownership(message, request.user.id, _chats_db)

        return Response(APIResponse.success(data=message))

    @action(detail=True, methods=["post"])
    def regenerate(self, request, pk=None):
        """AI javobni qayta generatsiya qilish."""
        from .chats import _chats_db

        message = _get_message_or_404(pk)
        _check_message_ownership(message, request.user.id, _chats_db)

        if message["role"] != "assistant":
            return Response(
                APIResponse.bad_request(
                    message="Faqat AI xabarlarini qayta generatsiya qilish mumkin"
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        chat = _chats_db.get(message["chat_id"])
        model = chat["model"] if chat else "gpt-4"

        now = datetime.now(timezone.utc).isoformat()

        new_msg_id = str(uuid.uuid4())
        new_message = {
            "id": new_msg_id,
            "chat_id": message["chat_id"],
            "role": "assistant",
            "content": f"[Qayta generatsiya] Yangi AI javob — model: {model}",
            "model": model,
            "tokens_used": 0,
            "parent_message_id": pk,
            "feedback": None,
            "created_at": now,
        }
        _messages_db[new_msg_id] = new_message

        return Response(
            APIResponse.success(data=new_message, message="AI javob qayta generatsiya qilindi"),
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def feedback(self, request, pk=None):
        """Xabarni baholash."""
        from .chats import _chats_db

        message = _get_message_or_404(pk)
        _check_message_ownership(message, request.user.id, _chats_db)

        rating = request.data.get("rating")
        comment = request.data.get("comment", "")

        if rating is None:
            return Response(
                APIResponse.bad_request(message="'rating' kiritilishi shart"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return Response(
                APIResponse.bad_request(message="'rating' 1 dan 5 gacha bo'lishi kerak"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        message["feedback"] = {
            "rating": rating,
            "comment": comment,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        return Response(
            APIResponse.success(data=message, message="Feedback qabul qilindi")
        )


def _get_message_or_404(pk: str | None) -> dict:
    """Xabar topilmasa 404 qaytaradi."""
    if not pk or pk not in _messages_db:
        raise ResourceNotFoundError("Xabar", str(pk or ""))
    return _messages_db[pk]


def _check_message_ownership(message: dict, user_id, chats_db: dict) -> None:
    """Foydalanuvchi xabar egasini tekshiradi (chat orqali)."""
    chat = chats_db.get(message["chat_id"])
    if not chat or chat["user_id"] != str(user_id):
        raise ResourceNotFoundError("Xabar", message["id"])
