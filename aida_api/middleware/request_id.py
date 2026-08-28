"""
Request ID Middleware — Har bir requestga unikal ID qo'shish.
"""
import uuid
import threading

_request_id_local = threading.local()


def get_request_id() -> str:
    """Joriy request ID ni olish."""
    return getattr(_request_id_local, "request_id", "")


def set_request_id(request_id: str):
    """Request ID ni o'rnatish."""
    _request_id_local.request_id = request_id


class RequestIDMiddleware:
    """
    Har bir requestga unikal ID qo'shish.
    
    Agar client X-Request-ID header yuborsa, uni ishlatadi.
    Aks holda, server generate qiladi.
    
    Header: X-Request-ID: req_abc123
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Client dan request ID olish yoki generate qilish
        request_id = request.META.get("HTTP_X_REQUEST_ID", "")
        if not request_id:
            request_id = f"req_{uuid.uuid4().hex[:16]}"

        # Request ga qo'shish
        request.request_id = request_id
        request.META["HTTP_X_REQUEST_ID"] = request_id

        # Thread-local ga saqlash
        set_request_id(request_id)

        # Response yaratish
        response = self.get_response(request)

        # Response ga request ID qo'shish
        response["X-Request-ID"] = request_id

        return response
