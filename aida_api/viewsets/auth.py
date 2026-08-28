"""
AIDA Enterprise API — Auth ViewSet

Register, Login, Logout, Token Refresh, Password Change, MFA, OAuth2
"""
from __future__ import annotations
import json
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from ..responses import APIResponse
from ..exceptions import ValidationError, AuthenticationError, InvalidTokenError
from ..auth.authentication import (
    generate_jwt_token, decode_jwt_token, hash_api_key,
)
from ..auth.token import TokenManager
from ..auth.mfa import generate_secret, generate_totp, verify_totp, get_provisioning_uri
from ..serializers.auth import (
    RegisterSerializer, LoginSerializer, TokenRefreshSerializer,
    TokenVerifySerializer, PasswordChangeSerializer, PasswordResetSerializer,
    PasswordResetConfirmSerializer, UserSerializer,
    APIKeyCreateSerializer, APIKeySerializer,
    MFAEnableSerializer, MFAVerifySerializer, MFADisableSerializer,
    OAuth2CallbackSerializer,
)


class AuthViewSet(viewsets.ViewSet):
    """
    Autentifikatsiya endpointlari.
    
    - POST /auth/register/ — Ro'yxatdan o'tish
    - POST /auth/login/ — Login
    - POST /auth/logout/ — Logout
    - POST /auth/token/refresh/ — Token yangilash
    - POST /auth/token/verify/ — Token tekshirish
    - GET  /auth/me/ — Joriy foydalanuvchi
    - POST /auth/password/change/ — Parol o'zgartirish
    - POST /auth/password/reset/ — Parol tiklash so'rovi
    - POST /auth/password/reset/confirm/ — Parol tiklash tasdig'i
    - POST /auth/mfa/enable/ — MFA yoqish
    - POST /auth/mfa/disable/ — MFA o'chirish
    - POST /auth/mfa/verify/ — MFA tekshirish
    - GET  /auth/oauth2/{provider}/ — OAuth2 redirect
    - GET  /auth/oauth2/{provider}/callback/ — OAuth2 callback
    """

    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"])
    def register(self, request):
        """Ro'yxatdan o'tish."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from ..models import User
        user = User.objects.create_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            first_name=serializer.validated_data.get("first_name", ""),
            last_name=serializer.validated_data.get("last_name", ""),
        )

        # Token yaratish
        tokens = TokenManager.create_tokens(user.id)

        return Response(
            APIResponse.created(
                data={
                    "user": UserSerializer(user).data,
                    "tokens": tokens,
                },
                message="Muvaffaqiyatli ro'yxatdan o'tdingiz.",
            ),
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"])
    def login(self, request):
        """Login."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from ..models import User
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationError("Email yoki parol noto'g'ri.")

        if not user.check_password(password):
            raise AuthenticationError("Email yoki parol noto'g'ri.")

        if not user.is_active:
            raise AuthenticationError("Hisobingiz faol emas.")

        # MFA tekshirish
        if user.mfa_enabled:
            mfa_code = serializer.validated_data.get("mfa_code", "")
            if not mfa_code:
                return Response(
                    APIResponse.success(
                        data={"mfa_required": True},
                        message="MFA kodi kiriting.",
                    )
                )
            if not verify_totp(user.mfa_secret, mfa_code):
                raise AuthenticationError("MFA kodi noto'g'ri.")

        # Token yaratish
        tokens = TokenManager.create_tokens(user.id)

        # Oxirgi kirish vaqtini yangilash
        from django.utils import timezone
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        return Response(
            APIResponse.success(
                data={
                    "user": UserSerializer(user).data,
                    "tokens": tokens,
                },
                message="Muvaffaqiyatli kirdingiz.",
            )
        )

    @action(detail=False, methods=["post"])
    def logout(self, request):
        """Logout."""
        # Hozircha oddiy — client tokenni o'chiradi
        return Response(
            APIResponse.success(message="Muvaffaqiyatli chiqdingiz.")
        )

    @action(detail=False, methods=["post"], url_path="token/refresh")
    def token_refresh(self, request):
        """Token yangilash."""
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh"]
        new_access_token = TokenManager.refresh_access_token(refresh_token)

        if not new_access_token:
            raise InvalidTokenError("Refresh token noto'g'ri yoki muddati tugagan.")

        return Response(
            APIResponse.success(
                data={"access": new_access_token},
                message="Token yangilandi.",
            )
        )

    @action(detail=False, methods=["post"], url_path="token/verify")
    def token_verify(self, request):
        """Token tekshirish."""
        serializer = TokenVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        payload = TokenManager.verify_token(token)

        if not payload:
            raise InvalidTokenError("Token noto'g'ri yoki muddati tugagan.")

        return Response(
            APIResponse.success(
                data={"valid": True, "payload": payload},
                message="Token yaroqli.",
            )
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Joriy foydalanuvchi ma'lumotlari."""
        return Response(
            APIResponse.success(
                data=UserSerializer(request.user).data,
            )
        )

    @action(detail=False, methods=["post"], url_path="password/change",
            permission_classes=[IsAuthenticated])
    def password_change(self, request):
        """Parol o'zgartirish."""
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            raise ValidationError("Joriy parol noto'g'ri.")

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        return Response(
            APIResponse.success(message="Parol muvaffaqiyatli o'zgartirildi.")
        )

    @action(detail=False, methods=["post"], url_path="password/reset")
    def password_reset(self, request):
        """Parol tiklash so'rovi."""
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Email yuborish (hozircha faqat log)
        from ..models import User
        try:
            user = User.objects.get(email=serializer.validated_data["email"])
            import secrets
            user.password_reset_token = secrets.token_hex(32)
            from django.utils import timezone
            import datetime
            user.password_reset_expires = timezone.now() + datetime.timedelta(hours=24)
            user.save(update_fields=["password_reset_token", "password_reset_expires"])
        except User.DoesNotExist:
            pass

        return Response(
            APIResponse.success(message="Parol tiklash havolasi emailga yuborildi.")
        )

    @action(detail=False, methods=["post"], url_path="password/reset/confirm")
    def password_reset_confirm(self, request):
        """Parol tiklash tasdig'i."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from ..models import User
        from django.utils import timezone

        try:
            user = User.objects.get(
                password_reset_token=serializer.validated_data["token"],
                password_reset_expires__gt=timezone.now(),
            )
        except User.DoesNotExist:
            raise ValidationError("Token noto'g'ri yoki muddati tugagan.")

        user.set_password(serializer.validated_data["new_password"])
        user.password_reset_token = ""
        user.password_reset_expires = None
        user.save(update_fields=["password", "password_reset_token", "password_reset_expires"])

        return Response(
            APIResponse.success(message="Parol muvaffaqiyatli tiklandi.")
        )

    # ── MFA ────────────────────────────────────────────────────────────────────

    @action(detail=False, methods=["post"], url_path="mfa/enable",
            permission_classes=[IsAuthenticated])
    def mfa_enable(self, request):
        """MFA yoqish."""
        serializer = MFAEnableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if user.mfa_enabled:
            return Response(
                APIResponse.bad_request(message="MFA allaqachon yoqilgan.")
            )

        # Secret yaratish
        secret = generate_secret()

        # Tasdiqlash kodini tekshirish
        if not verify_totp(secret, serializer.validated_data["code"]):
            return Response(
                APIResponse.bad_request(message="MFA kodi noto'g'ri.")
            )

        # MFA ni yoqish
        user.mfa_secret = secret
        user.mfa_enabled = True
        user.save(update_fields=["mfa_secret", "mfa_enabled"])

        # Provisioning URI
        uri = get_provisioning_uri(secret, user.email)

        return Response(
            APIResponse.success(
                data={
                    "secret": secret,
                    "provisioning_uri": uri,
                },
                message="MFA muvaffaqiyatli yoqildi.",
            )
        )

    @action(detail=False, methods=["post"], url_path="mfa/disable",
            permission_classes=[IsAuthenticated])
    def mfa_disable(self, request):
        """MFA o'chirish."""
        serializer = MFADisableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.mfa_enabled:
            return Response(
                APIResponse.bad_request(message="MFA yoqilmagan.")
            )

        # Parolni tekshirish
        if not user.check_password(serializer.validated_data["password"]):
            raise ValidationError("Parol noto'g'ri.")

        # MFA kodini tekshirish
        if not verify_totp(user.mfa_secret, serializer.validated_data["code"]):
            return Response(
                APIResponse.bad_request(message="MFA kodi noto'g'ri.")
            )

        # MFA ni o'chirish
        user.mfa_secret = ""
        user.mfa_enabled = False
        user.save(update_fields=["mfa_secret", "mfa_enabled"])

        return Response(
            APIResponse.success(message="MFA muvaffaqiyatli o'chirildi.")
        )

    @action(detail=False, methods=["post"], url_path="mfa/verify",
            permission_classes=[IsAuthenticated])
    def mfa_verify(self, request):
        """MFA kodini tekshirish."""
        serializer = MFAVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.mfa_enabled:
            return Response(
                APIResponse.bad_request(message="MFA yoqilmagan.")
            )

        is_valid = verify_totp(user.mfa_secret, serializer.validated_data["code"])

        return Response(
            APIResponse.success(
                data={"valid": is_valid},
                message="MFA kodi to'g'ri." if is_valid else "MFA kodi noto'g'ri.",
            )
        )

    # ── OAuth2 ─────────────────────────────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path=r"oauth2/(?P<provider>[^/.]+)")
    def oauth2_redirect(self, request, provider=None):
        """OAuth2 redirect."""
        from .oauth2 import get_oauth2_provider
        import secrets

        oauth2 = get_oauth2_provider(provider)
        if not oauth2:
            return Response(
                APIResponse.bad_request(message=f"Noto'g'ri OAuth2 provider: {provider}")
            )

        state = secrets.token_urlsafe(32)
        redirect_url = oauth2.get_redirect_url(state)

        return Response(
            APIResponse.success(
                data={"redirect_url": redirect_url, "state": state},
            )
        )

    @action(detail=False, methods=["get"], url_path=r"oauth2/(?P<provider>[^/.]+)/callback")
    def oauth2_callback(self, request, provider=None):
        """OAuth2 callback."""
        from .oauth2 import get_oauth2_provider

        oauth2 = get_oauth2_provider(provider)
        if not oauth2:
            return Response(
                APIResponse.bad_request(message=f"Noto'g'ri OAuth2 provider: {provider}")
            )

        code = request.query_params.get("code")
        if not code:
            return Response(
                APIResponse.bad_request(message="Code parametri topilmadi.")
            )

        # Token olish
        token_data = oauth2.exchange_code(code)
        if not token_data or "access_token" not in token_data:
            return Response(
                APIResponse.bad_request(message="OAuth2 token olishda xatolik.")
            )

        # Foydalanuvchi ma'lumotlarini olish
        user_info = oauth2.get_user_info(token_data["access_token"])
        if not user_info or not user_info.get("email"):
            return Response(
                APIResponse.bad_request(message="Foydalanuvchi ma'lumotlarini olishda xatolik.")
            )

        # Foydalanuvchini topish yoki yaratish
        from ..models import User
        user, created = User.objects.get_or_create(
            email=user_info["email"],
            defaults={
                "first_name": user_info.get("name", "").split()[0] if user_info.get("name") else "",
                "last_name": " ".join(user_info.get("name", "").split()[1:]) if user_info.get("name") else "",
            },
        )

        # Token yaratish
        tokens = TokenManager.create_tokens(user.id)

        return Response(
            APIResponse.success(
                data={
                    "user": UserSerializer(user).data,
                    "tokens": tokens,
                    "created": created,
                },
                message="OAuth2 orqali muvaffaqiyatli kirdingiz." if not created else "Hisob yaratildi va kirdingiz.",
            )
        )
