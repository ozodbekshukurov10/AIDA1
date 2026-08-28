"""
AIDA Enterprise API — Public API (Autentifikatsiya talab qilinmaydi)
"""
from django.urls import path
from django.http import JsonResponse


def api_info(request):
    """API ma'lumotlari."""
    return JsonResponse({
        "status": 200,
        "success": True,
        "message": "AIDA Public API",
        "data": {
            "name": "AIDA Enterprise API",
            "version": "1.0.0",
            "docs": "/api/v1/docs/",
            "health": "/api/v1/health/",
        },
    })


urlpatterns = [
    path("", api_info, name="public-api-info"),
]
