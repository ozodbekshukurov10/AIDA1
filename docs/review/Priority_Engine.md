# AIDA Priority Engine

**Document:** Book 2, Chapter 3 — Priority Engine
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Priority Engine determines the execution order of tasks based on urgency, impact, effort, dependency relationships, and business rules. It ensures critical tasks execute first while preventing starvation of lower-priority work.

---

## 2. Priority Levels

### 2.1 Level Definitions

| Level | Value | Color | SLA | Description |
|-------|-------|-------|-----|-------------|
| Emergency | 100 | 🔴 Red | 5 min | System down, security breach |
| Critical | 90 | 🟠 Orange | 15 min | Blocking other work |
| High | 80 | 🟡 Yellow | 1 hour | Important, near deadline |
| Normal | 50 | 🟢 Green | 4 hours | Standard work |
| Low | 30 | 🔵 Blue | 24 hours | Nice to have |
| Idle | 10 | ⚪ Gray | None | When nothing else to do |

### 2.2 Level Descriptions

| Level | When to Use | Examples |
|-------|-------------|----------|
| Emergency | Production down, data loss, security breach | Outage, hack, data corruption |
| Critical | Blocking other tasks, user-facing bug | Broken feature, blocked workflow |
| High | Important feature, near deadline | Active user request, sprint item |
| Normal | Regular development work | Feature implementation, refactoring |
| Low | Nice-to-have improvements | UI polish, tech debt |
| Idle | Background work, maintenance | Cleanup, documentation updates |

---

## 3. Priority Calculation

### 3.1 Composite Priority Formula

```python
def calculate_priority(task: Task) -> int:
    """
    Composite priority calculation.
    Returns value 0-100.
    """
    # Base priority from user request
    base = task.base_priority
    
    # Urgency factor (0-40 points)
    urgency = calculate_urgency(task)
    
    # Impact factor (0-30 points)
    impact = calculate_impact(task)
    
    # Effort factor (0-15 points)
    effort = calculate_effort_factor(task)
    
    # Dependency factor (0-15 points)
    dependency = calculate_dependency_factor(task)
    
    # Weighted sum
    priority = (
        base * 0.3 +
        urgency * 0.4 +
        impact * 0.3 +
        effort * 0.1 +
        dependency * 0.1
    )
    
    return min(100, max(0, int(priority)))
```

### 3.2 Urgency Calculation

```python
def calculate_urgency(task: Task) -> int:
    """Calculate urgency based on deadline."""
    if not task.deadline:
        return 0
    
    hours_left = (task.deadline - now()).total_seconds() / 3600
    
    if hours_left < 0:
        return 40  # Already overdue
    elif hours_left < 1:
        return 35  # Less than 1 hour
    elif hours_left < 4:
        return 30  # Less than 4 hours
    elif hours_left < 24:
        return 20  # Less than 1 day
    elif hours_left < 72:
        return 10  # Less than 3 days
    else:
        return 0   # No urgency
```

### 3.3 Impact Calculation

```python
def calculate_impact(task: Task) -> int:
    """Calculate impact based on affected users and business value."""
    score = 0
    
    # Affected users
    if task.affected_users > 1000:
        score += 15
    elif task.affected_users > 100:
        score += 10
    elif task.affected_users > 10:
        score += 5
    
    # Business value
    if task.business_value == "critical":
        score += 15
    elif task.business_value == "high":
        score += 10
    elif task.business_value == "medium":
        score += 5
    
    return min(30, score)
```

### 3.4 Effort Factor

```python
def calculate_effort_factor(task: Task) -> int:
    """Smaller tasks get priority boost (quick wins)."""
    duration_hours = task.estimated_duration / 3600
    
    if duration_hours < 0.25:   # < 15 min
        return 15
    elif duration_hours < 1:    # < 1 hour
        return 10
    elif duration_hours < 4:    # < 4 hours
        return 5
    else:
        return 0
```

### 3.5 Dependency Factor

```python
def calculate_dependency_factor(task: Task) -> int:
    """Tasks blocking others get priority boost."""
    blocking_count = len(task.blocks)
    
    if blocking_count > 5:
        return 15
    elif blocking_count > 3:
        return 10
    elif blocking_count > 1:
        return 5
    else:
        return 0
```

---

## 4. Priority Matrix

### 4.1 Urgency × Impact Matrix

```
                  IMPACT
              High    Medium    Low
         ┌─────────┬─────────┬─────────┐
  < 1h   │  100    │   90    │   80    │  ← Emergency/Critical
U        ├─────────┼─────────┼─────────┤
R  1-4h  │   90    │   70    │   60    │  ← High
G        ├─────────┼─────────┼─────────┤
E  4-24h │   70    │   50    │   40    │  ← Normal
N        ├─────────┼─────────┼─────────┤
C  1-3d  │   60    │   40    │   30    │  ← Low
Y        ├─────────┼─────────┼─────────┤
   3d+   │   50    │   30    │   10    │  ← Idle
         └─────────┴─────────┴─────────┘
```

### 4.2 Priority Decision Tree

```
Task Arrives
    │
    ├── Is production down?
    │   └── YES → Priority 100 (Emergency)
    │
    ├── Is there a security breach?
    │   └── YES → Priority 100 (Emergency)
    │
    ├── Is it blocking other tasks?
    │   └── YES → Priority 90 (Critical)
    │
    ├── Is there a deadline < 1 hour?
    │   └── YES → Priority 80 (High)
    │
    ├── Is it a user-facing feature?
    │   └── YES → Priority 70 (High-Normal)
    │
    ├── Is it blocking tasks?
    │   └── YES → Priority 60 (Normal-High)
    │
    └── Default → Priority 50 (Normal)
```

---

## 5. Starvation Prevention

