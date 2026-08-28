# AIDA — Enterprise Metrics Guide

## 1. Design Principles

Metrikalar — AIDA holatini sonli ko'rsatkichlar orqali ifodalaydi. Har bir metrika:
- **Aniq nomlangan** — `aida_{component}_{metric}{_unit}`
- **Tegli** (`labels`) — filtr va aggregatsiya uchun
- **Typed** — counter, gauge, histogram yoki summary
- **Dokumentlangan** — qanday yig'ilishi, qanday interpretatsiya qilinishi

**Current State**: Uch xil metrika kollektori mavjud (`webapp/monitoring/metrics.py`, `webapp/memory/metrics.py`, `BaseAgent._record()`). Hech biri Prometheus formatida emas.

## 2. Metrics Namespace

### 2.1 Naming Convention

```
aida_{component}_{metric_name}_{unit}

Component:  api, llm, agent, tool, db, cache, queue, system, security, plugin
Metric:     requests, latency, errors, tokens, memory, cpu, gpu
Unit:       total, ms, seconds, bytes, percent

Examples:
  aida_llm_requests_total
  aida_llm_latency_milliseconds
  aida_agent_calls_total
  aida_api_requests_total
  aida_cache_hits_total
  aida_db_query_duration_seconds
```

### 2.2 Metric Types

| Type | Description | Example | When |
|------|-------------|---------|------|
| **Counter** | Monotonik o'suvchi | `aida_llm_requests_total` | Request count, error count |
| **Gauge** | O'zgaruvchan qiymat | `aida_system_cpu_percent` | CPU, RAM, queue depth |
| **Histogram** | Taqsimot (P50/P95/P99) | `aida_api_latency_seconds` | API/LLM/agent latency |
| **Summary** | Quantile'lar bilan | `aida_llm_latency_seconds` | Client-side latency |

## 3. Metrics Catalog

### 3.1 System Metrics

| Metric | Type | Labels | Description | Source |
|--------|------|--------|-------------|--------|
| `aida_system_cpu_percent` | Gauge | `host` | CPU usage percentage | `psutil` |
| `aida_system_memory_percent` | Gauge | `host` | RAM usage percentage | `psutil` |
| `aida_system_memory_available_bytes` | Gauge | `host` | Available RAM in bytes | `psutil` |
| `aida_system_disk_percent` | Gauge | `mount` | Disk usage percentage | `psutil` |
| `aida_system_disk_free_bytes` | Gauge | `mount` | Free disk space | `psutil` |
| `aida_system_gpu_percent` | Gauge | `gpu` | GPU utilization | `pynvml` |
| `aida_system_gpu_memory_percent` | Gauge | `gpu` | GPU memory usage | `pynvml` |
| `aida_system_gpu_temperature` | Gauge | `gpu` | GPU temperature | `pynvml` |
| `aida_system_uptime_seconds` | Counter | — | System uptime | `time.monotonic()` |
| `aida_system_thread_count` | Gauge | — | Active threads | `threading.active_count()` |

### 3.2 API Metrics

| Metric | Type | Labels | Description | Source |
|--------|------|--------|-------------|--------|
| `aida_api_requests_total` | Counter | `endpoint`, `method`, `status` | Total requests | Middleware |
| `aida_api_latency_seconds` | Histogram | `endpoint`, `method` | Request latency | Middleware |
| `aida_api_request_size_bytes` | Histogram | `endpoint` | Request body size | Middleware |
| `aida_api_response_size_bytes` | Histogram | `endpoint` | Response body size | Middleware |
| `aida_api_active_requests` | Gauge | — | Current in-flight requests | Middleware |

### 3.3 LLM Metrics

