# AIDA Enterprise Database Architecture
## Database Architecture

**Versiya:** 1.0.0
**Sana:** 2026-07-03
**Muallif:** AIDA Database Team
**Holat:** Production-Ready Design

---

## 1. EXECUTIVE SUMMARY

AIDA tizimi millionlab foydalanuvchilar, milliardlab chat xabarlari, ko'plab AI agentlar va vektorli xotiralarni boshqarishga mo'ljallangan. Arxitektura quyidagi asosiy maqsadlarni ko'zlaydi:

- **Ishonchlilik:** ACID compliance, MA'LUMOT YO'QOLMAYDI
- **Tezlik:** ms darajasida query response, vector similarity search
- **Kengaytirilish:** Millionlardan milliardlarga o'sish imkoni
- **Xavfsizlik:** Encryption at rest + in transit, RLS, audit trail
- **Cloud Ready:** AWS / GCP / Azure ga deploy qilish imkoni

---

## 2. DATABASE STACK

```
┌─────────────────────────────────────────────────────────────────┐
│                    AIDA DATABASE STACK                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │          PRIMARY: PostgreSQL 16                          │   │
│  │  • ACID compliance                                       │   │
│  │  • JSONB fields (AI config, metadata)                    │   │
│  │  • Full-text search (tsvector/tsquery)                   │   │
│  │  • Table partitioning (messages, logs)                   │   │
│  │  • pgvector extension (embedding storage)               │   │
│  │  • Row-Level Security (multi-tenant)                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  VECTOR DB   │  │  CACHE DB    │  │   SESSION DB         │   │
│  │  pgvector    │  │  Redis 7     │  │   Redis 7 (DB 1)     │   │
│  │  (embedded   │  │  • App cache │  │   • Session tokens   │   │
│  │   in PG)     │  │  • Rate limit│  │   • JWT blacklist    │   │
│  │  OR Qdrant   │  │  • Pub/Sub   │  │   • Temp state       │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ ANALYTICS DB │  │   LOG DB     │  │  KNOWLEDGE DB        │   │
│  │  ClickHouse  │  │   Loki /     │  │  PostgreSQL + FTS    │   │
│  │  (optional)  │  │   Elastic    │  │  + pgvector          │   │
│  │  • Events    │  │   (optional) │  │  • Semantic search   │   │
│  │  • Metrics   │  │   • App logs │  │  • Document chunks   │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.1 PostgreSQL 16 — Primary Database

**Nima uchun tanlandi:**
- Django ORM bilan mukammal integratsiya
- JSONB \u2014 AI config va metadata uchun schema-flexible storage
- pgvector extension \u2014 alohida Vector DB kerak emas (boshlang'ich bosqich)
- Partitioning \u2014 messages va logs jadvallarini partition qilish
- Full-text search \u2014 knowledge va document qidiruvi
- Row-Level Security \u2014 multi-tenant izolyatsiya

**Muqobillari:** MySQL 8, CockroachDB, Supabase
**Tradeoff:** MySQL dan ko'ra murakkab, lekin JSONB va pgvector afzalligi hal qiluvchi

### 2.2 Redis 7 — Cache + Session Database

**Nima uchun tanlandi:**
- In-memory \u2014 nanosecond latency
- Django cache backend sifatida to'liq qo'llab-quvvatlanadi
- Pub/Sub \u2014 real-time agent communication uchun
- Lua scripting \u2014 atomic rate limiting
- Persistence (RDB + AOF) \u2014 restart safe

**Redis DB ajratish:**
```
DB 0: Application cache (model configs, frequently read data)
DB 1: Session storage (user sessions, JWT blacklist)
DB 2: Rate limiting (API request counters)
DB 3: Task queue (Celery broker)
DB 4: Pub/Sub channels (agent events)
```

### 2.3 pgvector — Vector Database

**Nima uchun tanlandi:**
- PostgreSQL ichida ishlaydi \u2014 alohida servis kerak emas
- ACID transaction ichida vector + relational join
- IVFFlat va HNSW index \u2014 million scale search
- Django ORM bilan ishlaydi

**Kengaytirish uchun muqobil (10M+ vectors):** Qdrant (dedicated vector DB)

**Tradeoff:** pgvector PostgreSQL resurslarini baham ko'radi. Juda katta hajmda Qdrant ajratilgan servis sifatida afzal.

### 2.4 ClickHouse — Analytics (Optional)

**Qachon kerak:** Kunlik 100M+ event bo'lganda
**Maqsad:** Usage analytics, cost tracking, performance reports
**Muqobil:** TimescaleDB (PostgreSQL extension, osonroq)

---

## 3. ARXITEKTURA DIAGRAMI

```
                        ┌─────────────────────┐
                        │   AIDA Application  │
                        │   (Django Backend)   │
                        └──────────┬──────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
   ┌──────────────────┐  ┌─────────────────┐  ┌────────────────┐
   │   PgBouncer      │  │   Redis Cluster  │  │  Qdrant        │
   │ (Connection Pool)│  │                 │  │  (optional)    │
   └────────┬─────────┘  └────────┬────────┘  └───────┬────────┘
            │                     │                    │
            ▼                     │                    │
   ┌──────────────────┐           │                    │
   │  PostgreSQL 16   │◄──────────┘                    │
   │  PRIMARY         │                                │
   │  + pgvector      │◄───────────────────────────────┘
   └────────┬─────────┘
            │  Streaming Replication
            ▼
   ┌──────────────────┐
   │  PostgreSQL 16   │
   │  READ REPLICA    │  ← Analytics queries, reports
   └──────────────────┘
            │
            │  WAL Archiving
            ▼
   ┌──────────────────┐
   │  S3 / MinIO      │  ← WAL files, backups
   │  (Backup Store)  │
   └──────────────────┘
