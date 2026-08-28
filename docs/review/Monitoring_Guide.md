# AIDA Event Bus Monitoring Guide

**Document:** Book 2, Chapter 4 — Monitoring Guide
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Monitoring Guide defines metrics, dashboards, alerting rules, and observability practices for the Event Bus. It ensures complete visibility into event flow, performance, and health.

---

## 2. Monitoring Architecture

### 2.1 Metrics Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EVENT BUS MONITORING                              │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Metrics Collection                         │   │
│  │  - Event counts (published, consumed, failed)                │   │
│  │  - Latency (publish, route, deliver, process)                │   │
│  │  - Queue depth (per queue, per subscriber)                   │   │
│  │  - Consumer lag (per subscriber)                             │   │
│  │  - Error rates (per topic, per subscriber)                   │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│     ↓                       │                                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Metrics Storage                            │   │
│  │  - Prometheus (time series)                                   │   │
│  │  - Redis (real-time counters)                                 │   │
│  │  - PostgreSQL (historical)                                    │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│     ↓                       │                                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Dashboards & Alerting                      │   │
│  │  - Grafana (real-time dashboards)                             │   │
│  │  - AlertManager (alert routing)                               │   │
│  │  - PagerDuty (incident management)                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Key Metrics

### 3.1 Throughput Metrics

| Metric | Type | Description | Target |
|--------|------|-------------|--------|
| `eventbus_published_total` | Counter | Total events published | Track |
| `eventbus_consumed_total` | Counter | Total events consumed | Track |
| `eventbus_delivered_total` | Counter | Total events delivered | Track |
| `eventbus_processed_total` | Counter | Total events processed | Track |
| `eventbus_failed_total` | Counter | Total events failed | < 1% |
| `eventbus_dropped_total` | Counter | Total events dropped | < 0.1% |

### 3.2 Latency Metrics

| Metric | Type | Description | Target |
|--------|------|-------------|--------|
| `eventbus_publish_latency_ms` | Histogram | Time to publish event | P95 < 10ms |
| `eventbus_route_latency_ms` | Histogram | Time to route event | P95 < 5ms |
| `eventbus_deliver_latency_ms` | Histogram | Time to deliver event | P95 < 50ms |
| `eventbus_process_latency_ms` | Histogram | Time to process event | P95 < 100ms |
| `eventbus_end_to_end_latency_ms` | Histogram | Total event lifecycle | P95 < 200ms |

### 3.3 Queue Metrics

| Metric | Type | Description | Target |
|--------|------|-------------|--------|
| `eventbus_queue_depth` | Gauge | Events in queue | < 1000 |
| `eventbus_queue_size_bytes` | Gauge | Queue size in bytes | < 100MB |
| `eventbus_consumer_lag` | Gauge | Events behind consumer | < 100 |
| `eventbus_consumer_rate` | Gauge | Events consumed per second | Track |

### 3.4 Error Metrics

| Metric | Type | Description | Target |
|--------|------|-------------|--------|
| `eventbus_error_rate` | Gauge | Error percentage | < 1% |
| `eventbus_retry_rate` | Gauge | Retry percentage | < 5% |
| `eventbus_dead_letter_rate` | Gauge | DLQ percentage | < 0.1% |
| `eventbus_auth_failure_rate` | Gauge | Auth failure rate | < 0.1% |

### 3.5 System Metrics

| Metric | Type | Description | Target |
|--------|------|-------------|--------|
| `eventbus_active_subscriptions` | Gauge | Active subscriptions | Track |
| `eventbus_cluster_nodes` | Gauge | Cluster node count | Track |
| `eventbus_partition_count` | Gauge | Partition count | Track |
| `eventbus_memory_usage_bytes` | Gauge | Memory usage | < 1GB |
| `eventbus_cpu_usage_percent` | Gauge | CPU usage | < 80% |

---

## 4. Dashboards

