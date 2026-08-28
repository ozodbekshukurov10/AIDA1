# AIDA — Security Logging System

## 1. Design Principles

Security logs — AIDA xavfsizlik tizimining asosiy audit manbai. Har bir xavfsizlik hodisasi **append-only**, **tamper-evident** tarzda qayd qilinadi va hech qachon o'chirilmaydi.

```
┌──────────────────────────────────────────────────────────┐
│              SECURITY LOGGING PRINCIPLES                 │
│                                                          │
│  ✅ Log everything — barcha auth hodisalari             │
│  ✅ Never trust client — server-side validation          │
│  ✅ Never log secrets — API keys, passwords redacted     │
│  ✅ Always log context — IP, user agent, session         │
│  ✅ Separate storage — security log ≠ application log    │
│  ✅ Real-time alerting — CRITICAL events → immediate     │
│  ✅ Immutable — append-only, no deletion                 │
└──────────────────────────────────────────────────────────┘
```

**Current State**: Hech qanday security logging mavjud emas. `webapp/security.py` dagi `authenticate_access_key()` va `RateLimiter` hech qanday log yozmaydi.

## 2. Security Event Categories

### 2.1 Authentication Events

| Event | Description | Severity | Alert |
|-------|-------------|----------|-------|
| `auth.login.success` | Muvaffaqiyatli login | INFO | No |
| `auth.login.failed` | Login urinishi muvaffaqiyatsiz | WARNING | After 5 failures |
| `auth.login.blocked` | Hisob bloklandi (ko'p urinish) | CRITICAL | Yes |
| `auth.logout` | Tizimdan chiqish | INFO | No |
| `auth.password.changed` | Parol o'zgartirildi | HIGH | Yes |
| `auth.password.reset` | Parol tiklandi | HIGH | Yes |
| `auth.token.issued` | Token berildi | INFO | No |
| `auth.token.refreshed` | Token yangilandi | INFO | No |
| `auth.token.revoked` | Token bekor qilindi | HIGH | Yes |
| `auth.token.expired` | Token muddati tugadi | LOW | No |
| `auth.session.created` | Yangi sessiya yaratildi | INFO | No |
| `auth.session.terminated` | Sessiya tugatildi | MEDIUM | No |
| `auth.mfa.required` | MFA talab qilindi | INFO | No |
| `auth.mfa.failed` | MFA muvaffaqiyatsiz | WARNING | After 3 failures |

```json
{
  "event": "auth.login.failed",
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "severity": "WARNING",
  "actor": {
    "username": "unknown_user",
    "ip_address": "203.0.113.42",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "country": "RU",
    "asn": "AS12345"
  },
  "target": {
    "method": "password",
    "provider": "local"
  },
  "details": {
    "failure_reason": "invalid_password",
    "attempt_number": 3,
    "throttle_remaining_seconds": 30
  },
  "risk_score": 0.45,
  "tags": ["brute_force_suspected"]
}
```

### 2.2 API Key Events

| Event | Description | Severity | Alert |
|-------|-------------|----------|-------|
| `apikey.created` | API key yaratildi | HIGH | Yes |
| `apikey.revoked` | API key bekor qilindi | HIGH | Yes |
| `apikey.used` | API key ishlatildi | INFO | No |
| `apikey.used.blocked` | Bloklangan API key ishlatildi | HIGH | Yes |
| `apikey.expired` | API key muddati tugadi | LOW | No |
| `apikey.rotation` | API key rotatsiya qilindi | HIGH | Yes |

```json
{
  "event": "apikey.created",
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "severity": "HIGH",
  "actor": {
    "user_id": "user_admin_001",
    "username": "admin@example.com",
    "ip_address": "192.168.1.100"
  },
  "target": {
    "key_name": "ci-cd-pipeline",
    "key_prefix": "aida_sk_abc...",
    "permissions": ["chat:write", "agent:read"],
    "expires_at": "2027-07-03T12:00:00Z"
  },
  "source": "admin_ui"
}
```

### 2.3 Access Control Events

| Event | Description | Severity | Alert |
|-------|-------------|----------|-------|
| `access.permitted` | Ruxsat berildi | INFO | No |
| `access.denied` | Ruxsat berilmadi | WARNING | No |
| `access.denied.unauthorized` | Avtorizatsiyasiz urinish | HIGH | Yes |
| `access.role.changed` | Rol o'zgartirildi | CRITICAL | Yes |
| `access.permission.granted` | Ruxsat berildi | HIGH | Yes |
| `access.permission.revoked` | Ruxsat olib tashlandi | HIGH | Yes |
| `access.admin.used` | Admin huquqlari ishlatildi | HIGH | Yes |

```json
{
  "event": "access.denied.unauthorized",
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "severity": "HIGH",
  "actor": {
    "user_id": "user_guest_001",
    "username": "guest@external.com",
    "ip_address": "198.51.100.23",
    "roles": ["viewer"]
  },
  "target": {
    "resource": "api/v1/admin/config",
    "method": "PUT",
    "required_role": "admin",
    "actual_role": "viewer"
  },
  "details": {
    "reason": "Insufficient permissions",
    "similar_attempts_last_hour": 7
  },
  "risk_score": 0.72
}
```

### 2.4 Token Validation Events

| Event | Description | Severity | Alert |
|-------|-------------|----------|-------|
| `token.validated` | Token tekshirildi | INFO | No |
| `token.invalid` | Token noto'g'ri | WARNING | No |
| `token.expired` | Token muddati tugagan | LOW | No |
| `token.tampered` | Token buzilgan | CRITICAL | Yes |
| `token.reused` | Token qayta ishlatilgan | CRITICAL | Yes |
| `token.malformed` | Token formati noto'g'ri | LOW | No |

```json
{
  "event": "token.tampered",
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "severity": "CRITICAL",
  "actor": {
    "ip_address": "45.33.32.156",
    "user_agent": "python-requests/2.31.0"
  },
  "target": {
    "token_type": "JWT",
    "failure_reason": "signature_mismatch",
    "algorithm_claimed": "HS256",
    "algorithm_expected": "HS256"
  },
  "details": {
    "token_jti": "tok_abc123",
    "iat_claim": "2026-07-03T11:00:00Z",
    "ip_geolocation": "United States, California"
  },
  "risk_score": 0.95
}
```

### 2.5 Secret Access Events

| Event | Description | Severity | Alert |
|-------|-------------|----------|-------|
| `secret.accessed` | Secret o'qildi | HIGH | Yes |
| `secret.accessed.unauthorized` | Ruxsatsiz secret o'qish | CRITICAL | Yes |
| `secret.rotated` | Secret rotatsiya qilindi | CRITICAL | Yes |
| `secret.expired` | Secret muddati tugadi | HIGH | Yes |
| `secret.leak_detected` | Secret sizib chiqishi aniqlandi | CRITICAL | Yes |

```json
{
  "event": "secret.accessed",
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "severity": "HIGH",
  "actor": {
    "service": "ModelGateway",
    "hostname": "aida-api-pod-3",
    "request_id": "req_def456"
  },
  "target": {
    "secret_name": "models.openai.api_key",
    "access_pattern": "startup_load",
    "access_count_today": 15
  }
}
```

### 2.6 Rate Limiting Events

| Event | Description | Severity | Alert |
|-------|-------------|----------|-------|
| `ratelimit.approaching` | Limitga yaqinlashish (80%) | LOW | No |
| `ratelimit.reached` | Limitga yetildi | WARNING | No |
| `ratelimit.exceeded` | Limit oshib ketdi | WARNING | No |
| `ratelimit.exceeded.repeated` | Qayta-qayta limit oshirildi | HIGH | Yes |
| `ratelimit.bypass_attempted` | Limitni chetlab o'tish urinishi | CRITICAL | Yes |

```json
{
  "event": "ratelimit.exceeded",
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "severity": "WARNING",
  "actor": {
    "ip_address": "10.0.0.42",
    "api_key_prefix": "aida_sk_abc...",
    "user_id": "user_batch_001"
  },
  "target": {
    "limit_name": "chat_requests_per_minute",
    "limit_value": 30,
    "actual_value": 47,
    "window_seconds": 60,
    "retry_after_seconds": 45
  },
  "details": {
    "burst_mode": true,
    "consecutive_violations": 2
  }
}
```

## 3. Security Log Schema

### 3.1 Standard Security Event

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "event_id", "event", "timestamp", "severity", "actor", "target", "risk_score"
  ],
  "properties": {
    "event_id": {"type": "string", "format": "uuid"},
    "event": {"type": "string", "pattern": "^[a-z]+\\.[a-z]+\\.[a-z]+$"},
    "timestamp": {"type": "string", "format": "date-time"},
    "severity": {"type": "string", "enum": ["LOW", "INFO", "WARNING", "HIGH", "CRITICAL"]},
    "actor": {
      "type": "object",
      "properties": {
        "user_id": {"type": "string"},
        "username": {"type": "string"},
        "ip_address": {"type": "string", "format": "ip"},
        "user_agent": {"type": "string"},
        "session_id": {"type": "string"},
        "roles": {"type": "array", "items": {"type": "string"}},
        "country": {"type": "string"},
        "asn": {"type": "string"}
      }
    },
    "target": {
      "type": "object",
      "properties": {
        "resource": {"type": "string"},
        "method": {"type": "string"},
        "action": {"type": "string"}
      }
    },
    "details": {"type": "object"},
    "risk_score": {"type": "number", "minimum": 0, "maximum": 1},
    "tags": {"type": "array", "items": {"type": "string"}},
    "source_ip": {"type": "string", "format": "ip"}
  }
}
```

## 4. Risk Scoring

Har bir security hodisa `risk_score` (0.0 — 1.0) bilan baholanadi:

| Factor | Weight | Example |
|--------|--------|---------|
| Unknown IP | +0.2 | First time seeing this IP |
| High-risk country | +0.3 | IP from sanctioned country |
| Tor/VPN detected | +0.4 | Proxy/VPN/anonymizer |
| Off-hours access | +0.1 | 03:00 AM local time |
| Previous violations | +0.15 per violation | History of failed attempts |
| Sensitive resource | +0.3 | Admin API, secrets, config |
| Brute force pattern | +0.5 | >10 attempts in 5 minutes |
| Known attack pattern | +0.6 | SQL injection, path traversal |

**Risk thresholds:**
- `0.0 – 0.3`: Normal — log only
- `0.3 – 0.6`: Suspicious — log + additional verification
- `0.6 – 0.8`: High risk — log + block + alert
- `0.8 – 1.0`: Critical — log + block + immediate alert + escalate

## 5. Security Log Storage

### 5.1 File Structure

```
logs/security/
├── security.2026-07-03.jsonl       # All security events (daily)
├── incidents.2026-07-03.jsonl      # HIGH+ severity (real-time)
├── auth.2026-07-03.jsonl           # Authentication events only
├── apikey.2026-07-03.jsonl         # API key events only
├── alerts.log                      # Real-time alert log
└── archive/
    └── security.2026-06.jsonl.gz   # Monthly archives
