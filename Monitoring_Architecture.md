# AIDA — Enterprise Monitoring & Observability Architecture

## 1. Architectural Overview

AIDA monitoring platformasi 5 qatlamli arxitektura asosida ishlaydi: Signal Collection → Metrics Processing → Storage → Visualization → Alerting.

```
+------------------------------------------------------------------+
|                      VISUALIZATION & ALERTING                     |
|   Grafana Dashboards · In-App Dashboard · PagerDuty · Slack      |
+------------------------------------------------------------------+
|                          STORAGE                                  |
|   Prometheus (TSDB) · SQLite (agent DB) · Loki (logs) · Tempo    |
+------------------------------------------------------------------+
|                        METRICS PROCESSING                         |
|   Aggregation · Downsampling · Threshold Evaluation · Enrichment  |
+------------------------------------------------------------------+
|                       SIGNAL COLLECTION                           |
|   Metrics (PUSH/PULL) · Logs · Events · Traces · Health Checks   |
+------------------------------------------------------------------+
|                         MONITORED COMPONENTS                      |
|   Backend · Frontend · AI Models · Agents · Workflows · API       |
|   Database · Redis · Vector DB · Cache · Queue · Plugins · Auth   |
+------------------------------------------------------------------+
```

### 1.1 Current State Analysis

| Component | Status | Location |
|-----------|--------|----------|
| SQLite metrics collector | ✅ Active | `webapp/monitoring/metrics.py` |
| Agent in-memory metrics | ✅ Active | `webapp/agents/base_agent.py:158` |
| SystemMonitor (self-improvement) | ✅ Active | `webapp/self_improvement/monitor.py` |
| API status endpoint | ✅ Active | `webapp/api/status.py:8` |
| Gateway health checks | ✅ Active | `webapp/llm/gateway.py:check_all_health()` |
| Provider health per-provider | ✅ Active | `webapp/llm/base.py:check_health()` |
| Event bus (domain events) | ✅ Active | `aidaos/domain/events.py` |
| Metrics DB (agent calls + HTTP) | ✅ Active | `webapp/memory/metrics.py` |
| Prometheus integration | ❌ Missing | No `prometheus_client` library usage |
| Grafana dashboards | ❌ Missing | No dashboard configuration files |
| Standard health endpoints | ❌ Missing | No `/health`, `/ready`, `/livez` |
| Distributed tracing | ❌ Missing | No OpenTelemetry/Jaeger |
| Alert system | ❌ Missing | No threshold-based alerting |
| System-level metrics (CPU/RAM/GPU) | ❌ Missing | No `psutil` or similar |
| Automated metrics recording | ❌ Missing | `record_request()` never called from middleware |
| Metrics persistence for agents | ❌ Missing | `BaseAgent.metrics` is in-memory only |

### 1.2 Monitoring Signals

AIDA monitoring 4 turdagi signalni yig'adi:

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   METRICS   │  │    LOGS     │  │   TRACES    │  │   EVENTS    │
│  (Numerical)│  │  (Textual)  │  │ (Distributed)│  │ (Domain)    │
├─────────────┤  ├─────────────┤  ├─────────────┤  ├─────────────┤
│ CPU/RAM/GPU │  │ AI Logs     │  │ LLM Request │  │ Agent start │
│ Request cnt  │  │ Agent Logs  │  │ Agent Exec  │  │ Task fail   │
│ Latency     │  │ Error Logs  │  │ DB Query    │  │ Config chg  │
│ Token usage │  │ Audit Logs  │  │ API Call    │  │ Plugin load │
│ Error rate  │  │ Security    │  │ Tool Exec   │  │ Deploy      │
│ Cache hit % │  │ Workflow    │  │ Workflow    │  │ Error       │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

## 2. Metrics Collection

### 2.1 Current Collectors

