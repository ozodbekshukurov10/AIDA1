from __future__ import annotations

import hashlib
import secrets
import time
from threading import Lock

from .models import AccessKey


KEY_PREFIX = "aida_"


def hash_key(raw_key: str, salt: str | None = None) -> str:
    if salt is None:
        salt = secrets.token_hex(16)
    key = hashlib.scrypt(
        raw_key.encode("utf-8"),
        salt=salt.encode("utf-8"),
        n=16384, r=8, p=1,
        dklen=64
    )
    return f"{salt}${key.hex()}"


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
    for access_key in AccessKey.objects.filter(is_active=True):
        stored = access_key.key_hash
        if "$" in stored:
            stored_salt, stored_hash = stored.split("$", 1)
            computed = hash_key(clean_key, salt=stored_salt)
            if computed == stored:
                access_key.mark_used()
                return access_key
        else:
            legacy_hash = hashlib.sha256(clean_key.encode("utf-8")).hexdigest()
            if legacy_hash == stored:
                access_key.mark_used()
                return access_key
    return None


class TokenBucket:
    def __init__(self, capacity: int, rate: float):
        self.capacity = capacity
        self.rate = rate
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self.lock = Lock()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        added = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + added)
        self.last_refill = now

    def consume(self, count: int = 1) -> bool:
        with self.lock:
            self._refill()
            if self.tokens >= count:
                self.tokens -= count
                return True
            return False

    def remaining(self) -> float:
        with self.lock:
            self._refill()
            return self.tokens


class RateLimiter:
    def __init__(self, capacity: int = 30, rate: float = 1.0):
        self.capacity = capacity
        self.rate = rate
        self._buckets: dict[str, tuple[TokenBucket, float]] = {}
        self._lock = Lock()
        self._cleanup_interval = 300.0

    def _cleanup(self):
        now = time.monotonic()
        stale = [k for k, (_, t) in self._buckets.items() if now - t > self._cleanup_interval]
        for k in stale:
            del self._buckets[k]

    def get_bucket(self, key: str) -> TokenBucket:
        with self._lock:
            self._cleanup()
            if key not in self._buckets:
                self._buckets[key] = (TokenBucket(self.capacity, self.rate), time.monotonic())
            return self._buckets[key][0]

    def check(self, key: str, count: int = 1) -> bool:
        return self.get_bucket(key).consume(count)

    def remaining(self, key: str) -> float:
        return self.get_bucket(key).remaining()

    def reset(self, key: str):
        with self._lock:
            self._buckets.pop(key, None)


rate_limiter = RateLimiter(capacity=30, rate=1.0)
