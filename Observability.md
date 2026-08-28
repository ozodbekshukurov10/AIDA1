# AIDA — Enterprise Observability Platform

## 1. Three Pillars of Observability

Observability — bu tizim ichida nima bo'layotganini tashqaridan so'rov yubormasdan tushunish imkoniyati. Uch asosiy ustunga asoslanadi:

```
┌──────────────────────────────────────────────────────────────┐
│                      OBSERVABILITY                            │
│                                                              │
│  ┌──────────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │     METRICS      │  │     LOGS     │  │    TRACES     │  │
│  │  (What?)         │  │  (Why?)      │  │  (Where?)     │  │
│  │                  │  │              │  │               │  │
│  │ CPU: 45%         │  │ Error: DB    │  │ Request →     │  │
│  │ Requests: 234    │  │ connection   │  │  Auth → API   │  │
│  │ Latency: 120ms   │  │ timeout at   │  │  → LLM → DB   │  │
│  │ Error rate: 0.5% │  │ 12:00:03     │  │  → Response   │  │
│  └──────────────────┘  └──────────────┘  └───────────────┘  │
│                                                              │
│              OpenTelemetry · Prometheus · Loki · Tempo        │
└──────────────────────────────────────────────────────────────┘
```

**Current State**: Faqat metrics ustuni qisman mavjud. Logs va traces to'liq implementatsiya qilinmagan.

## 2. Logging (Loki / Elasticsearch)

### 2.1 Current Logging

`aidaos/infrastructure/logging/__init__.py` JSON formatda log yozadi:

```json
{
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "level": "INFO",
  "logger": "aida.services.chat",
  "message": "Chat response generated",
  "module": "chat_service",
  "function": "chat",
  "context": {"session_id": "sess_abc123", "request_id": "req_def456"}
}
```

### 2.2 Target: Structured Logging → Loki

```
AIDA App → JSON logs (stdout + file) → Promtail → Loki → Grafana
```

**Promtail config**:

```yaml
# promtail.yml
scrape_configs:
  - job_name: aida
    static_configs:
      - targets: [localhost]
        labels:
          job: aida
          __path__: /var/log/aida/*.log
    pipeline_stages:
      - json:
          expressions:
            timestamp: timestamp
            level: level
            logger: logger
            request_id: context.request_id
            session_id: context.session_id
      - timestamp:
          source: timestamp
          format: RFC3339Nano
      - labels:
          level:
          logger:
```

### 2.3 Log Query Examples (LogQL)

```logql
# All errors in last hour
{job="aida"} |= "ERROR"

# Specific session
{job="aida"} | json | session_id="sess_abc123"

# LLM latency > 5s
{logger=~"aida.ai.*"} |= "response_time_ms" | json |
  response_time > 5000

# Rate of errors per minute
rate({job="aida", level="ERROR"}[5m])

# Errors by logger group
sum by (logger) (count_over_time({job="aida", level="ERROR"}[1h]))
```

## 3. Distributed Tracing (OpenTelemetry + Jaeger/Tempo)

### 3.1 Why Tracing?

AIDA'da bitta request bir necha servis va komponentlardan o'tadi:

```
User Request
  └── API Gateway
        └── Auth Middleware (5ms)
        └── Orchestrator (200ms)
              ├── Code Agent (2.1s)
              │     ├── LLM Call (1.8s)
              │     ├── Tool: search_code (120ms)
              │     └── Tool: read_file (45ms)
              ├── Security Agent (1.5s)
              │     └── LLM Call (1.2s)
              └── Response Assembly (50ms)
  └── Response (total: 4.2s)
```

Har bir qadamning qancha vaqt olganini ko'rish — tracing.

### 3.2 Trace Structure

```
Trace: req_abc123
  ├── Span: POST /api/v2/chat
  │     ├── Span: authenticate (3ms)
  │     ├── Span: route_to_agent (1ms)
  │     ├── Span: agent.code_review.execute (2.1s)
  │     │     ├── Span: llm.openai.generate (1.8s)
  │     │     │     ├── Event: "request_started" timestamp=...
  │     │     │     ├── Event: "response_received" timestamp=...
  │     │     │     └── Attributes: tokens=570, model="gpt-4o"
  │     │     ├── Span: tool.search_code (120ms)
  │     │     │     └── Attributes: query="CVE-2026", results=5
  │     │     └── Span: tool.read_file (45ms)
  │     │           └── Attributes: path="src/main.py", size=2KB
  │     └── Span: format_response (50ms)
  └── Root latency: 4.2s
```

