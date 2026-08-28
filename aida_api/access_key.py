"""
AIDA Enterprise API — Access Key Model

API keylarni saqlash va boshqarish.
"""
from __future__ import annotations
import uuid
import hashlib
import os
from django.db import models
from django.conf import settings


class AccessKey(models.Model):
    """
    API kalit — autentifikatsiya uchun.
    
    Format: aida_{random_32_hex}
    Saqlash: SHA256 hash
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_keys",
        verbose_name="Foydalanuvchi",
    )
    name = models.CharField(max_length=100, verbose_name="Kalit nomi")
    key_hash = models.CharField(max_length=64, unique=True, verbose_name="Kalit hash")
    key_prefix = models.CharField(max_length=12, verbose_name="Kalit prefiksi")
    
    # Permissions
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    scopes = models.JSONField(default=list, verbose_name="Ruxsatlar")
    
    # Rate limit
    rate_limit = models.IntegerField(default=100, verbose_name="So'rv chegarasi")
    
    # Usage tracking
    last_used_at = models.DateTimeField(blank=True, null=True, verbose_name="Oxirgi ishlatilgan")
    total_requests = models.IntegerField(default=0, verbose_name="Jami so'rvlar")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan")
    expires_at = models.DateTimeField(blank=True, null=True, verbose_name="Muddati tugaydi")

    class Meta:
        verbose_name = "API Kalit"
        verbose_name_plural = "API Kalitlar"
        ordering = ["-created_at"]
        db_table = "aida_access_keys"

    def __str__(self):
        return f"{self.name} ({self.key_prefix}...)"

    @classmethod
    def create_key(cls, user, name: str, scopes: list = None, rate_limit: int = 100, expires_at=None):
        """Yangi API kalit yaratish."""
        # Random key yaratish
        raw_key = f"aida_{os.urandom(24).hex()}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:12]

        access_key = cls.objects.create(
            user=user,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            scopes=scopes or [],
            rate_limit=rate_limit,
            expires_at=expires_at,
        )

        return access_key, raw_key

    def verify(self, raw_key: str) -> bool:
        """Kalitni tekshirish."""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return self.key_hash == key_hash

    def record_usage(self):
        """Ishlatilishni qayd etish."""
        from django.utils import timezone
        self.last_used_at = timezone.now()
        self.total_requests += 1
        self.save(update_fields=["last_used_at", "total_requests"])


from django.utils import timezone