| Metric | Type | Labels | Description | Source |
|--------|------|--------|-------------|--------|
| `aida_llm_requests_total` | Counter | `provider`, `model`, `status` | LLM request count | Provider wrapper |
| `aida_llm_latency_seconds` | Histogram | `provider`, `model` | Response time | Provider wrapper |
| `aida_llm_ttft_seconds` | Histogram | `provider`, `model` | Time to first token | Streaming wrapper |
| `aida_llm_tokens_total` | Counter | `provider`, `type` | Prompt/completion tokens | Provider wrapper |
| `aida_llm_tokens_per_request` | Histogram | `provider`, `type` | Tokens per request | Provider wrapper |
| `aida_llm_cost_total` | Counter | `provider`, `model` | Cumulative cost (USD) | Cost calculator |
| `aida_llm_rate_limited_total` | Counter | `provider` | Rate limit hits | Provider wrapper |
| `aida_llm_errors_total` | Counter | `provider`, `error_type` | Error breakdown | Error handler |
| `aida_llm_up` | Gauge | `provider` | Provider online (1/0) | Health check |
| `aida_llm_context_usage_percent` | Gauge | `provider`, `model` | Context window usage | Provider wrapper |

### 3.4 Agent Metrics

| Metric | Type | Labels | Description | Source |
|--------|------|--------|-------------|--------|
| `aida_agent_calls_total` | Counter | `agent`, `status` | Agent executions | BaseAgent |
| `aida_agent_latency_seconds` | Histogram | `agent` | Execution duration | BaseAgent |
| `aida_agent_tokens_total` | Counter | `agent` | Token consumption | BaseAgent |
| `aida_agent_tasks_assigned_total` | Counter | `agent` | Tasks assigned | Orchestrator |
| `aida_agent_tasks_completed_total` | Counter | `agent` | Tasks completed | Orchestrator |
| `aida_agent_tasks_failed_total` | Counter | `agent` | Tasks failed | Orchestrator |
| `aida_agent_retries_total` | Counter | `agent` | Retry count | Orchestrator |
| `aida_agent_queue_depth` | Gauge | `agent` | Pending tasks | Orchestrator |
| `aida_agent_up` | Gauge | `agent` | Agent online (1/0) | Heartbeat |
| `aida_agent_errors_total` | Counter | `agent`, `error_type` | Error breakdown | Error handler |

### 3.5 Tool Metrics

| Metric | Type | Labels | Description | Source |
|--------|------|--------|-------------|--------|
| `aida_tool_calls_total` | Counter | `tool`, `status` | Tool executions | Tool wrapper |
| `aida_tool_latency_seconds` | Histogram | `tool` | Execution duration | Tool wrapper |
| `aida_tool_errors_total` | Counter | `tool`, `error_type` | Error breakdown | Tool wrapper |
| `aida_tool_timeouts_total` | Counter | `tool` | Timeout count | Tool wrapper |

### 3.6 Database Metrics

| Metric | Type | Labels | Description | Source |
|--------|------|--------|-------------|--------|
| `aida_db_queries_total` | Counter | `operation` | Query count | DB wrapper |
| `aida_db_query_duration_seconds` | Histogram | `operation` | Query latency | DB wrapper |
| `aida_db_slow_queries_total` | Counter | `operation` | Slow queries (>100ms) | DB wrapper |
| `aida_db_connections_active` | Gauge | — | Active connections | Pool |
| `aida_db_connections_idle` | Gauge | — | Idle connections | Pool |
| `aida_db_connections_waiting` | Gauge | — | Waiting for connection | Pool |
| `aida_db_migration_status` | Gauge | — | Up-to-date (1) / pending (0) | Migrations |
| `aida_db_lock_wait_seconds` | Histogram | — | Lock wait time | Instrumentation |

### 3.7 Cache Metrics

| Metric | Type | Labels | Description | Source |
|--------|------|--------|-------------|--------|
| `aida_cache_hits_total` | Counter | `cache` | Cache hits | Redis/pylibmc |
| `aida_cache_misses_total` | Counter | `cache` | Cache misses | Redis/pylibmc |
| `aida_cache_hit_ratio` | Gauge | `cache` | Hit ratio | Calculated |
| `aida_cache_operations_total` | Counter | `cache`, `operation` | Get/set/delete count | Client wrapper |
| `aida_cache_evictions_total` | Counter | `cache` | Eviction count | Redis INFO |
| `aida_cache_memory_bytes` | Gauge | `cache` | Memory usage | Redis INFO |
| `aida_cache_keys_total` | Gauge | `cache` | Total keys | Redis DBSIZE |

### 3.8 Security Metrics

