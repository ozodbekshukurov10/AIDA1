# AIDA Event Routing Strategy

**Document:** Book 2, Chapter 4 — Routing Strategy
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Routing Strategy determines how events are delivered from publishers to subscribers. It supports multiple routing patterns including topic-based, content-based, priority-based, and header-based routing.

---

## 2. Routing Patterns

### 2.1 Pattern Overview

| Pattern | Description | Use Case |
|---------|-------------|----------|
| **Topic-Based** | Route by event topic | Default routing |
| **Content-Based** | Route by event payload | Conditional routing |
| **Priority-Based** | Route by event priority | Critical event handling |
| **Header-Based** | Route by event metadata | Custom routing |
| **Wildcard** | Route by topic pattern | Hierarchical routing |
| **Filter** | Route by custom filter | Complex routing |
| **Sticky** | Route to same consumer | Session affinity |
| **Broadcast** | Send to all consumers | System events |

---

## 3. Topic-Based Routing

### 3.1 Topic Hierarchy

```
{domain}.{entity}.{action}

system.lifecycle.startup
system.lifecycle.shutdown
system.health.check

user.session.connected
user.session.disconnected
user.message.sent
user.message.received

task.lifecycle.created
task.lifecycle.started
task.lifecycle.completed
task.lifecycle.failed

agent.lifecycle.started
agent.lifecycle.stopped
agent.task.assigned
agent.task.completed

ai.request.received
ai.response.generated
ai.token.generated

workflow.lifecycle.created
workflow.step.started
workflow.step.completed
```

### 3.2 Topic Matching Rules

```yaml
topic_matching:
  # Exact match
  - topic: "system.shutdown"
    match: exact
    
  # Single wildcard (*)
  - topic: "task.*"
    match: single_level
    # Matches: task.created, task.started, task.completed
    # Does NOT match: task.lifecycle.created
    
  # Multi-level wildcard (**)
  - topic: "user.**"
    match: multi_level
    # Matches: user.session.connected, user.message.sent
    
  # Combined
  - topic: "*.lifecycle.*"
    match: combined
    # Matches: system.lifecycle.startup, task.lifecycle.created
```

### 3.3 Topic Router

```python
class TopicRouter:
    def route(self, event: Event) -> list[Subscriber]:
        subscribers = []
        
        for subscriber in self.subscribers:
            if self.matches(event.topic, subscriber.topic_filter):
                subscribers.append(subscriber)
        
        return subscribers
    
    def matches(self, topic: str, filter: str) -> bool:
        # Exact match
        if topic == filter:
            return True
        
        # Single wildcard
        if '*' in filter:
            pattern = filter.replace('*', '[^.]+')
            return bool(re.match(f'^{pattern}$', topic))
        
        # Multi-level wildcard
        if '**' in filter:
            pattern = filter.replace('**', '.*')
            return bool(re.match(f'^{pattern}$', topic))
        
        return False
```

---

## 4. Content-Based Routing

### 4.1 Filter Expressions

```yaml
filters:
  # Equality
  - field: "payload.severity"
    operator: "eq"
    value: "critical"
    
  # Comparison
  - field: "payload.duration_ms"
    operator: "gt"
    value: 5000
    
  # Contains
  - field: "payload.tags"
    operator: "contains"
    value: "urgent"
    
  # Regex
  - field: "payload.message"
    operator: "matches"
    value: ".*error.*"
    
  # And/Or
  - operator: "and"
    filters:
      - field: "payload.severity"
        operator: "eq"
        value: "critical"
      - field: "payload.source"
        operator: "eq"
        value: "production"
```

### 4.2 Filter Engine

```python
class FilterEngine:
    def evaluate(self, event: Event, filter_expr: dict) -> bool:
        operator = filter_expr.get("operator", "and")
        
        if operator == "eq":
            return self.get_field(event, filter_expr["field"]) == filter_expr["value"]
        elif operator == "gt":
            return self.get_field(event, filter_expr["field"]) > filter_expr["value"]
        elif operator == "contains":
            return filter_expr["value"] in self.get_field(event, filter_expr["field"])
        elif operator == "matches":
            return bool(re.match(filter_expr["value"], str(self.get_field(event, filter_expr["field"]))))
        elif operator == "and":
            return all(self.evaluate(event, f) for f in filter_expr["filters"])
        elif operator == "or":
            return any(self.evaluate(event, f) for f in filter_expr["filters"])
        
        return False
```

---

## 5. Priority-Based Routing

### 5.1 Priority Queues

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRIORITY ROUTER                               │
│                                                                  │
│  Event Priority → Queue Selection                               │
│                                                                  │
│  90-100 (Emergency) → emergency_queue (dedicated workers)       │
│  70-89 (Critical)   → critical_queue (high-priority workers)    │
│  50-69 (Normal)     → standard_queue (normal workers)           │
│  30-49 (Low)        → background_queue (background workers)     │
│  0-29 (Idle)        → idle_queue (when resources available)     │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Priority Routing Rules

```yaml
priority_routing:
  emergency:
    queue: emergency_queue
    max_workers: 10
    timeout: 5s
    
  critical:
    queue: critical_queue
    max_workers: 20
    timeout: 30s
    
  normal:
    queue: standard_queue
    max_workers: 50
    timeout: 60s
    
  low:
    queue: background_queue
    max_workers: 30
    timeout: 300s
    
  idle:
    queue: idle_queue
    max_workers: 10
    timeout: 600s
```

---

## 6. Header-Based Routing

### 6.1 Header Fields

