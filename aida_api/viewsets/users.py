"""
AIDA Enterprise API — Users ViewSet

Foydalanuvchilarni boshqarish uchun CRUD endpointlari.
"""
from __future__ import annotations
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from ..responses import APIResponse
from ..exceptions import ResourceNotFoundError
from ..serializers.auth import UserSerializer


class UserViewSet(viewsets.ViewSet):
    """
    Foydalanuvchi boshqarish.

    - GET    /users/              — Foydalanuvchilar ro'yxati (admin)
    - POST   /users/              — Yangi foydalanuvchi yaratish (admin)
    - GET    /users/{id}/         — Foydalanuvchi profili
    - PUT    /users/{id}/         — Profilni to'liq yangilash (egasi)
    - PATCH  /users/{id}/         — Profilni qisman yangilash (egasi)
    - DELETE /users/{id}/         — Hisobni o'chirish (egasi)
    - GET    /users/{id}/profile/ — Kengaytirilgan profil
    - GET    /users/{id}/sessions/ — Foydalanuvchi sessiyalari
    - GET    /users/{id}/api-keys/ — Foydalanuvchi API kalitlari
    - GET    /users/{id}/activity/ — Faoliyat tarixi
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from ..models import User
        return User.objects.all()

    def get_object(self, pk):
        obj = self.get_queryset().filter(pk=pk).first()
        if obj is None:
            raise ResourceNotFoundError("Foydalanuvchi", str(pk))
        return obj

    def _check_owner_or_admin(self, request, user):
        """Egasi yoki admin ekanligini tekshirish."""
        return request.user.is_staff or request.user.id == user.id

    def list(self, request):
        """Foydalanuvchilar ro'yxati (faqat admin)."""
        if not request.user.is_staff:
            return Response(
                APIResponse.forbidden(message="Faqat admin foydalanuvchilar ro'yxatini ko'rishi mumkin."),
                status=status.HTTP_403_FORBIDDEN,
            )

        queryset = self.get_queryset()

        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(email__icontains=search)

        is_active = request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        is_premium = request.query_params.get("is_premium")
        if is_premium is not None:
            queryset = queryset.filter(is_premium=is_premium.lower() == "true")

        ordering = request.query_params.get("ordering", "-created_at")
        queryset = queryset.order_by(ordering)

        serializer = UserSerializer(queryset, many=True)
        return Response(APIResponse.success(serializer.data))

    def create(self, request):
        """Yangi foydalanuvchi yaratish (faqat admin)."""
        if not request.user.is_staff:
            return Response(
                APIResponse.forbidden(message="Faqat admin foydalanuvchi yarata oladi."),
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from ..models import User
        user = User.objects.create_user(
            email=serializer.validated_data["email"],
            password=request.data.get("password", ""),
            first_name=serializer.validated_data.get("first_name", ""),
            last_name=serializer.validated_data.get("last_name", ""),
        )

        return Response(
            APIResponse.created(
                data=UserSerializer(user).data,
                message="Foydalanuvchi muvaffaqiyatli yaratildi.",
            ),
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        """Foydalanuvchi profilini olish."""
        user = self.get_object(pk)

        if not self._check_owner_or_admin(request, user):
            return Response(
                APIResponse.forbidden(message="Siz boshqa foydalanuvchi profilini ko'ra olmaysiz."),
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(APIResponse.success(UserSerializer(user).data))

    def update(self, request, pk=None):
        """Profilni to'liq yangilash (faqat egasi)."""
        user = self.get_object(pk)

        if not self._check_owner_or_admin(request, user):
            return Response(
                APIResponse.forbidden(message="Faqat egasi profilni yangilay oladi."),
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UserSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(APIResponse.success(serializer.data))

    def partial_update(self, request, pk=None):
        """Profilni qisman yangilash (faqat egasi)."""
        user = self.get_object(pk)

        if not self._check_owner_or_admin(request, user):
            return Response(
                APIResponse.forbidden(message="Faqat egasi profilni yangilay oladi."),
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(APIResponse.success(serializer.data))

    def destroy(self, request, pk=None):
        """Hisobni o'chirish (faqat egasi)."""
        user = self.get_object(pk)

        if not self._check_owner_or_admin(request, user):
            return Response(
                APIResponse.forbidden(message="Faqat egasi hisobni o'chira oladi."),
                status=status.HTTP_403_FORBIDDEN,
            )

        user.delete()
        return Response(
            APIResponse.success(message="Hisob muvaffaqiyatli o'chirildi."),
        )

    @action(detail=True, methods=["get"])
    def profile(self, request, pk=None):
        """Kengaytirilgan foydalanuvchi profili."""
        user = self.get_object(pk)

        if not self._check_owner_or_admin(request, user):
            return Response(
                APIResponse.forbidden(message="Siz boshqa foydalanuvchi profilini ko'ra olmaysiz."),
                status=status.HTTP_403_FORBIDDEN,
            )

        from ..access_key import AccessKey
        api_keys_count = AccessKey.objects.filter(user=user).count()
        active_api_keys_count = AccessKey.objects.filter(user=user, is_active=True).count()

        profile_data = {
            "user": UserSerializer(user).data,
            "stats": {
                "api_keys_total": api_keys_count,
                "api_keys_active": active_api_keys_count,
            },
            "access": {
                "is_premium": user.is_premium,
                "is_enterprise": user.is_enterprise,
                "has_premium_access": user.has_premium_access(),
                "has_enterprise_access": user.has_enterprise_access(),
            },
        }

        return Response(APIResponse.success(profile_data))

    @action(detail=True, methods=["get"])
    def sessions(self, request, pk=None):
        """Foydalanuvchi sessiyalari."""
        user = self.get_object(pk)

        if not self._check_owner_or_admin(request, user):
            return Response(
                APIResponse.forbidden(message="Siz boshqa foydalanuvchi sessiyalarini ko'ra olmaysiz."),
                status=status.HTTP_403_FORBIDDEN,
            )

        sessions = []
        if hasattr(user, "session_set"):
            sessions = list(user.session_set.values("id", "ip_address", "user_agent", "created_at", "last_activity"))

        return Response(
            APIResponse.success(
                data=sessions,
                metadata={"total": len(sessions)},
            )
        )

    @action(detail=True, methods=["get"], url_path="api-keys")
    def api_keys(self, request, pk=None):
        """Foydalanuvchi API kalitlari."""
        user = self.get_object(pk)

        if not self._check_owner_or_admin(request, user):
            return Response(
                APIResponse.forbidden(message="Siz boshqa foydalanuvchi API kalitlarini ko'ra olmaysiz."),
                status=status.HTTP_403_FORBIDDEN,
            )

        from ..access_key import AccessKey
        from ..serializers.auth import APIKeySerializer

        keys = AccessKey.objects.filter(user=user).order_by("-created_at")
        serializer = APIKeySerializer(keys, many=True)

        return Response(
            APIResponse.success(
                data=serializer.data,
                metadata={"total": keys.count()},
            )
        )

    @action(detail=True, methods=["get"])
    def activity(self, request, pk=None):
        """Foydalanuvchi faoliyati tarixi."""
        user = self.get_object(pk)

        if not self._check_owner_or_admin(request, user):
            return Response(
                APIResponse.forbidden(message="Siz boshqa foydalanuvchi faoliyatini ko'ra olmaysiz."),
                status=status.HTTP_403_FORBIDDEN,
            )

        activity_log = []
        if hasattr(user, "activitylog_set"):
            activity_log = list(
                user.activitylog_set.order_by("-created_at").values(
                    "id", "action", "resource_type", "resource_id", "ip_address", "created_at"
                )[:50]
            )

        return Response(
            APIResponse.success(
                data=activity_log,
                metadata={"total": len(activity_log)},
            )
        )
