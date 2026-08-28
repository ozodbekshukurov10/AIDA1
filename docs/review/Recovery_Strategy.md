# AIDA Recovery Strategy

**Document:** Book 2, Chapter 1 — Recovery Strategy
**Version:** 1.0.0
**Date:** 2026-07-04

---

## Overview

The AI Kernel must be **self-healing** — automatically detecting failures, recovering from them, and maintaining service availability. This document defines the recovery strategies for every failure scenario.

---

## 1. Failure Categories

| Category | Examples | Severity | Recovery |
|----------|----------|----------|----------|
| **Transient** | Network timeout, rate limit | LOW | Retry |
| **Persistent** | Provider down, model unavailable | MEDIUM | Fallback |
| **Cascading** | Database overload, memory exhaustion | HIGH | Circuit breaker |
| **Fatal** | Data corruption, security breach | CRITICAL | Shutdown + alert |

---

## 2. Circuit Breaker Pattern

### 2.1 State Machine

```
CLOSED (normal operation)
    ↓ [failure_count ≥ threshold]
OPEN (all calls fail fast)
    ↓ [recovery_timeout elapsed]
HALF_OPEN (one test call)
    ↓ [success] → CLOSED
    ↓ [failure] → OPEN
```

### 2.2 Configuration

```yaml
circuit_breaker:
  # Per-component configuration
  models:
    failure_threshold: 5
    recovery_timeout: 30
    half_open_max_calls: 3
    monitoring_window: 60
    
  agents:
    failure_threshold: 3
    recovery_timeout: 60
    half_open_max_calls: 2
    monitoring_window: 120
    
  tools:
    failure_threshold: 5
    recovery_timeout: 30
    half_open_max_calls: 3
    monitoring_window: 60
    
  database:
    failure_threshold: 3
    recovery_timeout: 10
    half_open_max_calls: 1
    monitoring_window: 30
```

### 2.3 Circuit Breaker Events

| Event | Action |
|-------|--------|
| CircuitOpened | Log warning, emit metric, notify SRE |
| CircuitHalfOpened | Log info, emit metric |
| CircuitClosed | Log info, emit metric |

---

## 3. Retry Strategy

### 3.1 Retry Policies

```yaml
retry_policies:
  exponential_backoff:
    base_delay: 1
    max_delay: 30
    multiplier: 2
    jitter: true
    max_retries: 3
    
  fixed_delay:
    delay: 5
    max_retries: 3
    
  immediate:
    max_retries: 1
    
  respect_retry_after:
    max_retries: 5
    max_delay: 120
```

### 3.2 Per-Error-Type Retry Rules

| Error Type | Retry? | Policy | Max Retries |
|------------|--------|--------|-------------|
| Connection timeout | YES | exponential_backoff | 3 |
| Read timeout | YES | exponential_backoff | 3 |
| Rate limited (429) | YES | respect_retry_after | 5 |
| Service unavailable (503) | YES | exponential_backoff | 3 |
| Bad gateway (502) | YES | exponential_backoff | 2 |
| Authentication failure (401) | NO | — | 0 |
| Authorization failure (403) | NO | — | 0 |
| Not found (404) | NO | — | 0 |
| Validation error (400) | NO | — | 0 |
| Internal error (500) | YES | exponential_backoff | 2 |
| Model overloaded | YES | fixed_delay | 3 |
| Model unavailable | NO (fallback) | — | 0 |

### 3.3 Retry with Jitter

```python
def compute_retry_delay(attempt: int, base_delay: float, max_delay: float) -> float:
    """Exponential backoff with jitter."""
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter
```

---

## 4. Fallback Strategies

### 4.1 Model Fallback Chain

```
Primary Model (deepseek-coder)
  ↓ timeout/rate_limit
Fallback 1 (qwen2.5-coder)
  ↓ timeout/rate_limit
Fallback 2 (gpt-4)
  ↓ timeout
Local Model (rule-based)
  ↓ failure
Error Response
```

### 4.2 Agent Fallback

```
Primary Agent (CodeAgent)
  ↓ failure/unavailable
Fallback Agent (GeneralAgent)
  ↓ failure
Direct LLM Call (bypass agent)
  ↓ failure
Error Response
```

### 4.3 Tool Fallback

```
Primary Tool (git)
  ↓ unavailable
Alternative Tool (shell: git commands)
  ↓ unavailable
Skip Tool (agent adapts without tool)
  ↓ cannot proceed
Error Response
```

### 4.4 Memory System Fallback

