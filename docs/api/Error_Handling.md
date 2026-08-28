# AIDA Enterprise API Foundation
## Error Handling Guide

**Versiya:** 1.0.0
**Sana:** 2026-07-03
**Muallif:** AIDA API Team

---

## 1. STANDART ERROR FORMAT

Barcha error response'lar bir xil formatda bo'ladi:

```json
{
  "status": 422,
  "success": false,
  "message": "Validation failed",
  "error": {
    "code": "VALIDATION_ERROR",
    "description": "One or more request fields failed validation",
    "reason": "The 'title' field is required and cannot be blank",
    "recovery": "Provide a non-empty title between 1 and 500 characters",
    "fields": {
      "title": ["This field may not be blank."],
      "model_id": ["Enter a valid UUID."]
    },
    "docs": "https://docs.aida.ai/errors/VALIDATION_ERROR"
  },
  "request_id": "req_abc123xyz",
  "execution_time_ms": 8
}
```

### Error Object Fieldlari

| Field | Tur | Tavsif |
|-------|-----|--------|
| `code` | STRING | Machine-readable error kodi |
| `description` | STRING | Inson o'qi uchun tavsif |
| `reason` | STRING | Nima uchun xato yuz berdi |
| `recovery` | STRING | Muammoni hal qilish yo'li |
| `fields` | OBJECT | Validation xatolari (field bo'yicha) |
| `docs` | STRING | Hujjat URL |
| `trace_id` | STRING | Distributed trace (500 da) |

---

## 2. ERROR KATEGORIYALARI VA KODLARI

### 2.1 Validation Errors (422)

| Code | HTTP | Tavsif | Recovery |
|------|------|--------|----------|
| `VALIDATION_ERROR` | 422 | Umumiy validatsiya xatosi | Field xatolarini ko'ring |
| `REQUIRED_FIELD` | 422 | Majburiy field yo'q | Fieldni kiriting |
| `INVALID_FORMAT` | 422 | Format noto'g'ri | To'g'ri format qo'llang |
| `INVALID_UUID` | 422 | UUID format xatosi | UUID v4 format ishlatın |
| `INVALID_EMAIL` | 422 | Email format xatosi | Valid email kiriting |
| `FIELD_TOO_LONG` | 422 | Field maksimal uzunlikdan oshdi | Qisqartiring |
| `FIELD_TOO_SHORT` | 422 | Field minimal uzunlikdan kam | Uzaytiring |
| `INVALID_ENUM` | 422 | Ruxsatsiz qiymat | Ruxsatli qiymatlar ro'yxatiga qarang |
| `DUPLICATE_VALUE` | 422 | Qiymat allaqachon mavjud | Boshqa qiymat tanlang |
| `INVALID_DATE` | 422 | Sana formati noto'g'ri | ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ) |
| `PAYLOAD_TOO_LARGE` | 413 | So'rov hajmi limitdan oshdi | Faylni kichiklashtiring |

```json
// Misol: Ko'p field validation xatosi
{
  "status": 422,
  "success": false,
  "message": "Validation failed",
  "error": {
    "code": "VALIDATION_ERROR",
    "description": "Multiple fields failed validation",
    "reason": "Required fields are missing or have invalid values",
    "recovery": "Review the 'fields' object and correct each error",
    "fields": {
      "title": ["This field may not be blank."],
      "model_id": ["Enter a valid UUID."],
      "temperature": ["Ensure this value is less than or equal to 2.0."]
    },
    "docs": "https://docs.aida.ai/errors/VALIDATION_ERROR"
  },
  "request_id": "req_abc123"
}
```

---

### 2.2 Authentication Errors (401)

