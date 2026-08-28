# AIDA Enterprise Monitoring Platform
## Metrics Guide

**Versiya:** 1.0.0  
**Sana:** 2026-07-03  
**Muallif:** AIDA SRE Team  
**Holat:** Production-Ready Design

---

## 1. METRIKA TURLARI

### Prometheus Metrika Turlari

| Tur | Tavsif | Misol |
|-----|--------|-------|
| **Counter** | Faqat oshadi, reset bo'lmaydi | request_total, errors_total |
| **Gauge** | Ko'tariladi va tushadi | cpu_usage, active_connections |
| **Histogram** | Qiymatlarni bucketlarga taqsimlaydi | request_duration, response_size |
| **Summary** | Percentillarni hisoblaydi | api_latency_p95, api_latency_p99 |

---

## 2. NAMING CONVENTION

```
Metrika nomi formati:
{namespace}_{subsystem}_{metric_name}_{unit}

Misol:
  aida_api_requests_total           → counter
  aida_api_request_duration_seconds → histogram
  aida_db_connections_active        → gauge
  aida_model_tokens_input_total     → counter

Qoidalar:
  ✅ lowercase va underscore
  ✅ unit suffix (seconds, bytes, total, ratio)
  ✅ namespace bilan boshlanadi (aida_)
  ❌ camelCase ishlatilmaydi
  ❌ dashlari ishlatilmaydi
  ❌ PII ma'lumot label'da bo'lmasin
```

---

## 3. INFRASTRUCTURE METRICS

### 3.1 CPU Metrics

```
METRIC: node_cpu_seconds_total
TYPE:   Counter
LABELS: mode (user, system, idle, iowait, ...)
FORMULA: 100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
USAGE:  CPU usage percentage

METRIC: container_cpu_usage_seconds_total
TYPE:   Counter
LABELS: container, pod, namespace
USAGE:  Per-container CPU usage (Docker/K8s)

METRIC: aida_system_cpu_usage_percent
TYPE:   Gauge
LABELS: instance, core
USAGE:  AIDA custom CPU gauge (computed)
COLLECT INTERVAL: 15s
```

### 3.2 RAM Metrics

```
METRIC: node_memory_MemTotal_bytes
TYPE:   Gauge
LABELS: instance
USAGE:  Total RAM

METRIC: node_memory_MemAvailable_bytes
TYPE:   Gauge
LABELS: instance
USAGE:  Available RAM

METRIC: aida_system_ram_usage_percent
TYPE:   Gauge
LABELS: instance
FORMULA: 100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)
COLLECT INTERVAL: 15s
```

### 3.3 GPU Metrics

```
METRIC: nvidia_gpu_utilization_percent
TYPE:   Gauge
LABELS: gpu_index, gpu_name, instance
USAGE:  GPU compute utilization

METRIC: nvidia_gpu_memory_used_bytes
TYPE:   Gauge
LABELS: gpu_index, gpu_name, instance
USAGE:  GPU VRAM usage

METRIC: nvidia_gpu_memory_total_bytes
TYPE:   Gauge
LABELS: gpu_index, gpu_name, instance
USAGE:  GPU VRAM total

METRIC: nvidia_gpu_temperature_celsius
TYPE:   Gauge
LABELS: gpu_index, instance
USAGE:  GPU temperature
COLLECT INTERVAL: 15s
SOURCE: DCGM Exporter / nvidia-smi
```

### 3.4 Disk Metrics

```
METRIC: node_filesystem_size_bytes
TYPE:   Gauge
LABELS: device, fstype, mountpoint, instance
USAGE:  Total disk size

METRIC: node_filesystem_free_bytes
TYPE:   Gauge
LABELS: device, fstype, mountpoint, instance
USAGE:  Free disk space

METRIC: node_disk_read_bytes_total
TYPE:   Counter
LABELS: device, instance
USAGE:  Total bytes read from disk

METRIC: node_disk_written_bytes_total
TYPE:   Counter
LABELS: device, instance
USAGE:  Total bytes written to disk

METRIC: node_disk_io_time_seconds_total
TYPE:   Counter
LABELS: device, instance
USAGE:  Disk I/O utilization
COLLECT INTERVAL: 30s
```

### 3.5 Network Metrics

```
METRIC: node_network_receive_bytes_total
TYPE:   Counter
LABELS: device, instance
USAGE:  Bytes received

METRIC: node_network_transmit_bytes_total
TYPE:   Counter
LABELS: device, instance
USAGE:  Bytes transmitted

METRIC: node_network_receive_errs_total
TYPE:   Counter
LABELS: device, instance
USAGE:  Network receive errors

METRIC: node_network_transmit_errs_total
TYPE:   Counter
LABELS: device, instance
USAGE:  Network transmit errors
COLLECT INTERVAL: 15s
```

---

