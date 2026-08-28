# AIDA Workflow State Machine

**Document:** Book 2, Chapter 5 — Workflow State Machine
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Workflow State Machine defines all possible states a workflow can be in, the transitions between states, and the rules governing those transitions.

---

## 2. State Definitions

### 2.1 All States

| State | Description | Terminal |
|-------|-------------|----------|
| `created` | Workflow created, not yet validated | No |
| `validated` | Workflow validated, ready for planning | No |
| `planned` | Execution plan created | No |
| `scheduled` | Workflow scheduled for execution | No |
| `running` | Workflow currently executing | No |
| `waiting` | Waiting for dependency/approval/event | No |
| `paused` | Workflow paused by user/system | No |
| `completed` | Workflow successfully finished | Yes |
| `failed` | Workflow failed | Yes |
| `cancelled` | Workflow cancelled by user/system | Yes |
| `archived` | Workflow archived for history | Yes |

---

## 3. State Diagram

```
                              ┌──────────────────────────────────────────────────┐
                              │                                                  │
                              │                                                  │
                              ↓                                                  │
┌─────────┐   validate  ┌──────────┐   plan   ┌──────────┐   schedule  ┌──────────┐
│ created │────────────→│validated │─────────→│ planned  │────────────→│scheduled │
└─────────┘             └──────────┘          └──────────┘             └────┬────┘
     │                                                       │              │
     │ invalid                                               │ fail         │ start
     ↓                                                       ↓              ↓
┌─────────┐                                            ┌──────────┐  ┌──────────┐
│ failed  │←────────────────────────────────────────────│ failed   │  │ running  │
└─────────┘                                            └──────────┘  └────┬────┘
                                                                          │
                                                         ┌────────────────┼────────────────┐
                                                         │                │                │
                                                         ↓                ↓                ↓
                                                   ┌──────────┐   ┌──────────┐   ┌──────────┐
                                                   │ waiting  │   │ paused   │   │ failed   │
                                                   └────┬─────┘   └────┬─────┘   └──────────┘
                                                        │              │
                                                        │ ready        │ resume
                                                        │              │
                                                        └──────────────┘
                                                         │
                                                         ↓
                                                   ┌──────────┐
                                                   │ completed│
                                                   └──────────┘
```

---

## 4. State Transitions

### 4.1 Transition Table

| From State | To State | Trigger | Condition |
|------------|----------|---------|-----------|
| `created` | `validated` | `validate` | Validation passes |
| `created` | `failed` | `validate` | Validation fails |
| `validated` | `planned` | `plan` | Planning completes |
| `validated` | `failed` | `plan` | Planning fails |
| `planned` | `scheduled` | `schedule` | Resources available |
| `planned` | `failed` | `schedule` | Resources unavailable |
| `scheduled` | `running` | `start` | Executor ready |
| `scheduled` | `failed` | `start` | Executor fails |
| `running` | `completed` | `complete` | All steps done |
| `running` | `failed` | `fail` | Unrecoverable error |
| `running` | `waiting` | `wait` | Dependency/approval |
| `running` | `paused` | `pause` | User/system request |
| `waiting` | `running` | `ready` | Dependency ready |
| `waiting` | `failed` | `timeout` | Wait timeout |
| `paused` | `running` | `resume` | User/system request |
| `paused` | `cancelled` | `cancel` | User/system request |
| `running` | `cancelled` | `cancel` | User/system request |
| `waiting` | `cancelled` | `cancel` | User/system request |
| `completed` | `archived` | `archive` | Retention expired |
| `failed` | `archived` | `archive` | Retention expired |
| `cancelled` | `archived` | `archive` | Retention expired |