```
Full Memory (vector + TF-IDF)
  ↓ failure
Keyword Search Only (TF-IDF)
  ↓ failure
Recent History Only (last 10 messages)
  ↓ failure
No Memory Context (process without)
```

### 4.5 Database Fallback

```
Primary PostgreSQL
  ↓ failure
Read Replica
  ↓ failure
Redis Cache (cached data)
  ↓ failure
In-Memory Cache (single worker)
  ↓ failure
Error Response
```

---

## 5. Graceful Degradation

### 5.1 Degradation Levels

| Level | Condition | Behavior |
|-------|-----------|----------|
| **Level 0** | All systems healthy | Full functionality |
| **Level 1** | One model provider down | Use fallback models |
| **Level 2** | Memory system degraded | Process without memory context |
| **Level 3** | Multiple providers down | Use local model only |
| **Level 4** | Database degraded | Use cached data only |
| **Level 5** | Redis down | In-memory fallback (single worker) |
| **Level 6** | Critical system failure | Minimal responses only |

### 5.2 Degradation Response Templates

```yaml
degradation_responses:
  level_1:
    message: "Some AI models are temporarily unavailable. Using alternative model."
    quality: "slightly_reduced"
    
  level_2:
    message: "Memory system is temporarily unavailable. Processing without context."
    quality: "reduced"
    
  level_3:
    message: "Using local AI. Responses may be less sophisticated."
    quality: "minimal"
    
  level_4:
    message: "Database is temporarily unavailable. Using cached data."
    quality: "reduced"
    
  level_5:
    message: "System under high load. Some features may be slow."
    quality: "degraded"
    
  level_6:
    message: "System experiencing critical issues. Please try again later."
    quality: "minimal"
```

---

## 6. Workflow Recovery

### 6.1 Step Failure Recovery

```
Step Failed
    ↓
Classify Error
    ↓
┌────────────────┬────────────────┬────────────────┐
│ Transient      │ Persistent     │ Fatal          │
│                │                │                │
│ Retry step     │ Skip/replace   │ Abort workflow │
│ (max 3 times)  │ agent/model    │ + cleanup      │
│                │                │                │
│ If still fails │ If still fails │                │
│ → fallback     │ → abort        │                │
└────────────────┴────────────────┴────────────────┘
```

### 6.2 Workflow Checkpointing

```yaml
checkpointing:
  enabled: true
  interval: after_each_step
  store: redis
  ttl: 3600
  fields:
    - workflow_id
    - current_step
    - completed_steps
    - step_results
    - metadata
```

### 6.3 Workflow Resume

```
Workflow Failed
    ↓
Save Checkpoint
    ↓
Determine Recovery Strategy
    ↓
┌────────────────────────────────────────┐
│ Resume from last successful step       │
│ OR                                     │
│ Restart from beginning (if early)      │
│ OR                                     │
│ Skip failed step (if non-critical)     │
│ OR                                     │
│ Abort and notify user                  │
└────────────────────────────────────────┘
```

---

## 7. Data Recovery

### 7.1 Conversation Recovery

```
Conversation Lost (server restart, session expired)
    ↓
Check Redis (session cache)
    ↓ [found]
Restore from Redis
    ↓ [not found]
Check PostgreSQL (persistent storage)
    ↓ [found]
Restore from PostgreSQL
    ↓ [not found]
Start Fresh Conversation
```

### 7.2 Memory Recovery

```
Memory System Failure
    ↓
Switch to Read-Only Mode (process requests, don't store)
    ↓
Background Recovery Process
    ↓
Verify Data Integrity
    ↓
Resume Normal Operation
```

### 7.3 Knowledge Base Recovery

```
Knowledge Base Corruption
    ↓
Switch to Backup Knowledge Store
    ↓
Log Corruption Details
    ↓
Trigger Knowledge Rebuild
    ↓
Verify rebuilt data
    ↓
Resume Normal Operation
```

---

## 8. Alerting Rules

### 8.1 Critical Alerts (Page SRE Immediately)

```yaml
critical_alerts:
  - name: kernel_down
    condition: up{job="aida-kernel"} == 0
    duration: 1m
    severity: critical
    
  - name: error_rate_high
    condition: rate(aida_request_errors_total[5m]) / rate(aida_request_total[5m]) > 0.1
    duration: 5m
    severity: critical
    
  - name: latency_p99_high
    condition: histogram_quantile(0.99, aida_request_duration_seconds) > 10
    duration: 5m
    severity: critical
    
  - name: database_down
    condition: up{job="postgresql"} == 0
    duration: 1m
    severity: critical
```