| Code | HTTP | Tavsif | Recovery |
|------|------|--------|----------|
| `AUTH_REQUIRED` | 401 | Token taqdim etilmagan | Authorization header qo'shing |
| `TOKEN_INVALID` | 401 | Token noto'g'ri yoki buzilgan | Qayta login qiling |
| `TOKEN_EXPIRED` | 401 | Token muddati o'tgan | Refresh token ishlatib yangilang |
| `TOKEN_REVOKED` | 401 | Token bekor qilingan | Qayta login qiling |
| `TOKEN_BLACKLISTED` | 401 | Token blacklist'da | Qayta login qiling |
| `API_KEY_INVALID` | 401 | API kalit noto'g'ri | API kalitni tekshiring |
| `API_KEY_EXPIRED` | 401 | API kalit muddati o'tgan | Yangi API kalit yarating |
| `API_KEY_REVOKED` | 401 | API kalit bekor qilingan | Yangi API kalit yarating |
| `MFA_REQUIRED` | 401 | 2FA kodi talab qilinadi | MFA kodini kiriting |
| `MFA_INVALID` | 401 | 2FA kodi noto'g'ri | To'g'ri kodni kiriting |
| `SESSION_EXPIRED` | 401 | Sessiya muddati o'tgan | Qayta login qiling |

```json
// Misol: Token expired
{
  "status": 401,
  "success": false,
  "message": "Authentication failed",
  "error": {
    "code": "TOKEN_EXPIRED",
    "description": "The access token has expired",
    "reason": "Token expired at 2026-07-03T10:52:00Z",
    "recovery": "Use the refresh token to obtain a new access token via POST /api/v1/auth/token/refresh/",
    "docs": "https://docs.aida.ai/errors/TOKEN_EXPIRED"
  },
  "request_id": "req_abc123"
}
```

---

### 2.3 Authorization Errors (403)

| Code | HTTP | Tavsif | Recovery |
|------|------|--------|----------|
| `PERMISSION_DENIED` | 403 | Ushbu amal uchun ruxsat yo'q | Admin bilan bog'laning |
| `INSUFFICIENT_SCOPE` | 403 | Token scope yetarli emas | Kerakli scope bilan yangi token oling |
| `ORG_MEMBER_REQUIRED` | 403 | Org a'zosi emas | Org admindan taklif so'rang |
| `PROJECT_ACCESS_DENIED` | 403 | Loyihaga kirish taqiqlangan | Loyiha adminidan ruxsat so'rang |
| `ADMIN_REQUIRED` | 403 | Admin huquqi talab qilinadi | Admin bilan bog'laning |
| `PLAN_UPGRADE_REQUIRED` | 403 | Ushbu funksiya faqat yuqori planda | Planini yangilang |
| `QUOTA_EXCEEDED` | 403 | Kvota tugadi | Planini yangilang yoki kvotani oshiring |
| `RESOURCE_LOCKED` | 403 | Resurs qulflangan | Keyinroq urinib ko'ring |
| `IP_BLOCKED` | 403 | IP manzil bloklangan | Xizmat ko'rsatish bilan bog'laning |

---

### 2.4 Not Found Errors (404)

| Code | HTTP | Tavsif | Recovery |
|------|------|--------|----------|
| `NOT_FOUND` | 404 | Resurs topilmadi | ID'ni tekshiring |
| `CHAT_NOT_FOUND` | 404 | Chat topilmadi | Chat ID'ni tekshiring |
| `USER_NOT_FOUND` | 404 | Foydalanuvchi topilmadi | User ID'ni tekshiring |
| `PROJECT_NOT_FOUND` | 404 | Loyiha topilmadi | Loyiha ID'ni tekshiring |
| `AGENT_NOT_FOUND` | 404 | Agent topilmadi | Agent ID'ni tekshiring |
| `MODEL_NOT_FOUND` | 404 | AI modeli topilmadi | Mavjud modellar ro'yxatiga qarang |
| `PLUGIN_NOT_FOUND` | 404 | Plugin topilmadi | Plugin ID'ni tekshiring |
| `FILE_NOT_FOUND` | 404 | Fayl topilmadi | Fayl o'chirilgan bo'lishi mumkin |
| `ENDPOINT_NOT_FOUND` | 404 | Endpoint mavjud emas | API hujjatlariga qarang |

---

### 2.5 Business Logic Errors (409, 400)