| Collector | Type | Storage | Retention | Scope |
|-----------|------|---------|-----------|-------|
| `MetricsCollector` (monitoring) | SQLite | `webapp/monitoring/metrics.db` | 7 days | Agent + model stats |
| `MetricsCollector` (memory) | SQLite | `data/aida_metrics.db` | Unlimited | HTTP + agent calls |
| `BaseAgent.metrics` | In-memory dict | RAM | Process lifetime | Per-agent (calls, errors, latency, tokens) |
| `SystemMonitor` | In-memory lists | RAM | Capped at 1000 | Errors, snapshots, performance reports |

### 2.2 Target Metrics Collection

```python
# AIDA metrics namespace convention
aida_{component}_{metric}{_unit?}

Examples:
  aida_llm_requests_total{provider="openai",model="gpt-4o",status="success"}
  aida_llm_latency_ms{provider="ollama",model="llama3"}
  aida_llm_tokens_total{provider="anthropic",type="prompt"}
  aida_agent_calls_total{agent="code_review",status="success"}
  aida_agent_latency_ms{agent="security"}
  aida_agent_tasks_total{agent="orchestrator",status="completed"}
  aida_api_requests_total{endpoint="/chat",method="POST",status="200"}
  aida_api_latency_ms{endpoint="/status"}
  aida_cache_hits_total{cache="redis"}
  aida_cache_misses_total{cache="redis"}
  aida_db_query_duration_ms{query="select",table="metrics"}
  aida_tool_calls_total{tool="search_web",status="success"}
  aida_tool_latency_ms{tool="read_file"}
  aida_workflow_duration_ms{workflow="code_review"}
  aida_system_cpu_percent{host="node-1"}
  aida_system_memory_percent{host="node-1"}
  aida_system_gpu_percent{gpu="cuda:0"}
```

### 2.3 Collection Intervals

| Signal Type | Collection Interval | Export Method |
|-------------|-------------------|---------------|
| System metrics (CPU/RAM) | 15s | PUSH (agent) |
| GPU metrics | 30s | PUSH (agent) |
| HTTP request metrics | Per-request | Middleware |
| LLM call metrics | Per-call | Provider wrapper |
| Agent execution metrics | Per-execution | BaseAgent decorator |
| Tool execution metrics | Per-call | Tool wrapper |
| Cache metrics | 60s | PULL (exporter) |
| Database metrics | 60s | PULL (exporter) |
| Queue metrics | 30s | PULL (exporter) |

## 3. Metrics Storage

### 3.1 Storage Tiers

| Tier | Technology | Data | Retention | Query |
|------|-----------|------|-----------|-------|
| **Hot** | Prometheus (TSDB) | Recent metrics (15s interval) | 15 days | PromQL |
| **Warm** | Prometheus + Thanos | Downsampled metrics | 90 days | PromQL |
| **Cold** | S3 / GCS | Aggregated metrics (1h) | 1 year | Thanos query |
| **Agent DB** | SQLite | Agent calls + HTTP requests | 30 days | SQL |

### 3.2 Aggregation Windows

| Window | Aggregation | Example |
|--------|-------------|---------|
| 15s | Raw | `aida_llm_requests_total` (counter) |
| 5m | Rate + avg | `rate(aida_llm_requests_total[5m])` |
| 1h | Avg, P50, P95, P99 | `histogram_quantile(0.95, ...)` |
| 24h | Sum, avg, max | Daily rollup |
| 30d | Monthly trend | Monthly rollup |

## 4. Agent Monitoring

### 4.1 Current (In-Memory)

`BaseAgent.metrics` tracks per-agent:
- `calls` — total executions
- `errors` — failed executions
- `total_latency_ms` — cumulative latency
- `tokens_used` — cumulative token usage

### 4.2 Target (Persistent + Real-Time)

| Metric | Source | Collection | Visualization |
|--------|--------|------------|---------------|
| Current status | `BaseAgent.status` | On change | Status indicator (IDLE/RUNNING/ERROR) |
| Call count | `BaseAgent.metrics` | Per-execution | Counter chart |
| Error count | `BaseAgent.metrics` | On failure | Counter chart |
| Average latency | `BaseAgent.metrics` | Per-execution | Gauge chart |
| Token usage | `BaseAgent.metrics` | Per-execution | Area chart |
| Queue position | Orchestrator | Poll 30s | Gauge |
| Assigned tasks | Orchestrator | On assign | Counter |

