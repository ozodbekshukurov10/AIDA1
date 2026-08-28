# AIDA Event Bus Architecture

**Document:** Book 2, Chapter 4 — Event Bus Architecture
**Version:** 1.0.0
**Date:** 2026-07-04
**Author:** Principal Distributed Systems Architect / Enterprise Event-Driven Architect

---

## 1. Vision

The Event Bus is the **central nervous system** of AIDA. It enables all modules to communicate asynchronously through events without direct coupling. Every module publishes events when something happens, and subscribes to events it cares about. The Event Bus handles routing, delivery, persistence, and recovery.

### 1.1 Core Principles

| Principle | Description |
|-----------|-------------|
| **Loose Coupling** | Modules never call each other directly |
| **Event-First** | Everything is an event (commands, queries, state changes) |
| **At-Least-Once Delivery** | Events are never lost |
| **Replay Support** | Any event can be replayed from storage |
| **Observable** | Every event is tracked and auditable |
| **Distributed Ready** | Works across multiple nodes |
| **Plugin Friendly** | Plugins can publish and subscribe |

---

## 2. Architecture Overview

### 2.1 Layer Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EVENT PRODUCERS                               │
│                                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │   User   │ │   AI     │ │   Task   │ │  Agent   │ │  Plugin  │  │
│  │  Module  │ │  Kernel  │ │ Manager  │ │ Manager  │ │  Manager │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       │            │            │            │            │          │
└───────┼────────────┼────────────┼────────────┼────────────┼──────────┘
        │            │            │            │            │
        ↓            ↓            ↓            ↓            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         EVENT BUS CORE                               │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Event Router                               │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │  Topic   │  │  Filter  │  │ Transform│  │ Validate │    │   │
│  │  │  Router  │  │  Engine  │  │  Engine  │  │  Engine  │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Event Queue                                │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │ Priority │  │  Standard│  │ Delayed  │  │   Dead   │    │   │
│  │  │  Queue   │  │  Queue   │  │  Queue   │  │  Letter  │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Event Storage                               │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │  Active  │  │Completed │  │  Failed  │  │ Archived │    │   │
│  │  │  Store   │  │  Store   │  │  Store   │  │  Store   │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       EVENT CONSUMERS                                │
│                                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │   Task   │ │Workflow  │ │  Model   │ │ Memory   │ │Monitoring│  │
│  │ Manager  │ │ Engine   │ │  Router  │ │  Engine  │ │  Module  │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Relationship

```
EventBus
  ├── uses → EventRouter (route events to subscribers)
  ├── uses → EventQueue (buffer events for delivery)
  ├── uses → EventStorage (persist events for replay)
  ├── uses → EventValidator (validate event schemas)
  ├── uses → EventTransformer (transform event formats)
  └── uses → EventSecurity (authenticate, authorize, encrypt)

EventRouter
  ├── uses → TopicMatcher (match events to topics)
  ├── uses → FilterEngine (apply subscriber filters)
  └── uses → PriorityRouter (prioritize event delivery)

EventStorage
  ├── uses → ActiveStore (Redis - in-flight events)
  ├── uses → CompletedStore (PostgreSQL - processed events)
  ├── uses → FailedStore (PostgreSQL - failed events)
  └── uses → ArchiveStore (S3/PostgreSQL - old events)
```

---

## 3. Event Model

### 3.1 Event Object

```python
class Event:
    # Identity
    event_id: UUID
    event_type: str
    event_version: str  # "1.0"
    
    # Timing
    timestamp: datetime
    published_at: Optional[datetime]
    processed_at: Optional[datetime]
    
    # Source
    source: str          # "ai_kernel", "task_manager", etc.
    source_instance: str # Node ID in distributed setup
    
    # Target
    target: Optional[str]  # Specific consumer (or null for broadcast)
    topic: str             # "user.message", "task.completed", etc.
    
    # Priority
    priority: int  # 0-100
    
    # Correlation
    correlation_id: Optional[UUID]  # Links related events
    request_id: Optional[UUID]      # Original request
    parent_event_id: Optional[UUID] # Event that triggered this
    
    # Context
    user_id: Optional[UUID]
    session_id: Optional[UUID]
    task_id: Optional[UUID]
    agent_id: Optional[str]
    
    # Payload
    payload: dict
    payload_schema: str  # JSON Schema reference
    
    # Metadata
    metadata: dict
    tags: list[str]
    
    # State
    status: str  # created, published, queued, delivered, processed, failed
    
    # Security
    signature: Optional[str]
    encrypted: bool
```

