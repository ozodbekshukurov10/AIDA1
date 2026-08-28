# AIDA Enterprise Monitoring Platform
## Observability Guide

**Versiya:** 1.0.0  
**Sana:** 2026-07-03  
**Muallif:** AIDA SRE Team  
**Holat:** Production-Ready Design

---

## 1. OBSERVABILITY NIMA?

Observability — tizimning **ichki holatini** uning **tashqi chiqishlaridan** tushunish qobiliyati.

```
MONITORING vs OBSERVABILITY

MONITORING:
  "Server CPU 95% da"  ← Nima bo'lyapti? MA'LUM
  "Nima uchun?" ← NOMA'LUM

OBSERVABILITY:
  "Server CPU 95% da"  ← Nima bo'lyapti
  "gpt-4 model batch request tufayli" ← Nima uchun
  "request 14 ta subquery ochgan" ← Qayerda
  "agent-007 → workflow:X → model:gpt4 → query:Y" ← Qanday yo'l bilan
```

### Observability 3 ustuni

```
┌─────────────────────────────────────────────────────────────┐
│                  OBSERVABILITY PILLARS                       │
│                                                             │
│   ┌────────────┐   ┌────────────┐   ┌────────────────────┐  │
│   │  METRICS   │   │   LOGS     │   │     TRACES         │  │
│   │            │   │            │   │                    │  │
│   │ Nima       │   │ Nima       │   │ Qayerda            │  │
│   │ bo'lyapti? │   │ sodir      │   │ sekinlayapti?      │  │
│   │            │   │ bo'ldi?    │   │ Qaysi servisda?    │  │
│   │ (Prometheus│   │ (Loki)     │   │ (Tempo/Jaeger)     │  │
│   │  Grafana)  │   │            │   │                    │  │
│   └────────────┘   └────────────┘   └────────────────────┘  │
│                                                             │
│              Bu 3 ustun birgalikda = OBSERVABILITY         │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. OPENTELEMETRY ARXITEKTURASI

### 2.1 OTEL Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  OpenTelemetry Pipeline                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [AIDA Backend]                                             │
│      │                                                      │
│      │ OTEL SDK auto-instrumentation                        │
│      │ (Django middleware, DB calls, HTTP clients)         │
│      │                                                      │
│      ▼                                                      │
│  [OTEL Collector]                                           │
│      │                                                      │
│  ┌───┼────────────────┐                                    │
│  │   │                │                                    │
│  ▼   ▼                ▼                                    │
│ [Prometheus] [Loki]  [Tempo]                                │
│  (Metrics)  (Logs)  (Traces)                               │
│      │        │        │                                    │
│      └────────┼────────┘                                    │
│               │                                             │
│           [Grafana]                                         │
│     (Metrics + Logs + Traces birlashgan)                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 OTEL Collector Konfiguratsiya

```yaml
# otel-collector-config.yaml (Dizayn)

receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
  
  prometheus:
    config:
      scrape_configs:
        - job_name: 'aida-backend'
          scrape_interval: 15s
          static_configs:
            - targets: ['backend:8000']

processors:
  batch:
    timeout: 5s
    send_batch_size: 1000
  
  resource:
    attributes:
      - key: service.name
        value: aida-backend
        action: upsert
      - key: deployment.environment
        value: production
        action: upsert
  
  filter/exclude_pii:
    # User PII filtered at collector level
    spans:
      exclude:
        attributes:
          - key: user.email
          - key: user.phone

exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"
  
  loki:
    endpoint: http://loki:3100/loki/api/v1/push
  
  otlp/tempo:
    endpoint: http://tempo:4317
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, resource, filter/exclude_pii]
      exporters: [otlp/tempo]
    
    metrics:
      receivers: [otlp, prometheus]
      processors: [batch, resource]
      exporters: [prometheus]
    
    logs:
      receivers: [otlp]
      processors: [batch, resource, filter/exclude_pii]
      exporters: [loki]
```

---

## 3. DISTRIBUTED TRACING

### 3.1 Trace Nima?

```
Bir API request'ning to'liq yo'li:

REQUEST: POST /api/platform/chat/
│
├─ [Span 1] Django middleware         12ms
│
├─ [Span 2] Authentication check       4ms
│
├─ [Span 3] Rate limit check           2ms
│
├─ [Span 4] Request processing
│   ├─ [Span 4.1] DB query            18ms
│   ├─ [Span 4.2] Redis cache check    1ms
│   └─ [Span 4.3] AI model call      890ms
│       ├─ [Span 4.3.1] Prompt build   5ms
│       ├─ [Span 4.3.2] API call     878ms
│       └─ [Span 4.3.3] Parse resp    7ms
│
└─ [Span 5] Response serialize         3ms

