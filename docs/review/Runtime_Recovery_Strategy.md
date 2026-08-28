# AIDA Runtime Recovery Strategy

**Document:** Book 2, Chapter 2 — Runtime Recovery Strategy
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Runtime Engine must be **self-healing** — automatically detecting and recovering from worker crashes, sandbox failures, queue backlogs, and resource exhaustion. This document defines recovery strategies specific to the Runtime Engine layer.

---

## 2. Failure Categories

| Category | Examples | Severity | Impact | Recovery Strategy |
|----------|----------|----------|--------|-------------------|
| **Worker Crash** | Process OOM, segfault, timeout | HIGH | Task interrupted | Auto-restart + requeue |
| **Worker Stall** | Deadlock, infinite loop, resource leak | MEDIUM | Task stuck | Kill + requeue |
| **Sandbox Failure** | Container crash, network unreachable | HIGH | Untrusted code | Destroy + requeue |
| **Queue Overflow** | Redis memory exhaustion | CRITICAL | All new tasks blocked | Scale Redis + purge old |
| **Resource Exhaustion** | CPU/RAM/disk full | CRITICAL | System-wide slowdown | Kill tasks + alert |
| **Network Failure** | DNS, provider outage | MEDIUM | External calls fail | Fallback + retry |
| **State Corruption** | Redis data loss, inconsistent state | CRITICAL | Task state lost | Restore from checkpoint |
| **Cascading Failure** | Worker → Queue → Scheduler | CRITICAL | System-wide outage | Circuit breaker + isolation |

---

## 3. Worker Recovery

### 3.1 Worker Health Check

```yaml
worker_health_check:
  interval: 10s
  timeout: 5s
  
  checks:
    - type: heartbeat
      expected_interval: 10s
      missed_threshold: 3  # 30s without heartbeat = unhealthy
      
    - type: process_alive
      check: /proc/{pid}/status
      
    - type: resource_usage
      cpu_threshold: 95%  # Kill if CPU > 95% for 60s
      memory_threshold: 90%  # Kill if RAM > 90%
      
    - type: task_progress
      stalled_threshold: 120s  # No progress for 2 min = stalled
```

### 3.2 Worker Recovery Flow

```
Worker Failure Detected
    │
    ├── Worker type?
    │   ├── Streaming worker → Kill + don't requeue (client disconnected)
    │   ├── Background worker → Kill + requeue with incremented attempt
    │   └── Normal worker → Kill + requeue to same queue
    │
    ├── Recovery actions:
    │   1. Mark worker as UNHEALTHY
    │   2. Kill worker process (SIGTERM, then SIGKILL)
    │   3. Collect any partial results
    │   4. Requeue incomplete tasks
    │   5. Release allocated resources
    │   6. Spawn replacement worker
    │   7. Log incident
    │
    └── If worker fails 3+ times in 5 min:
        → Mark worker as DEAD
        → Alert operator
        → Don't spawn replacement (investigate root cause)
```

### 3.3 Worker Restart Strategy

```python
class WorkerRestartStrategy:
    def __init__(self):
        self.max_restarts = 5
        self.restart_window = 300  # 5 minutes
        self.cooldown_period = 10  # seconds between restarts
    
    def should_restart(self, worker: Worker) -> RestartDecision:
        recent_restarts = self.get_restarts(worker.id, window=self.restart_window)
        
        if recent_restarts >= self.max_restarts:
            return RestartDecision(
                should_restart=False,
                reason="Max restarts exceeded",
                action="alert_operator"
            )
        
        if worker.consecutive_failures >= 3:
            return RestartDecision(
                should_restart=False,
                reason="Consecutive failures",
                action="investigate"
            )
        
        return RestartDecision(
            should_restart=True,
            delay=self.cooldown_period,
            reason=f"Restart {recent_restarts + 1}/{self.max_restarts}"
        )
```

---

## 4. Sandbox Recovery

### 4.1 Sandbox Failure Scenarios

| Scenario | Detection | Recovery |
|----------|-----------|----------|
| Container crash | Exit code != 0 | Destroy + requeue task |
| Container OOM | OOM killed | Increase memory + requeue |
| Container timeout | Timeout exceeded | Kill + requeue with higher timeout |
| Network failure | DNS/connect timeout | Retry without network |
| Disk full | Write error | Cleanup + requeue |
| Security violation | Seccomp/AppArmor | Kill immediately + alert |

### 4.2 Sandbox Recovery Flow

```
Sandbox Failure Detected
    │
    ├── Failure type?
    │   ├── OOM → Increase memory limit → Create new sandbox → Requeue
    │   ├── Timeout → Increase timeout → Create new sandbox → Requeue
    │   ├── Crash → Collect logs → Create new sandbox → Requeue
    │   ├── Security → Kill + alert + don't requeue
    │   └── Unknown → Collect diagnostics → Create new sandbox → Requeue
    │
    ├── Recovery actions:
    │   1. Stop sandbox (kill + destroy)
    │   2. Collect logs and diagnostics
    │   3. Save partial results (if any)
    │   4. Create new sandbox with adjusted config
    │   5. Requeue task
    │
    └── If sandbox fails 3+ times:
        → Mark task as FAILED
        → Send to Dead Letter Queue
        → Alert operator
```

