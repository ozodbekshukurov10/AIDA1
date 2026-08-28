# AIDA Enterprise Monitoring Platform
## Health Checks Specification

**Versiya:** 1.0.0  
**Sana:** 2026-07-03  
**Muallif:** AIDA SRE Team  
**Holat:** Production-Ready Design

---

## 1. HEALTH CHECK ARXITEKTURASI

```
┌─────────────────────────────────────────────────────────────┐
│                   HEALTH CHECK SYSTEM                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────────────────────────────────────────────────┐  │
│   │              Health Check Orchestrator               │  │
│   │         (runs every 10s for critical,                │  │
│   │          every 30s for non-critical)                 │  │
│   └──────┬────────┬──────┬──────┬──────┬─────┬───────────┘  │
│          │        │      │      │      │     │              │
│      ┌───▼──┐ ┌───▼──┐ ┌─▼──┐ ┌▼────┐ ┌▼──┐ ┌▼────────┐   │
│      │Back  │ │Front │ │ DB │ │Redis│ │ AI│ │Plugins  │   │
│      │end   │ │end   │ │    │ │     │ │   │ │         │   │
│      └───┬──┘ └───┬──┘ └─┬──┘ └┬────┘ └┬──┘ └┬────────┘   │
│          │        │      │     │       │      │            │
│          └────────┴──────┴─────┴───────┴──────┘            │
│                            │                               │
│              ┌─────────────▼─────────────┐                 │
│              │   Health Check Results    │                 │
│              │   → Prometheus Metrics    │                 │
│              │   → Grafana Dashboard     │                 │
│              │   → Alertmanager          │                 │
│              └───────────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. HEALTH STATUS MODELI

### Status Darajalari

```
HEALTHY   → Servis to'liq ishlayapti
DEGRADED  → Servis qisman ishlayapti (performance muammosi)
UNHEALTHY → Servis ishlamayapti yoki kritik xatolik
UNKNOWN   → Status aniqlanmadi (network yoki timeout)
```

### Standard Health Check Response Format

```json
{
  "service": "backend",
  "status": "healthy",
  "timestamp": "2026-07-03T08:56:20Z",
  "version": "1.2.3",
  "uptime_seconds": 604800,
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "ai_provider": "healthy",
    "disk_space": "healthy",
    "memory": "healthy"
  },
  "response_time_ms": 12
}
```

---

## 3. BACKEND HEALTH CHECK

### 3.1 Endpoint

```
GET /api/health/
GET /api/health/detailed/    ← Admin only
```

### 3.2 Tekshiriladigan Komponentlar

```
Backend Health Checks:
├── Application Health
│   ├── Django application running          → process check
│   ├── WSGI server responding              → HTTP 200 check
│   ├── Middleware chain functional         → request pipeline
│   └── Static files serving               → /static/ accessible
├── Database Connectivity
│   ├── Connection pool available           → try_connect()
│   ├── Read query executing                → SELECT 1
│   ├── Write query executing               → temp table insert
│   └── Migration status                   → django_migrations
├── Cache (Redis) Connectivity
│   ├── Redis PING response                 → PING → PONG
│   ├── SET operation working               → test key write
│   └── GET operation working              → test key read
├── AI Provider Connectivity
│   ├── Provider endpoint reachable         → HEAD request
│   └── Authentication valid               → lightweight test call
├── Celery Workers
│   ├── At least 1 worker active            → celery inspect ping
│   └── Task queue not overflowed          → queue depth < limit
└── File System
    ├── Temp directory writable             → temp file write
    ├── Log directory writable             → log write test
    └── Disk space sufficient              → > 10% free
```

### 3.3 Health Check Intervallari

| Check turi | Interval | Timeout | Threshold |
|------------|----------|---------|-----------|
| HTTP alive | 10s | 5s | 3 consecutive failures |
| DB connection | 15s | 10s | 2 consecutive failures |
| Redis ping | 10s | 3s | 3 consecutive failures |
| AI provider | 60s | 30s | 2 consecutive failures |
| Celery workers | 30s | 15s | 3 consecutive failures |
| Disk space | 60s | 5s | Once (immediate alert) |

---

## 4. FRONTEND HEALTH CHECK

### 4.1 Tekshiriladigan Komponentlar

```
Frontend Health Checks:
├── Static Assets
│   ├── index.html accessible              → HTTP 200
│   ├── JS bundles loading                 → asset manifest check
│   └── CSS bundles loading               → asset manifest check
├── API Connectivity (from client)
│   ├── Backend API reachable              → /api/health/ call
│   └── WebSocket connection (if used)    → WS handshake
└── Core Web Vitals (via RUM)
    ├── LCP < 2.5s                        → 🟢 Good
    ├── FID < 100ms                       → 🟢 Good
    └── CLS < 0.1                         → 🟢 Good