### 4.2 Transition Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STATE TRANSITION MAP                               │
│                                                                      │
│  created ──→ validated ──→ planned ──→ scheduled ──→ running        │
│     │            │            │            │            │            │
│     │ fail       │ fail       │ fail       │ fail       │            │
│     ↓            ↓            ↓            ↓            │            │
│  failed ←───────────────────────────────────────────────┘            │
│                                                                      │
│  running ──→ completed                                              │
│     │                                                                │
│     ├──→ waiting ──→ running                                        │
│     │       │                                                       │
│     │       └──→ failed (timeout)                                   │
│     │                                                                │
│     ├──→ paused ──→ running                                         │
│     │       │                                                       │
│     │       └──→ cancelled                                          │
│     │                                                                │
│     ├──→ failed                                                     │
│     │                                                                │
│     └──→ cancelled                                                  │
│                                                                      │
│  completed ──→ archived                                             │
│  failed ──→ archived                                                │
│  cancelled ──→ archived                                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. State Machine Implementation

### 5.1 State Machine Class

```python
class WorkflowStateMachine:
    """Formal state machine for workflow lifecycle."""
    
    STATES = {
        "created": ["validated", "failed"],
        "validated": ["planned", "failed"],
        "planned": ["scheduled", "failed"],
        "scheduled": ["running", "failed"],
        "running": ["completed", "failed", "waiting", "paused", "cancelled"],
        "waiting": ["running", "failed", "cancelled"],
        "paused": ["running", "cancelled"],
        "completed": ["archived"],
        "failed": ["archived"],
        "cancelled": ["archived"],
        "archived": []
    }
    
    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        self.history: list[StateTransition] = []
    
    def transition(self, to_state: str, trigger: str, **kwargs) -> bool:
        """Execute state transition if valid."""
        from_state = self.workflow.status
        
        # Validate transition
        if to_state not in self.STATES.get(from_state, []):
            raise InvalidTransitionError(
                f"Cannot transition from {from_state} to {to_state}"
            )
        
        # Execute transition
        self.workflow.status = to_state
        self.workflow.updated_at = now()
        
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
            self.workflow.started_at = now()
        elif to_state in ["completed", "failed", "cancelled"]:
            self.workflow.completed_at = now()
        elif to_state == "waiting":
            self.workflow.waiting_since = now()
        elif to_state == "paused":
            self.workflow.paused_since = now()
```

---

## 6. Step State Machine

### 6.1 Step States

| State | Description | Terminal |
|-------|-------------|----------|
| `pending` | Step not yet started | No |
| `ready` | Step ready to execute | No |
| `running` | Step currently executing | No |
| `waiting` | Step waiting for dependency | No |
| `completed` | Step successfully finished | Yes |
| `failed` | Step failed | Yes |
| `skipped` | Step skipped (condition false) | Yes |
| `cancelled` | Step cancelled | Yes |

### 6.2 Step Transitions

| From | To | Trigger |
|------|-----|---------|
| `pending` | `ready` | Dependencies met |
| `ready` | `running` | Executor picks up |
| `running` | `completed` | Execution succeeds |
| `running` | `failed` | Execution fails |
| `running` | `waiting` | Waiting for approval |
| `waiting` | `running` | Approval received |
| `pending` | `skipped` | Condition false |
| `running` | `cancelled` | Cancel requested |
| `ready` | `cancelled` | Cancel requested |

---

## 7. Configuration

```yaml
state_machine:
  # Valid transitions
  transitions:
    created: [validated, failed]
    validated: [planned, failed]
    planned: [scheduled, failed]
    scheduled: [running, failed]
    running: [completed, failed, waiting, paused, cancelled]
    waiting: [running, failed, cancelled]
    paused: [running, cancelled]
    completed: [archived]
    failed: [archived]
    cancelled: [archived]
    archived: []
    
  # Timeouts
  timeouts:
    created: 3600s
    validated: 3600s
    planned: 86400s
    scheduled: 3600s
    running: 86400s
    waiting: 86400s
    paused: 604800s
    
  # Monitoring
  monitoring:
    enabled: true
    log_transitions: true
    metrics_interval: 15s
```