### 4.1 Overview Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│                  EVENT BUS OVERVIEW DASHBOARD                        │
│                                                                      │
│  Throughput:           Latency (P50/P95/P99):                      │
│  Published: 1234/s     Publish: 2ms / 5ms / 10ms                   │
│  Consumed:  1230/s     Route: 1ms / 3ms / 5ms                      │
│  Failed:    2/s        Deliver: 5ms / 20ms / 50ms                  │
│                        Process: 10ms / 50ms / 200ms                │
│                                                                      │
│  Queue Status:          Consumer Status:                            │
│  Queue depth: 45        Active: 12                                  │
│  DLQ depth: 2           Lagging: 0                                  │
│  Retry depth: 8         Idle: 3                                     │
│                                                                      │
│  Error Rate: 0.16%     Auth Failures: 0                             │
│                                                                      │
│  Cluster: 3/3 nodes healthy                                        │
│  Replication lag: 2ms                                              │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Subscriber Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│                  SUBSCRIBER DASHBOARD                                │
│                                                                      │
│  Subscriber       Status  Received  Processed  Failed  Lag  Rate   │
│  ─────────────────────────────────────────────────────────────────  │
│  task_manager     ACTIVE  15234     15230      4       0    45/s   │
│  workflow_engine  ACTIVE  8923      8920       3       0    28/s   │
│  ai_kernel        ACTIVE  23456     23450      6       2    89/s   │
│  memory_engine    ACTIVE  12345     12340      5       0    35/s   │
│  monitoring       ACTIVE  156789    156780     9       0    456/s  │
│  audit_log        ACTIVE  45678     45678      0       0    120/s  │
│  realtime_stream  PAUSED  0         0          0       0    0/s    │
│  plugin_manager   ACTIVE  2345      2340       5       1    8/s    │
│                                                                      │
│  Total: 8 subscribers (7 active, 1 paused)                         │
│  Total lag: 3 events                                               │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Topic Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│                  TOPIC DASHBOARD                                     │
│                                                                      │
│  Topic               Published/s  Consumed/s  Failed/s  Depth      │
│  ─────────────────────────────────────────────────────────────────  │
│  task.lifecycle       45           45          0         0          │
│  agent.lifecycle      28           28          0         0          │
│  ai.request           89           89          0         2          │
│  ai.response          89           89          0         0          │
│  user.message         35           35          0         0          │
│  workflow.step        15           15          0         0          │
│  memory.write         42           42          0         0          │
│  security.auth        12           12          0         0          │
│  monitoring.metrics   456          456         0         0          │
│                                                                      │
│  Total: 9 topics, 811 events/s                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Alerting Rules

### 5.1 Critical Alerts

| Alert | Condition | Duration | Action |
|-------|-----------|----------|--------|
| `EventBusDown` | Event Bus unreachable | 1m | Page on-call |
| `HighErrorRate` | error_rate > 5% | 5m | Page on-call |
| `ConsumerLagCritical` | consumer_lag > 10000 | 5m | Page on-call |
| `QueueOverflow` | queue_depth > 100000 | 2m | Page on-call |
| `ReplicationLagHigh` | replication_lag > 1s | 5m | Page on-call |

### 5.2 Warning Alerts

| Alert | Condition | Duration | Action |
|-------|-----------|----------|--------|
| `HighErrorRate` | error_rate > 1% | 10m | Slack alert |
| `ConsumerLagWarning` | consumer_lag > 1000 | 10m | Slack alert |
| `QueueDepthWarning` | queue_depth > 10000 | 10m | Slack alert |
| `LatencyHigh` | P95 > 500ms | 10m | Slack alert |
| `DeadLetterGrowing` | dlq_rate > 0.1% | 30m | Slack alert |

### 5.3 Alert Configuration

