# AIDA Enterprise API Foundation
## API Standards

**Versiya:** 1.0.0
**Sana:** 2026-07-03
**Muallif:** AIDA API Team

---

## 1. REQUEST STANDARTLARI

### 1.1 Majburiy Headers

```http
Authorization: Bearer {jwt_token}
Content-Type: application/json
Accept: application/json
X-Request-ID: {uuid4}          ← Client yuboradi yoki server generate qiladi
Accept-Language: uz             ← Localization
```

### 1.2 Optional Headers

```http
X-AIDA-Key: {api_key}           ← Platform API (JWT o'rniga)
X-Idempotency-Key: {uuid4}      ← POST uchun takroriy so'rov himoyasi
X-AIDA-Signature: sha256={hash} ← Request signing (API keys uchun)
If-None-Match: {etag}           ← Conditional GET (cache)
```

### 1.3 URL Strukturasi

```
https://api.aida.ai/api/v1/{resource}/{id}/{sub-resource}/

Qoidalar:
  ✅ Lowercase, plural noun
  ✅ Kebab-case (so'zlar orasida '-')
  ✅ UUID yoki slug ID
  ❌ Trailing slash (optional, lekin konsistent)
  ❌ Verb URL'da
  ❌ Query string'da action

Misollar:
  /api/v1/chats/
  /api/v1/chats/{chat_id}/
  /api/v1/chats/{chat_id}/messages/
  /api/v1/orgs/{org_slug}/projects/
  /api/v1/knowledge-bases/{id}/embeddings/
```

### 1.4 HTTP Methods

| Method | Maqsad | Body | Idempotent |
|--------|--------|------|------------|
| GET | O'qish | — | ✅ |
| POST | Yaratish | ✅ | ❌ |
| PUT | To'liq yangilash | ✅ | ✅ |
| PATCH | Qisman yangilash | ✅ | ✅ |
| DELETE | O'chirish | — | ✅ |
| OPTIONS | CORS preflight | — | ✅ |
| HEAD | Metadata only | — | ✅ |

### 1.5 Query Parameters Standartlari

```
Pagination:
  ?page=1&page_size=20          ← Offset-based (kichik dataset)
  ?cursor=eyJpZCI6MTAwfQ==      ← Cursor-based (katta dataset, default)
  ?limit=20&offset=0            ← Muqobil offset

Filtering:
  ?status=active                 ← Exact match
  ?status__in=active,pending     ← Multi-value
  ?created_at__gte=2026-01-01   ← Range (gte, lte, gt, lt)
  ?title__contains=hello         ← Partial match
  ?title__icontains=hello        ← Case-insensitive partial

Sorting:
  ?ordering=created_at           ← ASC
  ?ordering=-created_at          ← DESC (minus prefix)
  ?ordering=-created_at,title    ← Multi-sort

Search (full-text):
  ?search=keyword                ← Global search across searchable fields

Field selection:
  ?fields=id,title,created_at    ← Faqat kerakli fieldlar
  ?expand=user,project           ← Nested objects expand
```

---

## 2. RESPONSE STANDARTLARI

### 2.1 Standard Success Response

```json
{
  "status": 200,
  "success": true,
  "message": "Chat successfully created",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "New Chat",
    "created_at": "2026-07-03T10:37:52Z"
  },
  "metadata": {
    "version": "v1",
    "environment": "production"
  },
  "request_id": "req_abc123xyz",
  "execution_time_ms": 45
}
```

### 2.2 List Response (Pagination bilan)

```json
{
  "status": 200,
  "success": true,
  "message": "Chats retrieved successfully",
  "data": [
    { "id": "...", "title": "Chat 1" },
    { "id": "...", "title": "Chat 2" }
  ],
  "pagination": {
    "count": 142,
    "page": 1,
    "page_size": 20,
    "total_pages": 8,
    "has_next": true,
    "has_previous": false,
    "next_cursor": "eyJpZCI6MTAwfQ==",
    "previous_cursor": null,
    "next": "/api/v1/chats/?cursor=eyJpZCI6MTAwfQ==",
    "previous": null
  },
  "metadata": {
    "version": "v1",
    "filters_applied": {"status": "active"},
    "ordering": "-created_at"
  },
  "request_id": "req_abc123xyz",
  "execution_time_ms": 23
}
```

### 2.3 Error Response

