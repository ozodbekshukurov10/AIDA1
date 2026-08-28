# AIDA Enterprise Database Architecture
## Database Security

**Versiya:** 1.0.0
**Sana:** 2026-07-03
**Muallif:** AIDA Database Team

---

## 1. SECURITY ARXITEKTURASI (DEFENSE IN DEPTH)

```
┌─────────────────────────────────────────────────────────────────┐
│                   DEFENSE IN DEPTH MODEL                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LAYER 6: APPLICATION                                           │
│    Django ORM (no raw SQL), Input validation, Auth middleware    │
│                         │                                       │
│  LAYER 5: ACCESS CONTROL                                        │
│    Database roles (RLS), Column-level, Row-level security       │
│                         │                                       │
│  LAYER 4: ENCRYPTION IN TRANSIT                                 │
│    TLS 1.3, mTLS (microservices), Certificate pinning           │
│                         │                                       │
│  LAYER 3: ENCRYPTION AT REST                                    │
│    AES-256, Column-level encryption, Key Management (Vault/KMS)  │
│                         │                                       │
│  LAYER 2: NETWORK                                               │
│    VPC, Private subnet, Security groups, IP whitelist           │
│                         │                                       │
│  LAYER 1: PHYSICAL / CLOUD                                      │
│    Cloud provider security, Hardware encryption (EBS)           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. ENCRYPTION AT REST

### 2.1 Disk darajasida shifrlash

```
Cloud:
  AWS RDS:   AES-256 (EBS encryption avtomatik)
  GCP:       Google-managed encryption keys (default)
  Azure:     Azure Disk Encryption

Self-hosted:
  OS-level:  LUKS (Linux Unified Key Setup) — AES-256-XTS
  PG-level:  pg_tde extension (PostgreSQL 17+) yoki Transparent Data Encryption