### 3.2 Event Type

```python
class EventType:
    # System
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_HEALTH = "system.health"
    
    # User
    USER_MESSAGE = "user.message"
    USER_ACTION = "user.action"
    USER_FEEDBACK = "user.feedback"
    
    # AI
    AI_REQUEST = "ai.request"
    AI_RESPONSE = "ai.response"
    AI_TOKEN = "ai.token"
    
    # Task
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    
    # Agent
    AGENT_ASSIGNED = "agent.assigned"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    
    # Workflow
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STEP = "workflow.step"
    WORKFLOW_COMPLETED = "workflow.completed"
    
    # Memory
    MEMORY_STORED = "memory.stored"
    MEMORY_RETRIEVED = "memory.retrieved"
    
    # Security
    SECURITY_ALERT = "security.alert"
    SECURITY_AUDIT = "security.audit"
```

---

## 4. Event Channels

### 4.1 Channel Types

| Channel | Purpose | Persistence | Ordering | Delivery |
|---------|---------|-------------|----------|----------|
| `internal` | Module-to-module | Redis | Ordered | At-least-once |
| `external` | Client-facing | Redis | Ordered | At-most-once |
| `plugin` | Plugin communication | Redis | Unordered | At-least-once |
| `security` | Security events | PostgreSQL | Ordered | Exactly-once |
| `monitoring` | Metrics and alerts | Redis | Unordered | At-most-once |
| `workflow` | Workflow orchestration | Redis | Ordered | Exactly-once |
| `realtime` | WebSocket push | Redis Stream | Ordered | At-most-once |

### 4.2 Channel Configuration

```yaml
channels:
  internal:
    backend: redis
    max_size: 100000
    retention: 24h
    ordered: true
    
  external:
    backend: redis
    max_size: 10000
    retention: 1h
    ordered: true
    
  plugin:
    backend: redis
    max_size: 50000
    retention: 6h
    ordered: false
    
  security:
    backend: postgresql
    max_size: unlimited
    retention: 90d
    ordered: true
    
  monitoring:
    backend: redis
    max_size: 10000
    retention: 1h
    ordered: false
    
  workflow:
    backend: redis
    max_size: 50000
    retention: 24h
    ordered: true
    
  realtime:
    backend: redis_stream
    max_size: 10000
    retention: 10m
    ordered: true
```

---

## 5. Event Routing

### 5.1 Topic Structure

```
{domain}.{entity}.{action}

Examples:
  user.message.received
  task.created
  task.completed
  agent.assigned
  workflow.step.executed
  ai.response.generated
  memory.stored
  security.alert.raised
```

### 5.2 Routing Rules

```yaml
routing_rules:
  # Exact match
  - topic: "system.shutdown"
    subscribers: ["all"]
    
  # Wildcard match
  - topic: "task.*"
    subscribers: ["task_manager", "workflow_engine", "monitoring"]
    
  # Hierarchical wildcard
  - topic: "user.*"
    subscribers: ["ai_kernel", "memory_engine", "monitoring"]
    
  # Pattern match
  - topic: "agent.*.completed"
    subscribers: ["task_manager", "workflow_engine"]
    
  # Filtered
  - topic: "ai.token"
    subscribers: ["realtime_stream"]
    filter: "event.priority >= 50"
```

---

## 6. Event Storage

### 6.1 Storage Tiers

| Tier | Storage | Duration | Queryable | Purpose |
|------|---------|----------|-----------|---------|
| Hot | Redis | 1 hour | Yes | Active events |
| Warm | Redis | 24 hours | Yes | Recent events |
| Cold | PostgreSQL | 30 days | Yes | Historical events |
| Archive | PostgreSQL | 90 days | Yes | Compliance |
| Deleted | — | — | No | Purged |

### 6.2 Storage Schema

