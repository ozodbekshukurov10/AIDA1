"""
AIDA Enterprise API — API Key Management ViewSet

API keylarni boshqarish uchun CRUD endpointlari.
"""
from __future__ import annotations
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..responses import APIResponse
from ..exceptions import ResourceNotFoundError
from ..serializers.auth import APIKeyCreateSerializer, APIKeySerializer


class APIKeyViewSet(viewsets.ViewSet):
    """
    API Key boshqarish.
    
    - GET    /api-keys/           — API keylar ro'yxati
    - POST   /api-keys/           — Yangi API key yaratish
    - GET    /api-keys/{id}/      — Bitta API key
    - DELETE /api-keys/{id}/      — API keyni o'chirish
    - POST   /api-keys/{id}/revoke/ — API keyni bekor qilish
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """API keylar ro'yxati."""
        from ..access_key import AccessKey
        keys = AccessKey.objects.filter(user=request.user)
        serializer = APIKeySerializer(keys, many=True)
        return Response(APIResponse.success(serializer.data))

    def create(self, request):
        """Yangi API key yaratish."""
        serializer = APIKeyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from ..access_key import AccessKey
        access_key, raw_key = AccessKey.create_key(
            user=request.user,
            name=serializer.validated_data["name"],
            scopes=serializer.validated_data.get("scopes", []),
            rate_limit=serializer.validated_data.get("rate_limit", 100),
            expires_at=serializer.validated_data.get("expires_at"),
        )

        return Response(
            APIResponse.created(
                data={
                    "key": raw_key,
                    "id": str(access_key.id),
                    "name": access_key.name,
                    "key_prefix": access_key.key_prefix,
                },
                message="API key yaratildi. Kalitni xavfsiz joyda saqlang — bu ko'rinmaydi!",
            ),
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        """Bitta API key."""
        from ..access_key import AccessKey
        try:
            key = AccessKey.objects.get(id=pk, user=request.user)
        except AccessKey.DoesNotExist:
            raise ResourceNotFoundError("API key", str(pk))

        serializer = APIKeySerializer(key)
        return Response(APIResponse.success(serializer.data))

    def destroy(self, request, pk=None):
        """API keyni o'chirish."""
        from ..access_key import AccessKey
        try:
            key = AccessKey.objects.get(id=pk, user=request.user)
        except AccessKey.DoesNotExist:
            raise ResourceNotFoundError("API key", str(pk))

        key.delete()
        return Response(
            APIResponse.success(message="API key o'chirildi.")
        )

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        """API keyni bekor qilish (o'chirmasdan faolsizlantirish)."""
        from ..access_key import AccessKey
        try:
            key = AccessKey.objects.get(id=pk, user=request.user)
        except AccessKey.DoesNotExist:
            raise ResourceNotFoundError("API key", str(pk))

        key.is_active = False
        key.save(update_fields=["is_active"])

        return Response(
            APIResponse.success(message="API key bekor qilindi.")
        )

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """API keyni faollashtirish."""
        from ..access_key import AccessKey
        try:
            key = AccessKey.objects.get(id=pk, user=request.user)
        except AccessKey.DoesNotExist:
            raise ResourceNotFoundError("API key", str(pk))

        key.is_active = True
        key.save(update_fields=["is_active"])

        return Response(
            APIResponse.success(message="API key faollashtirildi.")
        )