---

## 5. Queue Recovery

### 5.1 Queue Health Monitoring

```yaml
queue_health:
  checks:
    - name: queue_depth
      warning: 10000
      critical: 50000
      
    - name: consumer_lag
      warning: 1000
      critical: 5000
      
    - name: processing_rate
      warning: "rate < 10/s for 5m"
      critical: "rate < 1/s for 2m"
      
    - name: retry_rate
      warning: "rate > 5%"
      critical: "rate > 20%"
      
    - name: dlq_rate
      warning: "rate > 1%"
      critical: "rate > 5%"
```

### 5.2 Queue Overflow Recovery

```
Queue Overflow Detected
    │
    ├── Immediate actions:
    │   1. Pause new enqueues for affected queue
    │   2. Scale consumers (add workers)
    │   3. Alert operator
    │
    ├── If Redis memory critical:
    │   1. Purge oldest messages from standard/background queues
    │   2. Move critical tasks to separate Redis instance
    │   3. Enable message compression
    │
    ├── If still overflowing:
    │   1. Reject new non-critical tasks (429 Too Many Requests)
    │   2. Route critical tasks to dedicated queue
    │   3. Scale Redis (add replicas)
    │
    └── After recovery:
        1. Resume normal operations
        2. Analyze root cause
        3. Adjust limits if needed
```

### 5.3 Redis Failure Recovery

```yaml
redis_recovery:
  # Primary fails → Sentinel promotes replica
  sentinel:
    enabled: true
    down_after: 5000ms
    failover_timeout: 10000ms
    
  # Queue persistence
  persistence:
    append_only: yes
    save_interval: 60s
    
  # Fallback: PostgreSQL queue
  postgresql_fallback:
    enabled: true
    sync_interval: 30s
```

---

## 6. Resource Exhaustion Recovery

### 6.1 Resource Monitoring

```yaml
resource_monitoring:
  cpu:
    warning: 80%
    critical: 95%
    action_warning: "throttle_new_tasks"
    action_critical: "kill_lowest_priority"
    
  memory:
    warning: 80%
    critical: 95%
    action_warning: "alert_operator"
    action_critical: "kill_oom_candidates"
    
  disk:
    warning: 80%
    critical: 95%
    action_warning: "cleanup_temp_files"
    action_critical: "purge_old_logs"
    
  gpu:
    warning: 90%
    critical: 98%
    action_warning: "throttle_gpu_tasks"
    action_critical: "kill_gpu_tasks"
```

### 6.2 Resource Recovery Flow

```
Resource Exhaustion Detected
    │
    ├── CPU exhaustion:
    │   ├── Throttle non-critical tasks
    │   ├── Kill tasks running > 300s
    │   └── Scale workers (if possible)
    │
    ├── Memory exhaustion:
    │   ├── Kill OOM candidates (lowest priority first)
    │   ├── Clear caches
    │   └── Alert operator
    │
    ├── Disk exhaustion:
    │   ├── Cleanup temp files
    │   ├── Purge old logs
    │   ├── Delete completed sandboxes
    │   └── Alert operator
    │
    └── GPU exhaustion:
        ├── Throttle GPU tasks
        ├── Kill long-running GPU tasks
        └── Fall back to CPU inference
```

---

## 7. Cascading Failure Prevention

### 7.1 Circuit Breaker

```yaml
circuit_breakers:
  worker_pool:
    failure_threshold: 5
    recovery_timeout: 30s
    half_open_max: 3
    
  queue:
    failure_threshold: 3
    recovery_timeout: 60s
    
  sandbox:
    failure_threshold: 3
    recovery_timeout: 30s
    
  resource_manager:
    failure_threshold: 2
    recovery_timeout: 120s
```

### 7.2 Bulkhead Pattern

```yaml
bulkhead:
  # Isolate critical components
  critical_queue:
    max_concurrent: 50
    max_wait: 10s
    
  standard_queue:
    max_concurrent: 200
    max_wait: 30s
    
  background_queue:
    max_concurrent: 100
    max_wait: 60s
    
  # Isolate worker pools
  code_workers:
    max_concurrent: 20
    
  ai_workers:
    max_concurrent: 10
    
  terminal_workers:
    max_concurrent: 30
```

### 7.3 Rate Limiting

```yaml
rate_limiting:
  per_task_type:
    code_generation: 10/s
    llm_inference: 5/s
    repository_analysis: 2/s
    browser_automation: 3/s
    
  per_user:
    free: 10/min
    pro: 100/min
    enterprise: 1000/min
    
  per_tenant:
    free: 100/min
    pro: 1000/min
    enterprise: 10000/min
```

---

## 8. Checkpoint & Restore

### 8.1 Workflow Checkpointing