```yaml
alerts:
  # Critical
  - name: EventBusDown
    expr: up{job="eventbus"} == 0
    for: 1m
    severity: critical
    action: page
    
  - name: HighErrorRate
    expr: eventbus_error_rate > 0.05
    for: 5m
    severity: critical
    action: page
    
  # Warning
  - name: ConsumerLagWarning
    expr: eventbus_consumer_lag > 1000
    for: 10m
    severity: warning
    action: slack
    
  - name: LatencyHigh
    expr: histogram_quantile(0.95, eventbus_deliver_latency_ms) > 500
    for: 10m
    severity: warning
    action: slack
```

---

## 6. Logging

### 6.1 Log Levels

| Level | When | What |
|-------|------|------|
| `ERROR` | Errors only | Failures, exceptions |
| `WARN` | Warnings | Degraded performance |
| `INFO` | Normal | Event flow, routing decisions |
| `DEBUG` | Debugging | Detailed event data |

### 6.2 Log Format

```json
{
  "timestamp": "2026-07-04T01:00:00Z",
  "level": "INFO",
  "logger": "eventbus.router",
  "message": "Event routed",
  "event_id": "uuid",
  "event_type": "task.completed",
  "topic": "task.lifecycle",
  "source": "task_manager",
  "targets": ["workflow_engine", "monitoring"],
  "latency_ms": 3,
  "correlation_id": "uuid"
}
```

### 6.3 Log Configuration

```yaml
logging:
  level: INFO
  
  # Structured logging
  format: json
  
  # Output
  outputs:
    - type: stdout
      format: json
    - type: file
      path: /var/log/eventbus/eventbus.log
      rotation: daily
      retention: 30d
    - type: elasticsearch
      host: localhost:9200
      index: eventbus-logs
      
  # Sensitive data
  redact_fields:
    - payload.credit_card
    - payload.ssn
    - metadata.api_key
```

---

## 7. Tracing

### 7.1 Distributed Tracing

```yaml
tracing:
  enabled: true
  
  # Provider
  provider: jaeger  # jaeger | zipkin | otel
  
  # Sampling
  sampling:
    strategy: probabilistic
    rate: 0.1  # 10% of events
    
  # Tags
  tags:
    - event_type
    - topic
    - source
    - priority
```

### 7.2 Trace Span

```python
class EventTraceSpan:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    
    operation: str  # publish, route, deliver, process
    start_time: datetime
    end_time: datetime
    
    tags: dict
    logs: list[dict]
```

---

## 8. Health Checks

### 8.1 Health Check Endpoints

| Endpoint | Description | Response |
|----------|-------------|----------|
| `/health` | Basic health check | 200 OK |
| `/health/ready` | Readiness probe | 200 / 503 |
| `/health/live` | Liveness probe | 200 / 503 |
| `/health/detail` | Detailed health | JSON |

### 8.2 Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2026-07-04T01:00:00Z",
  "components": {
    "redis": {
      "status": "healthy",
      "latency_ms": 1
    },
    "postgresql": {
      "status": "healthy",
      "latency_ms": 5
    },
    "router": {
      "status": "healthy",
      "active_subscriptions": 12
    },
    "queue": {
      "status": "healthy",
      "depth": 45
    }
  }
}
```

---

## 9. Configuration

```yaml
monitoring:
  # Metrics
  metrics:
    enabled: true
    provider: prometheus
    endpoint: /metrics
    interval: 15s
    
  # Dashboards
  dashboards:
    enabled: true
    provider: grafana
    auto_provision: true
    
  # Alerting
  alerting:
    enabled: true
    provider: alertmanager
    routes:
      - severity: critical
        action: page
      - severity: warning
        action: slack
        
  # Logging
  logging:
    level: INFO
    format: json
    outputs: [stdout, file, elasticsearch]
    
  # Tracing
  tracing:
    enabled: true
    provider: jaeger
    sampling_rate: 0.1
    
  # Health checks
  health_check:
    enabled: true
    endpoints: ["/health", "/health/ready", "/health/live"]
```