| Metric | Type | Labels | Description | Source |
|--------|------|--------|-------------|--------|
| `aida_security_logins_total` | Counter | `status` | Login attempts | Auth system |
| `aida_security_login_failures_total` | Counter | `reason` | Failed logins | Auth system |
| `aida_security_access_denied_total` | Counter | `resource` | Access denied | Authorization |
| `aida_security_token_validated_total` | Counter | `status` | Token validation | Auth middleware |
| `aida_security_token_invalid_total` | Counter | `reason` | Invalid tokens | Auth middleware |
| `aida_security_rate_limited_total` | Counter | `limiter` | Rate limit hits | Rate limiter |
| `aida_security_apikey_usage_total` | Counter | `key_prefix` | API key usage | Auth system |
| `aida_security_suspicious_events_total` | Counter | `type` | Suspicious activity | Security monitor |

### 3.9 Plugin Metrics

| Metric | Type | Labels | Description | Source |
|--------|------|--------|-------------|--------|
| `aida_plugin_installed_total` | Counter | — | Plugin installations | Plugin registry |
| `aida_plugin_errors_total` | Counter | `plugin` | Plugin errors | Plugin system |
| `aida_plugin_load_duration_seconds` | Histogram | `plugin` | Plugin load time | Plugin loader |
| `aida_plugin_up` | Gauge | `plugin` | Plugin active (1/0) | Plugin registry |

### 3.10 Workflow Metrics

| Metric | Type | Labels | Description | Source |
|--------|------|--------|-------------|--------|
| `aida_workflow_starts_total` | Counter | `workflow` | Workflow executions | Workflow engine |
| `aida_workflow_completions_total` | Counter | `workflow` | Successful completions | Workflow engine |
| `aida_workflow_failures_total` | Counter | `workflow` | Failed workflows | Workflow engine |
| `aida_workflow_duration_seconds` | Histogram | `workflow` | Total duration | Workflow engine |
| `aida_workflow_steps_total` | Histogram | `workflow` | Steps per workflow | Workflow engine |

## 4. Metrics Collection

### 4.1 Current Implementation

```python
# Current: BaseAgent._record() — in-memory only, no Prometheus
self.metrics["calls"] += 1
self.metrics["errors"] += 1
self.metrics["total_latency_ms"] += elapsed
self.metrics["tokens_used"] += tokens
```

### 4.2 Target Implementation

```python
# Target: Prometheus metrics wrapper
from prometheus_client import Counter, Histogram, Gauge

class AIDAMetrics:
    def __init__(self):
        # LLM Metrics
        self.llm_requests = Counter(
            'aida_llm_requests_total',
            'Total LLM requests',
            ['provider', 'model', 'status']
        )
        self.llm_latency = Histogram(
            'aida_llm_latency_seconds',
            'LLM request latency',
            ['provider', 'model'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
        )
        self.llm_tokens = Counter(
            'aida_llm_tokens_total',
            'Total tokens consumed',
            ['provider', 'type']  # type: prompt, completion
        )
        self.llm_cost = Counter(
            'aida_llm_cost_total',
            'Total cost in USD',
            ['provider', 'model']
        )

        # Agent Metrics
        self.agent_calls = Counter(
            'aida_agent_calls_total',
            'Total agent executions',
            ['agent', 'status']
        )
        self.agent_latency = Histogram(
            'aida_agent_latency_seconds',
            'Agent execution duration',
            ['agent'],
            buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0)
        )
        self.agent_tokens = Counter(
            'aida_agent_tokens_total',
            'Token consumption by agent',
            ['agent']
        )

        # API Metrics
        self.api_requests = Counter(
            'aida_api_requests_total',
            'Total API requests',
            ['endpoint', 'method', 'status']
        )
        self.api_latency = Histogram(
            'aida_api_latency_seconds',
            'API request latency',
            ['endpoint', 'method'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
        )

        # System Metrics
        self.cpu_usage = Gauge('aida_system_cpu_percent', 'CPU usage', ['host'])
        self.memory_usage = Gauge('aida_system_memory_percent', 'Memory usage', ['host'])
        self.gpu_usage = Gauge('aida_system_gpu_percent', 'GPU usage', ['gpu'])

metrics = AIDAMetrics()
```

