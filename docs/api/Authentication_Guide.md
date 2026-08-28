# AIDA Enterprise API Foundation
## Authentication Guide

**Versiya:** 1.0.0
**Sana:** 2026-07-03
**Muallif:** AIDA API Team

---

## 1. AUTHENTICATION ARXITEKTURASI

```
┌──────────────────────────────────────────────────────────────────┐
│                    AUTH METHODS                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  WEB APP          → JWT (Access + Refresh Token)                 │
│  MOBILE APP       → JWT (Access + Refresh Token)                 │
│  SDK / CLI        → Personal Access Token (PAT)                  │
│  EXTERNAL PLATFORM → API Key (X-AIDA-Key header)                │
│  SERVICE-TO-SERVICE → Internal Service Token                     │
│  ADMIN / STAFF    → JWT + MFA                                    │
│                                                                  │
│  OAuth2 Providers: GitHub, Google                                │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. JWT AUTHENTICATION

### 2.1 Token Tuzilishi

```
ACCESS TOKEN:
  Algorithm: RS256 (asymmetric — public key verification)
  Expiry:    15 daqiqa (production), 1 soat (development)
  Payload:
  {
    "sub": "user-uuid",
    "email_hash": "sha256-of-email",   ← PII: to'liq email emas
    "role": "user",
    "org_id": "org-uuid",
    "scopes": ["chat:read", "chat:write"],
    "iat": 1751534000,
    "exp": 1751534900,
    "jti": "unique-jwt-id"            ← Blacklist uchun
  }

REFRESH TOKEN:
  Algorithm: RS256
  Expiry:    30 kun
  Payload: minimal (sub, jti, exp)
  Saqlash:  HttpOnly, Secure, SameSite=Strict cookie

NIMA UCHUN RS256 (RSA):
  Asymmetric → Private key bilan sign, public key bilan verify
  Microservices uchun public key tarqatilishi mumkin
  HS256'da shared secret leak — barcha token'lar kompromi bo'ladi
  RS256'da private key faqat auth service'da
