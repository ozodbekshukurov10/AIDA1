# AIDA Event Lifecycle

**Document:** Book 2, Chapter 4 — Event Lifecycle
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Event Lifecycle defines the complete journey of an event from creation to archival. Every event passes through **9 stages**, each with specific inputs, processing logic, and outputs.

---

## 2. Lifecycle Stages

### 2.1 Complete Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EVENT LIFECYCLE                                │
│                                                                      │
│  1. Create                                                           │
│     ↓                                                                │
│  2. Validate                                                         │
│     ↓                                                                │
│  3. Enrich                                                           │
│     ↓                                                                │
│  4. Publish                                                          │
│     ↓                                                                │
│  5. Queue                                                            │
│     ↓                                                                │
│  6. Route                                                            │
│     ↓                                                                │
│  7. Deliver                                                          │
│     ↓                                                                │
│  8. Process                                                          │
│     ↓                                                                │
│  9. Acknowledge                                                      │
│     ↓                                                                │
│  10. Archive                                                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Stage Details

### 3.1 Stage 1 — Create

| Property | Value |
|----------|-------|
| Input | Module action / state change |
| Output | Raw event object |
| Duration | < 1ms |
| Failure | Event not created |

**Processing:**
```
1. Module detects action/state change
2. Create event object with:
   - Generate event_id (UUID)
   - Set event_type
   - Set timestamp
   - Set source module
   - Set payload
3. Return raw event
```

**Event Creation:**
```python
def create_event(
    event_type: str,
    source: str,
    payload: dict,
    **kwargs
) -> Event:
    return Event(
        event_id=uuid4(),
        event_type=event_type,
        timestamp=datetime.utcnow(),
        source=source,
        payload=payload,
        status="created",
        **kwargs
    )
```

---

### 3.2 Stage 2 — Validate

| Property | Value |
|----------|-------|
| Input | Raw event object |
| Output | Validated event |
| Duration | < 5ms |
| Failure | Event rejected |

**Processing:**
```
1. Validate event schema
2. Validate required fields
3. Validate field types
4. Validate payload structure
5. Validate topic format
6. Return validated event or validation error
```

**Validation Rules:**
```python
validation_rules:
  required_fields:
    - event_id: UUID
    - event_type: str
    - timestamp: datetime
    - source: str
    - topic: str
    - payload: dict
    
  field_types:
    event_id: uuid4
    event_type: str(max_length=100)
    timestamp: datetime
    source: str(max_length=50)
    topic: str(max_length=200)
    priority: int(min=0, max=100)
    payload: dict
    
  topic_format:
    pattern: "^[a-z]+\\.[a-z]+\\.[a-z]+$"
    example: "user.message.received"
```

---

### 3.3 Stage 3 — Enrich

| Property | Value |
|----------|-------|
| Input | Validated event |
| Output | Enriched event |
| Duration | < 10ms |
| Failure | Use defaults |

**Processing:**
```
1. Add correlation_id (if not present)
2. Add request_id (from context)
3. Add session_id (from context)
4. Add user_id (from context)
5. Add metadata (environment, version)
6. Add tags (for filtering)
7. Calculate priority (if not set)
8. Return enriched event
```

**Enrichment Rules:**
```python
enrichment_rules:
  correlation_id:
    generate_if_missing: true
    format: uuid4
    
  metadata:
    auto_add:
      - environment: "production"
      - version: "1.0.0"
      - node_id: "node-1"
      
  priority:
    calculate_if_missing: true
    rules:
      - event_type: "security.*"
        priority: 90
      - event_type: "system.*"
        priority: 80
      - event_type: "task.*"
        priority: 60
      - default: 50
```

---

### 3.4 Stage 4 — Publish

| Property | Value |
|----------|-------|
| Input | Enriched event |
| Output | Published event |
| Duration | < 5ms |
| Failure | Retry or drop |

**Processing:**
```
1. Sign event (if security enabled)
2. Encrypt payload (if encryption enabled)
3. Set status to "published"
4. Set published_at timestamp
5. Publish to Event Bus
6. Return published event
```

---

### 3.5 Stage 5 — Queue

| Property | Value |
|----------|-------|
| Input | Published event |
| Output | Queued event |
| Duration | < 2ms |
| Failure | Retry or dead letter |

**Processing:**
```
1. Determine target queue based on priority
2. Add to queue with correct priority
3. Set status to "queued"
4. Set queued_at timestamp
5. Return queued event
```

**Queue Selection:**
```python
def select_queue(event: Event) -> str:
    if event.priority >= 90:
        return "emergency_queue"
    elif event.priority >= 70:
        return "critical_queue"
    elif event.priority >= 50:
        return "standard_queue"
    else:
        return "background_queue"
```

---

### 3.6 Stage 6 — Route

| Property | Value |
|----------|-------|
| Input | Queued event |
| Output | Routed event |
| Duration | < 10ms |
| Failure | Dead letter |

**Processing:**
```
1. Match event topic to subscriber topics
2. Apply subscriber filters
3. Determine delivery targets
4. Set status to "routing"
5. Return routed event with targets
```

**Routing Logic:**
```python
def route_event(event: Event) -> list[Subscriber]:
    subscribers = []
    
    for subscriber in self.subscribers:
        # Topic match
        if not topic_matches(event.topic, subscriber.topic_filter):
            continue
        
        # Filter match
        if subscriber.filter and not evaluate_filter(subscriber.filter, event):
            continue
        
        # Permission check
        if not subscriber.has_permission(event.event_type):
            continue
        
        subscribers.append(subscriber)
    
    return subscribers
```

