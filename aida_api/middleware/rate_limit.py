"""
Rate Limiting Middleware — So'rvlar sonini cheklash.
"""
import time
from collections import defaultdict
from django.http import JsonResponse


class RateLimitMiddleware:
    """
    So'rvlar sonini cheklash (in-memory).
    
    Har bir IP uchun vaqt oralig'ida so'rvlar sonini cheklash.
    
    Headerlar:
    - X-RateLimit-Limit: 100
    - X-RateLimit-Remaining: 95
    - X-RateLimit-Reset: 1625097600
    """

    # Default cheklovlar (soniya ichida)
    DEFAULT_LIMITS = {
        "anonymous": 30,    # 1 daqiqada 30 ta
        "authenticated": 100,  # 1 daqiqada 100 ta
        "premium": 500,     # 1 daqiqada 500 ta
        "enterprise": 2000, # 1 daqiqada 2000 ta
    }

    WINDOW_SECONDS = 60  # Vaqt oraligi (soniya)

    def __init__(self, get_response):
        self.get_response = get_response
        self._requests = defaultdict(list)  # IP -> [timestamp, ...]

    def __call__(self, request):
        # Rate limit tekshirish (faqat API endpointlari uchun)
        if request.path.startswith("/api/"):
            client_ip = self._get_client_ip(request)
            tier = self._get_tier(request)

            # Record request timestamp
            self._requests[client_ip].append(time.time())

            if self._is_rate_limited(client_ip, tier):
                retry_after = self.WINDOW_SECONDS
                response = JsonResponse(
                    {
                        "status": 429,
                        "success": False,
                        "message": f"Juda ko'p so'rov. {retry_after} soniyadan keyin qayta urinib ko'ring.",
                        "error": {
                            "code": "RATE_LIMITED",
                            "description": "Juda ko'p so'rov",
                            "reason": "Rate limit oshib ketdi",
                            "recovery_suggestion": f"{retry_after} soniya kuting yoki premium plana o'ting.",
                        },
                    },
                    status=429,
                )
                response["Retry-After"] = str(retry_after)
                response["X-RateLimit-Limit"] = str(self.DEFAULT_LIMITS[tier])
                response["X-RateLimit-Remaining"] = "0"
                response["X-RateLimit-Reset"] = str(int(time.time()) + retry_after)
                return response

            # Rate limit headerlarini qo'shish
            limit = self.DEFAULT_LIMITS[tier]
            remaining = self._get_remaining(client_ip, tier)
            reset_time = int(time.time()) + self.WINDOW_SECONDS

            response = self.get_response(request)

            response["X-RateLimit-Limit"] = str(limit)
            response["X-RateLimit-Remaining"] = str(max(0, remaining))
            response["X-RateLimit-Reset"] = str(reset_time)

            return response

        return self.get_response(request)

    def _get_client_ip(self, request) -> str:
        """Client IP manzilini olish."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "0.0.0.0")

    def _get_tier(self, request) -> str:
        """Foydalanuvchi darajasini aniqlash."""
        if hasattr(request, "user") and request.user and request.user.is_authenticated:
            if hasattr(request.user, "is_premium") and request.user.is_premium:
                return "premium"
            if hasattr(request.user, "is_enterprise") and request.user.is_enterprise:
                return "enterprise"
            return "authenticated"
        return "anonymous"

    def _is_rate_limited(self, client_ip: str, tier: str) -> bool:
        """Rate limit oshib ketganini tekshirish."""
        now = time.time()
        window_start = now - self.WINDOW_SECONDS

        # Eski so'rovlarni tozalash
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip] if ts > window_start
        ]

        # Cheklovni tekshirish
        limit = self.DEFAULT_LIMITS.get(tier, 30)
        return len(self._requests[client_ip]) >= limit

    def _get_remaining(self, client_ip: str, tier: str) -> int:
        """Qolgan so'rvlar sonini hisoblash."""
        now = time.time()
        window_start = now - self.WINDOW_SECONDS

        active_requests = [
            ts for ts in self._requests[client_ip] if ts > window_start
        ]

        limit = self.DEFAULT_LIMITS.get(tier, 30)
        return limit - len(active_requests)
