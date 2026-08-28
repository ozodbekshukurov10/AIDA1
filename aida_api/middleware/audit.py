"""
Audit Middleware — API so'rovlari uchun audit logging.
"""
import time
import json
import logging

logger = logging.getLogger("aida_api.audit")


class AuditMiddleware:
    """
    API so'rovlari uchun audit logging.
    
    Har bir API requestini logga yozadi:
    - IP manzil
    - HTTP method
    - URL path
    - Status code
    - Vaqt
    - User agent
    - Request ID
    """

    # Logga yozilmasin kerak bo'lgan path'lar
    EXCLUDED_PATHS = {
        "/api/v1/health/",
        "/api/v1/status/",
        "/favicon.ico",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Faqat API endpointlari uchun audit
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        # Chiqarilishi kerak bo'lgan path'lar
        if request.path in self.EXCLUDED_PATHS:
            return self.get_response(request)

        start_time = time.monotonic()
        client_ip = self._get_client_ip(request)
        request_id = getattr(request, "request_id", "")

        # Request ni qayta ishlash
        response = self.get_response(request)

        # Vaqtni hisoblash
        execution_time_ms = int((time.monotonic() - start_time) * 1000)

        # Audit log yozish
        audit_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "ip": client_ip,
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:200],
            "execution_time_ms": execution_time_ms,
            "user_id": getattr(request.user, "id", None) if hasattr(request, "user") else None,
        }

        # Status code ga qarab log level
        if response.status_code >= 500:
            logger.error(f"AUDIT: {json.dumps(audit_data)}")
        elif response.status_code >= 400:
            logger.warning(f"AUDIT: {json.dumps(audit_data)}")
        else:
            logger.info(f"AUDIT: {json.dumps(audit_data)}")

        return response

    def _get_client_ip(self, request) -> str:
        """Client IP manzilini olish."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "0.0.0.0")