TOTAL: 930ms
BOTTLENECK: AI model API call (94.9%)
```

### 3.2 Tracing Stack

```
Instrumentatsiya:
  - opentelemetry-sdk-python
  - opentelemetry-instrumentation-django
  - opentelemetry-instrumentation-psycopg2
  - opentelemetry-instrumentation-redis
  - opentelemetry-instrumentation-requests (external HTTP)
  - Manual spans: AI calls, agent tasks, workflow steps

Storage: Grafana Tempo
  - Retention: 7 kun (hot), 30 kun (warm)
  - TraceQL query support
  - Exemplar linking (metrics → traces)

Sampling Strategy:
  - Tail-based sampling (error traces always kept)
  - Normal requests: 10% sampling
  - Slow requests (>1s): 100% sampling
  - Error requests: 100% sampling
```

### 3.3 Trace Attributes (Span Tags)

```
Standard attributes (barcha spanlarda):
  service.name          → "aida-backend"
  service.version       → "1.2.3"
  deployment.environment → "production"
  host.name             → server hostname

HTTP request spans:
  http.method           → "POST"
  http.url              → "/api/platform/chat/"  ← normalized
  http.status_code      → 200
  http.request_size     → bytes

Database spans:
  db.system            → "postgresql"
  db.operation         → "SELECT"
  db.statement         → SQL (sanitized, no values)

AI model spans:
  ai.model.name         → "gpt-4o"
  ai.provider           → "openai"
  ai.tokens.input       → 450
  ai.tokens.output      → 312
  ai.duration_ms        → 890

Agent spans:
  agent.id              → "agent-007"
  agent.task_type       → "document_processing"
  
QOSHILMAYDI (PII):
  ❌ user.id
  ❌ user.email
  ❌ request body content
  ❌ API keys
  ❌ passwords
```

---

## 4. STRUCTURED LOGGING

### 4.1 Log Format

Barcha AIDA loglar JSON formatda bo'lishi kerak:

```json
{
  "timestamp": "2026-07-03T08:56:20.685Z",
  "level": "INFO",
  "service": "aida-backend",
  "version": "1.2.3",
  "environment": "production",
  "trace_id": "abc123def456",
  "span_id": "789xyz",
  "message": "Chat request processed successfully",
  "context": {
    "endpoint": "/api/platform/chat/",
    "method": "POST",
    "status_code": 200,
    "duration_ms": 930,
    "model": "gpt-4o",
    "tokens_total": 762
  }
}
```

### 4.2 Log Darajalari

| Daraja | Ishlatish holati | Retain davri |
|--------|-----------------|--------------|
| **DEBUG** | Development only, batafsil | 1 kun (dev only) |
| **INFO** | Normal operatsiya hodisalari | 7 kun |
| **WARNING** | G'ayrioddiy holat, hali muammo emas | 30 kun |
| **ERROR** | Muammo yuz berdi, request/task bajarilmadi | 90 kun |
| **CRITICAL** | Servis-keng yoki data-threatening hodisa | 365 kun |
| **SECURITY** | Autentifikatsiya, ruxsat, anomaliya | 365 kun |

### 4.3 Log Kategoriyalari

```
CATEGORIES (log.category field):

REQUEST     → HTTP request/response
DATABASE    → DB query events
CACHE       → Redis operations
AI_MODEL    → AI model calls and responses
AGENT       → Agent lifecycle events
WORKFLOW    → Workflow state changes
AUTH        → Authentication/authorization events
SECURITY    → Security-related events
PLUGIN      → Plugin lifecycle events
SYSTEM      → System-level events
PERFORMANCE → Slow operations, performance anomalies
```

### 4.4 PII Filtering

```
Log yozishdan oldin quyidagi maydonlar MASKALANADI:

email:     "user@example.com"  →  "u***@e***.com"
phone:     "+998901234567"     →  "+9989*****67"
ip_address: "192.168.1.100"   →  "192.168.x.x"
api_key:    "sk-abc123xyz"    →  "sk-***[MASKED]***"
password:   any value         →  "[REDACTED]"
token:      any JWT/token     →  "[REDACTED]"
```

### 4.5 Log Aggregation (Loki)

```
Loki Label Strategy:

Loki labels (low cardinality):
  environment: production / staging / development
  service:     backend / frontend / celery / agent
  level:       INFO / WARNING / ERROR / CRITICAL
  component:   api / database / cache / ai / auth