```

### 4.2 Frontend Monitoring Metrikalari

```
Prometheus metrikalari (RUM orqali):
  frontend_lcp_seconds          → histogram
  frontend_fid_milliseconds     → histogram
  frontend_cls_score            → gauge
  frontend_page_load_seconds    → histogram
  frontend_js_errors_total      → counter
  frontend_api_errors_total     → counter
```

---

## 5. DATABASE HEALTH CHECK

### 5.1 Tekshiriladigan Komponentlar

```
Database Health Checks:
├── Connectivity
│   ├── TCP connection to DB port          → socket connect
│   ├── Authentication working             → login test
│   └── Simple query executing            → SELECT 1
├── Performance
│   ├── Query response time < 100ms        → timing check
│   ├── Active connections < 80% max       → pg_stat_activity
│   └── No long-running queries (>30s)    → pg_stat_activity
├── Integrity
│   ├── All migrations applied             → django_migrations
│   ├── No table bloat (>50%)             → table size check
│   └── WAL/binlog not lagging           → replication lag
└── Resources
    ├── Disk space > 20% free             → pg_database_size
    └── Table locks count normal          → pg_locks
```

### 5.2 Database Health Thresholds

| Metrika | Sog'lom | Ogohlantirish | Kritik |
|---------|---------|---------------|--------|
| Query time | < 100ms | 100ms–500ms | > 500ms |
| Active connections | < 60% max | 60–80% max | > 80% max |
| Long queries | 0 | 1–3 | > 3 |
| Disk usage | < 70% | 70–85% | > 85% |
| Replication lag | < 1s | 1–10s | > 10s |
| Table locks | 0 | 1–5 | > 5 |

---

## 6. REDIS HEALTH CHECK

### 6.1 Tekshiriladigan Komponentlar

```
Redis Health Checks:
├── Connectivity
│   ├── Redis PING response                → PING → PONG < 1ms
│   └── Authentication working            → AUTH test
├── Memory
│   ├── Used memory < 80% max             → INFO memory
│   ├── Memory fragmentation ratio < 1.5  → mem_fragmentation_ratio
│   └── No eviction happening            → evicted_keys delta
├── Performance
│   ├── Command latency < 1ms             → LATENCY check
│   ├── Blocked clients = 0              → INFO clients
│   └── Rejected connections = 0         → INFO stats
└── Persistence (if enabled)
    ├── Last successful save < 1h         → lastsave check
    └── RDB/AOF not failing              → rdb_last_bgsave_status
```

### 6.2 Redis Health Thresholds

| Metrika | Sog'lom | Ogohlantirish | Kritik |
|---------|---------|---------------|--------|
| Ping latency | < 1ms | 1–10ms | > 10ms |
| Memory usage | < 70% | 70–85% | > 85% |
| Hit rate | > 90% | 80–90% | < 80% |
| Blocked clients | 0 | 1–5 | > 5 |
| Evictions/min | 0 | 1–100 | > 100 |

---

## 7. VECTOR DATABASE HEALTH CHECK

### 7.1 Tekshiriladigan Komponentlar

```
Vector DB Health Checks (Chroma/Qdrant/Pinecone):
├── Connectivity
│   ├── Service endpoint reachable         → HTTP check
│   └── Authentication working            → test query
├── Collections
│   ├── All collections accessible         → list collections
│   └── Index not corrupted              → metadata check
├── Performance
│   ├── Search latency < 200ms            → test vector search
│   └── Insert latency < 100ms           → test vector insert
└── Storage
    ├── Storage usage < 80%              → disk check
    └── Index size normal                → collection stats
```

---

## 8. AI PROVIDER HEALTH CHECK

### 8.1 Tekshiriladigan Komponentlar

```
AI Provider Health Checks:
├── Per-Provider Checks
│   ├── OpenAI
│   │   ├── API endpoint reachable        → HEAD https://api.openai.com
│   │   ├── Status page check            → status.openai.com
│   │   └── Authentication valid         → lightweight test
│   ├── Anthropic
│   │   ├── API endpoint reachable        → HEAD https://api.anthropic.com
│   │   └── Authentication valid         → lightweight test
│   └── Local Models (Ollama/vLLM)
│       ├── Service running              → localhost health endpoint
│       ├── Model loaded                 → model list check
│       └── GPU available (if needed)   → CUDA device check
└── Fallback Strategy
    ├── Primary provider down → fallback to secondary
    ├── All cloud providers down → use local model
    └── All providers down → return graceful error