```yaml
checkpointing:
  enabled: true
  
  # When to checkpoint
  triggers:
    - "before_each_step"
    - "after_each_step"
    - "on_user_input"
    - "every_60s"
    
  # What to checkpoint
  data:
    - task_state
    - workflow_position
    - accumulated_results
    - resource_allocations
    - worker_assignments
    
  # Where to store
  storage:
    primary: redis
    backup: postgresql
    s3_backup: enabled
    
  # Retention
  retention:
    active: 24h
    completed: 7d
    failed: 30d
```

### 8.2 Checkpoint Restore Flow

```
System Crash & Restart
    │
    ├── Load last checkpoint for each active task
    │
    ├── For each task:
    │   ├── Restore task state
    │   ├── Restore workflow position
    │   ├── Restore accumulated results
    │   └── Re-enqueue for execution
    │
    ├── Rebuild worker pool
    │
    ├── Rebuild queue consumers
    │
    └── Resume normal operations
```

---

## 9. Graceful Degradation

### 9.1 Degradation Levels

| Level | Condition | Behavior |
|-------|-----------|----------|
| 0 | Normal | All features available |
| 1 | High load | Background tasks paused, non-essential features disabled |
| 2 | Resource pressure | Only critical + high priority tasks, sandbox limited |
| 3 | Severe degradation | Only critical tasks, minimal workers, no background |
| 4 | Emergency | System enters safe mode, accepts no new tasks |

### 9.2 Degradation Triggers

```yaml
degradation:
  level_1:
    triggers:
      - "worker_utilization > 80%"
      - "queue_depth > 5000"
    actions:
      - "pause_background_tasks"
      - "disable_non_essential_features"
      
  level_2:
    triggers:
      - "worker_utilization > 90%"
      - "queue_depth > 10000"
      - "memory_usage > 85%"
    actions:
      - "limit_to_critical_and_high"
      - "reduce_sandbox_concurrency"
      - "disable_browser_workers"
      
  level_3:
    triggers:
      - "worker_utilization > 95%"
      - "queue_depth > 50000"
      - "memory_usage > 95%"
    actions:
      - "limit_to_critical_only"
      - "minimal_worker_pool"
      - "reject_non_critical_tasks"
      
  level_4:
    triggers:
      - "system_failure"
      - "security_breach"
    actions:
      - "reject_all_new_tasks"
      - "complete_running_tasks"
      - "alert_operator"
```

---

## 10. Disaster Recovery

### 10.1 Recovery Objectives

| Metric | Target | Description |
|--------|--------|-------------|
| RTO | 30 min | Maximum downtime |
| RPO | 5 min | Maximum data loss |
| MTTR | 10 min | Mean time to recover |

### 10.2 Backup Strategy

```yaml
backup:
  redis:
    frequency: 1h
    retention: 7d
    method: RDB + AOF
    
  postgresql:
    frequency: 4h
    retention: 30d
    method: pg_dump + WAL
    
  configuration:
    frequency: on_change
    retention: 90d
    method: git
    
  checkpoints:
    frequency: real-time (per task)
    retention: 7d
    method: Redis + PostgreSQL
```

### 10.3 Failover Procedures

```
Primary Data Center Failure
    │
    ├── Detect: Health checks fail (30s)
    │
    ├── Declare: Disaster (1 min)
    │
    ├── Failover:
    │   1. DNS failover to secondary (5 min)
    │   2. Promote secondary Redis (2 min)
    │   3. Promote secondary PostgreSQL (5 min)
    │   4. Rebuild worker pool (5 min)
    │   5. Resume operations (10 min)
    │
    └── Total RTO: ~30 min
```

---

## 11. Chaos Engineering

### 11.1 Failure Injection

```yaml
chaos_engineering:
  enabled: false  # Enable in staging only
  
  experiments:
    - name: worker_crash
      schedule: "0 2 * * 1"  # Weekly Monday 2am
      action: "kill_random_worker"
      impact: "low"
      
    - name: queue_backlog
      schedule: "0 3 * * 1"
      action: "inject_10000_tasks"
      impact: "medium"
      
    - name: resource_exhaustion
      schedule: "0 4 * * 1"
      action: "consume_90_percent_memory"
      impact: "high"
      
    - name: network_partition
      schedule: "0 5 * * 1"
      action: "block_external_network"
      impact: "medium"
```

---

## 12. Configuration

```yaml
recovery:
  worker:
    health_check_interval: 10s
    max_restarts: 5
    restart_window: 300s
    max_consecutive_failures: 3
    
  sandbox:
    max_retries: 3
    retry_delay: 10s
    max_lifetime: 300s
    
  queue:
    max_retries: 3
    retry_delays: [10, 60, 300]
    dead_letter_after: 3
    
  resource:
    check_interval: 10s
    kill_threshold: 95%
    
  checkpointing:
    enabled: true
    interval: 60s
    
  degradation:
    enabled: true
    auto_degrade: true
    
  disaster_recovery:
    enabled: true
    rto: 1800
    rpo: 300
```