### 4.3 Provider Wrapper Pattern

```python
# Target: LLM provider wrapper with metrics
class MonitoredProvider:
    def __init__(self, provider: BaseProvider):
        self._provider = provider
        self._name = provider.__class__.__name__.lower()

    async def generate(self, model: str, messages: list, **kwargs):
        start = time.monotonic()
        try:
            response = await self._provider.generate(model, messages, **kwargs)
            metrics.llm_requests.labels(
                provider=self._name, model=model, status="success"
            ).inc()
            metrics.llm_latency.labels(
                provider=self._name, model=model
            ).observe(time.monotonic() - start)
            metrics.llm_tokens.labels(
                provider=self._name, type="prompt"
            ).inc(response.usage.prompt_tokens)
            metrics.llm_tokens.labels(
                provider=self._name, type="completion"
            ).inc(response.usage.completion_tokens)
            return response
        except Exception as e:
            metrics.llm_requests.labels(
                provider=self._name, model=model, status="error"
            ).inc()
            raise
```

## 5. Metrics Export

### 5.1 Prometheus Endpoint

```python
# urls.py
from django.urls import path
from aida.monitoring.metrics_export import metrics_view

urlpatterns = [
    path('metrics', metrics_view, name='prometheus-metrics'),
]
```

```python
# metrics_export.py
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from django.http import HttpResponse

def metrics_view(request):
    return HttpResponse(
        generate_latest(),
        content_type=CONTENT_TYPE_LATEST
    )
```

### 5.2 Prometheus Scrape Config

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'aida'
    scrape_interval: 15s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['aida-api:8000']
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: 'aida-api'

  - job_name: 'aida-system'
    scrape_interval: 30s
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'aida-gpu'
    scrape_interval: 30s
    static_configs:
      - targets: ['dcgm-exporter:9400']
```

## 6. Metrics Storage & Retention

| Metric Type | Resolution | Retention | Storage |
|-------------|-----------|-----------|---------|
| Raw metrics | 15s | 15 days | Prometheus TSDB |
| 5m downsampled | 5m | 90 days | Thanos |
| 1h aggregated | 1h | 1 year | S3 / GCS |
| Agent SQLite | Per-call | 30 days | Local SQLite |
| Cost data | Per-call | 3 years | PostgreSQL |

## 7. Metrics Dashboard (Grafana)

Har bir metrika uchun tavsiya qilingan vizualizatsiya:

| Metric Type | Chart Type | Panel | Example |
|-------------|-----------|-------|---------|
| Counter | Rate graph | `rate(aida_llm_requests_total[5m])` | Requests per minute |
| Gauge | Stat | `avg(aida_system_cpu_percent)` | Current CPU % |
| Histogram | Heatmap | `histogram_quantile(0.95, ...)` | Latency distribution |
| Summary | Quantile graph | `..._latency_seconds{quantile=~".*"}` | P50/P95/P99 lines |
| Counter | Bar gauge | `topk(5, ...)` | Top 5 agents by calls |

## 8. Implementation Priority

| Phase | Metric Group | Priority | Effort |
|-------|-------------|----------|--------|
| P0 | API metrics (requests, latency) | CRITICAL | Small |
| P0 | LLM metrics (requests, latency, tokens) | CRITICAL | Small |
| P0 | Agent metrics (calls, latency) | CRITICAL | Medium |
| P0 | `/metrics` Prometheus endpoint | CRITICAL | Small |
| P1 | System metrics (CPU, RAM) | HIGH | Medium |
| P1 | Database metrics | HIGH | Medium |
| P1 | Cache metrics | HIGH | Medium |
| P1 | Tool metrics | HIGH | Small |
| P2 | GPU metrics | MEDIUM | Medium |
| P2 | Security metrics | MEDIUM | Medium |
| P2 | Workflow metrics | MEDIUM | Medium |
| P2 | Cost tracking metrics | MEDIUM | Small |
| P3 | Plugin metrics | LOW | Small |
| P3 | Prometheus recording rules | LOW | Medium |
| P3 | Thanos for long-term storage | LOW | Large |
