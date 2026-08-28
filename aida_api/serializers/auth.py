"""
AIDA Enterprise API — Auth Serializers
"""
from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    """Ro'yxatdan o'tish uchun serializer."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(min_length=8, max_length=128, write_only=True)
    password_confirm = serializers.CharField(min_length=8, max_length=128, write_only=True)
    first_name = serializers.CharField(max_length=150, required=False, default="")
    last_name = serializers.CharField(max_length=150, required=False, default="")

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Parollar mos emas.")
        return attrs

    def validate_email(self, value):
        from ..models import User
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email allaqachon ro'yxatdan o'tgan.")
        return value


class LoginSerializer(serializers.Serializer):
    """Login uchun serializer."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)
    mfa_code = serializers.CharField(max_length=6, required=False, default="")


class TokenRefreshSerializer(serializers.Serializer):
    """Token refresh uchun serializer."""
    refresh = serializers.CharField(required=True)


class TokenVerifySerializer(serializers.Serializer):
    """Token tekshirish uchun serializer."""
    token = serializers.CharField(required=True)


class PasswordChangeSerializer(serializers.Serializer):
    """Parol o'zgartirish uchun serializer."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(min_length=8, max_length=128, required=True)
    new_password_confirm = serializers.CharField(min_length=8, max_length=128, required=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError("Yangi parollar mos emas.")
        return attrs


class PasswordResetSerializer(serializers.Serializer):
    """Parol tiklash so'rovi uchun serializer."""
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Parol tiklash tasdig'i uchun serializer."""
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(min_length=8, max_length=128, required=True)
    new_password_confirm = serializers.CharField(min_length=8, max_length=128, required=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError("Yangi parollar mos emas.")
        return attrs


class UserSerializer(serializers.Serializer):
    """Foydalanuvchi ma'lumotlari uchun serializer."""
    id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    avatar = serializers.ImageField(required=False)
    is_premium = serializers.BooleanField(read_only=True)
    is_enterprise = serializers.BooleanField(read_only=True)
    mfa_enabled = serializers.BooleanField(read_only=True)
    email_verified = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)

    class Meta:
        fields = [
            "id", "email", "first_name", "last_name", "avatar",
            "is_premium", "is_enterprise", "mfa_enabled",
            "email_verified", "created_at", "last_login",
        ]


class APIKeyCreateSerializer(serializers.Serializer):
    """API key yaratish uchun serializer."""
    name = serializers.CharField(max_length=100, required=True)
    scopes = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=[],
    )
    rate_limit = serializers.IntegerField(min_value=1, max_value=10000, default=100)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)


class APIKeySerializer(serializers.Serializer):
    """API key ma'lumotlari uchun serializer."""
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    key_prefix = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    scopes = serializers.ListField(child=serializers.CharField(), read_only=True)
    rate_limit = serializers.IntegerField(read_only=True)
    last_used_at = serializers.DateTimeField(read_only=True)
    total_requests = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    expires_at = serializers.DateTimeField(read_only=True)


class MFAEnableSerializer(serializers.Serializer):
    """MFA yoqish uchun serializer."""
    code = serializers.CharField(max_length=6, required=True)


class MFAVerifySerializer(serializers.Serializer):
    """MFA tekshirish uchun serializer."""
    code = serializers.CharField(max_length=6, required=True)


class MFADisableSerializer(serializers.Serializer):
    """MFA o'chirish uchun serializer."""
    code = serializers.CharField(max_length=6, required=True)
    password = serializers.CharField(required=True)


class OAuth2CallbackSerializer(serializers.Serializer):
    """OAuth2 callback uchun serializer."""
    code = serializers.CharField(required=True)
    state = serializers.CharField(required=False, default="")
