"""
AIDA Enterprise API — Custom Exceptions

Barcha API xatoliklari ushbu exceptionlardan kelib chiqishi kerak.
Each exception maps to a specific HTTP status code and error code.
"""
from __future__ import annotations
from typing import Any


class AIDAException(Exception):
    """AIDA asosiy exception sinfi."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "Ichki xatolik"
    reason: str = ""
    recovery: str = ""

    def __init__(
        self,
        message: str = "",
        reason: str = "",
        recovery: str = "",
        details: dict | list | None = None,
        status_code: int | None = None,
        error_code: str | None = None,
    ):
        self.message = message or self.__class__.message
        self.reason = reason or self.__class__.reason
        self.recovery = recovery or self.__class__.recovery
        self.details = details
        if status_code:
            self.status_code = status_code
        if error_code:
            self.error_code = error_code
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Exception ni dict ga aylantirish."""
        result = {
            "code": self.error_code,
            "description": self.message,
            "reason": self.reason,
            "recovery_suggestion": self.recovery,
        }
        if self.details:
            result["details"] = self.details
        return result


# ── Validation Errors ──────────────────────────────────────────────────────────

class ValidationError(AIDAException):
    status_code = 400
    error_code = "VALIDATION_ERROR"
    message = "Ma'lumotlar to'g'ri emas"
    recovery = "Kiritilgan ma'lumotlarni tekshiring."


class FieldValidationError(ValidationError):
    """Bitta field uchun xatolik."""

    def __init__(self, field: str, message: str, **kwargs):
        self.field = field
        details = {"field": field, "message": message}
        super().__init__(details=details, **kwargs)


class RequiredFieldError(ValidationError):
    """Majburiy field topilmadi."""

    def __init__(self, field: str, **kwargs):
        self.field = field
        super().__init__(
            message=f"'{field}' kiritilishi shart.",
            details={"field": field},
            **kwargs,
        )


class InvalidFormatError(ValidationError):
    """Noto'g'ri format."""

    def __init__(self, field: str, expected: str, **kwargs):
        self.field = field
        self.expected = expected
        super().__init__(
            message=f"'{field}' formati noto'g'ri. Kutilgan: {expected}",
            details={"field": field, "expected_format": expected},
            **kwargs,
        )


# ── Authentication Errors ──────────────────────────────────────────────────────

class AuthenticationError(AIDAException):
    status_code = 401
    error_code = "AUTH_REQUIRED"
    message = "Autentifikatsiya talab qilinadi"
    recovery = "Token yoki API key ni tekshiring."


class InvalidTokenError(AuthenticationError):
    error_code = "INVALID_TOKEN"
    message = "Token noto'g'ri yoki muddati tugagan"
    recovery = "Yangi token olish uchun /auth/login/ endpointiga murojaat qiling."


class ExpiredTokenError(AuthenticationError):
    error_code = "EXPIRED_TOKEN"
    message = "Token muddati tugagan"
    recovery = "Tokenni yangilash uchun /auth/token/refresh/ endpointini ishlating."


class InvalidAPIKeyError(AuthenticationError):
    error_code = "INVALID_API_KEY"
    message = "API key noto'g'ri"
    recovery = "To'g'ri API key ni kiriting yoki yangisini yarating."


class MissingAuthenticationError(AuthenticationError):
    error_code = "MISSING_AUTH"
    message = "Autentifikatsiya ma'lumotlari topilmadi"
    recovery = "Authorization header yoki API key qo'shing."


# ── Authorization Errors ───────────────────────────────────────────────────────

class AuthorizationError(AIDAException):
    status_code = 403
    error_code = "FORBIDDEN"
    message = "Ruxsat yo'q"
    recovery = "Sizda bu amalni bajarish uchun ruxsat yo'q."


class InsufficientPermissionsError(AuthorizationError):
    error_code = "INSUFFICIENT_PERMISSIONS"
    message = "Yetarli ruxsat yo'q"
    recovery = "Admin dan ruxsat so'rang yoki premium plana o'ting."


class OwnerRequiredError(AuthorizationError):
    error_code = "OWNER_REQUIRED"
    message = "Faqat egasi bajarishi mumkin"
    recovery = "Faqat resurs egasi bu amalni bajarishi mumkin."


# ── Business Errors ────────────────────────────────────────────────────────────

class BusinessError(AIDAException):
    status_code = 422
    error_code = "BUSINESS_ERROR"
    message = "Biznes qoidasi buzildi"


class ResourceNotFoundError(BusinessError):
    error_code = "NOT_FOUND"
    status_code = 404
    message = "Resurs topilmadi"

    def __init__(self, resource: str = "Resurs", resource_id: str = "", **kwargs):
        msg = f"{resource} topilmadi"
        if resource_id:
            msg = f"{resource} (ID: {resource_id}) topilmadi"
        super().__init__(message=msg, **kwargs)


class ResourceAlreadyExistsError(BusinessError):
    error_code = "ALREADY_EXISTS"
    status_code = 409
    message = "Resurs allaqachon mavjud"

    def __init__(self, resource: str = "Resurs", **kwargs):
        super().__init__(message=f"{resource} allaqachon mavjud.", **kwargs)