| Code | HTTP | Tavsif | Recovery |
|------|------|--------|----------|
| `DUPLICATE_RESOURCE` | 409 | Resurs allaqachon mavjud | Boshqa nom/slug ishlating |
| `SLUG_TAKEN` | 409 | Bu slug band | Boshqa slug tanlang |
| `EMAIL_ALREADY_EXISTS` | 409 | Bu email ro'yxatdan o'tgan | Login qiling yoki parol tiklang |
| `CHAT_ARCHIVED` | 400 | Chat arxivlangan | Arxivdan qaytaring |
| `WORKFLOW_RUNNING` | 409 | Workflow allaqachon ishlayapti | To'xtatib qayta ishga tushiring |
| `AGENT_BUSY` | 409 | Agent band | Keyinroq urinib ko'ring |
| `MAX_MEMBERS_REACHED` | 409 | Maksimal a'zo soni to'ldi | Planini yangilang |
| `TASK_ALREADY_COMPLETED` | 409 | Task allaqachon bajarilgan | Yangi task yarating |
| `INSUFFICIENT_BALANCE` | 402 | Balans yetarli emas | Hisobni to'ldiring |

---

### 2.6 AI Model Errors (502, 503, 504)

| Code | HTTP | Tavsif | Recovery |
|------|------|--------|----------|
| `AI_PROVIDER_ERROR` | 502 | AI provayder xatosi | Keyinroq urinib ko'ring |
| `AI_PROVIDER_UNAVAILABLE` | 503 | AI provayder mavjud emas | Boshqa model tanlang |
| `AI_TIMEOUT` | 504 | AI so'rovi vaqt tugadi | Qisqaroq prompt ishlating |
| `AI_RATE_LIMITED` | 429 | AI provayder limitni oshirdi | Keyinroq urinib ko'ring |
| `AI_CONTEXT_TOO_LONG` | 422 | Kontekst uzunligi limitdan oshdi | Suhbatni qisqartiring |
| `AI_CONTENT_FILTERED` | 422 | Kontent filtri blokladi | Mazmunni o'zgartiring |
| `AI_INSUFFICIENT_QUOTA` | 402 | AI kvota tugadi | Planini yangilang |
| `MODEL_NOT_AVAILABLE` | 503 | Model hozir mavjud emas | Boshqa model tanlang |
| `MODEL_DEPRECATED` | 410 | Model eskirgan | Yangi modelga o'ting |

```json
// Misol: AI provider xatosi
{
  "status": 502,
  "success": false,
  "message": "AI provider returned an error",
  "error": {
    "code": "AI_PROVIDER_ERROR",
    "description": "The AI provider (OpenAI) returned an unexpected error",
    "reason": "Provider returned: 'server_error' - An error occurred on the server side",
    "recovery": "Try again in a few seconds. If the issue persists, switch to a different model.",
    "fallback_models": ["claude-3-5-sonnet", "gemini-pro"],
    "docs": "https://docs.aida.ai/errors/AI_PROVIDER_ERROR"
  },
  "request_id": "req_abc123"
}
```

---

### 2.7 Tool & Plugin Errors

| Code | HTTP | Tavsif | Recovery |
|------|------|--------|----------|
| `TOOL_EXECUTION_ERROR` | 500 | Tool bajarishda xato | Tool loglarini ko'ring |
| `TOOL_TIMEOUT` | 504 | Tool vaqt tugadi | Timeout sozlamasini oshiring |
| `TOOL_NOT_AVAILABLE` | 503 | Tool hozir mavjud emas | Keyinroq urinib ko'ring |
| `TOOL_PERMISSION_DENIED` | 403 | Tool uchun ruxsat yo'q | Admin toolga ruxsat bersin |
| `PLUGIN_LOAD_ERROR` | 500 | Plugin yuklanmadi | Pluginni qayta o'rnating |
| `PLUGIN_EXECUTION_ERROR` | 500 | Plugin bajarishda xato | Plugin loglarini ko'ring |
| `PLUGIN_INCOMPATIBLE` | 422 | Plugin versiya mos emas | Pluginni yangilang |
| `SANDBOX_ERROR` | 500 | Sandbox xatosi | Kodni tekshiring |
| `SANDBOX_TIMEOUT` | 504 | Sandbox vaqt tugadi | Kodni optimallashtiing |
| `SANDBOX_MEMORY_EXCEEDED` | 422 | Xotira limiti oshdi | Kam xotira ishlatish |

---

### 2.8 Rate Limit Errors (429)

