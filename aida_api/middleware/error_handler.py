"""
Error Handler Middleware — Global xatoliklarni qayta ishlash.
"""
import json
import logging
import traceback
from django.http import JsonResponse
from ..exceptions import AIDAException
from ..responses import APIResponse

logger = logging.getLogger("aida_api.errors")


class ErrorHandlerMiddleware:
    """
    Global xatoliklarni qayta ishlash.
    
    Barcha xatoliklarni yakunalab, standart formatda javob qaytaradi:
    - AIDAException -> Maxsus xatolik formati
    - Django Http404 -> 404
    - ValidationError -> 400
    - Boshqa xatoliklar -> 500
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            return self._handle_exception(request, e)

    def process_exception(self, request, exception):
        """Django middleware uchun exception handler."""
        return self._handle_exception(request, exception)

    def _handle_exception(self, request, exception):
        """Xatolikni qayta ishlash."""
        request_id = getattr(request, "request_id", "")
        execution_time_ms = getattr(request, "execution_time_ms", 0)

        # AIDAException — maxsus xatoliklar
        if isinstance(exception, AIDAException):
            logger.warning(
                f"AIDA Exception: {exception.error_code} - {exception.message}",
                extra={"request_id": request_id, "path": request.path},
            )
            return JsonResponse(
                APIResponse.error(
                    code=exception.error_code,
                    message=exception.message,
                    reason=exception.reason,
                    recovery=exception.recovery,
                    status=exception.status_code,
                    details=exception.details,
                    request_id=request_id,
                    execution_time_ms=execution_time_ms,
                ),
                status=exception.status_code,
            )

        # Django Http404
        from django.http import Http404
        if isinstance(exception, Http404):
            return JsonResponse(
                APIResponse.not_found(
                    message="Sahifa yoki resurs topilmadi",
                    request_id=request_id,
                    execution_time_ms=execution_time_ms,
                ),
                status=404,
            )

        # Django ValidationError
        from django.core.exceptions import ValidationError as DjangoValidationError
        if isinstance(exception, DjangoValidationError):
            return JsonResponse(
                APIResponse.bad_request(
                    message=str(exception),
                    request_id=request_id,
                    execution_time_ms=execution_time_ms,
                ),
                status=400,
            )

        # JSON parse xatoliklari
        if hasattr(exception, "content_type") and "json" in str(getattr(exception, "content_type", "")):
            return JsonResponse(
                APIResponse.bad_request(
                    message="JSON formati noto'g'ri",
                    recovery="To'g'ri JSON formatida yuboring.",
                    request_id=request_id,
                    execution_time_ms=execution_time_ms,
                ),
                status=400,
            )

        # Boshqa xatoliklar — 500
        logger.error(
            f"Unhandled exception: {type(exception).__name__}: {exception}",
            extra={"request_id": request_id, "path": request.path},
            exc_info=True,
        )

        # Debug rejimida batafsil xatolik, production da umumiy
        from django.conf import settings
        details = None
        if settings.DEBUG:
            details = {
                "exception_type": type(exception).__name__,
                "traceback": traceback.format_exc().split("\n")[-5:],
            }

        return JsonResponse(
            APIResponse.server_error(
                message="Ichki xatolik yuz berdi. Keyinroq qayta urinib ko'ring.",
                details=details,
                request_id=request_id,
                execution_time_ms=execution_time_ms,
            ),
            status=500,
        )
