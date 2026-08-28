# AIDA Queue System

**Document:** Book 2, Chapter 2 — Queue System
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Queue System is the **nervous system** of the Runtime Engine. It provides reliable, durable, and prioritized task queuing that survives crashes, scales horizontally, and supports multiple delivery semantics.

---

## 2. Queue Architecture

### 2.1 Layer Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRODUCERS (Kernel / API)                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Enqueue
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                     QUEUE ROUTER                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Priority Classifier: critical(100) > high(80) >         │   │
│  │                       standard(50) > background(20)     │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────┬──────────────┬──────────────┬───────────────────────┘
           │              │              │
           ↓              ↓              ↓
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Critical   │ │  Standard   │ │ Background  │
│   Queue     │ │   Queue     │ │   Queue     │
│  (Redis)    │ │  (Redis)    │ │  (Redis)    │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │              │              │
       ↓              ↓              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     CONSUMER POOL                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Consumer │  │ Consumer │  │ Consumer │  │ Consumer │        │
│  │ Group 1  │  │ Group 2  │  │ Group 3  │  │ Group N  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Process
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Retry     │  │ Dead Letter │  │  Delayed    │             │
│  │   Queue     │  │   Queue     │  │   Queue     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Queue Types

| Queue | Purpose | Storage | Max Size | TTL |
|-------|---------|---------|----------|-----|
| `critical` | Security alerts, system failures | Redis List | 10,000 | 1h |
| `high` | User-facing tasks, API requests | Redis Sorted Set | 50,000 | 4h |
| `standard` | Normal processing | Redis Sorted Set | 100,000 | 24h |
| `background` | Batch jobs, training | Redis Sorted Set | 50,000 | 72h |
| `delayed` | Scheduled execution | Redis Sorted Set + Timer | 10,000 | 7d |
| `retry` | Failed task retry | Redis List | 10,000 | 24h |
| `dead_letter` | Permanently failed | PostgreSQL | Unlimited | Permanent |
| `stream` | Real-time events | Redis Stream | 1,000,000 | 7d |

---

## 4. Queue Interface

```python
class IQueueManager:
    # Core operations
    async def enqueue(queue: str, task: Task, priority: int = 50) -> QueuePosition
    async def dequeue(queue: str, timeout: int = 30) -> Optional[Task]
    async def peek(queue: str, count: int = 10) -> list[Task]
    async def size(queue: str) -> int
    
    # Task management
    async def ack(task_id: UUID) -> bool
    async def nack(task_id: UUID, requeue: bool = True) -> bool
    async def extend(task_id: UUID, additional_seconds: int) -> bool
    
    # Routing
    async def move(task_id: UUID, from_queue: str, to_queue: str) -> bool
    async def delay(task_id: UUID, delay_seconds: int) -> bool
    async def schedule(task_id: UUID, run_at: datetime) -> bool
    
    # Retry / DLQ
    async def retry(task_id: UUID) -> bool
    async def dead_letter(task_id: UUID, error: Exception) -> bool
    async def retry_all(queue: str) -> int
    
    # Maintenance
    async def purge(queue: str) -> int
    async def health_check() -> QueueHealth
```

---

## 5. Message Format

```python
class QueueMessage:
    message_id: UUID
    task_id: UUID
    queue: str
    priority: int
    body: bytes
    metadata: dict
    created_at: datetime
    expires_at: Optional[datetime]
    visible_after: datetime
    receive_count: int
    max_receives: int
    
class QueuePosition:
    task_id: UUID
    position: int
    queue: str
    estimated_wait: timedelta
```

---

## 6. Priority System

### 6.1 Priority Levels

```
100 ─── CRITICAL ─── System emergencies, security alerts
 90 ─── URGENT ───── User-facing errors, SLA breach risk
 80 ─── HIGH ─────── Active user requests, API calls
 70 ─── ELEVATED ─── Scheduled tasks near deadline
 60 ─── ABOVE_NORMAL 
 50 ─── STANDARD ─── Default priority
 40 ─── BELOW_NORMAL
 30 ─── LOW ──────── Background analysis, training
 20 ─── MINIMAL ──── Batch jobs, archival
 10 ─── BULK ─────── Cleanup, maintenance
```

### 6.2 Priority Boost Rules

| Trigger | Boost |
|---------|-------|
| User has active subscription | +10 |
| Task waited > 60s | +5 |
| Task waited > 300s | +15 |
| SLA deadline < 30s | +20 |
| Retry attempt > 2 | +10 |
| Security-critical task | +25 |