```json
{
  "status": 422,
  "success": false,
  "message": "Validation failed",
  "error": {
    "code": "VALIDATION_ERROR",
    "description": "One or more fields failed validation",
    "reason": "The 'title' field is required and cannot be empty",
    "recovery": "Provide a non-empty title with max 500 characters",
    "fields": {
      "title": ["This field may not be blank."],
      "model_id": ["Invalid UUID format."]
    },
    "docs": "https://docs.aida.ai/errors/VALIDATION_ERROR"
  },
  "request_id": "req_abc123xyz",
  "execution_time_ms": 8
}
```

### 2.4 HTTP Status Kodlari

| Kod | Nom | Ishlatilishi |
|-----|-----|-------------|
| 200 | OK | GET, PUT, PATCH muvaffaqiyatli |
| 201 | Created | POST — yangi resurs yaratildi |
| 202 | Accepted | Async task qabul qilindi |
| 204 | No Content | DELETE muvaffaqiyatli |
| 206 | Partial Content | Range yoki streaming response |
| 301 | Moved Permanently | HTTP → HTTPS redirect |
| 304 | Not Modified | ETag match (cache hit) |
| 400 | Bad Request | Noto'g'ri so'rov formati |
| 401 | Unauthorized | Auth kerak yoki invalid token |
| 403 | Forbidden | Auth OK, lekin ruxsat yo'q |
| 404 | Not Found | Resurs topilmadi |
| 405 | Method Not Allowed | HTTP method qo'llab-quvvatlanmaydi |
| 409 | Conflict | Duplicate resurs (slug conflict) |
| 410 | Gone | Deprecated API versiyasi |
| 413 | Payload Too Large | Request size limit oshib ketdi |
| 422 | Unprocessable Entity | Validation xatosi |
| 429 | Too Many Requests | Rate limit oshdi |
| 500 | Internal Server Error | Server xatosi |
| 502 | Bad Gateway | Upstream (AI provider) xatosi |
| 503 | Service Unavailable | Maintenance yoki overload |
| 504 | Gateway Timeout | Upstream timeout |

---

## 3. PAGINATION

### 3.1 Cursor-Based Pagination (Default)

```
Ishlatilishi: messages, audit_logs, events (yuqori hajmli, append-only)

Request:
  GET /api/v1/chats/{id}/messages/?limit=20
  GET /api/v1/chats/{id}/messages/?cursor=eyJpZCI6MTAwfQ==&limit=20

Cursor format:
  base64({"id": 100, "created_at": "2026-07-03T10:00:00Z"})

Response:
  "pagination": {
    "count": null,          ← cursor'da total count yo'q (performance)
    "limit": 20,
    "has_next": true,
    "has_previous": false,
    "next_cursor": "eyJpZCI6ODB9",
    "previous_cursor": null
  }

Afzallik:
  O(1) performance — OFFSET 1000000 muammosi yo'q
  Consistent results (yangi insert sahifani buzmaydi)
```

### 3.2 Offset-Based Pagination

```
Ishlatilishi: Admin panellar, kichik dataset, export

Request:
  GET /api/v1/users/?page=3&page_size=25

Response:
  "pagination": {
    "count": 1420,
    "page": 3,
    "page_size": 25,
    "total_pages": 57,
    "has_next": true,
    "has_previous": true,
    "next": "/api/v1/users/?page=4&page_size=25",
    "previous": "/api/v1/users/?page=2&page_size=25"
  }

Limit:
  page_size max: 100
  Default page_size: 20
```

---

## 4. FILTERING

### 4.1 Filter Operatorlari

```
Exact:       ?status=active
Not equal:   ?status__ne=deleted
Contains:    ?title__contains=hello
iContains:   ?title__icontains=hello
Starts with: ?username__startswith=admin
In list:     ?status__in=active,pending
Not in:      ?status__not_in=deleted,archived
Range >=:    ?created_at__gte=2026-01-01T00:00:00Z
Range <=:    ?created_at__lte=2026-12-31T23:59:59Z
Is null:     ?deleted_at__isnull=true
Is not null: ?deleted_at__isnull=false
```

### 4.2 JSONB Field Filtering

```
JSONB field ichidagi qiymatga filter:
  ?capabilities__has_key=vision
  ?config__temperature__gte=0.5
  ?metadata__source=github
```

---

## 5. SORTING

```
Standart:
  ?ordering=created_at          ← ASC
  ?ordering=-created_at         ← DESC
  ?ordering=-created_at,title   ← Multi-column

Har endpoint uchun allowed_ordering_fields belgilangan:
  chats:    created_at, updated_at, last_message_at, title
  messages: created_at
  users:    created_at, username, last_login_at

Ruxsatsiz field:
  ?ordering=hashed_password  → 400 Bad Request
```

