"""
AIDA Enterprise API — OAuth2 Providers

GitHub va Google OAuth2 integratsiyasi.
"""
from __future__ import annotations
import os
import json
from typing import Any
from urllib.parse import urlencode

try:
    import httpx
except ImportError:
    httpx = None


class OAuth2Provider:
    """OAuth2 provayderlari uchun asos sinf."""

    name = ""
    authorize_url = ""
    token_url = ""
    user_info_url = ""
    default_scope = ""

    def __init__(self):
        self.client_id = os.environ.get(f"{self.name.upper()}_CLIENT_ID", "")
        self.client_secret = os.environ.get(f"{self.name.upper()}_CLIENT_SECRET", "")
        self.redirect_uri = os.environ.get(
            f"{self.name.upper()}_REDIRECT_URI",
            f"http://localhost:8000/api/v1/auth/oauth2/{self.name}/callback/"
        )

    def get_redirect_url(self, state: str = "") -> str:
        """OAuth2 redirect URL yaratish."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.default_scope,
            "response_type": "code",
        }
        if state:
            params["state"] = state
        return f"{self.authorize_url}?{urlencode(params)}"

    def exchange_code(self, code: str) -> dict[str, Any] | None:
        """Authorization code ni token ga almashtirish."""
        if not httpx:
            return None

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            resp = httpx.post(self.token_url, data=data, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def get_user_info(self, access_token: str) -> dict[str, Any] | None:
        """Foydalanuvchi ma'lumotlarini olish."""
        if not httpx:
            return None

        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            resp = httpx.get(self.user_info_url, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None


class GitHubOAuth2(OAuth2Provider):
    """GitHub OAuth2 provayderi."""
    name = "github"
    authorize_url = "https://github.com/login/oauth/authorize"
    token_url = "https://github.com/login/oauth/access_token"
    user_info_url = "https://api.github.com/user"
    default_scope = "read:user user:email"

    def get_user_info(self, access_token: str) -> dict[str, Any] | None:
        """GitHub foydalanuvchi ma'lumotlarini olish."""
        if not httpx:
            return None

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }

        try:
            # Asosiy ma'lumotlar
            user_resp = httpx.get(self.user_info_url, headers=headers, timeout=10)
            user_resp.raise_for_status()
            user_data = user_resp.json()

            # Email ma'lumotlari
            email_resp = httpx.get("https://api.github.com/user/emails", headers=headers, timeout=10)
            emails = email_resp.json() if email_resp.status_code == 200 else []

            primary_email = ""
            for email in emails:
                if email.get("primary"):
                    primary_email = email["email"]
                    break

            return {
                "id": str(user_data.get("id")),
                "email": primary_email or user_data.get("email", ""),
                "name": user_data.get("name", ""),
                "login": user_data.get("login", ""),
                "avatar_url": user_data.get("avatar_url", ""),
            }
        except Exception:
            return None


class GoogleOAuth2(OAuth2Provider):
    """Google OAuth2 provayderi."""
    name = "google"
    authorize_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    default_scope = "openid email profile"

    def get_user_info(self, access_token: str) -> dict[str, Any] | None:
        """Google foydalanuvchi ma'lumotlarini olish."""
        if not httpx:
            return None

        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            resp = httpx.get(self.user_info_url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            return {
                "id": data.get("id"),
                "email": data.get("email"),
                "name": data.get("name"),
                "given_name": data.get("given_name", ""),
                "family_name": data.get("family_name", ""),
                "avatar_url": data.get("picture", ""),
            }
        except Exception:
            return None


# ── Registry ───────────────────────────────────────────────────────────────────

OAUTH2_PROVIDERS = {
    "github": GitHubOAuth2,
    "google": GoogleOAuth2,
}


def get_oauth2_provider(name: str) -> OAuth2Provider | None:
    """OAuth2 provayderini olish."""
    provider_cls = OAUTH2_PROVIDERS.get(name)
    if provider_cls:
        return provider_cls()
    return None


def get_available_providers() -> list[str]:
    """Mavjud provayderlar ro'yxati."""
    return list(OAUTH2_PROVIDERS.keys())