### 6.3 Fair Share Allocation

```yaml
fair_share:
  enabled: true
  
  tenant_shares:
    - tenant: "enterprise"
      min_share: 30%
      max_share: 60%
    - tenant: "pro"
      min_share: 20%
      max_share: 40%
    - tenant: "free"
      min_share: 10%
      max_share: 20%
      
  rebalance_interval: 30s
  starvation_prevention:
    enabled: true
    min_wait_boost: 60s
    max_boost: 30
```

---

## 7. Delivery Guarantees

### 7.1 At-Most-Once Delivery

```yaml
at_most_once:
  enabled: false
  use_case: Metrics, telemetry
  ack_required: false
```

### 7.2 At-Least-Once Delivery (Default)

```yaml
at_least_once:
  enabled: true
  ack_required: true
  visibility_timeout: 300s
  max_receive_count: 3
  on_max_receives: dead_letter
```

### 7.3 Exactly-Once Delivery

```yaml
exactly_once:
  enabled: false
  use_case: Financial transactions, billing
  implementation: Idempotency keys + deduplication
  dedup_window: 300s
```

---

## 8. Visibility Timeout

```
Task dequeued (visibility_timeout = 300s)
    │
    ├── Worker processing... (complete before timeout) → ACK
    │
    └── Worker crashes... (timeout expires)
         │
         └── Task becomes visible again → Requeued to same queue
```

```yaml
visibility_timeout:
  default: 300s
  by_task_type:
    simple_chat: 60s
    code_generation: 180s
    repository_analysis: 600s
    llm_inference: 120s
```

---

## 9. Retry Mechanism

### 9.1 Retry Strategy

```python
class RetryStrategy:
    max_retries: int = 3
    retry_delays: list[int] = [10, 60, 300]  # seconds
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retryable_errors: list[str] = [
        "TimeoutError",
        "ConnectionError",
        "RateLimitError",
        "ServiceUnavailableError",
    ]
    non_retryable_errors: list[str] = [
        "ValidationError",
        "AuthenticationError",
        "PermissionDeniedError",
    ]
```

### 9.2 Exponential Backoff

```
Attempt 1: 10s delay
Attempt 2: 20s delay (10 * 2)
Attempt 3: 40s delay (20 * 2)

With jitter:
Attempt 1: 10s + random(0-5s)
Attempt 2: 20s + random(0-10s)
Attempt 3: 40s + random(0-20s)
```

### 9.3 Retry Flow

```
Task Failed
    │
    ├── Error is retryable?
    │   ├── YES
    │   │   ├── Retries < max_retries?
    │   │   │   ├── YES → Calculate delay → Delay Queue
    │   │   │   │         └── After delay → Original Queue
    │   │   │   └── NO → Dead Letter Queue
    │   │   └── Log retry attempt
    │   └── NO
    │       └── Dead Letter Queue
    └── Update task status
```

---

## 10. Dead Letter Queue

### 10.1 Purpose

Tasks that fail permanently (max retries exceeded, non-retryable errors) go to the Dead Letter Queue for manual inspection, debugging, and potential reprocessing.

### 10.2 DLQ Interface

```python
class IDeadLetterQueue:
    async def list(filters: DLQFilter) -> list[DeadLetterTask]
    async def inspect(task_id: UUID) -> DeadLetterDetail
    async def retry(task_id: UUID) -> bool
    async def retry_all(queue: str) -> int
    async def archive(task_id: UUID) -> bool
    async def delete(task_id: UUID) -> bool
    async def get_stats() -> DLQStats
```

### 10.3 DLQ Data

```python
class DeadLetterTask:
    task_id: UUID
    original_queue: str
    error_type: str
    error_message: str
    error_traceback: str
    attempts: int
    first_attempt: datetime
    last_attempt: datetime
    task_payload: dict
    context: dict  # worker_id, sandbox_id, etc.
```

---

## 11. Delayed Queue

### 11.1 Purpose

Supports scheduling tasks for future execution (cron-like, delayed retry, rate limiting).

### 11.2 Implementation

```
┌─────────────────────────────────────────────────┐
│              DELAYED QUEUE                        │
│                                                  │
│  Redis Sorted Set:                               │
│    score = execution_timestamp                    │
│    member = task_id                              │
│                                                  │
│  Polling Worker (every 1s):                      │
│    1. ZRANGEBYSCORE queue 0 <now> LIMIT 100      │
│    2. For each task:                             │
│       - Move to ready queue                      │
│       - Remove from delayed set                  │
│    3. Repeat                                     │
└─────────────────────────────────────────────────┘
```

