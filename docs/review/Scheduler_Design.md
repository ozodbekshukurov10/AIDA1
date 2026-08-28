# AIDA Scheduler Design

**Document:** Book 2, Chapter 2 — Scheduler Design
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Scheduler is the **brain** of the Runtime Engine. It determines **when**, **where**, and **how** tasks execute by balancing priorities, resource availability, worker capabilities, and fairness constraints.

---

## 2. Architecture

### 2.1 Scheduler Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     SCHEDULER                                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Priority Queue Manager                       │   │
│  │  critical(100) > high(80) > standard(50) > background(20)│   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                   │
│  ┌──────────────────────────┴───────────────────────────────┐   │
│  │              Resource Availability Checker                │   │
│  │  CPU: 60% free | RAM: 45% free | GPU: 80% free          │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                   │
│  ┌──────────────────────────┴───────────────────────────────┐   │
│  │              Worker Capability Matcher                    │   │
│  │  task.type == "code" → code_workers                       │   │
│  │  task.type == "ai" → ai_workers                           │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                   │
│  ┌──────────────────────────┴───────────────────────────────┐   │
│  │              Fair Share Enforcer                          │   │
│  │  tenant "enterprise" min=30% max=60%                      │   │
│  │  tenant "pro" min=20% max=40%                             │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                   │
│  ┌──────────────────────────┴───────────────────────────────┐   │
│  │              Deadline Monitor                             │   │
│  │  SLA breach in 10s → boost priority to 100               │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ SchedulingDecision
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  task_id | worker_id | queue | priority | estimated_start       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Scheduling Algorithms

### 3.1 Algorithm Selection

| Algorithm | When Used | Description |
|-----------|-----------|-------------|
| `priority` | Default | Higher priority tasks first |
| `fifo` | Same priority | First in, first out |
| `fair_share` | Multi-tenant | Equal resource distribution per tenant |
| `deadline` | Time-sensitive | Earliest deadline first |
| `affinity` | Specialized tasks | Match task requirements to worker capabilities |
| `load_balance` | Distributed | Distribute across workers evenly |
| `resource_aware` | High load | Consider available resources |

### 3.2 Composite Algorithm (Default)

```python
class CompositeScheduler:
    """
    Combines multiple algorithms for optimal scheduling.
    
    Order of evaluation:
    1. Priority (always respected)
    2. Deadline (boost if SLA breach imminent)
    3. Fair Share (ensure tenant fairness)
    4. Affinity (match worker capabilities)
    5. Load Balance (distribute evenly)
    """
    
    def schedule(self, task: Task, context: SchedulingContext) -> SchedulingDecision:
        # Step 1: Base priority
        priority = task.priority
        
        # Step 2: Deadline boost
        if task.deadline:
            time_to_deadline = task.deadline - now()
            if time_to_deadline < timedelta(seconds=30):
                priority = max(priority, 100)
            elif time_to_deadline < timedelta(seconds=60):
                priority = max(priority, 90)
        
        # Step 3: Fair share adjustment
        tenant_share = self.fair_share.get_tenant_share(task.tenant_id)
        if tenant_share > tenant_share.max_share:
            priority = min(priority, 30)
        
        # Step 4: Find capable workers
        capable_workers = self.worker_pool.find_workers(
            type=task.required_worker_type,
            resources=task.resource_requirements,
            status="idle"
        )
        
        # Step 5: Select best worker (affinity + load balance)
        best_worker = self.select_worker(capable_workers, task)
        
        return SchedulingDecision(
            task_id=task.id,
            worker_id=best_worker.id,
            priority=priority,
            estimated_start=self.estimate_start(best_worker),
            reason=self.explain_decision(task, best_worker)
        )
```

---

## 4. Worker Selection

### 4.1 Worker Capability Matrix

| Worker Type | Code | AI | Research | Security | Terminal | Browser |
|-------------|------|----|----------|----------|----------|---------|
| General | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ |
| Code | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ |
| AI | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| Planning | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ |
| Research | ✗ | ✗ | ✓ | ✗ | ✗ | ✓ |
| Security | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ |
| Browser | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| Terminal | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| Sandbox | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ |
| Streaming | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

### 4.2 Selection Algorithm

```python
def select_worker(self, candidates: list[Worker], task: Task) -> Worker:
    if not candidates:
        raise NoWorkerAvailableError(task.id)
    
    # Score each candidate
    scored = []
    for worker in candidates:
        score = 0.0
        
        # Capability match (0-40 points)
        capability_score = self.score_capability(worker, task)
        score += capability_score * 0.4
        
        # Resource availability (0-30 points)
        resource_score = self.score_resources(worker, task)
        score += resource_score * 0.3
        
        # Load (0-20 points) - lower load = higher score
        load_score = 1.0 - worker.current_load
        score += load_score * 0.2
        
        # Affinity (0-10 points) - has this worker run similar tasks before?
        affinity_score = self.score_affinity(worker, task)
        score += affinity_score * 0.1
        
        scored.append((worker, score))
    
    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return scored[0][0]
```

