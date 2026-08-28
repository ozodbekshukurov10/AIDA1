"""
AIDA Enterprise API — Auth URL Patterns
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..viewsets.auth import AuthViewSet
from ..viewsets.api_keys import APIKeyViewSet

router = DefaultRouter()
router.trailing_slash = False
router.register(r"auth", AuthViewSet, basename="auth")
router.register(r"api-keys", APIKeyViewSet, basename="api-keys")

urlpatterns = [
    path("", include(router.urls)),
]