### 3.3 OpenTelemetry Implementation

```python
# aida/infrastructure/tracing/__init__.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_tracing(service_name: str = "aida", otlp_endpoint: str = "http://tempo:4317"):
    provider = TracerProvider(
        resource=Resource.create({
            "service.name": service_name,
            "service.version": "2.1.0",
            "deployment.environment": os.getenv("APP_ENV", "development"),
        })
    )
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return trace.get_tracer(__name__)


# Usage in code
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def process_request(request):
    with tracer.start_as_current_span("process_request") as span:
        span.set_attribute("request_id", request.id)
        span.set_attribute("user_id", request.user_id)

        with tracer.start_as_current_span("llm_call") as llm_span:
            llm_span.set_attribute("model", "gpt-4o")
            llm_span.set_attribute("tokens", 570)
            result = await llm.generate(...)

        return result
```

### 3.4 Auto-Instrumentation

```
# Django auto-instrumentation
opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter none \
    --service_name aida-api \
    python manage.py runserver

# Covers:
# - Django requests (URL, method, status code)
# - Database queries (SQL, duration)
# - HTTP client calls (requests, httpx)
# - Redis commands
```

### 3.5 Tracing Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OTEL_ENABLED` | `false` | Enable tracing |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://tempo:4317` | OTLP gRPC endpoint |
| `OTEL_SERVICE_NAME` | `aida` | Service name |
| `OTEL_SAMPLING_RATIO` | `1.0` | Sampling rate (0.0-1.0) |
| `OTEL_TRACES_EXPORTER` | `otlp` | Exporter type |

## 4. Correlation: Metrics + Logs + Traces

### 4.1 Request ID Propagation

Har bir request `request_id` bilan bog'lanadi va uchala pillar'da ham mavjud:

```python
# Middleware sets request_id
request_id = str(uuid.uuid4())

# Metrics: aida_api_requests_total{request_id="req_abc"}
# Logs:    {"level": "INFO", "request_id": "req_abc", ...}
# Traces:  TraceID = req_abc

# Jump from:
#   - Metrics (high latency) → Logs (error details)
#   - Logs (error message) → Trace (full request path)
#   - Trace (slow span) → Logs (context around span)
```

### 4.2 Unified Correlation ID

| ID Type | Format | Scope |
|---------|--------|-------|
| `request_id` | `req_{uuid8}` | Single HTTP request |
| `session_id` | `sess_{uuid8}` | User session |
| `trace_id` | W3C TraceContext | Distributed trace |
| `span_id` | W3C TraceContext | Single operation |

### 4.3 Correlation in Practice

```python
# Log entry with correlation ids
{
  "timestamp": "...",
  "level": "ERROR",
  "logger": "aida.ai.providers.openai",
  "message": "OpenAI API call failed after 3 retries",
  "request_id": "req_abc123",
  "trace_id": "tp_7a8b9c0d1e2f",
  "span_id": "sp_3a4b5c6d",
  "metadata": {
    "provider": "openai",
    "model": "gpt-4o",
    "error_type": "rate_limit",
    "retry_count": 3,
    "execution_time_ms": 45600
  }
}
```

## 5. Observability Stack Architecture

### 5.1 Development (Docker Compose)

```yaml
# docker-compose.observability.yml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes: [./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml]
    ports: ["9090:9090"]

  grafana:
    image: grafana/grafana:latest
    ports: ["3001:3000"]
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources

  loki:
    image: grafana/loki:latest
    ports: ["3100:3100"]
    volumes: [loki_data:/loki]

  promtail:
    image: grafana/promtail:latest
    volumes:
      - ./logs:/var/log/aida
      - ./monitoring/promtail.yml:/etc/promtail/config.yml

  tempo:
    image: grafana/tempo:latest
    ports: ["4317:4317", "4318:4318"]
    volumes: [tempo_data:/tmp/tempo]

  node-exporter:
    image: prom/node-exporter:latest
    network_mode: host

volumes:
  grafana_data:
  loki_data:
  tempo_data:
```

### 5.2 Production (Kubernetes)

