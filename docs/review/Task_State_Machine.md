# AIDA Task State Machine

**Document:** Book 2, Chapter 3 — Task State Machine
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Task State Machine defines all possible states a task can be in, the transitions between states, and the rules governing those transitions. It provides a formal, auditable model for task lifecycle management.

---

## 2. State Definitions

### 2.1 All States

| State | Description | Terminal |
|-------|-------------|----------|
| `created` | Task created, not yet processed | No |
| `queued` | Task in queue, waiting for scheduling | No |
| `analyzing` | Task being analyzed for decomposition | No |
| `planning` | Task being planned (decomposition) | No |
| `scheduled` | Task scheduled for execution | No |
| `assigned` | Task assigned to agent/model | No |
| `waiting` | Task waiting for dependencies | No |
| `running` | Task currently executing | No |
| `paused` | Task execution paused | No |
| `validating` | Task result being validated | No |
| `aggregating` | Results being aggregated | No |
| `reviewing` | Final review in progress | No |
| `completed` | Task successfully finished | Yes |
| `failed` | Task failed | Yes |
| `cancelled` | Task cancelled by user/system | Yes |
| `retrying` | Task being retried | No |
| `archived` | Task archived for history | Yes |

---

## 3. State Diagram

### 3.1 Complete State Machine

```
                                    ┌─────────────────────────────────┐
                                    │                                 │
                                    ↓                                 │
┌─────────┐   analyze   ┌─────────┐   plan   ┌─────────┐            │
│ created │────────────→│analyzing│─────────→│ planning│            │
└─────────┘             └─────────┘          └────┬────┘            │
                            │                     │                  │
                            │ fail                │ complete         │
                            ↓                     ↓                  │
                       ┌─────────┐          ┌─────────┐             │
                       │ failed  │←─────────│ queued  │             │
                       └─────────┘          └────┬────┘             │
                                                 │                  │
                                                 │ schedule         │
                                                 ↓                  │
                                            ┌─────────┐             │
                                            │scheduled│             │
                                            └────┬────┘             │
                                                 │                  │
                                                 │ assign           │
                                                 ↓                  │
                                            ┌─────────┐             │
                                            │assigned │             │
                                            └────┬────┘             │
                                                 │                  │
                                    ┌────────────┼────────────┐     │
                                    │            │            │     │
                                    ↓            ↓            ↓     │
                              ┌─────────┐ ┌─────────┐ ┌─────────┐  │
                              │ waiting │ │ running │ │ paused  │  │
                              └────┬────┘ └────┬────┘ └────┬────┘  │
                                   │           │            │       │
                                   │ ready     │ complete   │resume │
                                   │           ↓            │       │
                                   │      ┌─────────┐      │       │
                                   │      │validating│      │       │
                                   │      └────┬────┘      │       │
                                   │           │            │       │
                                   │           ↓            │       │
                                   │      ┌─────────┐      │       │
                                   │      │aggregating│     │       │
                                   │      └────┬────┘      │       │
                                   │           │            │       │
                                   │           ↓            │       │
                                   │      ┌─────────┐      │       │
                                   │      │reviewing │      │       │
                                   │      └────┬────┘      │       │
                                   │           │            │       │
                                   │           ↓            │       │
                                   │      ┌─────────┐      │       │
                                   │      │completed│      │       │
                                   │      └─────────┘      │       │
                                   │                       │       │
                                   └───────────────────────┘───────┘
                                            (dependency ready)
```

### 3.2 Simplified Flow

```
created → analyzing → planning → queued → scheduled → assigned → running → completed
                                    ↑         │
                                    │         │ fail
                                    │         ↓
                                    └────── retrying → failed
```

---

## 4. State Transitions

### 4.1 Transition Table