```

### 2.2 Qaysi Fieldlar MAJBURIY Shifrlanadi

```
HASHING (one-way, qaytarib bo'lmaydi):
  users.hashed_password     → Argon2id (Django default)
  sessions.token_hash       → SHA-256
  api_keys.key_hash         → SHA-256 (HMAC + secret salt)

  Nima uchun Argon2id:
    - Memory-hard: GPU brute force qiyinlashadi
    - time_cost=2, memory_cost=64MB, parallelism=2
    - Django: PASSWORD_HASHERS = ['django.contrib.auth.hashers.Argon2PasswordHasher']

ENCRYPTION (AES-256-GCM, reversible):
  users.email               → AES-256-GCM (login uchun lookup kerak)
  users.phone               → AES-256-GCM
  configurations.value      → AES-256-GCM (is_secret=TRUE bo'lganlar)
  api_keys.custom_instructions → AES-256-GCM (agar maxfiy)

  Nima uchun AES-256-GCM:
    - Authenticated encryption (data integrity ham ta'minlanadi)
    - Nonce (IV) har encryption'da random
    - GCM mode parallel ishlaydi (fast)

MASKING (ko'rsatish uchun):
  email:     "user@example.com" → "u***@e***.com"
  phone:     "+998901234567"    → "+99890*****"
  ip_masked: "192.168.1.100"   → "192.168.x.x"
  api_key:   "aida_sk_abc123"  → "aida_sk_***"
```

### 2.3 Key Management

```
Development:
  .env fayl → SECRET_KEY, DB_ENCRYPTION_KEY
  Hech qachon git'ga push qilinmaydi

Staging / Production:
  HashiCorp Vault yoki AWS KMS yoki Azure Key Vault

Key Rotation Siyosati:
  Har 90 kunda avtomatik key rotation
  Rotation jarayoni:
    1. Yangi key generatsiya
    2. Yangi key bilan re-encrypt (background job)
    3. Eski key deprecated (o'chirilmaydi — eski ma'lumotlar uchun)
    4. 30 kun keyni eski key o'chiriladi

Django implementation (konsepsiya):
  class EncryptedField:
      def encrypt(self, value, key_id='current'):
          key = KeyManager.get_key(key_id)
          nonce = os.urandom(12)
          cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
          ciphertext, tag = cipher.encrypt_and_digest(value.encode())
          return base64.b64encode(nonce + tag + ciphertext).decode()
```

---

## 3. ENCRYPTION IN TRANSIT

```
PostgreSQL Connection:
  sslmode = verify-full     (production)
  sslmode = require         (minimum acceptable)
  sslmode = disable         (TAQIQLANGAN production'da)

SSL Versiyasi:
  ssl_min_protocol_version = TLSv1.2   (minimum)
  ssl_max_protocol_version = TLSv1.3   (tavsiya)
  TLS 1.0 va 1.1 O'CHIRILGAN

Cipher Suites (tavsiya):
  TLS_AES_256_GCM_SHA384       (TLS 1.3)
  TLS_CHACHA20_POLY1305_SHA256 (TLS 1.3)

PgBouncer → PostgreSQL:
  server_tls_sslmode = verify-full
  server_tls_ca_file = /etc/ssl/certs/ca.crt

Application → PgBouncer:
  client_tls_sslmode = require
  client_tls_key_file = /etc/ssl/private/pgbouncer.key
  client_tls_cert_file = /etc/ssl/certs/pgbouncer.crt

Microservices (optional mTLS):
  Mutual TLS — har ikki tomon ham sertifikat taqdim etadi
  Service mesh: Istio / Linkerd avtomatik mTLS
```

---

## 4. DATABASE-LEVEL ACCESS CONTROL

### 4.1 PostgreSQL Roles

```
ROLE: aida_app
  Maqsad: Asosiy application user (Django)
  Ruxsatlar:
    SELECT, INSERT, UPDATE, DELETE — barcha application jadvallari
    EXECUTE — application functions
    USAGE — sequences
  Taqiqlar:
    DDL (CREATE, ALTER, DROP) — TAQIQLANGAN
    GRANT/REVOKE — TAQIQLANGAN
    pg_catalog, information_schema — TAQIQLANGAN

ROLE: aida_readonly
  Maqsad: Analytics, reporting, monitoring
  Ruxsatlar:
    SELECT — barcha jadvallar
  Taqiqlar:
    INSERT, UPDATE, DELETE — TAQIQLANGAN

ROLE: aida_migration
  Maqsad: Faqat migration vaqtida
  Ruxsatlar:
    DDL: CREATE TABLE, ALTER TABLE, CREATE INDEX, DROP
    DML: barcha
  Qoida: Faqat migration window'da aktiv, keyin REVOKE

ROLE: aida_backup
  Maqsad: pg_dump jarayoni
  Ruxsatlar:
    SELECT — barcha jadvallar
    pg_read_all_data built-in role
  Taqiqlar:
    DML, DDL — TAQIQLANGAN

ROLE: aida_monitor
  Maqsad: Prometheus postgres_exporter
  Ruxsatlar:
    SELECT ON pg_stat_user_tables, pg_stat_user_indexes
    pg_monitor built-in role
  Taqiqlar:
    Hech qanday user data ko'rinmaydi

ROLE: aida_admin
  Maqsad: Emergency DBA operations
  Ruxsatlar: SUPERUSER
  Qoida:
    Faqat 2 kishi ushbu rolega ega
    Har foydalanish audit_log'ga yoziladi
    MFA (multi-factor auth) majburiy
    Production'da direct login TAQIQLANGAN (bastion host orqali)
```

### 4.2 Row-Level Security (RLS)

```
Multi-tenant izolyatsiya uchun RLS:

projects jadvali:
  Policy: user_sees_own_org_projects
  USING:
    org_id IN (
      SELECT org_id FROM organization_members
      WHERE user_id = current_setting('app.current_user_id')::uuid
    )

chats jadvali:
  Policy: user_sees_own_chats
  USING:
    user_id = current_setting('app.current_user_id')::uuid

messages jadvali:
  Policy: user_sees_own_messages
  USING:
    chat_id IN (
      SELECT id FROM chats
      WHERE user_id = current_setting('app.current_user_id')::uuid
    )

RLS yoqish:
  ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
  ALTER TABLE projects FORCE ROW LEVEL SECURITY;
  -- FORCE: table owner ham policy'ga bo'ysunadi

Django integration:
  class DatabaseRouter:
      def db_for_read(self, model, **hints):
          connection.cursor().execute(
              "SET app.current_user_id = %s", [request.user.id]
          )
```

### 4.3 Column-Level Security

```
Maxfiy ustunlar faqat kerakli rolelarga ko'rinadi:

users.hashed_password:
  REVOKE SELECT ON COLUMN users.hashed_password FROM aida_app;
  -- Application hech qachon hash'ni o'qimaydi (faqat Auth service)

users.email (agar encrypted):
  REVOKE SELECT ON COLUMN users.email FROM aida_readonly;
  -- Analytics foydalanuvchi email'ini ko'rmaydi

configurations.value (is_secret=TRUE):
  Application-level: is_secret=TRUE qiymatlarni decrypt qilish
  faqat authorized service'lar uchun
```

---

## 5. SENSITIVE DATA MASKING

### 5.1 Masking Qoidalari

```
Dashboard, log va API response'larda:

email:
  "user@example.com"   →   "u***@e***.com"
  Pattern: first_char + *** + @ + first_domain_char + ***. + tld

phone:
  "+998901234567"      →   "+99890*****67"
  Pattern: country code + first 2 + ***** + last 2

ip_address:
  "192.168.1.100"      →   "192.168.x.x"
  Pattern: Keep first two octets, replace last two

api_key:
  "aida_sk_abc123xyz"  →   "aida_sk_***"
  Pattern: Keep prefix (aida_sk_), replace rest

password:
  any value            →   "[REDACTED]"

jwt_token:
  any value            →   "[TOKEN MASKED]"

credit_card:
  "4532015112830366"   →   "**** **** **** 0366"
```

### 5.2 Django Masking Middleware (Dizayn)

```python
# Barcha log yozuvlarida va API response'larda avtomatik masking

SENSITIVE_FIELDS = {
    'password', 'hashed_password', 'token', 'secret',
    'api_key', 'key', 'authorization', 'cookie', 'credit_card'
}

def mask_sensitive_data(data: dict) -> dict:
    """Recursive dict ichidagi maxfiy fieldlarni masklaydi"""
    result = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
            result[key] = '[REDACTED]'
        elif isinstance(value, dict):
            result[key] = mask_sensitive_data(value)
        elif isinstance(value, list):
            result[key] = [mask_sensitive_data(v) if isinstance(v, dict) else v
                          for v in value]
        else:
            result[key] = value
    return result
```

---

## 6. AUDIT TRAIL

### 6.1 Qaysi Operatsiyalar Log Qilinadi

```
AUTHENTICATION:
  user.login.success        → kim, qachon, qayerdan (subnet)
  user.login.failure        → sabab, urinish soni
  user.logout               → session ID (masked)
  user.password_change      → kim, qachon
  user.mfa_enabled/disabled → kim, qachon

AUTHORIZATION:
  permission.violation      → kim, nima qilmoqchi edi, qayerda
  role.change               → kim o'zgardi, eski rol, yangi rol, kim o'zgartirdi

DATA CHANGES (muhim entitylar):
  users.create/update/delete
  organizations.*
  projects.*
  agents.*
  workflows.*
  models.*
  providers.*
  plugins.*
  configurations.*
  api_keys.create/revoke

SECURITY EVENTS:
  api_key.invalid_attempt   → key prefix (masked), source subnet
  rate_limit.triggered      → endpoint, source subnet
  suspicious.activity       → tur, manbaa
  data.export               → kim, nima, qancha

SYSTEM:
  migration.run             → migration nomi, kim, natija
  backup.completed          → tur, hajm, davomiyligi
  config.change             → kalit, eski qiymat hash, yangi qiymat hash
```

### 6.2 AuditLog Immutability

```
Audit log o'chirib yoki o'zgartirib bo'lmasligi uchun:

USUL 1: PostgreSQL RLS + Trigger
  CREATE RULE no_update_audit AS ON UPDATE TO audit_logs DO INSTEAD NOTHING;
  CREATE RULE no_delete_audit AS ON DELETE TO audit_logs DO INSTEAD NOTHING;

USUL 2: aida_app rolega faqat INSERT
  GRANT INSERT ON audit_logs TO aida_app;
  REVOKE UPDATE, DELETE ON audit_logs FROM aida_app;

USUL 3: S3 Object Lock (backup)
  Audit log backup'lari S3 Compliance mode bilan lock qilinadi
  365 kun davomida hech kim o'chira olmaydi

pg_audit Extension:
  PostgreSQL'ning built-in audit extensioni
  DDL va DML operatsiyalarini avtomatik loglayd
  pgaudit.log = 'ddl, write, role'
```

### 6.3 Audit Log Retention

```
Retention:   365 kun (1 yil)
Arxivlash:   Choraklik partition'lar S3 Glacier'ga ko'chiriladi
Format:      JSONB (structured, queryable)
Immutable:   Ha (o'chirib/o'zgartirib bo'lmaydi)
Encryption:  AES-256 at rest
Compression: Glacierga yuklashdan oldin gzip

GDPR:
  User so'rovida — audit log qoladi, lekin user ID anonymize qilinadi
  Log qiymati saqlangani holda user ID NULL qilinadi
```

---

## 7. SQL INJECTION HIMOYASI

### 7.1 Django ORM — Asosiy Himoya

```python
# ✅ XAVFSIZ — Parametrized query (Django ORM)
users = User.objects.filter(email=email)

# ✅ XAVFSIZ — Raw query parametrized
users = User.objects.raw('SELECT * FROM users WHERE email = %s', [email])

# ❌ XAVFLI — String formatting
users = User.objects.raw(f'SELECT * FROM users WHERE email = {email}')

# ❌ XAVFLI — format
query = "SELECT * FROM users WHERE email = '%s'" % email

Qoida: Raw SQL FAQAT Django ORM qila olmagan holatlarda,
       va FAQAT parametrized (%s) bilan.
```

### 7.2 Input Validation

```python
# Barcha API input Django Serializer / Form orqali validate qilinadi
# Serializer'da:
class ChatSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=500, strip=True)
    # strip=True: leading/trailing whitespace olib tashlaydi
    # max_length: buffer overflow oldini oladi

# Email uchun:
email = serializers.EmailField()  # RFC 5322 format tekshiruvi

# UUID uchun:
id = serializers.UUIDField()  # Faqat valid UUID qabul qilinadi
```

### 7.3 WAF (Web Application Firewall)

```
Production'da WAF o'rnatilishi tavsiya qilinadi:
  AWS WAF — managed rules (SQL Injection, XSS)
  Cloudflare WAF — OWASP Core Rule Set
  ModSecurity — self-hosted

WAF qoidalari:
  SQL_INJECTION_MATCH: Blok
  XSS_MATCH: Blok
  BAD_BOTS: Blok yoki CAPTCHA
```

---

## 8. CONNECTION SECURITY

### 8.1 pg_hba.conf (Dizayn)

```
# Connection security rules

# Local socket — faqat postgres user
local   all   postgres   peer

# App user — SSL mandatory, faqat VPC network
hostssl   aida_db   aida_app       10.0.0.0/8   scram-sha-256
hostssl   aida_db   aida_readonly  10.0.0.0/8   scram-sha-256
hostssl   aida_db   aida_monitor   10.0.0.0/8   scram-sha-256

# Migration — faqat CI/CD subnet
hostssl   aida_db   aida_migration  10.0.1.0/24   scram-sha-256

# Barcha boshqa connection'lar rad etiladi
host   all   all   0.0.0.0/0   reject
```

### 8.2 Connection Limits

```
Per-role connection limits:
  aida_app:       max_connections = 100
  aida_readonly:  max_connections = 20
  aida_monitor:   max_connections = 5
  aida_migration: max_connections = 5
  aida_backup:    max_connections = 3

Idle connection timeout:
  tcp_keepalives_idle    = 60   (saniya)
  tcp_keepalives_interval = 10
  tcp_keepalives_count   = 6

PgBouncer:
  server_idle_timeout = 600   (10 daqiqa)
  client_idle_timeout = 300   (5 daqiqa)
```

---

## 9. VULNERABILITY MANAGEMENT

```
PostgreSQL Update Siyosati:
  Kritik CVE (CVSS 9+): 24 soat ichida patch
  Yuqori CVE (CVSS 7-9): 7 kun ichida
  O'rta CVE (CVSS 4-7):  30 kun ichida
  Past CVE (CVSS < 4):   Keyingi scheduled update

CVE Monitoring:
  PostgreSQL security announcements: postgresql.org/support/security
  Avtomatik CVE scanner: Trivy, Grype, Snyk

Extension Security:
  Faqat tekshirilgan extensionlar: pgvector, pgcrypto, pg_audit, pgBackRest
  Har yangi extension uchun security review majburiy
```

---

## 10. COMPLIANCE

### 10.1 GDPR

```
Article 25 — Privacy by Design:
  ✅ Default minimal ma'lumot yig'ish
  ✅ PII encryption at rest
  ✅ Access control (faqat kerakli rol ko'radi)
  ✅ Retention policy (avtomatik o'chirish)

Article 32 — Security of Processing:
  ✅ Encryption at rest va in transit
  ✅ Audit trail
  ✅ Backup va recovery
  ✅ Regular security testing

Article 17 — Right to Erasure:
  Jarayon:
    1. Foydalanuvchi so'rov yuboradi
    2. 30 kun ichida bajarilishi shart
    3. users.email → anonymized (user_{id}@deleted.aida.ai)
    4. users.first_name, last_name → "Deleted User"
    5. audit_logs.user_id → NULL qoladi (log saqlanganda ID yo'q)
    6. Backup'lardagi ma'lumotlar — retention tugaguncha qoladi (GDPR 17(3)(b))
    7. Foydalanuvchiga yozma tasdiqlash xati yuboriladi
```

### 10.2 SOC 2 Type II Considerations

```
Security:
  ✅ Access control (roles, RLS)
  ✅ Encryption
  ✅ Audit logging
  ✅ Vulnerability management

Availability:
  ✅ HA deployment (primary + replica)
  ✅ Backup + DR
  ✅ Monitoring + alerting

Confidentiality:
  ✅ Data classification
  ✅ Encryption (sensitive fields)
  ✅ Access logging
```

---

## 11. INCIDENT RESPONSE

```
Data Breach aniqlanganda:

DARHOL (0-1 soat):
  □ Incident Management'ga xabar berish
  □ Affected DB connection'larni bloklash
  □ Audit log'dan breach scope'ini aniqlash
  □ Evidence preservation (snapshot, logs)

QISQA MUDDATDA (1-24 soat):
  □ Vulnerability patch qilish
  □ Affected user'larni aniqlash
  □ Compromise scope assessment
  □ Temporary mitigations

GDPR NOTIFICATION (72 soat ichida):
  □ DPA (Data Protection Authority) ga xabar berish
  □ Affected users'ga xabar berish (agar kerak)
  □ Incident report tayyorlash

POST-INCIDENT:
  □ Root cause analysis
  □ Security controls yaxshilash
  □ Staff training
  □ Policy yangilash
```

---

## 12. SECURITY CHECKLIST (Deploy Oldidan)

```
DATABASE:
[ ] PostgreSQL eng yangi patch versiyasida
[ ] pg_hba.conf IP whitelist sozlangan
[ ] SSL mode verify-full (production)
[ ] Barcha default parollar o'zgartirilgan
[ ] aida_admin roli faqat zarur kishilarda

APPLICATION:
[ ] DB credentials .env faylda (git'da yo'q)
[ ] Connection string TLS rejimida
[ ] Django ORM ishlatiladi (raw SQL yo'q)
[ ] Input validation barcha endpointlarda

ENCRYPTION:
[ ] Sensitive fields encrypted (email, phone)
[ ] Password hashing Argon2id
[ ] API keys faqat hash saqlanadi
[ ] Key Management (Vault/KMS) sozlangan

AUDIT:
[ ] pg_audit extension yoqilgan
[ ] AuditLog jadval immutable (UPDATE/DELETE taqiqlangan)
[ ] Audit log retention 365 kun
[ ] S3 Object Lock (audit backup)

MONITORING:
[ ] Failed login alerts sozlangan
[ ] Suspicious activity detection
[ ] Unauthorized DB connection alert
[ ] Data export monitoring
```

---

*Hujjat AIDA Development Bible — Book 1, Chapter 8 asosida tayyorlangan.*
