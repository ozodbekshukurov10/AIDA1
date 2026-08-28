"""
AIDA Enterprise API — Admin API (Faqat admin foydalanuvchilar)
"""
from django.urls import path
from django.http import JsonResponse
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import permission_classes


@permission_classes([IsAdminUser])
def admin_info(request):
    """Admin API ma'lumotlari."""
    return JsonResponse({
        "status": 200,
        "success": True,
        "message": "AIDA Admin API — Faqat admin foydalanuvchilar",
        "data": {
            "name": "AIDA Admin API",
            "version": "1.0.0",
        },
    })


urlpatterns = [
    path("", admin_info, name="admin-api-info"),
]