---

### 3.7 Stage 7 — Deliver

| Property | Value |
|----------|-------|
| Input | Routed event + targets |
| Output | Delivered event |
| Duration | < 50ms |
| Failure | Retry or dead letter |

**Processing:**
```
1. For each target subscriber:
   a. Check subscriber availability
   b. Deliver event to subscriber
   c. Wait for acknowledgment (or timeout)
   d. Set delivered_at timestamp
2. Set status to "delivered"
3. Return delivered event
```

**Delivery Modes:**
| Mode | Description | Use Case |
|------|-------------|----------|
| `sync` | Wait for ack | Critical events |
| `async` | Fire and forget | Non-critical events |
| `batch` | Batch delivery | High-throughput |
| `streaming` | Continuous stream | Real-time updates |

---

### 3.8 Stage 8 — Process

| Property | Value |
|----------|-------|
| Input | Delivered event |
| Output | Processed event |
| Duration | Variable (1ms — 300s) |
| Failure | Retry or fail |

**Processing:**
```
1. Subscriber receives event
2. Subscriber processes event
3. Subscriber produces result
4. Set status to "processed"
5. Set processed_at timestamp
6. Return processed event
```

---

### 3.9 Stage 9 — Acknowledge

| Property | Value |
|----------|-------|
| Input | Processed event |
| Output | Acknowledged event |
| Duration | < 5ms |
| Failure | Requeue |

**Processing:**
```
1. Subscriber sends ack
2. Remove from queue
3. Set status to "acknowledged"
4. Set acknowledged_at timestamp
5. Move to completed store
6. Return acknowledged event
```

---

### 3.10 Stage 10 — Archive

| Property | Value |
|----------|-------|
| Input | Acknowledged event |
| Output | Archived event |
| Duration | < 10ms |
| Failure | Log warning |

**Processing:**
```
1. Check retention policy
2. If retention expired:
   a. Move to archive store
   b. Remove from active/completed store
3. Set status to "archived"
4. Return archived event
```

---

## 4. State Diagram

```
┌─────────┐   validate   ┌──────────┐   enrich   ┌──────────┐
│ created │─────────────→│ validated│────────────→│ enriched │
└─────────┘              └──────────┘             └────┬────┘
     │                                                  │
     │ invalid                                          │ publish
     ↓                                                  ↓
┌─────────┐                                      ┌──────────┐
│ rejected│                                      │ published│
└─────────┘                                      └────┬────┘
                                                       │
                                                       │ queue
                                                       ↓
                                                  ┌──────────┐
                                                  │  queued  │
                                                  └────┬────┘
                                                       │
                                                       │ route
                                                       ↓
                                                  ┌──────────┐
                                                  │  routed  │
                                                  └────┬────┘
                                                       │
                                                       │ deliver
                                                       ↓
                                                  ┌──────────┐
                                                  │ delivered│
                                                  └────┬────┘
                                                       │
                                                       │ process
                                                       ↓
                                                  ┌──────────┐
                                                  │ processed│
                                                  └────┬────┘
                                                       │
                                                       │ ack
                                                       ↓
                                                  ┌──────────┐
                                                  │acknowledged│
                                                  └────┬────┘
                                                       │
                                                       │ archive
                                                       ↓
                                                  ┌──────────┐
                                                  │ archived │
                                                  └──────────┘
```

---

## 5. Failure States

```
┌─────────┐   fail   ┌─────────┐
│ created │─────────→│ failed  │
└─────────┘          └────┬────┘
                          │
                          │ retry
                          ↓
                     ┌─────────┐
                     │ retrying│
                     └────┬────┘
                          │
                          ├── success → re-enter lifecycle
                          │
                          └── max retries → dead_letter → failed
```

---

## 6. Timing Summary

| Stage | Min | Average | Max |
|-------|-----|---------|-----|
| 1. Create | 0.1ms | 0.5ms | 1ms |
| 2. Validate | 1ms | 3ms | 5ms |
| 3. Enrich | 1ms | 5ms | 10ms |
| 4. Publish | 1ms | 3ms | 5ms |
| 5. Queue | 0.5ms | 1ms | 2ms |
| 6. Route | 2ms | 5ms | 10ms |
| 7. Deliver | 5ms | 20ms | 50ms |
| 8. Process | 1ms | 100ms | 300s |
| 9. Acknowledge | 0.5ms | 2ms | 5ms |
| 10. Archive | 1ms | 5ms | 10ms |
| **Total (fast)** | **12ms** | **145ms** | **360ms** |
| **Total (slow)** | **12ms** | **145ms** | **300s+** |

---

## 7. Configuration

```yaml
event_lifecycle:
  # Validation
  validation:
    enabled: true
    strict_mode: true
    schema_validation: true
    
  # Enrichment
  enrichment:
    auto_correlation_id: true
    auto_metadata: true
    auto_priority: true
    
  # Publishing
  publishing:
    sign_events: true
    encrypt_payload: false
    
  # Queueing
  queueing:
    priority_queues: true
    max_queue_size: 100000
    
  # Routing
  routing:
    wildcard_support: true
    filter_support: true
    
  # Delivery
  delivery:
    default_mode: async
    sync_timeout: 5000ms
    batch_size: 100
    
  # Acknowledgment
  acknowledgment:
    required: true
    timeout: 30000ms
    on_timeout: requeue
    
  # Archival
  archival:
    enabled: true
    retention:
      active: 1h
      completed: 24h
      failed: 7d
      archived: 90d
```