```

### 5.2 Retention

| Severity | Hot Storage | Archive | Total |
|----------|-------------|---------|-------|
| LOW/INFO | 30 days | 1 year | 1 year |
| WARNING | 90 days | 3 years | 3 years |
| HIGH | 1 year | 7 years | 7 years |
| CRITICAL | 2 years | 10 years | 10 years |

## 6. SIEM Integration

### 6.1 Supported Formats

| SIEM | Format | Protocol | Configuration |
|------|--------|----------|---------------|
| Splunk | JSON | HTTP Event Collector (HEC) | `AIDA_SIEM_SPLUNK_URL` |
| ELK Stack | JSON | Logstash TCP | `AIDA_SIEM_LOGSTASH_HOST` |
| QRadar | LEEF | Syslog TCP | `AIDA_SIEM_QRAADAR_HOST` |
| ArcSight | CEF | Syslog TCP | `AIDA_SIEM_ARCSIGHT_HOST` |
| Datadog | JSON | HTTP | `AIDA_SIEM_DATADOG_API_KEY` |

### 6.2 Alerting Rules

```yaml
rules:
  - name: brute_force_detection
    condition: "auth.login.failed > 5 in 5 minutes from same IP"
    action: block_ip
    duration: 30m

  - name: impossible_travel
    condition: "auth.login.success from country A then country B in < 10 minutes"
    action: challenge_mfa

  - name: api_key_abuse
    condition: "ratelimit.exceeded.repeated > 3 in 1 hour same API key"
    action: revoke_key

  - name: token_replay
    condition: "token.reused detected"
    action: revoke_all_tokens + alert

  - name: secret_leak
    condition: "secret.leak_detected"
    action: rotate_secret + alert + audit
```

## 7. Implementation Priority

| Phase | Component | Priority | Effort |
|-------|-----------|----------|--------|
| P0 | API key authentication logging (`apikey.used`) | CRITICAL | Small |
| P0 | Login success/failure logging | CRITICAL | Small |
| P0 | Rate limit exceeded logging | CRITICAL | Small |
| P1 | Separate security log file handler | HIGH | Medium |
| P1 | Token validation logging | HIGH | Small |
| P1 | Access denied logging | HIGH | Small |
| P2 | Risk scoring engine | MEDIUM | Large |
| P2 | IP geolocation enrichment | MEDIUM | Medium |
| P2 | Admin action logging | MEDIUM | Medium |
| P3 | SIEM integration (Splunk, ELK) | LOW | Large |
| P3 | Auto-blocking rules engine | LOW | Large |
| P3 | Real-time security dashboard | LOW | Large |
