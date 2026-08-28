# AIDA Event Subscription Model

**Document:** Book 2, Chapter 4 — Subscription Model
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Subscription Model defines how modules subscribe to events, manage subscriptions, and handle event delivery. It supports subscribe, unsubscribe, filter, replay, pause, and resume operations.

---

## 2. Subscription Interface

### 2.1 Core Operations

```python
class ISubscriptionManager:
    # Subscribe
    async def subscribe(
        subscriber_id: str,
        topic_filter: str,
        callback: Callable,
        options: SubscriptionOptions
    ) -> Subscription
    
    # Unsubscribe
    async def unsubscribe(subscription_id: str) -> bool
    
    # Filter
    async def update_filter(subscription_id: str, filter_expr: dict) -> bool
    
    # Replay
    async def replay(subscription_id: str, from_time: datetime) -> int
    
    # Pause
    async def pause(subscription_id: str) -> bool
    
    # Resume
    async def resume(subscription_id: str) -> bool
```

### 2.2 Subscription Object

```python
class Subscription:
    subscription_id: UUID
    subscriber_id: str
    topic_filter: str
    callback: Callable
    options: SubscriptionOptions
    
    # State
    status: str  # active, paused, cancelled
    created_at: datetime
    updated_at: datetime
    
    # Statistics
    events_received: int
    events_processed: int
    events_failed: int
    last_event_at: Optional[datetime]
    avg_processing_time_ms: float
    
    # Position
    last_offset: Optional[int]  # For replay
    last_event_id: Optional[UUID]
```

### 2.3 Subscription Options

```python
class SubscriptionOptions:
    # Delivery
    delivery_mode: str = "async"  # sync, async, batch
    batch_size: int = 1
    batch_timeout_ms: int = 1000
    
    # Filtering
    filter_expr: Optional[dict] = None
    priority_min: int = 0
    priority_max: int = 100
    
    # Retry
    max_retries: int = 3
    retry_delay_ms: int = 1000
    
    # Buffering
    buffer_size: int = 1000
    backpressure: str = "drop_oldest"  # drop_oldest, drop_newest, block
    
    # Concurrency
    concurrency: int = 1
    ordered: bool = True
    
    # Retention
    retention_hours: int = 24
```

---

## 3. Subscription Patterns

### 3.1 Point-to-Point

```
┌──────────────┐         ┌──────────────┐
│   Publisher  │ ──────→ │  Subscriber  │
└──────────────┘         └──────────────┘

One event → One subscriber
Use case: Task assignment, command execution
```

### 3.2 Publish-Subscribe

```
                    ┌──────────────┐
               ┌──→ │  Subscriber 1│
┌──────────────┤    └──────────────┘
│   Publisher  │ ──→ ┌──────────────┐
│              │    │  Subscriber 2│
└──────────────┤    └──────────────┘
               └──→ ┌──────────────┐
                    │  Subscriber 3│
                    └──────────────┘

One event → Multiple subscribers
Use case: System events, notifications
```

### 3.3 Request-Reply

```
┌──────────────┐         ┌──────────────┐
│   Requester  │ ──────→ │   Responder  │
│              │ ←────── │              │
└──────────────┘         └──────────────┘

Request event → Reply event
Use case: AI queries, API calls
```

### 3.4 Competing Consumers

```
                    ┌──────────────┐
                    │  Consumer 1  │
┌──────────────┐ ──→└──────────────┘
│   Publisher  │ ──→ ┌──────────────┐
│              │    │  Consumer 2  │
└──────────────┘ ──→└──────────────┘
                    ┌──────────────┐
                    │  Consumer 3  │
                    └──────────────┘

One event → One consumer (competing)
Use case: Task processing, load balancing
```

---

## 4. Subscription Management

### 4.1 Subscribe

