# AIDA Enterprise API Foundation
## API Architecture

**Versiya:** 1.0.0
**Sana:** 2026-07-03
**Muallif:** AIDA API Team
**Holat:** Production-Ready Design

---

## 1. EXECUTIVE SUMMARY

AIDA API Platformasi millionlab foydalanuvchilar, AI agentlar, mobil ilovalar, veb ilovalar va tashqi tizimlar bilan xavfsiz, tez va barqaror ishlay oladigan enterprise darajasidagi API ekotizimi. Arxitektura RESTful prinsiplar, OpenAPI 3.1 standartlari va cloud-native deployment modeliga asoslanadi.

---

## 2. ARXITEKTURA UMUMIY KO'RINISHI

```
┌───────────────────────────────────────────────────────────────────────┐
│                        API PLATFORM                                   │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   ┌─────────┐  ┌──────────┐  ┌────────┐  ┌──────────┐  ┌──────────┐  │
│   │ Web App │  │Mobile App│  │SDK/CLI │  │3rd Party │  │AI Agents │  │
│   └────┬────┘  └────┬─────┘  └───┬────┘  └────┬─────┘  └────┬─────┘  │
│        └────────────┴────────────┴─────────────┴─────────────┘        │
│                                  │                                    │
│                    ┌─────────────▼──────────────┐                     │
│                    │        API GATEWAY          │                     │
│                    │  • Rate Limiting            │                     │
│                    │  • Auth Verification        │                     │
│                    │  • Request ID injection     │                     │
│                    │  • CORS / Security headers  │                     │
│                    │  • SSL Termination          │                     │
│                    └─────────────┬──────────────┘                     │
│                                  │                                    │
│         ┌────────────────────────┼────────────────────────┐           │
│         │                        │                        │           │
│  ┌──────▼──────┐        ┌────────▼────────┐      ┌───────▼───────┐   │
│  │ /api/v1/    │        │ /api/internal/  │      │ /api/admin/   │   │
│  │ /api/v2/    │        │ (service-to-    │      │ (staff only)  │   │
│  │ /api/public/│        │  service)       │      │               │   │
│  └──────┬──────┘        └────────┬────────┘      └───────┬───────┘   │
│         │                        │                        │           │
│         └────────────────────────┼────────────────────────┘           │
│                                  │                                    │
│                    ┌─────────────▼──────────────┐                     │
│                    │      DJANGO REST API        │                     │
│                    │  (DRF + custom middleware)  │                     │
│                    └─────────────┬──────────────┘                     │
│                                  │                                    │
│     ┌──────────┬─────────────────┼──────────────┬──────────┐          │
│     │          │                 │              │          │          │
│  ┌──▼───┐  ┌───▼──┐         ┌───▼──┐       ┌───▼──┐  ┌───▼──┐       │
│  │  DB  │  │Redis │         │ Queue│       │ AI   │  │Vector│       │
│  │ (PG) │  │      │         │Celery│       │Models│  │  DB  │       │
│  └──────┘  └──────┘         └──────┘       └──────┘  └──────┘       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 3. ASOSIY PRINSIPLAR VA TEXNIK ASOSLAR

### 3.1 RESTful + Resource Oriented

```
Prinsip: Har bir URL resurs (noun), HTTP method amal (verb)

✅ TO'G'RI:
  GET    /api/v1/chats/          → Chatlar ro'yxati
  POST   /api/v1/chats/          → Yangi chat yaratish
  GET    /api/v1/chats/{id}/     → Bitta chat
  PUT    /api/v1/chats/{id}/     → To'liq yangilash
  PATCH  /api/v1/chats/{id}/     → Qisman yangilash
  DELETE /api/v1/chats/{id}/     → O'chirish

❌ NOTO'G'RI:
  POST /api/v1/createChat/       → RPC style
  GET  /api/v1/getChats/         → Verb URL'da
  POST /api/v1/deleteChat/       → DELETE method ishlatilmagan
