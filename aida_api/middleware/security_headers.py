"""
Security Headers Middleware — Xavfsizlik headerlarini qo'shish.
"""


class SecurityHeadersMiddleware:
    """
    API uchun xavfsizlik headerlarini qo'shish.
    
    Qo'shadi:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: camera=(), microphone=(), geolocation=()
    - Cache-Control: no-store, no-cache, must-revalidate
    - Pragma: no-cache
    """

    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Barcha xavfsizlik headerlarini qo'shish
        for header, value in self.SECURITY_HEADERS.items():
            response[header] = value

        return response