## 4. APPLICATION METRICS (BACKEND)

### 4.1 API Metrics

```
METRIC: aida_http_requests_total
TYPE:   Counter
LABELS: method, endpoint, status_code
USAGE:  Total HTTP requests
NOTE:   endpoint label normalized (no IDs in path)

METRIC: aida_http_request_duration_seconds
TYPE:   Histogram
LABELS: method, endpoint
BUCKETS: [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
USAGE:  Request latency distribution (p50, p95, p99 derivable)

METRIC: aida_http_request_size_bytes
TYPE:   Histogram
LABELS: method, endpoint
USAGE:  Request payload sizes

METRIC: aida_http_response_size_bytes
TYPE:   Histogram
LABELS: method, endpoint
USAGE:  Response payload sizes

METRIC: aida_http_errors_total
TYPE:   Counter
LABELS: method, endpoint, error_type
USAGE:  HTTP error count

COLLECT INTERVAL: On every request (push)
```

### 4.2 Authentication Metrics

```
METRIC: aida_auth_login_attempts_total
TYPE:   Counter
LABELS: status (success, failure), method (password, token, sso)
USAGE:  Login attempt tracking

METRIC: aida_auth_failed_logins_total
TYPE:   Counter
LABELS: reason (wrong_password, expired_token, locked)
USAGE:  Failed login analysis
NOTE:   IP yoki username label'ga qo'shilmaydi (PII himoyasi)

METRIC: aida_auth_active_sessions_count
TYPE:   Gauge
LABELS: method
USAGE:  Active user sessions

METRIC: aida_auth_token_refresh_total
TYPE:   Counter
LABELS: status (success, failure)
USAGE:  Token refresh events

COLLECT INTERVAL: On every auth event (push)
```

### 4.3 Queue Metrics (Celery)

```
METRIC: aida_queue_depth
TYPE:   Gauge
LABELS: queue_name
USAGE:  Tasks waiting in queue

METRIC: aida_queue_tasks_total
TYPE:   Counter
LABELS: queue_name, status (success, failure, retry)
USAGE:  Task completion stats

METRIC: aida_queue_task_duration_seconds
TYPE:   Histogram
LABELS: task_name, queue_name
USAGE:  Task execution time

METRIC: aida_queue_workers_active
TYPE:   Gauge
LABELS: queue_name
USAGE:  Active worker count

COLLECT INTERVAL: 15s (Celery Flower / custom exporter)
```

---

## 5. DATABASE METRICS

```
METRIC: aida_db_queries_total
TYPE:   Counter
LABELS: operation (select, insert, update, delete), table, status
USAGE:  Query count by type

METRIC: aida_db_query_duration_seconds
TYPE:   Histogram
LABELS: operation, table
BUCKETS: [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
USAGE:  Query latency

METRIC: aida_db_slow_queries_total
TYPE:   Counter
LABELS: table, operation
THRESHOLD: > 100ms
USAGE:  Slow query counter

METRIC: aida_db_connections_active
TYPE:   Gauge
LABELS: instance
USAGE:  Active DB connections

METRIC: aida_db_connections_max
TYPE:   Gauge
LABELS: instance
USAGE:  Max allowed connections

METRIC: aida_db_locks_total
TYPE:   Counter
LABELS: lock_type
USAGE:  Lock events

METRIC: aida_db_migration_status
TYPE:   Gauge
LABELS: migration_name
VALUES: 1=applied, 0=pending
USAGE:  Migration state tracking

METRIC: aida_db_index_usage_ratio
TYPE:   Gauge
LABELS: table, index
USAGE:  Index effectiveness

COLLECT INTERVAL: 30s (postgres_exporter)
```

---

## 6. CACHE METRICS (REDIS)

```
METRIC: aida_cache_hits_total
TYPE:   Counter
LABELS: cache_name, key_prefix
USAGE:  Cache hit count

METRIC: aida_cache_misses_total
TYPE:   Counter
LABELS: cache_name, key_prefix
USAGE:  Cache miss count

METRIC: aida_cache_hit_ratio
TYPE:   Gauge
LABELS: cache_name
FORMULA: hits / (hits + misses)
USAGE:  Cache effectiveness

METRIC: aida_cache_size_bytes
TYPE:   Gauge
LABELS: instance
USAGE:  Current Redis memory usage

METRIC: aida_cache_evictions_total
TYPE:   Counter
LABELS: instance
USAGE:  Evicted key count

METRIC: aida_cache_keys_total
TYPE:   Gauge
LABELS: instance, database
USAGE:  Total key count

METRIC: aida_cache_connected_clients
TYPE:   Gauge
LABELS: instance
USAGE:  Redis client connections

COLLECT INTERVAL: 15s (redis_exporter)
```

---

## 7. AI MODEL METRICS