### 4.3 Affinity Tracking

```python
class AffinityTracker:
    """Tracks worker-task affinity for better future scheduling."""
    
    def record(self, worker_id: str, task_type: str, success: bool, duration: float):
        key = f"{worker_id}:{task_type}"
        if key not in self.history:
            self.history[key] = AffinityRecord()
        
        record = self.history[key]
        record.total_tasks += 1
        record.success_rate = (record.success_rate * (record.total_tasks - 1) + (1.0 if success else 0.0)) / record.total_tasks
        record.avg_duration = (record.avg_duration * (record.total_tasks - 1) + duration) / record.total_tasks
    
    def score(self, worker_id: str, task_type: str) -> float:
        key = f"{worker_id}:{task_type}"
        if key not in self.history:
            return 0.5  # neutral
        record = self.history[key]
        return record.success_rate * 0.7 + (1.0 - min(record.avg_duration / 60.0, 1.0)) * 0.3
```

---

## 5. Fair Share System

### 5.1 Purpose

Prevents any single tenant from monopolizing resources while guaranteeing minimum resource allocation.

### 5.2 Fair Share Algorithm

```python
class FairShareEnforcer:
    def allocate(self, tenants: list[Tenant], total_resources: float) -> dict[str, float]:
        """
        Allocates resources using weighted fair queuing.
        
        Returns: {tenant_id: allocated_share}
        """
        # Calculate demand per tenant
        demand = {t.id: t.pending_tasks for t in tenants}
        total_demand = sum(demand.values())
        
        if total_demand == 0:
            return {}
        
        allocation = {}
        
        for tenant in tenants:
            # Base share from config
            base_share = tenant.config.min_share
            
            # Demand-weighted adjustment
            demand_ratio = demand[tenant.id] / total_demand if total_demand > 0 else 0
            
            # Weighted allocation
            weighted = (base_share + demand_ratio) / 2
            
            # Clamp to min/max
            clamped = max(tenant.config.min_share, min(weighted, tenant.config.max_share))
            
            allocation[tenant.id] = clamped * total_resources
        
        # Normalize to total resources
        total_allocated = sum(allocation.values())
        if total_allocated > total_resources:
            scale = total_resources / total_allocated
            allocation = {k: v * scale for k, v in allocation.items()}
        
        return allocation
```

### 5.3 Starvation Prevention

```python
class StarvationPrevention:
    """
    Ensures no task waits indefinitely.
    
    Rules:
    - Any task waiting > 60s gets +5 priority boost
    - Any task waiting > 300s gets +15 priority boost
    - Any task waiting > 600s gets promoted to HIGH priority
    - Security tasks bypass all starvation checks
    """
    
    def adjust_priority(self, task: Task) -> int:
        if task.task_type == "security":
            return task.priority  # bypass
        
        wait_time = (now() - task.created_at).total_seconds()
        
        if wait_time > 600:
            return max(task.priority, 80)
        elif wait_time > 300:
            return task.priority + 15
        elif wait_time > 60:
            return task.priority + 5
        
        return task.priority
```

---

## 6. Deadline Scheduling

### 6.1 Deadline Types

| Type | Default SLA | Consequence of Miss |
|------|-------------|---------------------|
| `user_response` | 30s | User sees "taking longer" message |
| `api_timeout` | 60s | HTTP 504 response |
| `streaming_token` | 5s | Token delivery lag |
| `batch_job` | 1h | Delayed completion notification |
| `security_scan` | 5min | Delayed security response |
| `workflow_step` | Varies | Workflow pauses |

### 6.2 Deadline-Aware Scheduling

```python
class DeadlineScheduler:
    def schedule(self, task: Task) -> SchedulingDecision:
        time_to_deadline = task.deadline - now()
        
        if time_to_deadline < timedelta(seconds=0):
            # Already missed deadline
            return self.schedule_urgent(task)
        
        if time_to_deadline < timedelta(seconds=10):
            # Critical - must run now
            task.priority = 100
            return self.schedule_immediate(task)
        
        if time_to_deadline < timedelta(seconds=30):
            # Urgent - high priority
            task.priority = max(task.priority, 90)
            return self.schedule_high_priority(task)
        
        # Normal scheduling with deadline awareness
        return self.schedule_normal(task)
```

---

## 7. Multi-Queue Scheduler

### 7.1 Queue Weights

```
┌─────────────────────────────────────────────────────────┐
│                   SCHEDULER                              │
│                                                          │
│  Queue Weights:                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │ Critical   │  │   High     │  │ Standard   │        │
│  │ Weight: 50 │  │ Weight: 30 │  │ Weight: 15 │        │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘        │
│         │               │               │                │
│         ↓               ↓               ↓                │
│  ┌────────────┐  ┌────────────┐                           │
│  │Background  │  │  Delayed   │                           │
│  │Weight: 4   │  │ Weight: 1  │                           │
│  └────────────┘  └────────────┘                           │
│                                                          │
│  Total Weight: 100                                       │
│                                                          │
│  Per cycle (100 tasks):                                  │
│    Critical: 50 tasks                                    │
│    High: 30 tasks                                        │
│    Standard: 15 tasks                                    │
│    Background: 4 tasks                                   │
│    Delayed: 1 task                                       │
└─────────────────────────────────────────────────────────┘
```