| From State | To State | Trigger | Condition |
|------------|----------|---------|-----------|
| `created` | `analyzing` | `start_analysis` | Request received |
| `created` | `failed` | `analysis_failed` | Invalid request |
| `analyzing` | `planning` | `analysis_complete` | Intent detected |
| `analyzing` | `failed` | `analysis_failed` | Cannot analyze |
| `planning` | `queued` | `planning_complete` | Decomposition done |
| `planning` | `failed` | `planning_failed` | Cannot decompose |
| `queued` | `scheduled` | `schedule_task` | Worker available |
| `queued` | `failed` | `queue_timeout` | Waited too long |
| `scheduled` | `assigned` | `assign_task` | Agent available |
| `scheduled` | `queued` | `unassign` | Agent unavailable |
| `assigned` | `running` | `start_execution` | Resources allocated |
| `assigned` | `queued` | `unassign` | Resources unavailable |
| `running` | `validating` | `execution_complete` | Task finished |
| `running` | `retrying` | `execution_failed` | Transient error |
| `running` | `failed` | `execution_failed` | Fatal error |
| `running` | `paused` | `pause_task` | User/system request |
| `running` | `cancelled` | `cancel_task` | User/system request |
| `paused` | `running` | `resume_task` | User/system request |
| `paused` | `cancelled` | `cancel_task` | User/system request |
| `validating` | `aggregating` | `validation_passed` | Result valid |
| `validating` | `retrying` | `validation_failed` | Result invalid |
| `aggregating` | `reviewing` | `aggregation_complete` | Results merged |
| `reviewing` | `completed` | `review_passed` | Quality check passed |
| `reviewing` | `retrying` | `review_failed` | Quality check failed |
| `retrying` | `queued` | `retry_task` | Retry allowed |
| `retrying` | `failed` | `max_retries_exceeded` | Retries exhausted |
| `completed` | `archived` | `archive_task` | Retention expired |
| `failed` | `archived` | `archive_task` | Retention expired |
| `cancelled` | `archived` | `archive_task` | Retention expired |

---

## 5. State Machine Implementation

### 5.1 State Machine Class

```python
class TaskStateMachine:
    """Formal state machine for task lifecycle."""
    
    STATES = {
        "created": ["analyzing", "failed"],
        "analyzing": ["planning", "failed"],
        "planning": ["queued", "failed"],
        "queued": ["scheduled", "failed"],
        "scheduled": ["assigned", "queued"],
        "assigned": ["running", "queued"],
        "running": ["validating", "retrying", "failed", "paused", "cancelled"],
        "paused": ["running", "cancelled"],
        "validating": ["aggregating", "retrying"],
        "aggregating": ["reviewing"],
        "reviewing": ["completed", "retrying"],
        "retrying": ["queued", "failed"],
        "completed": ["archived"],
        "failed": ["archived"],
        "cancelled": ["archived"],
        "archived": []
    }
    
    def __init__(self, task: Task):
        self.task = task
        self.history: list[StateTransition] = []
    
    def transition(self, to_state: str, trigger: str, **kwargs) -> bool:
        """Execute state transition if valid."""
        from_state = self.task.status
        
        # Validate transition
        if to_state not in self.STATES.get(from_state, []):
            raise InvalidTransitionError(
                f"Cannot transition from {from_state} to {to_state}"
            )
        
        # Execute transition
        self.task.status = to_state
        self.task.updated_at = now()
        
        # Record history
        self.history.append(StateTransition(
            from_state=from_state,
            to_state=to_state,
            trigger=trigger,
            timestamp=now(),
            metadata=kwargs
        ))
        
        # Execute side effects
        self.execute_side_effects(from_state, to_state, trigger)
        
        return True
    
    def execute_side_effects(self, from_state: str, to_state: str, trigger: str):
        """Execute side effects of state transition."""
        if to_state == "running":
            self.task.started_at = now()
        elif to_state in ["completed", "failed", "cancelled"]:
            self.task.completed_at = now()
        elif to_state == "retrying":
            self.task.retry_count += 1
```

### 5.2 State Transition Events

```python
class StateTransitionEvent:
    task_id: UUID
    from_state: str
    to_state: str
    trigger: str
    timestamp: datetime
    metadata: dict
    user_id: Optional[UUID]
    agent_id: Optional[str]
```

---

## 6. State Validation

### 6.1 Pre-Transition Checks