```

### 8.2 AI Provider Health Thresholds

| Metrika | Sog'lom | Degraded | Unhealthy |
|---------|---------|----------|-----------|
| Response time | < 2s | 2–5s | > 5s |
| Success rate | > 98% | 95–98% | < 95% |
| Consecutive failures | 0 | 1–2 | > 2 |
| Rate limit remaining | > 20% | 5–20% | < 5% |

---

## 9. PLUGIN SYSTEM HEALTH CHECK

### 9.1 Tekshiriladigan Komponentlar

```
Plugin Health Checks:
├── Plugin Registry
│   ├── Registry service running          → process check
│   └── Plugin list loadable             → list plugins
├── Per-Plugin Checks
│   ├── Plugin module importable          → import test
│   ├── Plugin config valid              → schema validation
│   ├── Plugin dependencies met          → dependency check
│   └── Plugin not erroring             → last execution status
└── Plugin Isolation
    ├── Plugin sandbox functional         → sandbox test
    └── No plugin resource leaks         → memory delta check
```

---

## 10. AGENT HEALTH CHECK

### 10.1 Tekshiriladigan Komponentlar

```
Agent Health Checks:
├── Agent Process
│   ├── Agent process running            → process_id check
│   ├── Agent responding to ping         → heartbeat check
│   └── Agent memory within limits       → memory check
├── Agent Functionality
│   ├── Agent can receive tasks          → queue connectivity
│   ├── Agent can execute basic task     → lightweight test
│   └── Agent can report results        → result bus check
└── Agent Stability
    ├── Restart count < threshold        → restart count check
    ├── Error rate < 5%                 → error rate check
    └── No deadlock detected            → timeout check
```

---

## 11. HEALTH CHECK DASHBOARD

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AIDA HEALTH STATUS                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ BACKEND  │ │FRONTEND  │ │DATABASE  │ │  REDIS   │ │VECTOR DB │  │
│  │          │ │          │ │          │ │          │ │          │  │
│  │  🟢      │ │  🟢      │ │  🟢      │ │  🟢      │ │  🟡      │  │
│  │ HEALTHY  │ │ HEALTHY  │ │ HEALTHY  │ │ HEALTHY  │ │DEGRADED  │  │
│  │ 99.98%   │ │ 99.95%   │ │ 99.99%   │ │ 100%     │ │ 97.2%    │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                            │
│  │AI MODELS │ │ PLUGINS  │ │  AGENTS  │                            │
│  │          │ │          │ │          │                            │
│  │  🟢      │ │  🟢      │ │  🟡      │                            │
│  │ HEALTHY  │ │ HEALTHY  │ │DEGRADED  │                            │
│  │ 99.1%    │ │ 98.4%    │ │ 83.3%    │                            │
│  └──────────┘ └──────────┘ └──────────┘                            │
│                                                                     │
│  Overall System Health: 🟡 DEGRADED (2 services need attention)    │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ HEALTH CHECK HISTORY (Last 24h)                               │  │
│  │                                                               │  │
│  │ backend   ████████████████████████████████████████████ 100%  │  │
│  │ database  ████████████████████████████████████████████ 100%  │  │
│  │ redis     ████████████████████████████████████████████ 100%  │  │
│  │ vector_db ████████████████████████████░░░░░█████████░░  94%  │  │
│  │ agents    █████████████████████████████░░████████░░███  87%  │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 12. HEALTH CHECK PROMETHEUS METRICS

```
# Service up/down (1=healthy, 0=unhealthy)
aida_health_check_status{service="backend"}          1
aida_health_check_status{service="frontend"}         1
aida_health_check_status{service="database"}         1
aida_health_check_status{service="redis"}            1
aida_health_check_status{service="vector_db"}        0.5  # degraded
aida_health_check_status{service="ai_provider"}      1
aida_health_check_status{service="plugins"}          1
aida_health_check_status{service="agents"}           0.8  # some agents down

# Health check duration
aida_health_check_duration_seconds{service="backend"}   0.012
aida_health_check_duration_seconds{service="database"}  0.045

# Last successful check timestamp
aida_health_check_last_success_timestamp{service="backend"}  1751534180

# Total health check count
aida_health_checks_total{service="backend", status="success"}  8640
aida_health_checks_total{service="backend", status="failure"}  2
```

---

*Hujjat AIDA Development Bible — Book 1, Chapter 7 asosida tayyorlangan.*
