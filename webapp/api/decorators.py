from __future__ import annotations
import functools
import json
import logging
import os
import time
from urllib.parse import urlparse

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..security import authenticate_access_key, RateLimiter

logger = logging.getLogger("webapp.api")

_limiter = RateLimiter()


def api_endpoint(require_key: bool = True, methods: list[str | None] = None):
    def decorator(view_func):
        @csrf_exempt
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            start = time.monotonic()
            client_ip = request.META.get("REMOTE_ADDR", "unknown")
            if not _limiter.check(client_ip):
                return JsonResponse({"error": "Rate limit exceeded. Try again later."}, status=429)
            if require_key:
                key = request.GET.get("key", "") or request.headers.get("X-API-Key", "")
                if not key:
                    return JsonResponse({"error": "API key required. Add ?key= or X-API-Key header."}, status=401)
                if not authenticate_access_key(key):
                    return JsonResponse({"error": "Invalid API key"}, status=403)
            try:
                result = view_func(request, *args, **kwargs)
                latency = int((time.monotonic() - start) * 1000)
                if isinstance(result, JsonResponse):
                    logger.info(f"[API] {request.method} {request.path} {result.status_code} {latency}ms")
                return result
            except Exception as e:
                latency = int((time.monotonic() - start) * 1000)
                logger.error(f"[API] {request.method} {request.path} ERROR: {e} ({latency}ms)")
                return JsonResponse({"error": "Internal server error"}, status=500)
        return wrapper
    return decorator


def parse_json_body(request):
    try:
        return json.loads(request.body)
    except (ValueError, AttributeError):
        return {}
