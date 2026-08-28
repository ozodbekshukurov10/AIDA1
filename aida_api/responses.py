"""
AIDA Enterprise API — Standard Response Envelope

Barcha API endpointlari ushbu formatda javob qaytarishi shart:
{
    "status": 200,
    "success": true,
    "message": "OK",
    "data": {...},
    "metadata": {...},
    "pagination": {...},
    "request_id": "req_abc123",
    "execution_time_ms": 45
}
"""
from __future__ import annotations
import time
import uuid
from typing import Any


def generate_request_id() -> str:
    """Unikal request ID yaratish."""
    return f"req_{uuid.uuid4().hex[:16]}"


class APIResponse:
    """Standart API response envelope."""

    @staticmethod
    def success(
        data: Any = None,
        message: str = "OK",
        status: int = 200,
        metadata: dict | None = None,
        pagination: dict | None = None,
        request_id: str = "",
        execution_time_ms: int = 0,
    ) -> dict:
        """Muvaffaqiyatli response."""
        return {
            "status": status,
            "success": True,
            "message": message,
            "data": data,
            "metadata": metadata or {},
            "pagination": pagination,
            "request_id": request_id or generate_request_id(),
            "execution_time_ms": execution_time_ms,
        }

    @staticmethod
    def error(
        code: str,
        message: str,
        reason: str = "",
        recovery: str = "",
        status: int = 400,
        details: dict | list | None = None,
        request_id: str = "",
        execution_time_ms: int = 0,
    ) -> dict:
        """Xatolik response."""
        error_obj = {
            "code": code,
            "description": message,
            "reason": reason,
            "recovery_suggestion": recovery,
        }
        if details:
            error_obj["details"] = details

        return {
            "status": status,
            "success": False,
            "message": message,
            "error": error_obj,
            "request_id": request_id or generate_request_id(),
            "execution_time_ms": execution_time_ms,
        }

    @staticmethod
    def paginated(
        data: list,
        total: int,
        page: int,
        page_size: int,
        message: str = "OK",
        status: int = 200,
        metadata: dict | None = None,
        request_id: str = "",
        execution_time_ms: int = 0,
    ) -> dict:
        """Sahifalangan response."""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return {
            "status": status,
            "success": True,
            "message": message,
            "data": data,
            "metadata": metadata or {},
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
            "request_id": request_id or generate_request_id(),
            "execution_time_ms": execution_time_ms,
        }

    @staticmethod
    def created(data: Any = None, message: str = "Yaratildi", **kwargs) -> dict:
        """201 Created response."""
        return APIResponse.success(data=data, message=message, status=201, **kwargs)

    @staticmethod
    def no_content(message: str = "O'chirildi") -> dict:
        """204 No Content response."""
        return {"status": 204, "success": True, "message": message}

    @staticmethod
    def bad_request(message: str = "Noto'g'ri so'rov", **kwargs) -> dict:
        """400 Bad Request response."""
        return APIResponse.error(
            code="BAD_REQUEST", message=message, status=400, **kwargs
        )

    @staticmethod
    def unauthorized(message: str = "Autentifikatsiya talab qilinadi", **kwargs) -> dict:
        """401 Unauthorized response."""
        return APIResponse.error(
            code="AUTH_REQUIRED", message=message, status=401, **kwargs
        )

    @staticmethod
    def forbidden(message: str = "Ruxsat yo'q", **kwargs) -> dict:
        """403 Forbidden response."""
        return APIResponse.error(
            code="FORBIDDEN", message=message, status=403, **kwargs
        )

    @staticmethod
    def not_found(message: str = "Topilmadi", **kwargs) -> dict:
        """404 Not Found response."""
        return APIResponse.error(
            code="NOT_FOUND", message=message, status=404, **kwargs
        )

    @staticmethod
    def conflict(message: str = "Mavjud", **kwargs) -> dict:
        """409 Conflict response."""
        return APIResponse.error(
            code="CONFLICT", message=message, status=409, **kwargs
        )

    @staticmethod
    def rate_limited(retry_after: int = 60, **kwargs) -> dict:
        """429 Too Many Requests response."""
        return APIResponse.error(
            code="RATE_LIMITED",
            message=f"Juda ko'p so'rov. {retry_after} soniyadan keyin qayta urinib ko'ring.",
            status=429,
            recovery=f"{retry_after} soniya kutib turing yoki premium plana o'ting.",
            **kwargs,
        )

    @staticmethod
    def server_error(message: str = "Ichki xatolik", **kwargs) -> dict:
        """500 Internal Server Error response."""
        return APIResponse.error(
            code="INTERNAL_ERROR", message=message, status=500, **kwargs
        )

    @staticmethod
    def not_implemented(message: str = "Hali amalga oshirilmagan", **kwargs) -> dict:
        """501 Not Implemented response."""
        return APIResponse.error(
            code="NOT_IMPLEMENTED", message=message, status=501, **kwargs
        )
