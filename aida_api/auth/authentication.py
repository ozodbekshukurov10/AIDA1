"""
AIDA Enterprise API — Authentication Classes

JWT + API Key autentifikatsiya tizimi.
"""
from __future__ import annotations
import hashlib
import hmac
import os
import time
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from rest_framework import authentication, exceptions

User = get_user_model()

# JWT sozlamalari (production da .env dan olinishi kerak)
JWT_SECRET_KEY = os.environ.get("AIDA_JWT_SECRET", "aida-dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_LIFETIME = 15 * 60  # 15 daqiqa
JWT_REFRESH_TOKEN_LIFETIME = 7 * 24 * 60 * 60  # 7 kun


def generate_jwt_token(user_id: int, token_type: str = "access") -> str:
    """JWT token yaratish."""
    import json
    import base64

    now = int(time.time())
    if token_type == "access":
        exp = now + JWT_ACCESS_TOKEN_LIFETIME
    else:
        exp = now + JWT_REFRESH_TOKEN_LIFETIME

    payload = {
        "user_id": user_id,
        "type": token_type,
        "iat": now,
        "exp": exp,
    }

    # Oddiy JWT yaratish (production da PyJWT ishlatish kerak)
    header = base64.urlsafe_b64encode(json.dumps({"alg": JWT_ALGORITHM, "typ": "JWT"}).encode()).decode().rstrip("=")
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = hmac.new(JWT_SECRET_KEY.encode(), f"{header}.{body}".encode(), hashlib.sha256).hexdigest()

    return f"{header}.{body}.{signature}"


def decode_jwt_token(token: str) -> dict | None:
    """JWT token ni decode qilish."""
    import json
    import base64

    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header, body, signature = parts

        # Signature ni tekshirish
        expected_sig = hmac.new(JWT_SECRET_KEY.encode(), f"{header}.{body}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None

        # Payload ni decode qilish
        padding = 4 - len(body) % 4
        body += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(body))

        # Muddatni tekshirish
        if payload.get("exp", 0) < time.time():
            return None

        return payload
    except Exception:
        return None


# ── API Key Utilities ──────────────────────────────────────────────────────────

def generate_api_key() -> str:
    """API key yaratish."""
    random_bytes = os.urandom(24)
    return f"aida_{random_bytes.hex()}"


def hash_api_key(api_key: str) -> str:
    """API key ni hash qilish."""
    return hashlib.sha256(api_key.encode()).hexdigest()


# ── Authentication Classes ─────────────────────────────────────────────────────

class JWTAuthentication(authentication.BaseAuthentication):
    """
    JWT Token autentifikatsiya.
    
    Header: Authorization: Bearer <token>
    """

    def authenticate(self, request):
        auth = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth.startswith("Bearer "):
            return None

        token = auth[7:]
        if not token:
            return None

        payload = decode_jwt_token(token)
        if payload is None:
            raise exceptions.AuthenticationFailed("Token noto'g'ri yoki muddati tugagan.")

        if payload.get("type") != "access":
            raise exceptions.AuthenticationFailed("Noto'g'ri token turi.")

        try:
            user = User.objects.get(id=payload["user_id"])
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("Foydalanuvchi topilmadi.")

        return (user, token)


class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    API Key autentifikatsiya.
    
    Ushlash usullari:
    1. Header: X-API-Key: aida_...
    2. Header: Authorization: Bearer aida_...
    3. Query: ?key=aida_...
    """

    def authenticate(self, request):
        api_key = None

        # 1. X-API-Key header
        api_key = request.META.get("HTTP_X_API_KEY")

        # 2. Bearer token (API key formatida)
        if not api_key:
            auth = request.META.get("HTTP_AUTHORIZATION", "")
            if auth.startswith("Bearer ") and auth[7:].startswith("aida_"):
                api_key = auth[7:]

        # 3. Query parameter
        if not api_key:
            api_key = request.GET.get("key")

        if not api_key or not api_key.startswith("aida_"):
            return None

        # API key ni tekshirish (hash comparison)
        key_hash = hash_api_key(api_key)

        # Database dan qidirish (hozircha oddiy)
        try:
            from webapp.models import AccessKey
            key_obj = AccessKey.objects.get(key_hash__startswith=key_hash[:16], is_active=True)
        except (AccessKey.DoesNotExist, Exception):
            raise exceptions.AuthenticationFailed("API key noto'g'ri yoki faol emas.")

        return (key_obj.user, api_key)


class CombinedAuthentication(authentication.BaseAuthentication):
    """
    Bir nechta autentifikatsiya usulini birlashtirish.
    
    Tartibi:
    1. JWT token tekshirish
    2. API key tekshirish
    3. Session auth (Django admin uchun)
    """

    def authenticate(self, request):
        # 1. JWT
        jwt_auth = JWTAuthentication()
        result = jwt_auth.authenticate(request)
        if result:
            return result

        # 2. API Key
        api_key_auth = APIKeyAuthentication()
        result = api_key_auth.authenticate(request)
        if result:
            return result

        # 3. Session (faqat Django admin uchun)
        if request.path.startswith("/admin/"):
            from rest_framework.authentication import SessionAuthentication
            session_auth = SessionAuthentication()
            try:
                return session_auth.authenticate(request)
            except Exception:
                pass

        return None
