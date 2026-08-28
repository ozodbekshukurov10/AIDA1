"""
AIDA Enterprise API — Initial Migration

User model va AccessKey model yaratish.
"""
from django.db import migrations, models
import django.contrib.auth.models
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        # ── User Model ─────────────────────────────────────────────────────
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        max_length=254, unique=True, verbose_name="Email"
                    ),
                ),
                (
                    "first_name",
                    models.CharField(blank=True, max_length=150, verbose_name="Ism"),
                ),
                (
                    "last_name",
                    models.CharField(blank=True, max_length=150, verbose_name="Familiya"),
                ),
                (
                    "avatar",
                    models.ImageField(blank=True, null=True, upload_to="avatars/"),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Faol"),
                ),
                (
                    "is_staff",
                    models.BooleanField(default=False, verbose_name="Admin"),
                ),
                (
                    "is_premium",
                    models.BooleanField(default=False, verbose_name="Premium"),
                ),
                (
                    "is_enterprise",
                    models.BooleanField(default=False, verbose_name="Enterprise"),
                ),
                (
                    "mfa_enabled",
                    models.BooleanField(default=False, verbose_name="MFA yoqilgan"),
                ),
                (
                    "mfa_secret",
                    models.CharField(blank=True, max_length=32, verbose_name="MFA secret"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Yangilangan"),
                ),
                (
                    "email_verified",
                    models.BooleanField(default=False, verbose_name="Email tasdiqlangan"),
                ),
                (
                    "email_verification_token",
                    models.CharField(blank=True, max_length=64),
                ),
                (
                    "password_reset_token",
                    models.CharField(blank=True, max_length=64),
                ),
                (
                    "password_reset_expires",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to.",
                        related_name="aida_users",
                        related_query_name="aida_user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="aida_users",
                        related_query_name="aida_user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "Foydalanuvchi",
                "verbose_name_plural": "Foydalanuvchilar",
                "ordering": ["-created_at"],
                "db_table": "aida_users",
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        # ── AccessKey Model ────────────────────────────────────────────────
        migrations.CreateModel(
            name="AccessKey",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=100, verbose_name="Kalit nomi"),
                ),
                (
                    "key_hash",
                    models.CharField(max_length=64, unique=True, verbose_name="Kalit hash"),
                ),
                (
                    "key_prefix",
                    models.CharField(max_length=12, verbose_name="Kalit prefiksi"),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Faol"),
                ),
                (
                    "scopes",
                    models.JSONField(default=list, verbose_name="Ruxsatlar"),
                ),
                (
                    "rate_limit",
                    models.IntegerField(default=100, verbose_name="So'rv chegarasi"),
                ),
                (
                    "last_used_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Oxirgi ishlatilgan"
                    ),
                ),
                (
                    "total_requests",
                    models.IntegerField(default=0, verbose_name="Jami so'rvlar"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan"),
                ),
                (
                    "expires_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Muddati tugaydi"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="api_keys",
                        to="aida_api.user",
                        verbose_name="Foydalanuvchi",
                    ),
                ),
            ],
            options={
                "verbose_name": "API Kalit",
                "verbose_name_plural": "API Kalitlar",
                "ordering": ["-created_at"],
                "db_table": "aida_access_keys",
            },
        ),
    ]
