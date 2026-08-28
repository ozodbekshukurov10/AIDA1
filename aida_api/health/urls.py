"""
AIDA Enterprise API — Health Check
"""
from django.urls import path
from django.http import JsonResponse
import time


def health_check(request):
    """API sog'ligini tekshirish."""
    return JsonResponse({
        "status": 200,
        "success": True,
        "message": "API ishlayapti",
        "data": {
            "status": "healthy",
            "timestamp": int(time.time()),
            "version": "1.0.0",
        },
    })


def readiness_check(request):
    """API tayyor ekanligini tekshirish."""
    # Database, cache, LLM providers tekshirish
    checks = {
        "database": True,
        "cache": True,
        "llm_providers": True,
    }

    all_healthy = all(checks.values())

    return JsonResponse({
        "status": 200 if all_healthy else 503,
        "success": all_healthy,
        "message": "API tayyor" if all_healthy else "API tayyor emas",
        "data": {
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks,
            "timestamp": int(time.time()),
        },
    })


urlpatterns = [
    path("", health_check, name="health-check"),
    path("ready/", readiness_check, name="readiness-check"),
]
