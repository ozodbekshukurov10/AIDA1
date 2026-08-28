"""
AIDA Enterprise API — Rate Limiting / Throttling
"""
from rest_framework.throttling import SimpleRateThrottle, AnonRateThrottle


class AnonymousThrottle(AnonRateThrottle):
    """Anonim foydalanuvchilar uchun cheklov."""
    scope = "anonymous"
    rate = "30/min"


class UserThrottle(SimpleRateThrottle):
    """Oddiy foydalanuvchilar uchun cheklov."""
    scope = "user"
    rate = "100/min"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return f"throttle_user_{request.user.id}"
        return None


class PremiumThrottle(SimpleRateThrottle):
    """Premium foydalanuvchilar uchun cheklov."""
    scope = "premium"
    rate = "500/min"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            if getattr(request.user, "is_premium", False):
                return f"throttle_premium_{request.user.id}"
        return None


class EnterpriseThrottle(SimpleRateThrottle):
    """Enterprise foydalanuvchilar uchun cheklov."""
    scope = "enterprise"
    rate = "2000/min"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            if getattr(request.user, "is_enterprise", False):
                return f"throttle_enterprise_{request.user.id}"
        return None


class AgentThrottle(SimpleRateThrottle):
    """AI agentlar uchun cheklov."""
    scope = "agent"
    rate = "100/min"

    def get_cache_key(self, request, view):
        # API key bilan kirgan foydalanuvchilar
        api_key = request.META.get("HTTP_X_API_KEY", "")
        if api_key and api_key.startswith("aida_"):
            return f"throttle_agent_{api_key[:20]}"
        return None
