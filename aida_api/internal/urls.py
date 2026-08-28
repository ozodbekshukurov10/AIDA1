"""
AIDA Enterprise API — Internal API (Service-to-Service)
"""
from django.urls import path
from django.http import JsonResponse


def internal_info(request):
    """Internal API ma'lumotlari."""
    return JsonResponse({
        "status": 200,
        "success": True,
        "message": "AIDA Internal API — Faqat service-to-service",
        "data": {
            "name": "AIDA Internal API",
            "version": "1.0.0",
        },
    })


urlpatterns = [
    path("", internal_info, name="internal-api-info"),
]
