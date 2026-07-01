"""Clean API routes — thin layer that delegates to use cases."""

from __future__ import annotations
import json
import logging
from typing import Any

logger = logging.getLogger("aidaos.presentation.api")


class APIResponse:
    """Standard API response format."""

    def __init__(self, data: Any = None, error: str = "", status: int = 200):
        self.data = data
        self.error = error
        self.status = status

    def to_dict(self) -> dict:
        if self.error:
            return {"success": False, "error": self.error}
        return {"success": True, "data": self.data}

    @classmethod
    def ok(cls, data: Any = None) -> APIResponse:
        return cls(data=data, status=200)

    @classmethod
    def created(cls, data: Any = None) -> APIResponse:
        return cls(data=data, status=201)

    @classmethod
    def error(cls, message: str, status: int = 400) -> APIResponse:
        return cls(error=message, status=status)

    @classmethod
    def not_found(cls, message: str = "Not found") -> APIResponse:
        return cls(error=message, status=404)

    @classmethod
    def server_error(cls, message: str = "Internal server error") -> APIResponse:
        return cls(error=message, status=500)
