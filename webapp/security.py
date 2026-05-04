from __future__ import annotations

import hashlib
import secrets

from .models import AccessKey


KEY_PREFIX = "aida_"


def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_access_key(name: str) -> tuple[AccessKey, str]:
    return generate_access_key_with_profile(name=name, profile={})


def generate_access_key_with_profile(name: str, profile: dict[str, str]) -> tuple[AccessKey, str]:
    secret = f"{KEY_PREFIX}{secrets.token_urlsafe(30)}"
    access_key = AccessKey.objects.create(
        name=name.strip() or "Default key",
        prefix=secret[:18],
        key_hash=hash_key(secret),
        platform_name=str(profile.get("platform_name", "")).strip(),
        business_type=str(profile.get("business_type", "")).strip(),
        audience=str(profile.get("audience", "")).strip(),
        tone=str(profile.get("tone", "")).strip(),
        assistant_goal=str(profile.get("assistant_goal", "")).strip(),
        custom_instructions=str(profile.get("custom_instructions", "")).strip(),
    )
    return access_key, secret


def authenticate_access_key(raw_key: str) -> AccessKey | None:
    clean_key = raw_key.strip()
    if not clean_key:
        return None
    key_hash = hash_key(clean_key)
    try:
        access_key = AccessKey.objects.get(key_hash=key_hash, is_active=True)
    except AccessKey.DoesNotExist:
        return None
    access_key.mark_used()
    return access_key