---

## 6. SEARCH

```
Full-text search:
  GET /api/v1/knowledge/?search=Django REST framework

Qidiruv qamrovi (har endpoint'da belgilangan):
  knowledge:   title, processed_content
  chats:       title
  agents:      name, description
  documents:   filename, original_filename

Search response:
  "metadata": {
    "search_query": "Django REST framework",
    "search_fields": ["title", "processed_content"],
    "total_matches": 42
  }
```

---

## 7. FIELD SELECTION

```
Faqat kerakli fieldlarni olish (bandwidth tejash):

Request:
  GET /api/v1/chats/?fields=id,title,last_message_at

Response:
  "data": [
    {"id": "...", "title": "...", "last_message_at": "..."}
  ]

Expand (nested objects):
  GET /api/v1/chats/?expand=user,project

Response:
  "data": [{
    "id": "...",
    "user": {               ← Full user object (FK expand qilingan)
      "id": "...",
      "username": "..."
    },
    "project": { ... }
  }]
```

---

## 8. LOCALIZATION

```
Request:
  Accept-Language: uz          ← O'zbek
  Accept-Language: en          ← Ingliz
  Accept-Language: ru          ← Rus
  Accept-Language: uz-UZ,uz;q=0.9,en;q=0.8  ← Priority order

Response:
  Content-Language: uz

Error messages tarjimasi:
  "message": "Tasdiqlash muvaffaqiyatsiz bo'ldi"  (uz)
  "message": "Validation failed"                  (en)

Qo'llab-quvvatlanadigan tillar:
  en (default), uz, ru, tr, ar
```

---

## 9. IDEMPOTENCY

```
POST so'rovlari uchun takroriy xavfsizlik:

Header:
  X-Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000

Mexanizm:
  1. Idempotency key Redis'da 24 soat saqlanadi
  2. Birinchi request: bajariladi, natija saqlanadi
  3. Takroriy request: saqlanagan natija qaytariladi (DB'ga ikkinchi yozuv yo'q)

Response header:
  X-Idempotent-Replayed: true  ← Agar takroriy bo'lsa

Ishlatilishi:
  POST /api/v1/chats/          ← Duplicate chat yaratishni oldini oladi
  POST /api/v1/tasks/run/      ← Task ikki marta ishga tushishini oldini oladi
```

---

## 10. ETag VA CACHING

```
GET response headers:
  ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
  Cache-Control: private, max-age=60
  Last-Modified: Fri, 03 Jul 2026 10:37:52 GMT

Conditional GET:
  If-None-Match: "33a64df..."
  → 304 Not Modified (body yo'q, bandwidth tejaladi)

Cache qoidalari:
  GET /api/v1/models/           Cache-Control: public, max-age=300  (5 min)
  GET /api/v1/config/           Cache-Control: private, max-age=60
  GET /api/v1/chats/{id}/       Cache-Control: private, no-cache
  POST/PUT/PATCH/DELETE         Cache-Control: no-store
```

---

## 11. RATE LIMITING RESPONSE

```
Rate limit headers (har response'da):
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 87
  X-RateLimit-Reset: 1751538000    ← Unix timestamp
  X-RateLimit-Window: 60           ← Sekunda

Rate limit oshganda (429):
  Retry-After: 45                  ← Sekunda

Response body:
{
  "status": 429,
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "description": "Too many requests",
    "reason": "You have exceeded 100 requests per minute",
    "recovery": "Wait 45 seconds before retrying, or upgrade your plan"
  }
}
```

---

## 12. DATETIME STANDARTLARI

```
Format:   ISO 8601 + UTC timezone
Pattern:  YYYY-MM-DDTHH:MM:SS.sssZ

Misollar:
  "created_at": "2026-07-03T10:37:52.685Z"
  "expires_at": "2026-08-03T00:00:00.000Z"

Qoidalar:
  ✅ Har doim UTC (Z suffix)
  ✅ Millisecond precision
  ❌ Unix timestamp (API response'da)
  ❌ Locale-specific format ("03/07/2026")
  ❌ Timezone-aware string ("2026-07-03T10:37:52+05:00")
     (ichki saqlanadi, API'da UTC)

Client mas'uliyati:
  UTC'ni local timezone'ga convert qilish client tomonida
```

---

*Hujjat AIDA Development Bible — Book 1, Chapter 9 asosida tayyorlangan.*