| Code | HTTP | Tavsif | Recovery |
|------|------|--------|----------|
| `RATE_LIMIT_EXCEEDED` | 429 | Umumiy rate limit | Kutib urinib ko'ring |
| `RATE_LIMIT_IP` | 429 | IP bo'yicha limit | Keyinroq urinib ko'ring |
| `RATE_LIMIT_ENDPOINT` | 429 | Endpoint-specific limit | Kutib urinib ko'ring |
| `RATE_LIMIT_AI` | 429 | AI so'rovlari limiti | Premium planga o'ting |

```json
// Misol: Rate limit
{
  "status": 429,
  "success": false,
  "message": "Rate limit exceeded",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "description": "You have exceeded the request rate limit",
    "reason": "100 requests per minute limit reached (plan: free)",
    "recovery": "Wait 45 seconds before retrying. Upgrade to Premium for 500 req/min."
  },
  "request_id": "req_abc123"
}
```

---

### 2.9 Database Errors (500, 503)

| Code | HTTP | Tavsif | Recovery |
|------|------|--------|----------|
| `DATABASE_ERROR` | 500 | Umumiy DB xatosi | Keyinroq urinib ko'ring |
| `DATABASE_UNAVAILABLE` | 503 | DB mavjud emas | Keyinroq urinib ko'ring |
| `DATABASE_TIMEOUT` | 504 | DB so'rovi vaqt tugadi | Keyinroq urinib ko'ring |
| `TRANSACTION_FAILED` | 500 | Transaksiya bajarilmadi | Amaliyotni qaytariladi |

---

### 2.10 Internal Server Errors (500)

| Code | HTTP | Tavsif | Recovery |
|------|------|--------|----------|
| `INTERNAL_ERROR` | 500 | Ichki server xatosi | Keyinroq urinib ko'ring |
| `SERVICE_UNAVAILABLE` | 503 | Servis mavjud emas | Status sahifasini ko'ring |
| `GATEWAY_TIMEOUT` | 504 | Gateway timeout | Keyinroq urinib ko'ring |
| `MAINTENANCE_MODE` | 503 | Texnik xizmat | Keyinroq urinib ko'ring |
| `FEATURE_DISABLED` | 501 | Funksiya o'chirilgan | Admin bilan bog'laning |

```json
// Misol: Internal server error (trace_id bilan)
{
  "status": 500,
  "success": false,
  "message": "An unexpected error occurred",
  "error": {
    "code": "INTERNAL_ERROR",
    "description": "The server encountered an unexpected condition",
    "reason": "An internal error occurred while processing your request",
    "recovery": "Please try again. If the issue persists, contact support with the trace_id.",
    "trace_id": "abc123def456789",
    "support": "support@aida.ai",
    "docs": "https://docs.aida.ai/errors/INTERNAL_ERROR"
  },
  "request_id": "req_abc123"
}
```

---

## 3. ERROR HANDLING PRINSIPLARI

### 3.1 Xavfsiz Error Xabarlar

```
❌ TAQIQLANGAN (ma'lumot chiqarish):
  "Database error: column 'hashed_password' does not exist"
  "File not found: /var/secrets/api_keys.json"
  "Connection refused to 10.0.1.45:5432 (postgres)"
  "User with ID 550e8400... has role 'admin'"

✅ TO'G'RI (umumiy xabar):
  "An internal error occurred. Please try again."
  "The requested resource was not found."
  "Authentication failed."

Qoida:
  Production'da ichki xatolar foydalanuvchiga chiqarilmaydi.
  trace_id yoziladi — support xodimi trace_id bilan loglardan topa oladi.
```

### 3.2 Error Logging

```
Har error quyidagicha loglanadi:

ERROR darajasi:
  - 5xx errors: log level ERROR
  - 429 (rate limit): log level WARNING
  - 4xx (client error): log level INFO

Log tarkibi:
  - request_id, trace_id
  - user_id (agar auth bo'lsa)
  - endpoint, method
  - error_code, error_message (to'liq, internal)
  - stack_trace (5xx uchun)
  - duration_ms
```

### 3.3 Retry Tavsiyalari (SDK uchun)

