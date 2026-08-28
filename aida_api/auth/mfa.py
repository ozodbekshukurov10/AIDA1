"""
AIDA Enterprise API — MFA (Multi-Factor Authentication)

TOTP-based MFA — Google Authenticator, Authy va boshqalar uchun.
"""
from __future__ import annotations
import hashlib
import hmac
import os
import struct
import time
from typing import Any


def generate_secret(length: int = 20) -> str:
    """MFA secret yaratish."""
    return os.urandom(length).hex().upper()[:32]


def generate_totp(secret: str, time_step: int = 30, digits: int = 6) -> str:
    """TOTP kod generatsiya qilish."""
    # Vaqtni time step bo'linishiga bo'lish
    counter = int(time.time()) // time_step

    # Counter ni bytes ga aylantirish
    counter_bytes = struct.pack(">Q", counter)

    # HMAC-SHA1 hisoblash
    secret_bytes = bytes.fromhex(secret)
    hmac_hash = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()

    # Dynamic truncation
    offset = hmac_hash[-1] & 0x0F
    truncated = struct.unpack(">I", hmac_hash[offset:offset + 4])[0]
    truncated &= 0x7FFFFFFF

    # Kodni generatsiya qilish
    code = truncated % (10 ** digits)
    return str(code).zfill(digits)


def verify_totp(secret: str, code: str, window: int = 1) -> bool:
    """
    TOTP kodni tekshirish.
    
    window: Necha time step oldingi/kelajakdagi kodlarni qabul qilish.
    """
    time_step = 30
    current_counter = int(time.time()) // time_step

    for offset in range(-window, window + 1):
        counter = current_counter + offset
        counter_bytes = struct.pack(">Q", counter)
        secret_bytes = bytes.fromhex(secret)
        hmac_hash = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()

        dynamic_offset = hmac_hash[-1] & 0x0F
        truncated = struct.unpack(">I", hmac_hash[dynamic_offset:dynamic_offset + 4])[0]
        truncated &= 0x7FFFFFFF

        expected_code = str(truncated % (10 ** 6)).zfill(6)
        if hmac.compare_digest(code, expected_code):
            return True

    return False


def get_provisioning_uri(secret: str, email: str, issuer: str = "AIDA") -> str:
    """Google Authenticator uchun provisioning URI yaratish."""
    import urllib.parse
    params = {
        "secret": secret,
        "issuer": issuer,
        "algorithm": "SHA1",
        "digits": 6,
        "period": 30,
    }
    return f"otpauth://totp/{urllib.parse.quote(issuer)}:{urllib.parse.quote(email)}?{urllib.parse.urlencode(params)}"


def generate_backup_codes(count: int = 8) -> list[str]:
    """Backup code'lar generatsiya qilish."""
    codes = []
    for _ in range(count):
        code = os.urandom(4).hex().upper()
        formatted = f"{code[:4]}-{code[4:]}"
        codes.append(formatted)
    return codes