```

### 3.2 Stateless

```
Har bir request o'zida barcha kerakli ma'lumotni olib yuradi:
  - Authentication: Authorization header
  - Request ID: X-Request-ID header
  - Version: URL da (/api/v1/)
  - Locale: Accept-Language header

Server hech qanday session state saqlamaydi.
Horizontal scaling uchun zarur — har server har requestni bajarishi mumkin.
```

### 3.3 Versioned by Default

```
Versioning URL'da (path versioning):
  /api/v1/  → Hozirgi barqaror versiya
  /api/v2/  → Keyingi versiya (parallel)

Nima uchun path versioning:
  - Browser cache'da ishlaydi
  - Proxy/CDN uchun qulay
  - SDK'larda aniq
  - Content-type header versioning'dan sodda
```

---

## 4. API VERSIONING STRATEGIYASI

### 4.1 Versiya Nomenklaturasi

```
/api/v1/          Birinchi barqaror versiya
/api/v2/          Ikkinchi versiya (breaking changes)
/api/internal/    Servislar orasidagi ichki API
/api/admin/       Staff/superuser faqat
/api/public/      Autentifikatsiyasiz ommaviy endpointlar
```

### 4.2 Versiya Lifecycle

```
ALPHA:     Inernal testing, istalgan o'zgarish mumkin
BETA:      Public testing, breaking change'lar e'lon qilinadi
STABLE:    Production, 12+ oy qo'llab-quvvatlanadi
DEPRECATED: 6 oy ogohlantirish, keyin SUNSET
SUNSET:    O'chirilgan, 410 Gone qaytaradi
```

### 4.3 Version Migration Strategiyasi

```
Bosqich 1 — Parallel ish (3 oy):
  v1 va v2 parallel ishlaydi
  v2 release notes e'lon qilinadi
  SDK yangilangan versiyalar chiqariladi

Bosqich 2 — Deprecation (3 oy):
  v1 Deprecated header qo'shiladi:
  Deprecation: version="v1", sunset="2027-01-01"
  Sunset: Sat, 01 Jan 2027 00:00:00 GMT
  Link: </api/v2/migration-guide>; rel="deprecation"

Bosqich 3 — Sunset (0 kun):
  v1 → 410 Gone
  Body: {"error": "API v1 retired. Migrate to v2: /api/v2/"}

Backward Compatibility qoidalari:
  MINOR (patch, v1 ichida):
    ✅ Yangi optional field qo'shish
    ✅ Yangi endpoint qo'shish
    ✅ Response'ga yangi field qo'shish
  BREAKING (yangi major versiya kerak):
    ❌ Mavjud field o'chirish
    ❌ Field nomini o'zgartirish
    ❌ URL strukturasini o'zgartirish
    ❌ Required field qo'shish
```

### 4.4 Versiya Qarorlari Matriksi

| O'zgarish turi | v1 patch | Yangi v2 |
|----------------|----------|----------|
| Yangi endpoint | ✅ | — |
| Yangi optional field | ✅ | — |
| Field o'chirish | ❌ | ✅ |
| URL o'zgartirish | ❌ | ✅ |
| Auth mexanizmi | ❌ | ✅ |
| Response format | ❌ | ✅ |

---

## 5. API MODULLARI ARXITEKTURASI

### 5.1 Core Modules

```
AUTHENTICATION MODULE:
  Prefix: /api/v1/auth/
  Maqsad: Login, logout, token management, OAuth2
  Rate limit: Strict (5 req/min anonymous)

USER MODULE:
  Prefix: /api/v1/users/
  Maqsad: User CRUD, profile, settings
  Auth: JWT required

ORGANIZATION MODULE:
  Prefix: /api/v1/orgs/
  Maqsad: Org CRUD, members, billing
  Auth: JWT + org membership

PROJECT MODULE:
  Prefix: /api/v1/projects/
  Maqsad: Project CRUD, settings, members
  Auth: JWT + project membership
