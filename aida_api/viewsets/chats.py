"""
AIDA Enterprise API — Chat ViewSet

Chatlarni boshqarish uchun CRUD va maxsus endpointlar.
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
_chats_db: dict[str, dict] = {}


class ChatViewSet(viewsets.ViewSet):
    """
    Chat boshqarish.

    - GET    /chats/                    — Chatlar ro'yxati
    - POST   /chats/                    — Yangi chat yaratish
    - GET    /chats/{id}/               — Bitta chat
    - PUT    /chats/{id}/               — Chatni to'liq yangilash
    - DELETE /chats/{id}/               — Chatni o'chirish
    - POST   /chats/{id}/send-message/  — Xabar yuborish va AI javob olish
    - GET    /chats/{id}/history/       — Chat tarixi
    - POST   /chats/{id}/archive/       — Chatni arxivlash
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Chatlar ro'yxati (faqat foydalanuvchining o'ziga tegishli)."""
        user_id = str(request.user.id)
        user_chats = [
            chat for chat in _chats_db.values()
            if chat["user_id"] == user_id
        ]

        search = request.query_params.get("search")
        if search:
            user_chats = [
                c for c in user_chats
                if search.lower() in c["title"].lower()
            ]

        archived = request.query_params.get("archived")
        if archived is not None:
            user_chats = [c for c in user_chats if c["is_archived"] == (archived.lower() == "true")]

        user_chats.sort(key=lambda c: c["updated_at"], reverse=True)

        return Response(APIResponse.success(data=user_chats))

    def create(self, request):
        """Yangi chat yaratish."""
        title = request.data.get("title", "Untitled Chat")
        model = request.data.get("model", "gpt-4")

        chat_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        chat = {
            "id": chat_id,
            "user_id": str(request.user.id),
            "title": title,
            "model": model,
            "is_archived": False,
            "created_at": now,
            "updated_at": now,
        }
        _chats_db[chat_id] = chat

        return Response(
            APIResponse.created(data=chat, message="Chat yaratildi"),
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        """Bitta chatni olish."""
        chat = _get_chat_or_404(pk)
        _check_ownership(chat, request.user.id)
        return Response(APIResponse.success(data=chat))

    def update(self, request, pk=None):
        """Chatni to'liq yangilash."""
        chat = _get_chat_or_404(pk)
        _check_ownership(chat, request.user.id)

        chat["title"] = request.data.get("title", chat["title"])
        chat["model"] = request.data.get("model", chat["model"])
        chat["updated_at"] = datetime.now(timezone.utc).isoformat()

        return Response(APIResponse.success(data=chat, message="Chat yangilandi"))

    def destroy(self, request, pk=None):
        """Chatni o'chirish."""
        chat = _get_chat_or_404(pk)
        _check_ownership(chat, request.user.id)

        del _chats_db[pk]
        return Response(
            APIResponse.success(message="Chat o'chirildi"),
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(detail=True, methods=["post"])
    def send_message(self, request, pk=None):
        """Xabar yuborish va AI javob olish."""
        from .messages import _messages_db

        chat = _get_chat_or_404(pk)
        _check_ownership(chat, request.user.id)

        content = request.data.get("content")
        if not content:
            return Response(
                APIResponse.bad_request(message="'content' kiritilishi shart"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = datetime.now(timezone.utc).isoformat()

        user_msg_id = str(uuid.uuid4())
        user_message = {
            "id": user_msg_id,
            "chat_id": pk,
            "role": "user",
            "content": content,
            "created_at": now,
        }
        _messages_db[user_msg_id] = user_message

        ai_msg_id = str(uuid.uuid4())
        ai_message = {
            "id": ai_msg_id,
            "chat_id": pk,
            "role": "assistant",
            "content": f"AI javob: Sizning so'rovingiz qabul qilindi — '{content[:50]}...'",
            "model": chat["model"],
            "tokens_used": len(content.split()) * 2,
            "created_at": now,
        }
        _messages_db[ai_msg_id] = ai_message

        chat["updated_at"] = now

        return Response(
            APIResponse.success(
                data={"user_message": user_message, "ai_message": ai_message},
                message="Xabar yuborildi",
            ),
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        """Chat tarixi (barcha xabarlar)."""
        from .messages import _messages_db

        chat = _get_chat_or_404(pk)
        _check_ownership(chat, request.user.id)

        messages = [
            msg for msg in _messages_db.values()
            if msg["chat_id"] == pk
        ]
        messages.sort(key=lambda m: m["created_at"])

        return Response(APIResponse.success(data=messages))

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """Chatni arxivlash."""
        chat = _get_chat_or_404(pk)
        _check_ownership(chat, request.user.id)

        chat["is_archived"] = True
        chat["updated_at"] = datetime.now(timezone.utc).isoformat()

        return Response(APIResponse.success(data=chat, message="Chat arxivlandi"))


def _get_chat_or_404(pk: str | None) -> dict:
    """Chat topilmasa 404 qaytaradi."""
    if not pk or pk not in _chats_db:
        raise ResourceNotFoundError("Chat", str(pk or ""))
    return _chats_db[pk]


def _check_ownership(chat: dict, user_id) -> None:
    """Foydalanuvchi chat egasini tekshiradi."""
    if chat["user_id"] != str(user_id):
        raise ResourceNotFoundError("Chat", chat["id"])