### 7.2 Adaptive Weight Adjustment

```yaml
adaptive_weights:
  enabled: true
  
  rules:
    - condition: "critical_queue_depth > 0"
      action: "increase_critical_weight: 2x"
      
    - condition: "high_queue_age > 60s"
      action: "increase_high_weight: 1.5x"
      
    - condition: "background_queue_depth > 1000"
      action: "decrease_background_weight: 0.5x"
      
    - condition: "worker_utilization > 90%"
      action: "decrease_all_weights: 0.8x"
```

---

## 8. Resource-Aware Scheduling

### 8.1 Resource Checking

```python
class ResourceAwareScheduler:
    def can_schedule(self, task: Task, worker: Worker) -> bool:
        # Check CPU
        if task.resources.cpu > worker.available_cpu:
            return False
        
        # Check memory
        if task.resources.memory_mb > worker.available_memory_mb:
            return False
        
        # Check GPU (if required)
        if task.resources.gpu_required:
            if task.resources.gpu_vram_mb > worker.available_gpu_vram_mb:
                return False
        
        # Check disk
        if task.resources.disk_mb > worker.available_disk_mb:
            return False
        
        # Check network (if required)
        if task.resources.network_required:
            if not worker.network_available:
                return False
        
        return True
```

### 8.2 Resource Prediction

```python
class ResourcePredictor:
    """
    Predicts resource requirements based on task characteristics.
    
    Uses historical data for similar tasks.
    """
    
    def predict(self, task_type: str, task_size: float) -> ResourceEstimate:
        history = self.get_history(task_type)
        
        if not history:
            return self.default_estimate(task_type)
        
        # Calculate percentiles
        cpu_p50 = np.percentile([h.cpu_used for h in history], 50)
        cpu_p95 = np.percentile([h.cpu_used for h in history], 95)
        mem_p50 = np.percentile([h.memory_used for h in history], 50)
        mem_p95 = np.percentile([h.memory_used for h in history], 95)
        duration_p50 = np.percentile([h.duration for h in history], 50)
        duration_p95 = np.percentile([h.duration for h in history], 95)
        
        # Scale by task size
        scale = task_size / np.mean([h.size for h in history])
        
        return ResourceEstimate(
            cpu=cpu_p95 * scale,
            memory_mb=mem_p95 * scale,
            duration=duration_p95 * scale,
            confidence=len(history) / 100  # more history = more confident
        )
```

---

## 9. Scheduler Configuration

```yaml
scheduler:
  algorithm: composite
  tick_interval: 100ms
  
  priority:
    enabled: true
    levels: 10
    
  fair_share:
    enabled: true
    rebalance_interval: 30s
    min_share: 10%
    max_share: 60%
    
  deadline:
    enabled: true
    check_interval: 1s
    urgent_threshold: 10s
    high_threshold: 30s
    
  resource_aware:
    enabled: true
    check_interval: 5s
    buffer_percent: 10
    
  load_balance:
    enabled: true
    algorithm: least_loaded
    max_imbalance: 20%
    
  starvation_prevention:
    enabled: true
    boost_thresholds:
      - wait: 60s
        boost: 5
      - wait: 300s
        boost: 15
      - wait: 600s
        promote_to: high
        
  monitoring:
    enabled: true
    metrics_interval: 15s
    log_decisions: true
```

---

## 10. Monitoring & Observability

### 10.1 Scheduler Metrics

```
Scheduler Metrics:
  - scheduling_latency_p50: 5ms
  - scheduling_latency_p95: 25ms
  - scheduling_latency_p99: 100ms
  - decisions_per_second: 500
  - queue_wait_time_p50: 2s
  - queue_wait_time_p95: 30s
  - queue_wait_time_p99: 120s
  - worker_utilization: 65%
  - resource_efficiency: 78%
  - fairness_score: 0.92
  - starvation_incidents: 0
```

### 10.2 Dashboard

```
┌─────────────────────────────────────────────────────────┐
│                  SCHEDULER DASHBOARD                     │
│                                                          │
│  Queue Depths:        Worker Utilization:                │
│  Critical: 12         [████████░░] 80%                   │
│  High: 45             CPU:  [██████░░░░] 60%             │
│  Standard: 128        RAM:  [███████░░░] 70%             │
│  Background: 67       GPU:  [███░░░░░░░] 30%             │
│                                                          │
│  Fair Share:          Scheduling Latency:                │
│  Enterprise: 35%      P50: 5ms                           │
│  Pro: 30%             P95: 25ms                          │
│  Free: 25%            P99: 100ms                         │
│                                                          │
│  Starvation:          SLA Compliance:                    │
│  Boosted: 3 tasks     Met: 99.2%                         │
│  Promoted: 0 tasks    Missed: 0.8%                       │
└─────────────────────────────────────────────────────────┘
```