```yaml
delayed_queue:
  poll_interval: 1s
  batch_size: 100
  max_delay: 30d
```

---

## 12. Stream Queue

### 12.1 Purpose

Real-time streaming of events, tokens, progress updates from workers to clients.

### 12.2 Stream Events

```python
class StreamEvent:
    event_id: UUID
    stream_name: str
    event_type: str  # "token", "progress", "status", "error"
    data: dict
    timestamp: datetime
    
class StreamConsumer:
    consumer_id: str
    stream_name: str
    last_event_id: Optional[UUID]
    group: Optional[str]
```

### 12.3 Stream Configuration

```yaml
streams:
  token_stream:
    max_length: 10000
    retention: 1h
    consumer_group: "token_processors"
    
  progress_stream:
    max_length: 1000
    retention: 10m
    
  event_stream:
    max_length: 100000
    retention: 24h
    consumer_groups:
      - "analytics"
      - "audit_log"
      - "real_time_dashboard"
```

---

## 13. Consumer Groups

### 13.1 Purpose

Consumer groups enable **competing consumers** — multiple workers can process tasks from the same queue without duplicate processing.

### 13.2 Consumer Group Configuration

```yaml
consumer_groups:
  code_workers:
    queue: standard
    consumers: 10
    prefetch: 5
    batch_size: 1
    
  ai_workers:
    queue: high
    consumers: 5
    prefetch: 2
    batch_size: 1
    
  background_workers:
    queue: background
    consumers: 20
    prefetch: 10
    batch_size: 5
```

### 13.3 Prefetch

```yaml
prefetch:
  enabled: true
  
  # How many messages to prefetch ahead
  count:
    simple_task: 10
    medium_task: 5
    heavy_task: 2
    gpu_task: 1
    
  # When to fetch more
  threshold: 0.5  # Fetch when 50% of prefetched are processed
```

---

## 14. Monitoring & Metrics

### 14.1 Key Metrics

```
Queue Metrics (per queue):
  - queue_depth: Number of tasks in queue
  - enqueue_rate: Tasks/second added
  - dequeue_rate: Tasks/second consumed
  - processing_time_p50: Median processing time
  - processing_time_p95: 95th percentile processing time
  - processing_time_p99: 99th percentile processing time
  - retry_rate: Percentage of tasks retried
  - dlq_rate: Percentage of tasks sent to DLQ
  - age_of_oldest: Age of oldest unprocessed task
  - consumer_lag: Distance between producer and consumer positions
```

### 14.2 Alerting

```yaml
alerts:
  - name: queue_depth_high
    condition: queue_depth > 10000
    duration: 5m
    severity: warning
    
  - name: queue_depth_critical
    condition: queue_depth > 50000
    duration: 2m
    severity: critical
    
  - name: processing_time_high
    condition: processing_time_p95 > 60s
    duration: 10m
    severity: warning
    
  - name: dlq_rate_high
    condition: dlq_rate > 5%
    duration: 15m
    severity: warning
    
  - name: consumer_lag_high
    condition: consumer_lag > 1000
    duration: 5m
    severity: warning
```

---

## 15. Disaster Recovery

### 15.1 Persistence

```yaml
persistence:
  redis:
    append_only: yes
    save_interval: 60s
    replica_count: 2
    
  postgresql_dql:
    enabled: true
    sync_interval: 30s
    
  backup:
    enabled: true
    interval: 1h
    retention: 7d
```

### 15.2 Failover

```
Redis Primary fails
    │
    ├── Sentinel detects failure (5s)
    │
    ├── Promotes replica to primary (10s)
    │
    ├── Updates DNS / connection pool (5s)
    │
    └── Total downtime: < 20s
```

---

## 16. Configuration

```yaml
queue_system:
  redis:
    url: redis://localhost:6379/0
    pool_size: 20
    timeout: 5s
    
  queues:
    critical:
      max_size: 10000
      message_ttl: 3600
      visibility_timeout: 120
    high:
      max_size: 50000
      message_ttl: 14400
      visibility_timeout: 300
    standard:
      max_size: 100000
      message_ttl: 86400
      visibility_timeout: 300
    background:
      max_size: 50000
      message_ttl: 259200
      visibility_timeout: 600
      
  retry:
    max_retries: 3
    retry_delays: [10, 60, 300]
    dead_letter_after: 3
    
  monitoring:
    metrics_interval: 15s
    health_check_interval: 10s
```