```python
async def subscribe(
    subscriber_id: str,
    topic_filter: str,
    callback: Callable,
    options: SubscriptionOptions = None
) -> Subscription:
    """Create new subscription."""
    
    # Validate subscriber
    if not await self.validate_subscriber(subscriber_id):
        raise InvalidSubscriberError(subscriber_id)
    
    # Validate topic filter
    if not self.validate_topic_filter(topic_filter):
        raise InvalidTopicFilterError(topic_filter)
    
    # Create subscription
    subscription = Subscription(
        subscription_id=uuid4(),
        subscriber_id=subscriber_id,
        topic_filter=topic_filter,
        callback=callback,
        options=options or SubscriptionOptions(),
        status="active",
        created_at=datetime.utcnow()
    )
    
    # Store subscription
    await self.store.save(subscription)
    
    # Register with router
    self.router.register(subscription)
    
    # Log subscription
    logger.info("subscription_created", subscription_id=subscription.subscription_id)
    
    return subscription
```

### 4.2 Unsubscribe

```python
async def unsubscribe(subscription_id: str) -> bool:
    """Remove subscription."""
    
    # Get subscription
    subscription = await self.store.get(subscription_id)
    if not subscription:
        return False
    
    # Unregister from router
    self.router.unregister(subscription_id)
    
    # Mark as cancelled
    subscription.status = "cancelled"
    await self.store.save(subscription)
    
    # Log unsubscription
    logger.info("subscription_removed", subscription_id=subscription_id)
    
    return True
```

### 4.3 Update Filter

```python
async def update_filter(subscription_id: str, filter_expr: dict) -> bool:
    """Update subscription filter."""
    
    subscription = await self.store.get(subscription_id)
    if not subscription:
        return False
    
    # Validate filter
    if not self.validate_filter(filter_expr):
        raise InvalidFilterError(filter_expr)
    
    # Update filter
    subscription.options.filter_expr = filter_expr
    subscription.updated_at = datetime.utcnow()
    await self.store.save(subscription)
    
    # Update router
    self.router.update_filter(subscription_id, filter_expr)
    
    return True
```

### 4.4 Pause & Resume

```python
async def pause(subscription_id: str) -> bool:
    """Pause subscription (stop receiving events)."""
    
    subscription = await self.store.get(subscription_id)
    if not subscription:
        return False
    
    subscription.status = "paused"
    await self.store.save(subscription)
    
    # Pause router
    self.router.pause(subscription_id)
    
    return True

async def resume(subscription_id: str) -> bool:
    """Resume subscription."""
    
    subscription = await self.store.get(subscription_id)
    if not subscription:
        return False
    
    subscription.status = "active"
    await self.store.save(subscription)
    
    # Resume router
    self.router.resume(subscription_id)
    
    return True
```

### 4.5 Replay

```python
async def replay(subscription_id: str, from_time: datetime) -> int:
    """Replay events from a specific time."""
    
    subscription = await self.store.get(subscription_id)
    if not subscription:
        return 0
    
    # Get events from storage
    events = await self.storage.get_events_after(
        topic_filter=subscription.topic_filter,
        after=from_time
    )
    
    # Replay events
    count = 0
    for event in events:
        try:
            await subscription.callback(event)
            count += 1
        except Exception as e:
            logger.error("replay_error", event_id=event.event_id, error=str(e))
    
    logger.info("replay_completed", subscription_id=subscription_id, count=count)
    
    return count
```

---

## 5. Subscriber Registry

### 5.1 Registered Subscribers

| Subscriber | Topics | Description |
|------------|--------|-------------|
| `task_manager` | `task.*`, `agent.*` | Task lifecycle management |
| `workflow_engine` | `workflow.*`, `task.*` | Workflow orchestration |
| `ai_kernel` | `ai.*`, `user.*` | AI processing |
| `memory_engine` | `memory.*`, `user.*` | Memory management |
| `knowledge_engine` | `knowledge.*` | Knowledge base |
| `monitoring` | `**` | System monitoring |
| `audit_log` | `security.*`, `system.*` | Audit trail |
| `realtime_stream` | `ai.token`, `task.progress` | Real-time updates |
| `analytics` | `user.*`, `task.*`, `ai.*` | Analytics |
| `plugin_manager` | `plugin.*` | Plugin lifecycle |