```json
{
  "agent_id": "code_review",
  "status": "running",
  "uptime_seconds": 86400,
  "total_calls": 1523,
  "success_rate": 96.7,
  "avg_latency_ms": 2340,
  "p95_latency_ms": 5600,
  "total_tokens": 14500000,
  "current_task": "Review PR #43",
  "queue_position": 0,
  "last_error": null,
  "last_seen": "2026-07-03T12:00:00Z"
}
```

## 5. AI Model Monitoring

### 5.1 Per-Provider Metrics

| Metric | Source | Type |
|--------|--------|------|
| Request count | Provider wrapper | Counter |
| Success rate | Provider wrapper | Gauge |
| Failure breakdown | Error handler | Counter (by error type) |
| Average response time | Provider wrapper | Histogram |
| P50/P95/P99 latency | Provider wrapper | Histogram |
| Token count (prompt/completion) | Provider wrapper | Counter |
| Token cost (USD) | Cost calculator | Counter |
| TTFT (time to first token) | Streaming wrapper | Histogram |
| Context window usage | Provider wrapper | Gauge |
| Rate limit remaining | Response headers | Gauge |

### 5.2 Provider Health

```python
# Currently: check_all_health() with 30s TTL cache
# Target: Prometheus metrics + endpoint
aida_llm_up{provider="openai"} 1
aida_llm_up{provider="ollama"} 0  # offline
```

## 6. API Monitoring

### 6.1 Per-Endpoint Metrics

Har bir API endpoint uchun:

| Metric | Source | Current |
|--------|--------|---------|
| Request count | Middleware | ❌ Not collected |
| Status code distribution | Middleware | ❌ Not collected |
| Average latency | Middleware | ✅ `api_endpoint` decorator logs |
| P95/P99 latency | Middleware | ❌ Not collected |
| Error rate | Middleware | ❌ Not collected |
| Request size | Middleware | ❌ Not collected |
| Response size | Middleware | ❌ Not collected |

Current `api_endpoint` decorator logs: `{method} {path} → {status} ({latency}ms)`.
Target: Structured Prometheus metrics from a middleware.

### 6.2 API Middleware (Target)

```python
class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000

        metrics.api_requests_total.labels(
            endpoint=request.path,
            method=request.method,
            status=response.status_code,
        ).inc()

        metrics.api_latency_ms.labels(
            endpoint=request.path,
            method=request.method,
        ).observe(duration_ms)

        return response
```

## 7. Database Monitoring

### 7.1 Metrics

| Metric | Source | Current | Target |
|--------|--------|---------|--------|
| Query count | DB wrapper | ❌ | Counter |
| Slow queries (>100ms) | DB wrapper | ❌ | Counter with query fingerprint |
| Connection count | Pool stats | ❌ | Gauge |
| Connection wait time | Pool stats | ❌ | Histogram |
| Lock wait time | DB instrumentation | ❌ | Gauge |
| Migration status | Migration runner | ❌ | Gauge (up-to-date=1) |

## 8. Cache Monitoring

### 8.1 Metrics

| Metric | Source | Current | Target |
|--------|--------|---------|--------|
| Cache hits | Redis client | ❌ | Counter |
| Cache misses | Redis client | ❌ | Counter |
| Hit ratio | Calculated | ❌ | Gauge |
| Cache size | Redis INFO | ❌ | Gauge |
| Eviction count | Redis INFO | ❌ | Counter |
| Memory usage | Redis INFO | ❌ | Gauge |

## 9. Event-Driven Monitoring

### 9.1 Current EventBus