```
METRIC: aida_model_requests_total
TYPE:   Counter
LABELS: model_name, provider, status (success, failure, timeout)
USAGE:  Total AI model requests

METRIC: aida_model_request_duration_seconds
TYPE:   Histogram
LABELS: model_name, provider
BUCKETS: [0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
USAGE:  Model response time

METRIC: aida_model_tokens_input_total
TYPE:   Counter
LABELS: model_name, provider
USAGE:  Input tokens consumed

METRIC: aida_model_tokens_output_total
TYPE:   Counter
LABELS: model_name, provider
USAGE:  Output tokens generated

METRIC: aida_model_tokens_max_per_request
TYPE:   Gauge
LABELS: model_name, provider
USAGE:  Max tokens per single request

METRIC: aida_model_memory_usage_bytes
TYPE:   Gauge
LABELS: model_name, provider
USAGE:  Model memory footprint (local models)

METRIC: aida_model_cost_usd_total
TYPE:   Counter
LABELS: model_name, provider
USAGE:  Cumulative cost in USD

METRIC: aida_model_success_rate
TYPE:   Gauge
LABELS: model_name, provider
FORMULA: rate(requests{status="success"}[5m]) / rate(requests_total[5m])
USAGE:  Rolling success rate

METRIC: aida_model_rate_limit_remaining_percent
TYPE:   Gauge
LABELS: provider
USAGE:  Provider rate limit remaining capacity

COLLECT INTERVAL: On each model call (push)
```

---

## 8. AGENT METRICS

```
METRIC: aida_agent_status
TYPE:   Gauge
LABELS: agent_id, agent_name
VALUES: 1=idle, 2=running, 0=error, -1=stopped
USAGE:  Current agent status

METRIC: aida_agent_tasks_total
TYPE:   Counter
LABELS: agent_id, agent_name, status (assigned, completed, failed)
USAGE:  Task statistics per agent

METRIC: aida_agent_task_duration_seconds
TYPE:   Histogram
LABELS: agent_id, agent_name, task_type
USAGE:  Agent task execution time

METRIC: aida_agent_retry_count_total
TYPE:   Counter
LABELS: agent_id, agent_name, reason
USAGE:  Task retry count

METRIC: aida_agent_queue_position
TYPE:   Gauge
LABELS: agent_id
USAGE:  Agent position in queue (0 = active)

METRIC: aida_agent_pool_size
TYPE:   Gauge
LABELS: status (active, idle, error, stopped)
USAGE:  Agent pool composition

COLLECT INTERVAL: 10s (agent heartbeat push)
```

---

## 9. WORKFLOW METRICS

```
METRIC: aida_workflow_runs_total
TYPE:   Counter
LABELS: workflow_name, status (started, completed, failed)
USAGE:  Workflow execution count

METRIC: aida_workflow_current_step
TYPE:   Gauge
LABELS: workflow_id, workflow_name
USAGE:  Current step number

METRIC: aida_workflow_total_steps
TYPE:   Gauge
LABELS: workflow_id, workflow_name
USAGE:  Total steps in workflow

METRIC: aida_workflow_execution_time_seconds
TYPE:   Histogram
LABELS: workflow_name
USAGE:  End-to-end workflow duration

METRIC: aida_workflow_step_duration_seconds
TYPE:   Histogram
LABELS: workflow_name, step_name
USAGE:  Per-step execution time

METRIC: aida_workflow_errors_total
TYPE:   Counter
LABELS: workflow_name, step_name, error_type
USAGE:  Workflow error count

METRIC: aida_workflow_active_count
TYPE:   Gauge
LABELS: workflow_name
USAGE:  Currently running workflow instances

COLLECT INTERVAL: On each workflow state change (push)
```

---

## 10. SECURITY METRICS

```
METRIC: aida_security_failed_logins_total
TYPE:   Counter
LABELS: reason
NOTE:   IP va username label'ga QOSHILMAYDI (PII)
USAGE:  Failed login tracking

METRIC: aida_security_suspicious_activity_total
TYPE:   Counter
LABELS: activity_type, severity
USAGE:  Suspicious event tracking

METRIC: aida_security_permission_violations_total
TYPE:   Counter
LABELS: violation_type, endpoint
NOTE:   User identifier maskalanadi
USAGE:  Permission violation tracking

METRIC: aida_security_api_abuse_total
TYPE:   Counter
LABELS: abuse_type
NOTE:   API key maskalanadi
USAGE:  API abuse events

METRIC: aida_security_rate_limit_triggered_total
TYPE:   Counter
LABELS: endpoint, limit_type
NOTE:   Faqat aggregated, individual IP yo'q
USAGE:  Rate limit activations

COLLECT INTERVAL: On each security event (push)
```

---

## 11. METRIKA SAQLASH SIYOSATI

### 11.1 Yig'ish Intervallari