```sql
-- Active Events (Redis)
-- Key: event:{event_id}
-- Value: JSON event object
-- TTL: 1 hour

-- Completed Events (PostgreSQL)
CREATE TABLE events_completed (
    event_id UUID PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    source VARCHAR(50) NOT NULL,
    topic VARCHAR(200) NOT NULL,
    priority INT NOT NULL,
    payload JSONB NOT NULL,
    metadata JSONB,
    processed_at TIMESTAMP,
    processing_time_ms INT,
    INDEX idx_topic (topic),
    INDEX idx_timestamp (timestamp),
    INDEX idx_source (source)
);

-- Failed Events (PostgreSQL)
CREATE TABLE events_failed (
    event_id UUID PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    source VARCHAR(50) NOT NULL,
    topic VARCHAR(200) NOT NULL,
    payload JSONB NOT NULL,
    error_type VARCHAR(100),
    error_message TEXT,
    retry_count INT,
    last_retry TIMESTAMP,
    INDEX idx_topic (topic),
    INDEX idx_error (error_type)
);
```

---

## 7. Distributed Event Bus

### 7.1 Cluster Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DISTRIBUTED EVENT BUS                         │
│                                                                  │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │   Node 1     │ ←──→ │   Node 2     │ ←──→ │   Node 3     │  │
│  │  (Leader)    │      │  (Follower)  │      │  (Follower)  │  │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘  │
│         │                     │                     │           │
│         └─────────────────────┼─────────────────────┘           │
│                               │                                 │
│                     ┌─────────┴─────────┐                      │
│                     │   Redis Cluster   │                      │
│                     │   (6 nodes)       │                      │
│                     └───────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Replication

```yaml
replication:
  mode: async  # async | sync
  factor: 3    # Replicate to 3 nodes
  
  sync:
    # Wait for all replicas before ack
    min_replicas: 2
    timeout: 100ms
    
  async:
    # Fire and forget
    background_sync: true
    sync_interval: 100ms
```

### 7.3 Partitioning

```yaml
partitioning:
  enabled: true
  strategy: topic_hash  # topic_hash | round_robin | sticky
  
  # Partition count
  partitions: 12
  
  # Partition assignment
  assignment: consistent_hash
  
  # Rebalancing
  rebalance_on_node_join: true
  rebalance_on_node_leave: true
  rebalance_interval: 60s
```

---

## 8. Failure Recovery

### 8.1 Recovery Strategies

| Strategy | When | Description |
|----------|------|-------------|
| Retry | Transient failure | Retry with backoff |
| Replay | Event lost | Replay from storage |
| Dead Letter | Permanent failure | Move to DLQ |
| Alternative Route | Path blocked | Find alternate path |
| Backup Publisher | Publisher down | Use backup publisher |
| Manual Recovery | Unknown failure | Alert operator |

### 8.2 Dead Letter Queue

```yaml
dead_letter_queue:
  enabled: true
  max_size: 10000
  retention: 7d
  
  # Actions on dead letter
  actions:
    - alert_operator: true
    - log_error: true
    - store_for_replay: true
    
  # Auto-retry from DLQ
  auto_retry:
    enabled: true
    max_retries: 3
    retry_delay: 60s
```

---

## 9. Configuration

```yaml
event_bus:
  # Core
  backend: redis
  redis_url: redis://localhost:6379/0
  
  # Channels
  channels:
    internal:
      enabled: true
      max_size: 100000
    external:
      enabled: true
      max_size: 10000
    security:
      enabled: true
      max_size: unlimited
    monitoring:
      enabled: true
      max_size: 10000
      
  # Routing
  routing:
    enabled: true
    wildcard_support: true
    pattern_matching: true
    
  # Storage
  storage:
    active_ttl: 3600
    completed_retention: 86400
    failed_retention: 604800
    archive_retention: 7776000
    
  # Delivery
  delivery:
    max_retries: 3
    retry_delays: [10, 60, 300]
    batch_size: 100
    flush_interval: 1s
    
  # Distributed
  distributed:
    enabled: false
    replication_factor: 3
    partitions: 12
    
  # Monitoring
  monitoring:
    enabled: true
    metrics_interval: 15s
    log_events: false  # Enable for debugging
```