`aidaos/domain/events.py` already defines monitoring-relevant events:
- `AGENT_STARTED`, `AGENT_COMPLETED`, `AGENT_FAILED`
- `WORKFLOW_STARTED`, `WORKFLOW_COMPLETED`, `WORKFLOW_FAILED`
- `METRICS_UPDATED`, `ERROR_LOGGED`

### 9.2 Target Event-Driven Metrics

```python
# Event → Metrics mapping
EVENT_METRICS_MAP = {
    DomainEventType.AGENT_STARTED: lambda e: metrics.agent_calls.labels(
        agent=e.agent_name, status="started").inc(),
    DomainEventType.AGENT_COMPLETED: lambda e: (
        metrics.agent_calls.labels(agent=e.agent_name, status="completed").inc(),
        metrics.agent_latency.labels(agent=e.agent_name).observe(e.duration_ms),
    ),
    DomainEventType.AGENT_FAILED: lambda e: metrics.agent_calls.labels(
        agent=e.agent_name, status="failed").inc(),
}
```

## 10. Existing vs Target Architecture

| Aspect | Current (Phase 0) | Target (Phase 2) |
|--------|-------------------|-------------------|
| Metrics format | SQLite rows | Prometheus (OpenMetrics) |
| Collection | Manual (never called) | Automatic (middleware + wrappers) |
| Storage | SQLite (2 separate DBs) + in-memory | Prometheus TSDB + SQLite + Thanos |
| Retention | 7 days / unlimited / process | Policy-based (15d → 90d → 1yr) |
| System metrics | None | `psutil` + `pynvml` exporters |
| Health checks | `/api/v2/status/` | `/health`, `/ready`, `/livez` |
| Alerting | None | Threshold rules → Slack/PagerDuty |
| Dashboard | None | Grafana + In-App |
| Tracing | None | OpenTelemetry + Jaeger |
| Events | In-process (unused) | Event → Prometheus metrics bridge |

## 11. Service Discovery

### 11.1 What to Monitor

```
Backend (Django)            → /health, /metrics
  ├── API endpoints          → Middleware metrics
  ├── LLM Gateway            → Provider health + metrics
  ├── Agent Orchestrator      → Agent status + metrics
  ├── Tool Registry          → Tool call metrics
  ├── Memory Engine          → Hit rate, latency
  ├── Plugin System          → Load status, errors
  └── Auth System            → Login rate, error rate

Frontend (React/Vite)        → Web Vitals, error tracking
  ├── LCP, FID, CLS          → Browser metrics
  ├── API call latency       → Frontend monitoring
  └── Error rates             → Sentry/Rollbar

Infrastructure              → Node exporter + cAdvisor
  ├── Docker containers       → Container metrics
  ├── Kubernetes pods         → Kube state metrics
  ├── PostgreSQL              → PG exporter
  ├── Redis                   → Redis exporter
  └── Qdrant                  → Vector DB exporter
```

## 12. Implementation Roadmap

| Phase | Component | Timeline | Effort |
|-------|-----------|----------|--------|
| P0 | Prometheus metrics endpoint | Week 1 | Small |
| P0 | API metrics middleware | Week 1 | Small |
| P0 | `/health` + `/ready` endpoints | Week 1 | Small |
| P0 | LLM provider metrics wrapper | Week 2 | Medium |
| P1 | Agent metrics → Prometheus bridge | Week 2 | Medium |
| P1 | System metrics exporter (CPU/RAM/GPU) | Week 3 | Medium |
| P1 | Grafana dashboards (basic) | Week 3 | Medium |
| P1 | Database + cache metrics | Week 4 | Medium |
| P2 | Alert rules (CPU, latency, errors) | Week 4 | Small |
| P2 | Slack/PagerDuty notifications | Week 5 | Medium |
| P2 | Docker Compose with Prometheus/Grafana | Week 5 | Small |
| P3 | OpenTelemetry tracing | Week 6 | Large |
| P3 | Kubernetes monitoring (kube-prometheus) | Week 7 | Large |
| P3 | In-app dashboard | Week 8 | Large |
| P3 | Cost tracking dashboard | Week 8 | Medium |
