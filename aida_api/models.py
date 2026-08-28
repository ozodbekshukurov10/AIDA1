"""
AIDA Enterprise API — User Model

Custom User model — email-based authentication.
"""
from __future__ import annotations
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """User manager — email-based authentication."""

    def create_user(self, email: str, password: str = None, **extra_fields):
        if not email:
            raise ValueError("Email kiritilishi shart.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    AIDA foydalanuvchi modeli.
    
    Email-based autentifikatsiya.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, verbose_name="Email")
    first_name = models.CharField(max_length=150, blank=True, verbose_name="Ism")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="Familiya")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    is_staff = models.BooleanField(default=False, verbose_name="Admin")
    is_premium = models.BooleanField(default=False, verbose_name="Premium")
    is_enterprise = models.BooleanField(default=False, verbose_name="Enterprise")
    
    # MFA
    mfa_enabled = models.BooleanField(default=False, verbose_name="MFA yoqilgan")
    mfa_secret = models.CharField(max_length=32, blank=True, verbose_name="MFA secret")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan")
    last_login = models.DateTimeField(blank=True, null=True, verbose_name="Oxirgi kirish")
    
    # Email verification
    email_verified = models.BooleanField(default=False, verbose_name="Email tasdiqlangan")
    email_verification_token = models.CharField(max_length=64, blank=True)
    
    # Password reset
    password_reset_token = models.CharField(max_length=64, blank=True)
    password_reset_expires = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"
        ordering = ["-created_at"]
        db_table = "aida_users"

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def display_name(self):
        return self.full_name or self.email.split("@")[0]

    def has_premium_access(self):
        return self.is_premium or self.is_enterprise or self.is_staff

    def has_enterprise_access(self):
        return self.is_enterprise or self.is_staff


# ── AccessKey Model ────────────────────────────────────────────────────────────
import hashlib
import os


class AccessKey(models.Model):
    """
    API kalit — autentifikatsiya uchun.
    
    Format: aida_{random_32_hex}
    Saqlash: SHA256 hash
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "User",
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
        self.last_used_at = timezone.now()
        self.total_requests += 1
        self.save(update_fields=["last_used_at", "total_requests"])