class DuplicateEntryError(BusinessError):
    error_code = "DUPLICATE_ENTRY"
    status_code = 409
    message = "Takroriy ma'lumot"

    def __init__(self, field: str = "", **kwargs):
        msg = "Bu ma'lumot allaqachon mavjud."
        if field:
            msg = f"'{field}' qiymati allaqachon mavjud."
        super().__init__(message=msg, **kwargs)


class QuotaExceededError(BusinessError):
    error_code = "QUOTA_EXCEEDED"
    status_code = 429
    message = "Kvota tugadi"
    recovery = "Premium plana o'ting yoki kvota tiklanishini kuting."


class OperationNotAllowedError(BusinessError):
    error_code = "OPERATION_NOT_ALLOWED"
    message = "Amal ruxsat etilmagan"
    recovery = "Boshqa amalni sinab ko'ring."


# ── AI Errors ──────────────────────────────────────────────────────────────────

class AIError(AIDAException):
    status_code = 502
    error_code = "AI_ERROR"
    message = "AI model xatosi"


class ModelNotAvailableError(AIError):
    error_code = "MODEL_NOT_AVAILABLE"
    message = "AI model mavjud emas"
    recovery = "Boshqa model tanlang yoki modelni yuklang."


class ProviderError(AIError):
    error_code = "PROVIDER_ERROR"
    message = "AI provayder xatosi"

    def __init__(self, provider: str = "", **kwargs):
        msg = "AI provayder bilan bog'lanishda xatolik"
        if provider:
            msg = f"{provider} provayderida xatolik"
        super().__init__(message=msg, **kwargs)


class ModelTimeoutError(AIError):
    error_code = "MODEL_TIMEOUT"
    message = "AI model vaqt chegarasini oshirdi"
    recovery = "Qayta urinib ko'ring yoki kichikroq model tanlang."


class PromptTooLongError(AIError):
    error_code = "PROMPT_TOO_LONG"
    message = "So'rov juda uzun"
    recovery = "So'rovni qisqartiring."


class ContentFilteredError(AIError):
    error_code = "CONTENT_FILTERED"
    message = "Kontent filtrlangan"
    recovery = "Boshqa so'rov yuboring."


# ── Tool Errors ────────────────────────────────────────────────────────────────

class ToolError(AIDAException):
    status_code = 500
    error_code = "TOOL_ERROR"
    message = "Vosita xatosi"


class ToolNotFoundError(ToolError):
    error_code = "TOOL_NOT_FOUND"
    status_code = 404
    message = "Vosita topilmadi"

    def __init__(self, tool_name: str = "", **kwargs):
        msg = "Vosita topilmadi"
        if tool_name:
            msg = f"'{tool_name}' vositasi topilmadi"
        super().__init__(message=msg, **kwargs)


class ToolExecutionError(ToolError):
    error_code = "TOOL_EXECUTION_ERROR"
    message = "Vosita bajarilishida xatolik"


class ToolPermissionError(ToolError):
    error_code = "TOOL_PERMISSION_ERROR"
    status_code = 403
    message = "Vosita uchun ruxsat yo'q"


class ToolTimeoutError(ToolError):
    error_code = "TOOL_TIMEOUT"
    message = "Vosita vaqt chegarasini oshirdi"


# ── Plugin Errors ──────────────────────────────────────────────────────────────

class PluginError(AIDAException):
    status_code = 500
    error_code = "PLUGIN_ERROR"
    message = "Plugin xatosi"


class PluginNotFoundError(PluginError):
    error_code = "PLUGIN_NOT_FOUND"
    status_code = 404
    message = "Plugin topilmadi"


class PluginInstallError(PluginError):
    error_code = "PLUGIN_INSTALL_ERROR"
    message = "Plugin o'rnatishda xatolik"


class PluginPermissionError(PluginError):
    error_code = "PLUGIN_PERMISSION_ERROR"
    status_code = 403
    message = "Plugin uchun ruxsat yo'q"


# ── Database Errors ────────────────────────────────────────────────────────────

class DatabaseError(AIDAException):
    status_code = 500
    error_code = "DATABASE_ERROR"
    message = "Ma'lumotlar bazasi xatosi"
    recovery = "Keyinroq qayta urinib ko'ring."


class ConnectionError(DatabaseError):
    error_code = "DB_CONNECTION_ERROR"
    message = "Ma'lumotlar bazasiga bog'lanib bo'lmadi"


class QueryError(DatabaseError):
    error_code = "DB_QUERY_ERROR"
    message = "So'rov bajarishda xatolik"


# ── Rate Limiting Errors ──────────────────────────────────────────────────────

class RateLimitError(AIDAException):
    status_code = 429
    error_code = "RATE_LIMITED"
    message = "Juda ko'p so'rov"
    recovery = "Bir oz kutib turing yoki premium plana o'ting."

    def __init__(self, retry_after: int = 60, **kwargs):
        self.retry_after = retry_after
        super().__init__(
            message=f"Juda ko'p so'rov. {retry_after} soniyadan keyin qayta urinib ko'ring.",
            **kwargs,
        )
