"""
AIDA Enterprise API — Token Manager
"""
from __future__ import annotations
from typing import Any
from .authentication import generate_jwt_token, decode_jwt_token


class TokenManager:
    """JWT tokenlarni boshqarish."""

    @staticmethod
    def create_tokens(user_id: int) -> dict[str, str]:
        """Access va refresh token yaratish."""
        return {
            "access": generate_jwt_token(user_id, "access"),
            "refresh": generate_jwt_token(user_id, "refresh"),
        }

    @staticmethod
    def refresh_access_token(refresh_token: str) -> str | None:
        """Refresh token dan yangi access token yaratish."""
        payload = decode_jwt_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            return None
        return generate_jwt_token(payload["user_id"], "access")

    @staticmethod
    def verify_token(token: str) -> dict | None:
        """Token ni tekshirish."""
        return decode_jwt_token(token)