### 5.1 Age-Based Boost

```python
class StarvationPrevention:
    """Prevent tasks from waiting indefinitely."""
    
    def adjust_priority(self, task: Task) -> int:
        wait_time = (now() - task.created_at).total_seconds() / 60  # minutes
        
        if wait_time > 480:    # > 8 hours
            return task.priority + 30
        elif wait_time > 240:  # > 4 hours
            return task.priority + 20
        elif wait_time > 60:   # > 1 hour
            return task.priority + 10
        elif wait_time > 30:   # > 30 min
            return task.priority + 5
        
        return task.priority
```

### 5.2 Fair Share Rules

```yaml
fair_share:
  # Minimum share per priority level
  min_share:
    emergency: 50%  # Always gets at least 50%
    critical: 30%
    high: 20%
    normal: 10%
    low: 5%
    idle: 1%
    
  # Maximum share per priority level
  max_share:
    emergency: 100%
    critical: 60%
    high: 40%
    normal: 30%
    low: 15%
    idle: 5%
```

### 5.3 Aging Algorithm

```python
def age_priority(task: Task, current_time: datetime) -> int:
    """
    Gradually increase priority of waiting tasks.
    Prevents starvation while maintaining priority order.
    """
    age_minutes = (current_time - task.created_at).total_seconds() / 60
    
    # Aging curve
    if age_minutes < 30:
        aging = 0
    elif age_minutes < 60:
        aging = 1
    elif age_minutes < 120:
        aging = 3
    elif age_minutes < 240:
        aging = 5
    elif age_minutes < 480:
        aging = 10
    else:
        aging = 20
    
    return min(100, task.priority + aging)
```

---

## 6. Priority Rules

### 6.1 Override Rules

| Rule | Condition | Action |
|------|-----------|--------|
| Emergency Override | Production down | Set priority to 100 |
| Security Override | Security breach | Set priority to 100 |
| Deadline Override | < 1 hour to deadline | Set priority to 90 |
| Blocking Override | Blocks > 5 tasks | Set priority to 80 |
| User Override | User explicitly requests | Set priority to 80 |

### 6.2 De-prioritization Rules

| Rule | Condition | Action |
|------|-----------|--------|
| Stale Task | No progress for 2 hours | Reduce priority by 10 |
| Failed Retry | 3+ retry attempts | Reduce priority by 5 |
| Resource Heavy | Requires > 8GB RAM | Reduce priority by 5 |
| Long Running | > 4 hours estimated | Reduce priority by 5 |

---

## 7. Priority Queue

### 7.1 Queue Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRIORITY QUEUE                                 │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Priority 100 (Emergency)     [5 tasks]                  │   │
│  │  Priority 90 (Critical)       [12 tasks]                 │   │
│  │  Priority 80 (High)           [28 tasks]                 │   │
│  │  Priority 50 (Normal)         [156 tasks]                │   │
│  │  Priority 30 (Low)            [89 tasks]                 │   │
│  │  Priority 10 (Idle)           [34 tasks]                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Total: 324 tasks                                               │
│  Next: Priority 100 tasks first                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Queue Operations

```python
class PriorityTaskQueue:
    def enqueue(self, task: Task):
        priority = calculate_priority(task)
        task.priority = priority
        self.queue.put((-priority, task.created_at, task))
    
    def dequeue(self) -> Optional[Task]:
        if self.queue.empty():
            return None
        _, _, task = self.queue.get()
        return task
    
    def peek(self) -> Optional[Task]:
        if self.queue.empty():
            return None
        _, _, task = self.queue.peek()
        return task
```

---

## 8. Priority Monitoring

### 8.1 Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Priority Distribution | Tasks per priority level | Balanced |
| Average Wait Time | Time in queue by priority | < SLA |
| Starvation Rate | Tasks waiting > SLA | 0% |
| Priority Accuracy | Correctly prioritized tasks | > 95% |
| Override Rate | Manual priority overrides | < 5% |

### 8.2 Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│                  PRIORITY ENGINE DASHBOARD                        │
│                                                                  │
│  Priority Distribution:                                         │
│  Emergency: ████████████████████ 5 (1.5%)                       │
│  Critical:  ████████████████████████████ 12 (3.7%)              │
│  High:      ████████████████████████████████████████ 28 (8.6%)  │
│  Normal:    ████████████████████████████████████████████ 156 (48.1%)
│  Low:       ████████████████████████████ 89 (27.5%)             │
│  Idle:      ████████████ 34 (10.5%)                             │
│                                                                  │
│  Wait Times (P50/P95):                                          │
│  Emergency: 2s / 5s                                             │
│  Critical:  10s / 30s                                           │
│  High:      30s / 2min                                          │
│  Normal:    5min / 30min                                        │
│  Low:       30min / 4h                                          │
│  Idle:      2h / 24h                                            │
│                                                                  │
│  Starvation: 0 tasks waiting > SLA                              │
│  Overrides: 3 (0.9%)                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Configuration

```yaml
priority_engine:
  # Calculation weights
  weights:
    base: 0.3
    urgency: 0.4
    impact: 0.3
    effort: 0.1
    dependency: 0.1
    
  # SLA per priority level
  sla:
    emergency: 300     # 5 min
    critical: 900      # 15 min
    high: 3600         # 1 hour
    normal: 14400      # 4 hours
    low: 86400         # 24 hours
    idle: null         # No SLA
    
  # Starvation prevention
  starvation:
    enabled: true
    aging_threshold: 30  # minutes
    max_aging_boost: 30
    
  # Fair share
  fair_share:
    enabled: true
    rebalance_interval: 60s
    
  # Monitoring
  monitoring:
    enabled: true
    metrics_interval: 15s
    alert_on_starvation: true
```