```

### 5.2 AI Core Modules

```
CHAT MODULE:
  Prefix: /api/v1/chats/
  Maqsad: Suhbatlar boshqaruvi
  Special: Streaming support (SSE)

MESSAGE MODULE:
  Prefix: /api/v1/chats/{id}/messages/
  Maqsad: Xabarlar, AI javob yaratish
  Special: Token streaming, cancellation

AI MODELS MODULE:
  Prefix: /api/v1/models/
  Maqsad: Available models ro'yxati, test

PROVIDER MODULE:
  Prefix: /api/v1/providers/
  Maqsad: AI provider boshqaruvi (admin)

AGENT MODULE:
  Prefix: /api/v1/agents/
  Maqsad: Agent CRUD, run, monitor
  Special: WebSocket events

TASK MODULE:
  Prefix: /api/v1/tasks/
  Maqsad: Task management, queue

WORKFLOW MODULE:
  Prefix: /api/v1/workflows/
  Maqsad: Workflow CRUD, run, monitor

MEMORY MODULE:
  Prefix: /api/v1/memory/
  Maqsad: Conversation memory management

KNOWLEDGE MODULE:
  Prefix: /api/v1/knowledge/
  Maqsad: Knowledge base CRUD, search

RAG MODULE:
  Prefix: /api/v1/rag/
  Maqsad: Retrieval-Augmented Generation queries

EMBEDDING MODULE:
  Prefix: /api/v1/embeddings/
  Maqsad: Vector embedding yaratish, qidirish
```

### 5.3 Repository & Code Modules

```
REPOSITORY MODULE:
  Prefix: /api/v1/repositories/
  Maqsad: Repo CRUD, sync

REPOSITORY ANALYZER MODULE:
  Prefix: /api/v1/repositories/{id}/analyze/
  Maqsad: Code analysis, dependency map

GIT MODULE:
  Prefix: /api/v1/git/
  Maqsad: Git operations (clone, diff, log)

GITHUB MODULE:
  Prefix: /api/v1/github/
  Maqsad: GitHub OAuth, repo import, webhooks
```

### 5.4 Tool & Execution Modules

```
TERMINAL MODULE:
  Prefix: /api/v1/terminal/
  Maqsad: Secure shell execution
  Special: WebSocket based

PYTHON SANDBOX MODULE:
  Prefix: /api/v1/sandbox/python/
  Maqsad: Safe Python code execution
  Security: Container isolation

DOCKER MODULE:
  Prefix: /api/v1/docker/
  Maqsad: Container management (admin)

BROWSER MODULE:
  Prefix: /api/v1/browser/
  Maqsad: Headless browser automation
```

### 5.5 Platform Modules

```
PLUGIN MODULE:
  Prefix: /api/v1/plugins/
  Maqsad: Plugin management

FILE MODULE:
  Prefix: /api/v1/files/
  Maqsad: File upload/download (chunked)
  Special: Multipart, streaming

MONITORING MODULE:
  Prefix: /api/v1/monitoring/
  Maqsad: System status, metrics (admin/internal)

LOGS MODULE:
  Prefix: /api/v1/logs/
  Maqsad: Log access (admin)

CONFIGURATION MODULE:
  Prefix: /api/v1/config/
  Maqsad: System/org/project/user settings

PLATFORM MODULE (legacy):
  Prefix: /api/platform/
  Maqsad: Tashqi platformalar uchun (API key auth)
  Endpoint: POST /api/platform/chat/
```

---

## 6. MIDDLEWARE STACK

```
Request lifecycle (yuqoridan pastga):

1. SecurityHeadersMiddleware
   → HTTPS redirect, HSTS, X-Frame-Options, CSP

2. CORSMiddleware
   → Origin whitelist, preflight handling

3. RequestIDMiddleware
   → X-Request-ID generate/propagate

4. RateLimitMiddleware
   → Token bucket algorithm, per-user/role limits

5. AuthenticationMiddleware
   → JWT verify, API key lookup, session check

6. LocalizationMiddleware
   → Accept-Language → request.LANGUAGE_CODE

