"""
Timing Middleware — Har bir request uchun vaqt o'lchash.
"""
import time
from .request_id import set_request_id


class TimingMiddleware:
    """
    Har bir request uchun bajarilish vaqtini o'lchash.
    
    Response header ga qo'shadi:
    - X-Execution-Time: 45ms
    
    Response body ga qo'shadi:
    - execution_time_ms: 45
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.monotonic()

        # Request ni qayta ishlash
        response = self.get_response(request)

        # Vaqtni hisoblash
        execution_time_ms = int((time.monotonic() - start_time) * 1000)

        # Request ga qo'shish
        request.execution_time_ms = execution_time_ms

        # Response header ga qo'shish
        response["X-Execution-Time"] = f"{execution_time_ms}ms"

        return response
