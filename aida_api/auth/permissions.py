"""
AIDA Enterprise API — Permission Classes
"""
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Faqat resurs egasi uchun ruxsat."""

    def has_object_permission(self, request, view, obj):
        # Admin har doim ruxsatga ega
        if request.user and request.user.is_staff:
            return True

        # Object da owner/created_by/user field bor tekshirish
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        if hasattr(obj, "created_by"):
            return obj.created_by == request.user
        if hasattr(obj, "user"):
            return obj.user == request.user

        return False


class IsAdminUser(permissions.BasePermission):
    """Faqat admin foydalanuvchilar uchun ruxsat."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Autentifikatsiya talab qilinadi yoki faqat o'qish.
    
    - GET, HEAD, OPTIONS — hamma uchun ochiq
    - POST, PUT, PATCH, DELETE — faqat autentifikatsiya qilingan
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class IsPremiumUser(permissions.BasePermission):
    """Premium foydalanuvchilar uchun ruxsat."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, "is_premium", False) or request.user.is_staff


class IsEnterpriseUser(permissions.BasePermission):
    """Enterprise foydalanuvchilar uchun ruxsat."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, "is_enterprise", False) or request.user.is_staff


class IsAgentUser(permissions.BasePermission):
    """AI agentlar uchun ruxsat (API key orqali)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # API key bilan kirgan foydalanuvchilar agent hisoblanadi
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        api_key = request.META.get("HTTP_X_API_KEY", "")
        return bool(api_key or (auth.startswith("Bearer ") and auth[7:].startswith("aida_")))