```
Prometheus Operator → kube-prometheus-stack (Helm)
  ├── prometheus-server       — Metrics storage
  ├── alertmanager            — Alert routing
  ├── grafana                 — Dashboards
  ├── prometheus-node-exporter — Node metrics
  └── kube-state-metrics      — K8s object metrics

Grafana Loki Stack (Helm)
  ├── loki                    — Log storage
  ├── promtail                — Log collection (DaemonSet)
  └── tempo                   — Trace storage

OpenTelemetry Collector (DaemonSet)
  └── Receives traces from apps → Tempo
```

## 6. SLA / SLO / SLI Definitions

### 6.1 Service Level Indicators

| SLI | Definition | Source |
|-----|-----------|--------|
| API Availability | `(total - 5xx) / total` | `aida_api_requests_total` |
| API Latency (P95) | `histogram_quantile(0.95, ...)` | `aida_api_latency_seconds` |
| LLM Availability | `(total - errors) / total` | `aida_llm_requests_total` |
| LLM Latency (P95) | `histogram_quantile(0.95, ...)` | `aida_llm_latency_seconds` |
| Agent Success Rate | `successful / total` | `aida_agent_calls_total` |
| Agent Latency (P95) | `histogram_quantile(0.95, ...)` | `aida_agent_latency_seconds` |
| Database Availability | `health_check_status` | `aida_health_check_status` |

### 6.2 Service Level Objectives

| Service | SLO | Measurement Window |
|---------|-----|-------------------|
| API | 99.9% availability, P95 < 500ms | 30 days |
| LLM Gateway | 99.5% availability, P95 < 10s | 30 days |
| Agents | 95% success rate, P95 < 60s | 7 days |
| Database | 99.95% availability | 30 days |
| Cache | 90% hit ratio | 24 hours |

### 6.3 Error Budget

```
Monthly Error Budget = (1 - SLO) * total_requests

Example (API SLO 99.9%):
  Total requests/month: 1,000,000
  Error budget: 1,000 errors
  Burn rate alert when > 10% budget consumed in 1 hour
```

## 7. Observability Maturity Model

| Level | Name | Characteristics | AIDA Status |
|-------|------|----------------|-------------|
| **L0** | Reactive | Users report issues | ✅ Current (logs only) |
| **L1** | Monitoring | Basic dashboards, health checks | 🔄 In progress |
| **L2** | Observability | Metrics + Logs + Traces correlated | 📅 Phase 2 |
| **L3** | Proactive | Anomaly detection, predictive | 📅 Phase 3 |
| **L4** | Autonomous | Auto-remediation, self-healing | 📅 Future |

## 8. Runbooks

Har bir muhim alert uchun runbook:

| Alert | Runbook Link | Auto-Remediation |
|-------|-------------|------------------|
| DatabaseDown | [Runbook: DB Recovery](./runbooks/db_recovery.md) | Connection pool retry |
| LLMProviderDown | [Runbook: Provider Failover](./runbooks/llm_failover.md) | Auto-fallback to next provider |
| HighCPUUsage | [Runbook: CPU Throttling](./runbooks/cpu_throttling.md) | — |
| DiskSpaceLow | [Runbook: Disk Cleanup](./runbooks/disk_cleanup.md) | Auto-cleanup logs |
| AgentCrashLoop | [Runbook: Agent Recovery](./runbooks/agent_recovery.md) | Auto-restart agent |

## 9. Implementation Priority

| Phase | Component | Priority | Effort |
|-------|-----------|----------|--------|
| P0 | Request ID propagation across all logs | CRITICAL | Medium |
| P0 | Structured logging → Loki/Promtail | CRITICAL | Medium |
| P1 | OpenTelemetry auto-instrumentation (Django) | HIGH | Medium |
| P1 | Trace → Logs correlation | HIGH | Medium |
| P1 | Docker Compose for full observability stack | HIGH | Small |
| P1 | Grafana datasource provisioning | HIGH | Small |
| P2 | Manual tracing for AI/Agent operations | MEDIUM | Large |
| P2 | SLI/SLO dashboard | MEDIUM | Medium |
| P2 | Grafana Tempo trace exploration | MEDIUM | Medium |
| P3 | Anomaly detection | LOW | Large |
| P3 | Error budget tracking | LOW | Medium |
| P3 | Self-healing runbook automation | LOW | Large |