```

### 2.2 Token Lifecycle

```
1. Login:
   POST /api/v1/auth/login/
   Response:
     access_token  → Response body (localStorage'da saqlanishi mumkin)
     refresh_token → HttpOnly cookie (JS'dan ko'rinmaydi)

2. Request yuborish:
   Authorization: Bearer {access_token}

3. Access token eskirganda (401 Unauthorized):
   POST /api/v1/auth/token/refresh/
   Cookie: refresh_token={...}
   → Yangi access_token qaytariladi

4. Logout:
   POST /api/v1/auth/logout/
   → refresh_token cookie o'chiriladi
   → access_token JTI blacklist'ga qo'shiladi (Redis, 15 min TTL)

5. Forced logout (barcha qurilmalar):
   DELETE /api/v1/users/{id}/sessions/
   → Barcha refresh token'lar bekor qilinadi
```

### 2.3 Token Blacklist

```
Mexanizm:
  Redis SET: blacklist:{jti} = "1"
  TTL: access_token remaining expiry time

Har request'da:
  JWT verify (signature + expiry)
  Redis'da JTI mavjudligi tekshirish
  → Blacklist'da bo'lsa: 401 Unauthorized

Nima uchun Redis (DB emas):
  Har request'da tekshirish → microsecond latency kerak
  TTL = access token muddati → avtomatik tozalanadi
```

---

## 3. REFRESH TOKEN ROTATION

```
Rotation:
  Har refresh qilinganida yangi refresh_token yaratiladi
  Eski refresh_token bekor qilinadi

Leak Detection:
  Eski (allaqachon bekor qilingan) refresh_token ishlatilsa:
  → Barcha tokenlar bekor qilinadi
  → User login qilishga majbur
  → Security alert yaratiladi

Expiry:
  Aktiv foydalanish: 30 kun sliding window
  Inaktiv: 30 kundan keyin logout
```

---

## 4. API KEY AUTHENTICATION

### 4.1 API Key Tuzilishi

```
Format:  aida_sk_{random_32_chars}
Misol:   aida_sk_x7k2mN9pQrT4vYwZ8aB1cD3eFgH5jL6

Saqlash (DB):
  key_hash: SHA-256(api_key)  ← Faqat hash saqlanadi
  key_prefix: "aida_sk_x7k2"  ← Ko'rsatish uchun (oxirgi 4 belgi)

Ishlatilishi:
  Header: X-AIDA-Key: aida_sk_x7k2mN9p...

Lookup:
  Redis'da hash cache: apikey:{hash} → user_id (5 min TTL)
  Miss → DB'dan lookup, cache'ga yozish
```

### 4.2 API Key Scopes

```
Scope'lar:
  chat:read       → Chat o'qish
  chat:write      → Chat yaratish va yozish
  agent:read      → Agent holati ko'rish
  agent:run       → Agent ishga tushirish
  knowledge:read  → Knowledge o'qish
  knowledge:write → Knowledge qo'shish
  files:upload    → Fayl yuklash
  admin:*         → Barcha admin operatsiyalar

Default scope (platform keys): chat:read, chat:write
```

### 4.3 Request Signing (Optional)

```
Muhim API'lar uchun HMAC-SHA256 imzo:

Signature = HMAC-SHA256(
  key = api_secret,
  data = "{method}\n{path}\n{timestamp}\n{body_sha256}"
)

Headers:
  X-AIDA-Timestamp: 1751534000
  X-AIDA-Signature: sha256={base64_signature}

Tekshirish:
  |client_timestamp - server_time| <= 300 sek (5 min window)
  → Replay attack oldini oladi
```

---

## 5. OAUTH2 AUTHENTICATION

### 5.1 Qo'llab-quvvatlanadigan Provayderlar

```
GitHub OAuth2:
  Scopes: user:email, read:user, read:org
  Callback: /api/v1/auth/oauth2/github/callback/
  Use case: Developer users, repo import

Google OAuth2:
  Scopes: openid, email, profile
  Callback: /api/v1/auth/oauth2/google/callback/
  Use case: Enterprise users, SSO
```

### 5.2 OAuth2 Flow

```
1. Client: GET /api/v1/auth/oauth2/github/
   → Redirect to GitHub with state parameter

2. GitHub: User grants permission
   → Redirect to /api/v1/auth/oauth2/github/callback/?code=...&state=...

3. Server:
   → State verification (CSRF protection)
   → GitHub API: POST /login/oauth/access_token
   → User email fetch
   → User create/link in DB
   → JWT issuing → same as normal login

4. Client: Receives JWT tokens
```

### 5.3 OAuth2 State Parameter

```
State = base64({
  "csrf_token": random_32_bytes,
  "redirect_uri": "/dashboard",
  "timestamp": 1751534000
})

Redis'da 10 daqiqa saqlanadi:
  oauth_state:{csrf_token} = "1"

Callback'da:
  State decode qilinadi
  Redis'da mavjudligi tekshiriladi
  → CSRF attack himoyasi
```

---

## 6. PERSONAL ACCESS TOKEN (PAT)

```
Maqsad: SDK, CLI, CI/CD integration

PAT = API Key'ning maxsus ko'rinishi:
  Format:    aida_pat_{random_40_chars}
  Saqlash:   SHA-256 hash (api_keys jadvalida)
  Expiry:    Foydalanuvchi tanlaydi (30 kun / 1 yil / hech qachon)
  Scopes:    Yaratishda belgilanadi

Farqi API Key'dan:
  PAT — foydalanuvchi shaxsan uchun (developer, CLI)
  API Key — platforma integratsiyasi uchun (boshqa app)

Yaratish:
  POST /api/v1/users/{id}/api-keys/
  {
    "name": "My CLI Token",
    "scopes": ["chat:read", "chat:write"],
    "expires_in_days": 365,
    "type": "pat"
  }

Response (faqat bir marta ko'rsatiladi!):
  {
    "key": "aida_pat_...",   ← Bu yagona ko'rsatilish
    "id": "...",
    "prefix": "aida_pat_x7k2"
  }
```

---

## 7. RATE LIMITING

### 7.1 Rate Limit Siyosati

| Foydalanuvchi turi | Limit | Window | Burst |
|-------------------|-------|--------|-------|
| **Anonymous** | 10 req | 1 daqiqa | 20 |
| **Authenticated (free)** | 100 req | 1 daqiqa | 200 |
| **Premium** | 500 req | 1 daqiqa | 1000 |
| **Enterprise** | 2000 req | 1 daqiqa | 5000 |
| **Admin** | 10000 req | 1 daqiqa | 20000 |
| **AI Agent** | 200 req | 1 daqiqa | 500 |
| **Platform API Key** | 300 req | 1 daqiqa | 600 |

### 7.2 Endpoint-Specific Limits

| Endpoint | Limit | Window | Sabab |
|----------|-------|--------|-------|
| POST /auth/login/ | 5 req | 1 daqiqa | Brute force himoya |
| POST /auth/register/ | 3 req | 1 soat | Spam oldini olish |
| POST /messages/stream/ | 10 req | 1 daqiqa | AI compute cost |
| POST /embeddings/create/ | 50 req | 1 daqiqa | AI cost |
| POST /sandbox/python/execute/ | 20 req | 1 daqiqa | Compute cost |
| GET /files/{id}/download/ | 100 req | 1 soat | Bandwidth |

### 7.3 Token Bucket Algoritmi

```
Mexanizm:
  Har foydalanuvchi uchun Redis'da bucket:
    ratelimit:{user_id}:{window} = {count}
    TTL = window seconds

  Har request:
    count = INCR ratelimit:{user_id}:{window}
    EXPIRE ratelimit:{user_id}:{window} 60
    if count > limit: 429 Too Many Requests

  Sliding window (aniqroq):
    ratelimit:sliding:{user_id} = sorted set
    zadd timestamp:requestid
    zremrangebyscore 0 (now-60sec)
    count = zcard

Rate limit headers:
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 87
  X-RateLimit-Reset: 1751534060
  Retry-After: 45   (faqat 429 da)
```

### 7.4 IP-Based Rate Limiting

```
Anonymous foydalanuvchilar uchun IP bo'yicha:
  ratelimit:ip:{ip_subnet}  ← Subnet (192.168.x.x) ishlatiladi, to'liq IP emas

DDoS himoyasi:
  API Gateway darajasida (nginx / AWS WAF):
    limit_conn_zone $binary_remote_addr zone=conn:10m;
    limit_conn conn 20;           ← Bir vaqtda max 20 connection
    limit_req zone=global rate=1000r/s;  ← Global limit
```

---

## 8. SESSION TOKEN

```
Session token = Database'da saqlanadigan token (mobile apps)

Foydalanish holati:
  Mobile app'lar JWT'dan farqli o'laroq session-based bo'lishi mumkin

Format:    aida_sess_{random_64_chars}
Saqlash:   sessions jadvalida token_hash (SHA-256)
Expiry:    30 kun inaktiv bo'lganda

Auth flow:
  Login → Session yaratiladi → token bir marta ko'rsatiladi
  Har request: Header Authorization: Token {session_token}
  Server: SHA-256(token) → sessions jadvalida lookup

Farqi JWT'dan:
  JWT: stateless, DB tekshiruvi yo'q
  Session: stateful, har request'da DB/Redis lookup
  Afzallik: Istalgan vaqtda bekor qilish mumkin (JWT'da 15 min kutiladi)
```

---

## 9. MULTI-FACTOR AUTHENTICATION (MFA)

```
Qo'llab-quvvatlanadigan usullar:
  TOTP: Google Authenticator, Authy (RFC 6238)
  SMS: (optional, kaminchi xavfsizlik)
  Backup codes: 8 ta bir martalik kodlar

Majburiy MFA:
  Admin role: MAJBURIY
  Enterprise plan: Org admin tomonidan majburiy qilinishi mumkin

MFA Flow:
  1. Login (email + password) → 200 OK + "mfa_required": true + temp_token
  2. POST /api/v1/auth/mfa/verify/
     { "code": "123456", "temp_token": "..." }
  3. Muvaffaqiyatli → access_token + refresh_token

TOTP Secrets:
  DB'da AES-256 encrypt holda saqlanadi
  QR code bir marta ko'rsatiladi
```

---

## 10. XAVFSIZLIK QOIDALARI

```
Token Saqlash (Client Side):
  access_token:  → memory (localStorage xavfli — XSS)
  refresh_token: → HttpOnly Cookie (JS kirishi yo'q)
  API key:       → Foydalanuvchi o'zi xavfsiz saqlaydi

HTTPS Only:
  Barcha auth endpoint'lar HTTPS majburiy
  HTTP → 301 redirect HTTPS

Parol Talablari:
  Minimum: 8 belgi
  Tavsiya: 12+ belgi, uppercase + lowercase + raqam + belgi
  Hashing: Argon2id (time=2, memory=64MB, parallel=2)
  Eski parol qayta ishlatilishi: 3 ta oxirgi parol check

Account Lockout:
  5 muvaffaqiyatsiz login → 15 daqiqa lock
  10 muvaffaqiyatsiz → 1 soat lock
  20+ → Admin intervention kerak
  IP va account bo'yicha alohida tracking
```

---

*Hujjat AIDA Development Bible — Book 1, Chapter 9 asosida tayyorlangan.*