### 5.2 Subscriber Configuration

```yaml
subscribers:
  task_manager:
    topics:
      - "task.**"
      - "agent.**"
    concurrency: 5
    ordered: true
    max_retries: 3
    
  workflow_engine:
    topics:
      - "workflow.**"
      - "task.**"
    concurrency: 3
    ordered: true
    max_retries: 3
    
  ai_kernel:
    topics:
      - "ai.**"
      - "user.**"
    concurrency: 10
    ordered: true
    max_retries: 3
    
  monitoring:
    topics:
      - "**"
    concurrency: 1
    ordered: false
    max_retries: 0
    
  audit_log:
    topics:
      - "security.**"
      - "system.**"
    concurrency: 1
    ordered: true
    max_retries: 0
```

---

## 6. Backpressure Handling

### 6.1 Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `drop_oldest` | Drop oldest event in buffer | Non-critical events |
| `drop_newest` | Drop newest event | Critical events |
| `block` | Block publisher until space | Critical events |
| `scale_up` | Increase consumer count | Auto-scaling |
| `dead_letter` | Move to dead letter queue | Failed events |

### 6.2 Configuration

```yaml
backpressure:
  strategy: drop_oldest
  
  thresholds:
    warning: 0.7  # 70% buffer full
    critical: 0.9  # 90% buffer full
    
  actions:
    warning:
      - alert_operator: false
      - log_warning: true
    critical:
      - alert_operator: true
      - scale_consumers: true
      - dead_letter_oldest: true
```

---

## 7. Monitoring

### 7.1 Subscription Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Active subscriptions | Currently active | Track |
| Events received | Total received | Track |
| Events processed | Total processed | Track |
| Events failed | Total failed | < 1% |
| Avg processing time | Per event | < 100ms |
| Queue depth | Events waiting | < 1000 |
| Consumer lag | Events behind | < 100 |

### 7.2 Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│                  SUBSCRIPTION DASHBOARD                           │
│                                                                  │
│  Active Subscriptions: 12                                       │
│                                                                  │
│  Subscriber Status:                                             │
│  task_manager:     [ACTIVE]  received: 1523, processed: 1520   │
│  workflow_engine:  [ACTIVE]  received: 892, processed: 890     │
│  ai_kernel:        [ACTIVE]  received: 2341, processed: 2338   │
│  monitoring:       [ACTIVE]  received: 15623, processed: 15620 │
│  audit_log:        [ACTIVE]  received: 4521, processed: 4521   │
│  realtime_stream:  [PAUSED]  received: 0, processed: 0         │
│                                                                  │
│  Queue Depths:                                                  │
│  task_manager:     3                                             │
│  workflow_engine:  2                                             │
│  ai_kernel:        3                                             │
│  monitoring:       3                                             │
│                                                                  │
│  Consumer Lag:                                                  │
│  task_manager:     0                                             │
│  workflow_engine:  0                                             │
│  ai_kernel:        0                                             │
│  monitoring:       0                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Configuration

```yaml
subscriptions:
  # Default options
  defaults:
    delivery_mode: async
    batch_size: 1
    max_retries: 3
    buffer_size: 1000
    
  # Backpressure
  backpressure:
    strategy: drop_oldest
    warning_threshold: 0.7
    critical_threshold: 0.9
    
  # Replay
  replay:
    enabled: true
    max_replay_events: 10000
    replay_timeout: 60s
    
  # Monitoring
  monitoring:
    enabled: true
    metrics_interval: 15s
    
  # Limits
  limits:
    max_subscriptions_per_subscriber: 100
    max_total_subscriptions: 1000
    max_filter_complexity: 10
```