7. RequestLoggingMiddleware
   → Structured log (method, path, user, request_id)

8. View (Django REST Framework)
   → Validation, Business logic, Response

9. ResponseMiddleware
   → Standard format wrap, execution time inject

10. AuditMiddleware
    → Audit log (write operations)
```

---

## 7. SECURITY ARXITEKTURASI

```
HTTPS ONLY:
  HTTP → 301 Redirect HTTPS
  HSTS: max-age=31536000; includeSubDomains; preload

SECURITY HEADERS (har response'da):
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  X-XSS-Protection: 1; mode=block
  Referrer-Policy: strict-origin-when-cross-origin
  Content-Security-Policy: default-src 'self'
  Permissions-Policy: camera=(), microphone=(), geolocation=()

CORS:
  Allowed origins: whitelist (env config)
  Allowed methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
  Allowed headers: Content-Type, Authorization, X-Request-ID
  Max age: 86400 (24 soat preflight cache)
  Credentials: true (JWT cookie uchun)

CSRF:
  SameSite=Strict cookie
  CSRF token (Django default, form-based)
  API: JWT stateless → CSRF kerak emas

INPUT VALIDATION:
  DRF Serializer'da barcha field validated
  Max request size: 10MB (file upload: 100MB)
  Request timeout: 30 sek (AI calls: 120 sek)

OUTPUT ENCODING:
  JSON response: content-type: application/json; charset=utf-8
  HTML entity encoding (template'larda)
  Sensitive data masking (response filter)

REQUEST SIGNING (API Keys uchun):
  HMAC-SHA256 signature optional
  Header: X-AIDA-Signature: sha256={hash}
  Prevents replay attacks
```

---

## 8. CLOUD NATIVE DEPLOYMENT

```
Load Balancer (AWS ALB / GCP HTTPS LB):
  → SSL termination
  → Health check: GET /api/health/
  → Sticky sessions: NO (stateless)
  → Connection draining: 30 sek

API Gateway (Kong / AWS API Gateway / nginx):
  → Rate limiting (Redis backend)
  → Request transformation
  → Response caching (GET requests, 60s TTL)
  → Circuit breaker

Auto-scaling:
  Trigger: CPU > 70% yoki RPS > 1000/instance
  Scale-up: +2 instance
  Scale-down: CPU < 30% for 15 min
  Min instances: 2 (HA)
  Max instances: 20

Health Endpoints:
  GET /api/health/           → Liveness probe (200 = OK)
  GET /api/health/ready/     → Readiness probe (DB, Redis check)
  GET /api/health/detailed/  → Full status (admin only)
```

---

## 9. PERFORMANCE MAQSADLARI

| Metrika | Target | Kritik |
|---------|--------|--------|
| API p50 latency | < 100ms | < 500ms |
| API p95 latency | < 500ms | < 2s |
| API p99 latency | < 1s | < 5s |
| AI chat p50 | < 2s (TTFT) | < 5s |
| Throughput | 1000 RPS/instance | 500 RPS |
| Error rate | < 0.1% | < 1% |
| Uptime | 99.9% | 99% |

TTFT = Time To First Token (streaming boshlanishi)

---

## 10. API GATEWAY KONFIGURATSIYASI

```
NGINX upstream konfiguratsiya (dizayn):

upstream aida_backend {
    least_conn;
    server backend-1:8000 weight=1;
    server backend-2:8000 weight=1;
    keepalive 32;
}

Rate limit zones:
  zone=anonymous:10m  rate=10r/m
  zone=authenticated:50m  rate=100r/m
  zone=premium:50m  rate=500r/m
  zone=enterprise:50m  rate=2000r/m

Timeout'lar:
  proxy_connect_timeout:  5s
  proxy_read_timeout:     120s (AI calls uchun)
  proxy_send_timeout:     30s
```

---

*Hujjat AIDA Development Bible — Book 1, Chapter 9 asosida tayyorlangan.*
