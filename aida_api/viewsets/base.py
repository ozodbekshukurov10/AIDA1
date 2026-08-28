"""
AIDA Enterprise API — Base ViewSet
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from ..responses import APIResponse


class AIDABaseViewSet(viewsets.ViewSet):
    """
    Barcha AIDA viewsetlar uchun asos sinf.
    
    Standart CRUD amallar:
    - list: Ro'yxat olish (GET)
    - create: Yaratish (POST)
    - retrieve: Bitta element (GET /{id}/)
    - update: To'liq yangilash (PUT /{id}/)
    - partial_update: Qisman yangilash (PATCH /{id}/)
    - destroy: O'chirish (DELETE /{id}/)
    
    Har bir response standart envelope formatida:
    {
        "status": 200,
        "success": true,
        "message": "OK",
        "data": {...},
        "request_id": "req_abc123",
        "execution_time_ms": 45
    }
    """

    def list(self, request):
        """Ro'yxat olish."""
        try:
            queryset = self.get_queryset()
            queryset = self.apply_filters(request, queryset)
            queryset = self.apply_search(request, queryset)
            queryset = self.apply_sorting(request, queryset)

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(APIResponse.success(serializer.data))
        except Exception as e:
            return Response(
                APIResponse.server_error(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def create(self, request):
        """Yaratish."""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = self.perform_create(serializer)
            return Response(
                APIResponse.created(
                    serializer.data,
                    message="Muvaffaqiyatli yaratildi",
                ),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                APIResponse.server_error(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def retrieve(self, request, pk=None):
        """Bitta element olish."""
        try:
            instance = self.get_object(pk)
            serializer = self.get_serializer(instance)
            return Response(APIResponse.success(serializer.data))
        except Exception as e:
            return Response(
                APIResponse.not_found(message=str(e)),
                status=status.HTTP_404_NOT_FOUND,
            )

    def update(self, request, pk=None):
        """To'liq yangilash."""
        try:
            instance = self.get_object(pk)
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(APIResponse.success(serializer.data))
        except Exception as e:
            return Response(
                APIResponse.server_error(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def partial_update(self, request, pk=None):
        """Qisman yangilash."""
        try:
            instance = self.get_object(pk)
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(APIResponse.success(serializer.data))
        except Exception as e:
            return Response(
                APIResponse.server_error(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def destroy(self, request, pk=None):
        """O'chirish."""
        try:
            instance = self.get_object(pk)
            self.perform_destroy(instance)
            return Response(
                APIResponse.success(message="Muvaffaqiyatli o'chirildi"),
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return Response(
                APIResponse.server_error(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # ── Helper Methods ──────────────────────────────────────────────────────────

    def get_queryset(self):
        """Queryset olish (override qilish kerak)."""
        if hasattr(self, "queryset"):
            return self.queryset
        return []

    def get_serializer(self, *args, **kwargs):
        """Serializer olish."""
        if hasattr(self, "serializer_class"):
            kwargs.setdefault("context", {"request": self.request, "view": self})
            return self.serializer_class(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)

    def get_object(self, pk=None):
        """Bitta object olish."""
        queryset = self.get_queryset()
        if hasattr(queryset, "filter"):
            obj = queryset.filter(pk=pk).first()
        else:
            obj = None

        if obj is None:
            from ..exceptions import ResourceNotFoundError
            raise ResourceNotFoundError("Resurs", str(pk))

        return obj

    def paginate_queryset(self, queryset):
        """Sahifalash."""
        if hasattr(self, "paginator"):
            return self.paginator.paginate_queryset(queryset, self.request, view=self)
        return None

    def get_paginated_response(self, data):
        """Sahifalangan response."""
        if hasattr(self, "paginator"):
            return self.paginator.get_paginated_response(data)
        return Response(APIResponse.success(data))

    def apply_filters(self, request, queryset):
        """Filtrlarni qo'llash (override qilish mumkin)."""
        return queryset

    def apply_search(self, request, queryset):
        """Qidiruvni qo'llash (override qilish mumkin)."""
        search = request.query_params.get("search")
        if search and hasattr(queryset, "filter"):
            # Oddiy search — nom bo'yicha
            if hasattr(queryset.model, "name"):
                queryset = queryset.filter(name__icontains=search)
        return queryset

    def apply_sorting(self, request, queryset):
        """Saralashni qo'llash."""
        ordering = request.query_params.get("ordering", "-created_at")
        if ordering and hasattr(queryset, "order_by"):
            queryset = queryset.order_by(ordering)
        return queryset

    def perform_create(self, serializer):
        """Yaratish amali."""
        return serializer.save()

    def perform_update(self, serializer):
        """Yangilash amali."""
        return serializer.save()

    def perform_destroy(self, instance):
        """O'chirish amali."""
        instance.delete()