```python
class EventHeader:
    # Routing headers
    route_to: Optional[str]      # Specific consumer
    route_by: Optional[str]      # Routing key
    channel: Optional[str]       # Channel name
    partition: Optional[int]     # Partition key
    
    # Delivery headers
    delivery_mode: str           # sync, async, batch
    priority: int                # 0-100
    ttl: int                     # Time to live (seconds)
    
    # Correlation headers
    correlation_id: Optional[UUID]
    request_id: Optional[UUID]
    parent_event_id: Optional[UUID]
```

### 6.2 Header Routing Rules

```yaml
header_routing:
  # Route by channel
  - header: "channel"
    values:
      internal: ["task_manager", "workflow_engine"]
      external: ["api_gateway", "websocket"]
      security: ["security_monitor", "audit_log"]
      
  # Route by partition
  - header: "partition"
    strategy: hash
    key: "user_id"
    partitions: 12
    
  # Route by delivery mode
  - header: "delivery_mode"
    values:
      sync: ["critical_handler"]
      async: ["standard_handler"]
      batch: ["batch_handler"]
```

---

## 7. Wildcard Routing

### 7.1 Wildcard Patterns

| Pattern | Example | Matches |
|---------|---------|---------|
| `*` | `task.*` | `task.created`, `task.started` |
| `**` | `user.**` | `user.session.connected`, `user.message.sent` |
| `#` | `agent.#.completed` | `agent.code_agent.completed` |
| `{a,b}` | `task.{created,started}` | `task.created`, `task.started` |
| `[0-9]` | `node.[0-9]` | `node.0`, `node.1` |

### 7.2 Wildcard Router

```python
class WildcardRouter:
    def match(self, topic: str, pattern: str) -> bool:
        # Convert pattern to regex
        regex = self.pattern_to_regex(pattern)
        return bool(re.match(regex, topic))
    
    def pattern_to_regex(self, pattern: str) -> str:
        # Replace wildcards with regex
        pattern = pattern.replace('.', '\\.')
        pattern = pattern.replace('*', '[^.]+')
        pattern = pattern.replace('**', '.+')
        pattern = pattern.replace('#', '[^.]+')
        return f'^{pattern}$'
```

---

## 8. Filter Routing

### 8.1 Filter Types

| Type | Description | Example |
|------|-------------|---------|
| `expression` | Python expression | `event.priority > 50` |
| `sql_like` | SQL WHERE clause | `priority > 50 AND source = 'api'` |
| `jsonpath` | JSONPath query | `$.payload.severity == 'critical'` |
| `cel` | Common Expression Language | `event.priority > 50` |

### 8.2 Filter Configuration

```yaml
filter_routing:
  enabled: true
  
  filters:
    - name: critical_events
      expression: "event.priority >= 90"
      subscribers: ["critical_handler", "audit_log"]
      
    - name: user_events
      expression: "event.topic.startswith('user.')"
      subscribers: ["user_handler", "analytics"]
      
    - name: error_events
      expression: "'error' in event.payload"
      subscribers: ["error_handler", "alerting"]
      
    - name: high_value_users
      expression: "event.user_id in HIGH_VALUE_USERS"
      subscribers: ["priority_handler"]
```

---

## 9. Sticky Routing

### 9.1 Purpose

Ensure events from the same user/session always go to the same consumer for session affinity.

### 9.2 Configuration

```yaml
sticky_routing:
  enabled: true
  
  # Sticky key
  key: "user_id"  # or "session_id", "task_id"
  
  # Partition count
  partitions: 12
  
  # Hash strategy
  hash: consistent  # consistent | modulo
  
  # Rebalance
  rebalance_interval: 300s
```

---

## 10. Broadcast Routing

### 10.1 Purpose

Send events to all subscribers (used for system events, audit events).

### 10.2 Configuration

```yaml
broadcast_routing:
  enabled: true
  
  # Broadcast topics
  topics:
    - "system.**"
    - "security.**"
    - "audit.**"
    
  # Exclude specific subscribers
  exclude:
    - monitoring  # Too noisy
```

---

## 11. Routing Rules Configuration

```yaml
routing_rules:
  # Priority order (first match wins)
  rules:
    # 1. Emergency events → dedicated queue
    - topic: "security.violation.*"
      priority: 100
      queue: emergency_queue
      subscribers: ["security_handler", "audit_log"]
      
    # 2. System events → broadcast
    - topic: "system.**"
      broadcast: true
      subscribers: ["all"]
      
    # 3. Task events → task manager
    - topic: "task.**"
      subscribers: ["task_manager", "monitoring"]
      
    # 4. User events → AI kernel
    - topic: "user.**"
      subscribers: ["ai_kernel", "memory_engine"]
      
    # 5. Default
    - topic: "**"
      subscribers: ["default_handler"]
```

---

## 12. Configuration

```yaml
routing:
  # Default strategy
  default_strategy: topic_based
  
  # Strategies
  strategies:
    topic_based:
      enabled: true
      wildcard_support: true
      
    content_based:
      enabled: true
      filter_engine: cel
      
    priority_based:
      enabled: true
      queue_count: 5
      
    header_based:
      enabled: true
      
    sticky:
      enabled: true
      key: user_id
      
    broadcast:
      enabled: true
      
  # Performance
  performance:
    max_routes_per_second: 10000
    route_timeout: 10ms
    batch_routing: true
    batch_size: 100
    
  # Monitoring
  monitoring:
    log_routes: false
    metrics_interval: 15s
```