```python
def validate_transition(task: Task, to_state: str) -> ValidationResult:
    """Validate if transition is allowed."""
    
    # Check if transition is valid
    valid_transitions = TaskStateMachine.STATES.get(task.status, [])
    if to_state not in valid_transitions:
        return ValidationResult(
            valid=False,
            reason=f"Invalid transition: {task.status} → {to_state}"
        )
    
    # Check pre-conditions
    if to_state == "running":
        if not task.assigned_agent:
            return ValidationResult(
                valid=False,
                reason="No agent assigned"
            )
        if not task.allocated_resources:
            return ValidationResult(
                valid=False,
                reason="No resources allocated"
            )
    
    if to_state == "completed":
        if not task.result:
            return ValidationResult(
                valid=False,
                reason="No result to complete"
            )
    
    return ValidationResult(valid=True)
```

### 6.2 Post-Transition Actions

```python
def execute_post_transition(task: Task, to_state: str):
    """Execute actions after state transition."""
    
    actions = {
        "created": lambda t: log_task_created(t),
        "analyzing": lambda t: start_analysis(t),
        "planning": lambda t: start_planning(t),
        "queued": lambda t: enqueue_task(t),
        "scheduled": lambda t: schedule_task(t),
        "assigned": lambda t: assign_agent(t),
        "running": lambda t: start_execution(t),
        "paused": lambda t: pause_execution(t),
        "validating": lambda t: start_validation(t),
        "aggregating": lambda t: start_aggregation(t),
        "reviewing": lambda t: start_review(t),
        "completed": lambda t: complete_task(t),
        "failed": lambda t: handle_failure(t),
        "cancelled": lambda t: cancel_task(t),
        "retrying": lambda t: prepare_retry(t),
        "archived": lambda t: archive_task(t),
    }
    
    action = actions.get(to_state)
    if action:
        action(task)
```

---

## 7. State Monitoring

### 7.1 State Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Tasks in Created | Tasks not yet processed | < 10 |
| Tasks in Queue | Tasks waiting to run | < 100 |
| Tasks Running | Tasks currently executing | < 50 |
| Tasks Completed | Successfully finished tasks | Maximize |
| Tasks Failed | Failed tasks | < 5% |
| Tasks Retrying | Tasks being retried | < 10 |
| Average Time in Queue | Time waiting in queue | < 30s |
| Average Time Running | Time executing | < 5min |
| Average Time in Validation | Time validating | < 30s |

### 7.2 Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│                  TASK STATE DASHBOARD                             │
│                                                                  │
│  Current State Distribution:                                    │
│  Created:    ██ 2                                               │
│  Analyzing:  █ 1                                                │
│  Planning:   █ 1                                                │
│  Queued:     ████████████ 12                                    │
│  Scheduled:  ███ 3                                              │
│  Assigned:   ███ 3                                              │
│  Running:    ████████████████████████████ 28                    │
│  Paused:     █ 1                                                │
│  Validating: █████ 5                                            │
│  Aggregating:██ 2                                               │
│  Reviewing:  █ 1                                                │
│  Completed:  ████████████████████████████████████████ 42        │
│  Failed:     ██ 2                                               │
│  Retrying:   █ 1                                                │
│                                                                  │
│  State Transitions (last hour):                                 │
│  Total: 156                                                     │
│  Successful: 154 (98.7%)                                        │
│  Failed: 2 (1.3%)                                               │
│                                                                  │
│  Average Times:                                                 │
│  Queue wait: 12s                                                │
│  Execution: 45s                                                 │
│  Validation: 8s                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Configuration

```yaml
state_machine:
  # Valid transitions
  transitions:
    created: [analyzing, failed]
    analyzing: [planning, failed]
    planning: [queued, failed]
    queued: [scheduled, failed]
    scheduled: [assigned, queued]
    assigned: [running, queued]
    running: [validating, retrying, failed, paused, cancelled]
    paused: [running, cancelled]
    validating: [aggregating, retrying]
    aggregating: [reviewing]
    reviewing: [completed, retrying]
    retrying: [queued, failed]
    completed: [archived]
    failed: [archived]
    cancelled: [archived]
    archived: []
    
  # Timeouts
  timeouts:
    analyzing: 60s
    planning: 300s
    queued: 3600s
    scheduled: 300s
    assigned: 60s
    running: 3600s
    paused: 86400s
    validating: 120s
    aggregating: 60s
    reviewing: 120s
    retrying: 300s
    
  # Monitoring
  monitoring:
    enabled: true
    log_transitions: true
    metrics_interval: 15s
```