```

---

## 4. ACID COMPLIANCE

| Database | Atomicity | Consistency | Isolation | Durability |
|----------|-----------|-------------|-----------|------------|
| PostgreSQL | ✅ Transaction | ✅ Constraints, FK | ✅ MVCC (READ COMMITTED default) | ✅ WAL |
| Redis | ✅ MULTI/EXEC | ⚠️ Application-level | ⚠️ Single-threaded | ✅ RDB+AOF |
| pgvector | ✅ PG transaction | ✅ PG constraints | ✅ MVCC | ✅ WAL |

**Isolation Level tanlov:**
```
Default:       READ COMMITTED    (yaxshi balans)
Critical ops:  SERIALIZABLE      (payment, config change)
Reporting:     REPEATABLE READ   (consistent snapshot)
```

---

## 5. HIGH AVAILABILITY

### 5.1 PostgreSQL HA

```
┌─────────────────────────────────────────────────┐
│               PostgreSQL HA Setup               │
│                                                 │
│  ┌───────────────┐     ┌───────────────────┐    │
│  │  PRIMARY      │────▶│  READ REPLICA 1   │    │
│  │  (read+write) │     │  (read only)      │    │
│  └───────┬───────┘     └───────────────────┘    │
│          │                                      │
│          │  Streaming Replication               │
│          │                                      │
│          └────────▶ ┌───────────────────┐       │
│                     │  READ REPLICA 2   │       │
│                     │  (standby/DR)     │       │
│                     └───────────────────┘       │
│                                                 │
│  Failover: Patroni / pg_auto_failover           │
│  VIP: HAProxy / Keepalived                      │
│  RPO: ~0 (synchronous replica uchun)            │
│  RTO: ~30 saniya (avtomatik failover)           │
└─────────────────────────────────────────────────┘
```

### 5.2 Redis HA

```
Development:  Redis Sentinel (3 node: 1 master + 2 replica + 3 sentinel)
Production:   Redis Cluster (6 node: 3 master + 3 replica, 16384 hash slots)
```

---

## 6. SCALABILITY STRATEGIYASI

### 6.1 Vertical Scaling Limitleri

| Komponent | Min | Recommended | Max (vertical) |
|-----------|-----|-------------|----------------|
| PostgreSQL RAM | 4 GB | 32 GB | 512 GB |
| PostgreSQL CPU | 2 cores | 16 cores | 128 cores |
| Redis RAM | 1 GB | 8 GB | 256 GB |
| Disk (SSD) | 100 GB | 1 TB | 64 TB |

### 6.2 Horizontal Scaling

```
READ SCALING:
  PostgreSQL Read Replicas (1 → 5+)
  PgBouncer load balancing across replicas
  Django DATABASE_ROUTERS (read/write split)

WRITE SCALING:
  Sharding (application-level, by organization_id)
  Citus extension (distributed PostgreSQL)
  Partitioning (messages by month, logs by week)

VECTOR SCALING:
  pgvector → Qdrant migration (10M+ vectors)
  Qdrant sharding (horizontal)
```

### 6.3 Connection Pooling (PgBouncer)

```
Pool mode:     transaction (best for Django)
pool_size:     25 per application instance
max_client_conn: 1000
server_idle_timeout: 600s