### 8.2 Warning Alerts (Notify SRE Channel)

```yaml
warning_alerts:
  - name: model_degraded
    condition: aida_model_health_status{status="degraded"} == 1
    duration: 5m
    severity: warning
    
  - name: circuit_breaker_open
    condition: aida_circuit_breaker_state{state="open"} == 1
    duration: 1m
    severity: warning
    
  - name: queue_depth_high
    condition: aida_request_queue_depth > 1000
    duration: 5m
    severity: warning
    
  - name: memory_usage_high
    condition: aida_kernel_memory_usage > 0.8
    duration: 10m
    severity: warning
```

### 8.3 Info Alerts (Log Only)

```yaml
info_alerts:
  - name: model_fallback
    condition: increase(aida_model_fallback_total[5m]) > 0
    severity: info
    
  - name: workflow_retried
    condition: increase(aida_workflow_retry_total[5m]) > 0
    severity: info
```

---

## 9. Disaster Recovery

### 9.1 Backup Strategy

| Data | Backup Frequency | Retention | Method |
|------|-----------------|-----------|--------|
| PostgreSQL | Daily | 30 days | pg_dump + S3 |
| Redis | Every 6 hours | 7 days | RDB + AOF |
| Knowledge Base | Daily | 30 days | File copy |
| Configuration | On change | 90 days | Git |
| Audit Logs | Real-time | 1 year | Streaming to S3 |

### 9.2 Recovery Procedures

**Database Recovery:**
```
1. Stop application traffic
2. Restore PostgreSQL from latest backup
3. Apply WAL logs (point-in-time recovery)
4. Verify data integrity
5. Resume traffic
RTO: 30 minutes | RPO: 5 minutes
```

**Full System Recovery:**
```
1. Provision new infrastructure
2. Deploy application from container image
3. Restore database from backup
4. Restore Redis from backup
5. Update DNS records
6. Verify health checks
7. Resume traffic
RTO: 2 hours | RPO: 1 hour
```

---

## 10. Recovery Testing

### 10.1 Chaos Engineering

| Experiment | Frequency | Duration | Blast Radius |
|------------|-----------|----------|--------------|
| Kill random pod | Weekly | 5 min | 10% traffic |
| Network partition | Monthly | 10 min | 20% traffic |
| Database failover | Monthly | 15 min | 50% traffic |
| Full region failure | Quarterly | 30 min | 100% traffic |

### 10.2 Recovery Validation

```yaml
recovery_validation:
  - test: circuit_breaker_opens_on_failure
    frequency: daily
    expected: circuit opens after 5 failures
    
  - test: fallback_model_used
    frequency: daily
    expected: fallback model responds within 5s
    
  - test: workflow_resume_after_failure
    frequency: weekly
    expected: workflow resumes from checkpoint
    
  - test: database_failover
    frequency: monthly
    expected: service resumes within 30s
```

---

## 11. Incident Response Playbook

### 11.1 Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| P1 | Complete service outage | 15 minutes | All models down |
| P2 | Major feature degraded | 30 minutes | Memory system down |
| P3 | Minor feature affected | 2 hours | One model unavailable |
| P4 | Cosmetic issue | 24 hours | Log formatting |

### 11.2 Response Steps

```
1. DETECT: Alert fires or user reports
2. TRIAGE: Determine severity and impact
3. MITIGATE: Apply immediate fix or workaround
4. INVESTIGATE: Root cause analysis
5. RESOLVE: Permanent fix
6. REVIEW: Post-incident review
7. PREVENT: Add monitoring/tests to prevent recurrence
```

### 11.3 Common Incidents

| Incident | Mitigation | Root Cause Fix |
|----------|------------|----------------|
| Model provider down | Enable fallback | Add circuit breaker |
| Database overloaded | Enable read replicas | Optimize queries |
| Memory exhaustion | Restart worker | Fix memory leak |
| Rate limiting | Reduce request rate | Implement queuing |
| Network timeout | Retry with backoff | Increase timeouts |
| Cache stampede | Enable cache locking | Implement cache warming |

---

## 12. Recovery Metrics

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| Mean Time to Detect (MTTD) | <1 minute | >5 minutes |
| Mean Time to Recover (MTTR) | <15 minutes | >30 minutes |
| Recovery Success Rate | >99% | <95% |
| Circuit Breaker Open Rate | <1% of time | >5% of time |
| Fallback Usage Rate | <5% of requests | >20% of requests |
| Data Loss Incidents | 0 per year | >0 |