Loki stream labels qo'shilmaydi:
  ❌ user_id    (high cardinality)
  ❌ request_id (high cardinality)
  ❌ trace_id   (Tempo'da bor)

LogQL query misoli:
  {service="backend", level="ERROR"} |= "AI model"
  | json
  | line_format "{{.timestamp}} {{.message}} (model={{.context.model}})"
```

---

## 5. METRICS, LOGS, TRACES INTEGRATSIYASI

### 5.1 Exemplars (Metrics → Traces)

```
Prometheus histogram'larda exemplar qo'shiladi:

# Misol: Sekin request uchun trace_id saqlanadi
aida_http_request_duration_seconds_bucket{
  le="2.5", 
  method="POST", 
  endpoint="/api/platform/chat/"
} 1234 # {trace_id="abc123"} 2.1

Grafana'da: Histogram panelda sekin request → Tempo trace'iga o'tish
```

### 5.2 Logs → Traces

```
Har bir log yozuvida trace_id va span_id mavjud.
Grafana Loki'da log yozuvidan → Tempo trace'iga o'tish.

Loki → Tempo derived field:
  Pattern: trace_id=([0-9a-f]{32})
  URL: http://tempo:3000/explore?traceId=${__value.raw}
```

### 5.3 Traces → Logs

```
Tempo'da trace ko'rib, usha trace'ga tegishli loglarni
Loki'da qidirish:

LogQL:
  {service="backend"} | json | trace_id="abc123def456"
```

---

## 6. SERVICE LEVEL OBJECTIVES (SLO)

### 6.1 AIDA SLO Ro'yxati

```
SLO 1: API Availability
  Target:   99.9% (43.8 min/month downtime ruxsat)
  Window:   30 kun rolling
  Measure:  successful_requests / total_requests

SLO 2: API Latency
  Target:   95% of requests < 1s
  Window:   24 soat rolling
  Measure:  p95 latency < 1000ms

SLO 3: AI Model Success Rate
  Target:   99% of model calls successful
  Window:   24 soat rolling
  Measure:  successful_model_calls / total_model_calls

SLO 4: Agent Task Completion
  Target:   95% of tasks complete without retry
  Window:   7 kun rolling
  Measure:  completed_without_retry / total_assigned

SLO 5: Health Check Uptime
  Target:   99.95% all critical services UP
  Window:   30 kun rolling
  Measure:  healthy_minutes / total_minutes
```

### 6.2 Error Budget

```
SLO: 99.9% availability
Error Budget: 0.1% per month = 43.8 daqiqa

Error Budget Dashboard:
  ┌──────────────────────────────────────────────────┐
  │  Error Budget: API Availability                  │
  │                                                  │
  │  Month budget:   43.8 min                        │
  │  Used so far:    12.3 min (28.1%)                │
  │  Remaining:      31.5 min (71.9%)                │
  │  Days left:      22 of 30                        │
  │                                                  │
  │  Burn rate: 0.56x  ✅ (< 1x is sustainable)     │
  │                                                  │
  │  ████████████████████░░░░░░░░░░░░░░░  28.1%     │
  └──────────────────────────────────────────────────┘

Burn Rate Alertlari:
  burn_rate > 1.0 for 1h  → P3 MEDIUM (sustainable emas)
  burn_rate > 5.0 for 30m → P2 HIGH   (tez yonmoqda)
  burn_rate > 14.4 for 5m → P1 CRITICAL (1 soatda bitadi)
```

---

## 7. RUNBOOK TEMPLATE

Har bir kritik alert uchun Runbook bo'lishi kerak:

```markdown
# Runbook: [Alert Nomi]

## Holat
Alert: [AlertName]
Severity: [P1/P2/P3]

## Simptomlar
- [Foydalanuvchi ko'rgan muammo]
- [Texnik belgi]

## Tashxis qadamlari
1. [1-qadam]
2. [2-qadam]
3. [3-qadam]

## Hal qilish yo'llari
### Holat A: [X bo'lsa]
  → [Bu qiling]

### Holat B: [Y bo'lsa]
  → [Bu qiling]

## Eskalatsiya
Agar 15 daqiqada yechilmasa → [kim ga]

## Post-mortem
Alert yopilgandan keyin root cause yozing.
```

---

## 8. CAPACITY PLANNING

### 8.1 Monitoring Tizimining O'z Resurslari

| Komponent | Min RAM | Recommended RAM | Disk/day |
|-----------|---------|-----------------|---------|
| Prometheus | 2 GB | 8 GB | ~1 GB |
| VictoriaMetrics | 1 GB | 4 GB | ~200 MB (compressed) |
| Grafana | 256 MB | 1 GB | < 100 MB |
| Loki | 1 GB | 4 GB | ~500 MB |
| Tempo | 1 GB | 4 GB | ~2 GB |
| Alertmanager | 128 MB | 256 MB | < 10 MB |
| OTEL Collector | 256 MB | 1 GB | — |
| **Total** | **~6 GB** | **~22 GB** | **~4 GB/day** |

### 8.2 Metrika Cardinality Estimate

```
Taxminiy active time series:
  Infrastructure metrics:   ~500
  API metrics:              ~2,000  (50 endpoints × 40 labels)
  Database metrics:         ~300
  Cache metrics:            ~100
  AI model metrics:         ~400  (10 models × 40 metrics)
  Agent metrics:            ~1,000  (50 agents × 20 metrics)
  Workflow metrics:         ~500
  Security metrics:         ~200
  ─────────────────────────────
  TOTAL:                    ~5,000 time series

Prometheus RAM estimate:
  5,000 series × ~5KB = ~25 MB active
  Sehr comfortable, scaling OK up to 1M series
```

---

## 9. OBSERVABILITY MATURITY MODEL

```
Level 1 — BASIC ✅ (AIDA minimum)
  ✓ Health check endpoints
  ✓ Basic metrics (CPU, RAM, API)
  ✓ Error logging
  ✓ Uptime alerting

Level 2 — REACTIVE ✅ (AIDA target)
  ✓ Structured JSON logs
  ✓ Distributed tracing
  ✓ SLO tracking
  ✓ Alert routing
  ✓ Error budgets

Level 3 — PROACTIVE 🎯 (AIDA future)
  → Anomaly detection (ML-based)
  → Auto-remediation scripts
  → Predictive capacity alerts
  → Business metrics correlation

Level 4 — AUTONOMOUS 🔮 (AIDA long-term)
  → Self-healing infrastructure
  → Auto-scaling based on prediction
  → AI-driven root cause analysis
  → Zero-touch incident resolution
```

---

## 10. OBSERVABILITY CHECKLIST

### Deploy oldidan

```
[ ] Barcha yangi endpoint'lar metrika chiqarayaptimi?
[ ] Yangi servis health check endpoint'iga egami?
[ ] Structured logging qo'shilganmi?
[ ] PII maydonlar logdan olib tashlanganlmi?
[ ] Tracing spans to'g'ri nomlanganmi?
[ ] Alert rules yangi metrikalar uchun yozimdanmi?
[ ] Grafana dashboard yangilanganlmi?
[ ] Runbook yangi alertlar uchun yozimdanmi?
[ ] SLO target tasdiqlanganlmi?
```

### Incident paytida

```
[ ] Metrics dashboard tekshirildi
[ ] Error logs ko'rildi (Loki)
[ ] Failing request trace'i Tempo'da topildi
[ ] Root cause aniqlandi
[ ] Runbook follow qilindi
[ ] Escalation qoidalari amal qilindi
```

### Incident dan keyin

```
[ ] Post-mortem yozildi
[ ] Alert threshold to'g'rilandi (kerak bo'lsa)
[ ] Runbook yangilandi
[ ] Error budget impact hisoblandi
[ ] Monitoring coverage gap'lari yopildi
```

---

## 11. GLOSSARY

| Atama | Ta'rif |
|-------|--------|
| **SLO** | Service Level Objective — servis sifat maqsadi |
| **SLA** | Service Level Agreement — mijoz bilan kelishuv |
| **SLI** | Service Level Indicator — SLO'ni o'lchaydigan metrika |
| **Error Budget** | SLO'dan ruxsat berilgan xato miqdori |
| **MTTD** | Mean Time To Detect — muammoni aniqlash vaqti |
| **MTTR** | Mean Time To Resolve — muammoni yechish vaqti |
| **MTTF** | Mean Time To Failure — keyingi nosozlikka qadar vaqt |
| **Cardinality** | Unique time series soni |
| **Exemplar** | Metrikani aniq trace'ga bog'lovchi yozuv |
| **Span** | Trace ichidagi bir operatsiya birligi |
| **Trace** | Bir request'ning to'liq sayohat yozuvi |
| **p95/p99** | 95-/99-percentil latensiya |
| **Burn Rate** | Error budget'ni sarflash tezligi |
| **Dead Man's Switch** | Doim yoniq bo'lishi kerak bo'lgan watchdog alert |

---

*Hujjat AIDA Development Bible — Book 1, Chapter 7 asosida tayyorlangan.*