Django settings:
  CONN_MAX_AGE = 0  (PgBouncer manages connections)
  CONN_HEALTH_CHECKS = True
```

---

## 7. PERFORMANCE PRINSIPLARI

### 7.1 Pagination Strategiyasi

```
OFFSET PAGINATION (kichik dataset, admin):
  GET /api/messages/?page=1&page_size=20
  Problem: OFFSET 1000000 juda sekin

CURSOR-BASED PAGINATION (recommended, production):
  GET /api/messages/?cursor=eyJpZCI6MTAwMH0&page_size=20
  Cursor: base64({"id": 1000, "created_at": "2026-07-03"})
  Afzallik: O(1) performance, consistent results

KEYSET PAGINATION (messages, logs):
  WHERE (created_at, id) < (cursor_time, cursor_id)
  ORDER BY created_at DESC, id DESC
  LIMIT 20
```

### 7.2 N+1 Query Muammosi va Yechim

```python
# YOMON — N+1 query
chats = Chat.objects.filter(user=user)
for chat in chats:
    print(chat.messages.count())  # N ta query!

# YAXSHI — select_related / prefetch_related
chats = Chat.objects.filter(user=user).prefetch_related(
    Prefetch('messages', queryset=Message.objects.order_by('-created_at')[:5])
)
```

### 7.3 Caching Strategiyasi

```
CACHE-ASIDE (lazy loading):
  1. App cache'ni tekshiradi
  2. Miss bo'lsa → DB'dan o'qiydi
  3. Cache'ga yozadi
  Ishlatish: User profile, model configs, plugin manifests

WRITE-THROUGH:
  1. DB'ga yozadi
  2. Cache'ni yangilaydi
  Ishlatish: Configuration, system settings

CACHE INVALIDATION:
  Key pattern: aida:{entity}:{id}:{version}
  TTL: 5min (hot data), 1h (cold data), 24h (static config)
```

### 7.4 Batch Operations

```
Bulk insert: Message.objects.bulk_create(messages, batch_size=1000)
Bulk update: Message.objects.bulk_update(messages, ['status'], batch_size=500)
Chunked delete: .filter(...).delete() → chunked (10000 per batch)
```

---

## 8. TABLE PARTITIONING

```sql
-- Messages: Range partitioning by month
-- Partition pruning — faqat kerakli partition scan qilinadi

messages          → messages_2026_01, messages_2026_02, ...
system_logs       → system_logs_2026_w01, system_logs_2026_w02, ...
audit_logs        → audit_logs_2026_q1, audit_logs_2026_q2, ...
embeddings        → embeddings_shard_01..10 (HASH partitioning by knowledge_id)
```

---

## 9. CLOUD READINESS

| Cloud | Managed Service | Notes |
|-------|----------------|-------|
| AWS | RDS PostgreSQL 16 / Aurora PostgreSQL | Multi-AZ, automated backups |
| GCP | Cloud SQL PostgreSQL / AlloyDB | HA, read replicas |
| Azure | Azure Database for PostgreSQL Flexible | Zone redundant |
| Self-hosted | PostgreSQL + Patroni + HAProxy | Full control |

**Cloud migration qoidalari:**
- Connection string environment variable'da (`.env`)
- Hech qachon hardcoded
- PgBouncer cloud'da ham ishlatiladi (RDS Proxy muqobil)

---

## 10. MULTI-DATABASE DJANGO ROUTER

```python
# Django DATABASE_ROUTERS dizayni

Databases:
  'default':   PostgreSQL Primary (read + write)
  'replica':   PostgreSQL Read Replica (read only)
  'cache':     Redis (Django cache framework)
  'analytics': ClickHouse (optional, analytics queries)

Router qoidalari:
  - SELECT → replica (agar mavjud bo'lsa)
  - INSERT/UPDATE/DELETE → default (primary)
  - Transaction ichida → default (primary)
  - Analytics model → analytics DB
```

---

## 11. FUTURE-PROOF QARORLAR

| Qaror | Hozir | Kelajak |
|-------|-------|---------|
| UUID primary keys | UUID v4 | UUID v7 (sortable) |
| Vector storage | pgvector | Qdrant (10M+ vectors) |
| Analytics | PostgreSQL | ClickHouse (100M+ events) |
| Full-text search | PostgreSQL FTS | Elasticsearch (complex search) |
| Sharding | Partitioning | Citus distributed |
| Time-series | PostgreSQL | TimescaleDB extension |

---

*Hujjat AIDA Development Bible — Book 1, Chapter 8 asosida tayyorlangan.*