| Metrika turi | Interval | Sabab |
|--------------|----------|-------|
| CPU, RAM, Network | 15s | Real-time monitoring |
| API requests | Push (per-request) | Yuqori granularlik |
| DB queries | 30s | DB overhead kamaytirish |
| Redis | 15s | Cache state tez o'zgaradi |
| AI model calls | Push (per-call) | Aniq hisob |
| Agent status | 10s | Tez reaksiya |
| Health checks | 10–60s | Servis turini qarang |
| Disk, GPU | 30s | Sekin o'zgaradi |

### 11.2 Retention Siyosati

```
Storage Tiers:

TIER 1 — Hot (Prometheus local TSDB)
  Retention:  15 gün
  Resolution: 15s (as-is)
  Use case:   Real-time dashboard, alerting

TIER 2 — Warm (VictoriaMetrics)
  Retention:  90 gün
  Resolution: 1m (downsampled)
  Use case:   Trend analysis, weekly reports

TIER 3 — Cold (Object Storage: S3 / MinIO)
  Retention:  365 gün
  Resolution: 5m (heavily downsampled)
  Use case:   Capacity planning, compliance, auditing
```

### 11.3 Aggregatsiya Qoidalari

```
Recording Rules (Prometheus):

# API success rate (har 5 daqiqada bir hisoblash)
record: aida_api_success_rate_5m
expr:   rate(aida_http_requests_total{status_code!~"5.."}[5m])
        / rate(aida_http_requests_total[5m])

# Average model response time
record: aida_model_avg_response_seconds_5m
expr:   rate(aida_model_request_duration_seconds_sum[5m])
        / rate(aida_model_request_duration_seconds_count[5m])

# Agent utilization rate
record: aida_agent_utilization_5m
expr:   count(aida_agent_status == 2)   # running
        / count(aida_agent_status >= 0)  # all non-stopped
```

### 11.4 Siqish (Compression)

| Tier | Format | Siqish koeffitsiyenti |
|------|--------|-----------------------|
| Hot | Prometheus TSDB blocks | ~10x |
| Warm | VictoriaMetrics | ~20x |
| Cold | Parquet + gzip (S3) | ~50x |

### 11.5 Backup

```
Backup Strategiyasi:

Prometheus snapshots:
  Frequency: Har 6 soatda
  Location:  S3 bucket (aida-monitoring-backup)
  Retention: 30 kun

VictoriaMetrics backup:
  Frequency: Har kecha 02:00
  Location:  S3 bucket (aida-monitoring-archive)
  Retention: 90 kun

Grafana dashboards:
  Method:    Grafana API export → JSON
  Frequency: Har deploy da
  Location:  Git repo (docs/monitoring/grafana/)
  Retention: Git history
```

---

## 12. HIGH CARDINALITY MUAMMOLARI

### ❌ Qilmaslik

```
# XATO — user_id label yuqori cardinality yaratadi
aida_api_requests_total{user_id="12345"}   ← YOMON

# XATO — session_id har request yangi time series
aida_api_requests_total{session_id="abc"}  ← YOMON

# XATO — URL parametrli endpoint
aida_api_requests_total{endpoint="/api/users/123/profile"}  ← YOMON
```

### ✅ To'g'ri yondashuv

```
# TO'G'RI — endpoint normalized
aida_api_requests_total{endpoint="/api/users/:id/profile"}  ← YAXSHI

# TO'G'RI — user segmenti (aggregated)
aida_api_requests_total{user_type="premium"}  ← YAXSHI

# TO'G'RI — faqat kerakli labellar
aida_api_requests_total{method="POST", status_code="200"}  ← YAXSHI
```

---

## 13. CUSTOM METRICS QO'SHISH QOIDALARI

Yangi metrika qo'shishda majburiy jarayon:

```
1. NAMING
   ✓ aida_ namespace bilan boshlang
   ✓ unit suffix qo'shing (_total, _seconds, _bytes, _ratio)
   ✓ mavjud metrikalar bilan nomlar to'qnashmaydi

2. LABELS
   ✓ max 5 label
   ✓ PII bo'lmagan qiymatlar faqat
   ✓ low-cardinality (< 100 unique value)

3. TYPE
   ✓ oshuvchi qiymat → Counter
   ✓ o'zgaruvchan → Gauge
   ✓ latency/size → Histogram
   ✓ percentile kerak → Summary (faqat kerak bo'lsa)

4. DOCUMENTATION
   ✓ bu fayl (Metrics_Guide.md)ga qo'shing
   ✓ alert rule yozing (kerak bo'lsa)
   ✓ Grafana panel qo'shing

5. REVIEW
   ✓ SRE review talab qilinadi
   ✓ Cardinality estimate taqdim eting
```

---

*Hujjat AIDA Development Bible — Book 1, Chapter 7 asosida tayyorlangan.*