```
RETRY qilish kerak:
  429 → Retry-After headerga qarab kuting
  503 → Exponential backoff: 1s, 2s, 4s, 8s (max 3 ta)
  504 → 1 marta retry
  502 → 1 marta retry (AI provider xatosi)

RETRY qilish kerak EMAS:
  400, 422 → Client xatosi (ma'lumot noto'g'ri)
  401, 403 → Auth xatosi (tokenni yangilang)
  404 → Resurs yo'q
  409 → Conflict (logika xatosi)

Exponential Backoff:
  attempt 1: darhol
  attempt 2: 1 sek kutish
  attempt 3: 2 sek kutish
  attempt 4: 4 sek kutish
  Max attempts: 3 (default), 5 (premium)
  Jitter: ±random(0, 500ms) — thundering herd oldini olish
```

---

## 4. ERROR KODI KATALOGI (TO'LIQ RO'YXAT)

```
AUTH_*:
  AUTH_REQUIRED, TOKEN_INVALID, TOKEN_EXPIRED, TOKEN_REVOKED,
  TOKEN_BLACKLISTED, API_KEY_INVALID, API_KEY_EXPIRED, API_KEY_REVOKED,
  MFA_REQUIRED, MFA_INVALID, SESSION_EXPIRED

PERMISSION_*:
  PERMISSION_DENIED, INSUFFICIENT_SCOPE, ORG_MEMBER_REQUIRED,
  PROJECT_ACCESS_DENIED, ADMIN_REQUIRED, PLAN_UPGRADE_REQUIRED,
  QUOTA_EXCEEDED, RESOURCE_LOCKED, IP_BLOCKED

VALIDATION_*:
  VALIDATION_ERROR, REQUIRED_FIELD, INVALID_FORMAT, INVALID_UUID,
  INVALID_EMAIL, FIELD_TOO_LONG, FIELD_TOO_SHORT, INVALID_ENUM,
  DUPLICATE_VALUE, INVALID_DATE, PAYLOAD_TOO_LARGE

NOT_FOUND_*:
  NOT_FOUND, CHAT_NOT_FOUND, USER_NOT_FOUND, PROJECT_NOT_FOUND,
  AGENT_NOT_FOUND, MODEL_NOT_FOUND, PLUGIN_NOT_FOUND, FILE_NOT_FOUND,
  ENDPOINT_NOT_FOUND

BUSINESS_*:
  DUPLICATE_RESOURCE, SLUG_TAKEN, EMAIL_ALREADY_EXISTS,
  CHAT_ARCHIVED, WORKFLOW_RUNNING, AGENT_BUSY,
  MAX_MEMBERS_REACHED, TASK_ALREADY_COMPLETED, INSUFFICIENT_BALANCE

AI_*:
  AI_PROVIDER_ERROR, AI_PROVIDER_UNAVAILABLE, AI_TIMEOUT,
  AI_RATE_LIMITED, AI_CONTEXT_TOO_LONG, AI_CONTENT_FILTERED,
  AI_INSUFFICIENT_QUOTA, MODEL_NOT_AVAILABLE, MODEL_DEPRECATED

TOOL_*:
  TOOL_EXECUTION_ERROR, TOOL_TIMEOUT, TOOL_NOT_AVAILABLE,
  TOOL_PERMISSION_DENIED, PLUGIN_LOAD_ERROR, PLUGIN_EXECUTION_ERROR,
  PLUGIN_INCOMPATIBLE, SANDBOX_ERROR, SANDBOX_TIMEOUT, SANDBOX_MEMORY_EXCEEDED

RATE_*:
  RATE_LIMIT_EXCEEDED, RATE_LIMIT_IP, RATE_LIMIT_ENDPOINT, RATE_LIMIT_AI

DB_*:
  DATABASE_ERROR, DATABASE_UNAVAILABLE, DATABASE_TIMEOUT, TRANSACTION_FAILED

SYSTEM_*:
  INTERNAL_ERROR, SERVICE_UNAVAILABLE, GATEWAY_TIMEOUT,
  MAINTENANCE_MODE, FEATURE_DISABLED
```

---

*Hujjat AIDA Development Bible — Book 1, Chapter 9 asosida tayyorlangan.*
