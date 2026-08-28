# AIDA Tool Health

**Document:** Book 2, Chapter 9 - Tool Health
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

Tool Health monitoring tracks **availability, latency, error rate, success rate, CPU usage, and RAM usage** for every tool. It enables proactive failure detection and automatic tool rotation.

---

## 2. Health Metrics

| Metric | Description | Threshold |
|--------|-------------|-----------|
| Availability | Uptime percentage | > 99% |
| Latency | Average response time | < 5s |
| Error Rate | Failed executions / total | < 5% |
| Success Rate | Successful executions / total | > 95% |
| CPU Usage | Average CPU utilization | < 80% |
| RAM Usage | Average memory utilization | < 80% |

---

## 3. Health Status

| Status | Criteria | Action |
|--------|----------|--------|
| healthy | All metrics within thresholds | Use freely |
| degraded | Some metrics exceeded | Use with caution |
| unhealthy | Critical metrics exceeded | Avoid use |
| offline | Unavailable | Do not use |

---

## 4. Health Check Process

```
1. Load tool descriptor
2. Execute health check command
3. Measure response time
4. Check for errors
5. Update health metrics
6. Calculate health status
7. If status changed: emit event
8. Store health record
```

---

## 5. Health History

```
HealthRecord:
  tool_id: string
  timestamp: datetime
  status: HealthStatus
  availability: float
  latency_ms: int
  error_rate: float
  success_rate: float
  cpu_percent: float
  ram_percent: float
  last_error: string
```

---

## 6. Configuration

```yaml
tool_health:
  enabled: true
  check_interval: 60
  history_retention: 30d
  
  thresholds:
    availability: 0.99
    latency_ms: 5000
    error_rate: 0.05
    success_rate: 0.95
    cpu_percent: 80
    ram_percent: 80
  
  actions:
    on_degraded: warn
    on_unhealthy: disable
    on_offline: remove
```
