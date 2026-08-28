# AIDA Workflow Recovery Strategy

**Document:** Book 2, Chapter 5 — Recovery Strategy
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Recovery Strategy handles workflow failures through automatic retry, rollback, alternative strategies, and human intervention. It ensures maximum workflow completion rate while maintaining system stability.

---

## 2. Recovery Strategies

### 2.1 Strategy Overview

| Strategy | When | Description |
|----------|------|-------------|
| `retry_step` | Transient failure | Retry the failed step |
| `retry_workflow` | Transient failure | Retry entire workflow from checkpoint |
| `alternative_agent` | Agent unavailable | Use different agent |
| `alternative_model` | Model unavailable | Use different model |
| `alternative_tool` | Tool unavailable | Use different tool |
| `alternative_approach` | Logic failure | Different strategy |
| `rollback` | Wrong direction | Revert to checkpoint |
| `skip_step` | Non-critical step | Skip and continue |
| `human_approval` | Unknown failure | Ask human for help |
| `degrade` | Resource exhaustion | Reduce quality |

---

## 3. Step-Level Recovery

### 3.1 Step Recovery Flow

```
Step Failed
    │
    ├── Is failure transient?
    │   ├── YES → Retry count < max?
    │   │         ├── YES → Wait delay → Retry step
    │   │         └── NO → Continue to next strategy
    │   └── NO → Continue to next strategy
    │
    ├── Try alternative agent?
    │   ├── YES → Execute with alternative
    │   │         ├── Success → Continue
    │   │         └── Failure → Continue
    │   └── NO → Continue
    │
    ├── Try alternative model?
    │   ├── YES → Execute with alternative
    │   │         ├── Success → Continue
    │   │         └── Failure → Continue
    │   └── NO → Continue
    │
    ├── Try alternative approach?
    │   ├── YES → Execute with different strategy
    │   │         ├── Success → Continue
    │   │         └── Failure → Continue
    │   └── NO → Continue
    │
    ├── Is step critical?
    │   ├── YES → Request human approval
    │   └── NO → Skip step → Continue
    │
    └── Mark workflow as FAILED
```

### 3.2 Step Retry Configuration

```yaml
step_retry:
  max_retries: 3
  base_delay: 10s
  multiplier: 2.0
  jitter: true
  
  retryable_errors:
    - TimeoutError
    - ConnectionError
    - RateLimitError
    - ServiceUnavailableError
    
  non_retryable_errors:
    - ValidationError
    - AuthenticationError
    - PermissionDeniedError
```

---

## 4. Workflow-Level Recovery

### 4.1 Workflow Recovery Flow

```
Workflow Failed
    │
    ├── Has checkpoint?
    │   ├── YES → Rollback to checkpoint
    │   │         ├── Success → Resume execution
    │   │         └── Failure → Continue
    │   └── NO → Continue
    │
    ├── Can retry from start?
    │   ├── YES → Retry workflow
    │   │         ├── Success → Continue
    │   │         └── Failure → Continue
    │   └── NO → Continue
    │
    ├── Can degrade?
    │   ├── YES → Reduce quality/requirements
    │   │         ├── Success → Continue
    │   │         └── Failure → Continue
    │   └── NO → Continue
    │
    └── Request human intervention
```

### 4.2 Workflow Retry Configuration

```yaml
workflow_retry:
  max_retries: 2
  retry_from: checkpoint  # checkpoint | start
  
  retry_conditions:
    - step_failures >= 3
    - critical_step_failed
    - timeout_exceeded
    
  no_retry_conditions:
    - user_cancelled
    - budget_exceeded
    - manual_failure
```

---

## 5. Rollback Strategy

### 5.1 Rollback Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| `step` | Rollback single step | Step produced wrong output |
| `checkpoint` | Rollback to checkpoint | Multiple steps failed |
| `workflow` | Rollback entire workflow | Complete failure |

### 5.2 Rollback Process

```
Rollback Triggered
    │
    ├── Determine rollback level
    │
    ├── Find rollback target
    │   ├── Step-level: Previous step state
    │   ├── Checkpoint-level: Latest checkpoint
    │   └── Workflow-level: Initial state
    │
    ├── Execute rollback
    │   ├── Restore state
    │   ├── Undo changes (if possible)
    │   └── Release resources
    │
    ├── Verify rollback
    │   ├── Validate state
    │   └── Check consistency
    │
    └── Resume or complete
```

### 5.3 Rollback Configuration

```yaml
rollback:
  enabled: true
  
  levels:
    step:
      enabled: true
      auto: false
      
    checkpoint:
      enabled: true
      auto: true
      
    workflow:
      enabled: true
      auto: false
      
  # Undo changes
  undo_changes:
    enabled: true
    methods:
      - git_revert
      - database_rollback
      - file_restore
      
  # Verification
  verify:
    enabled: true
    validate_state: true
    check_consistency: true
```

---

## 6. Alternative Strategy

### 6.1 Alternative Agent

```yaml
alternative_agents:
  code_agent:
    primary: code_agent
    fallback: planner_agent
    
  test_agent:
    primary: test_agent
    fallback: code_agent
    
  security_agent:
    primary: security_agent
    fallback: code_agent
```

### 6.2 Alternative Model

```yaml
alternative_models:
  pro:
    primary: pro
    fallback: flash
    
  flash:
    primary: flash
    fallback: low
    
  low:
    primary: low
    fallback: flash
```

### 6.3 Alternative Approach

```yaml
alternative_approaches:
  code_generation:
    - approach: direct
    - approach: step_by_step
    - approach: simplified
    
  testing:
    - approach: unit_tests
    - approach: integration_tests
    - approach: manual_testing
```

---

## 7. Human Intervention

### 7.1 Human Intervention Triggers

| Trigger | Description | Action |
|---------|-------------|--------|
| `max_retries_exceeded` | All retries failed | Ask human |
| `unknown_error` | Unexpected error | Ask human |
| `critical_step_failed` | Critical step failed | Ask human |
| `budget_exceeded` | Cost too high | Ask human |
| `quality_below_threshold` | Quality too low | Ask human |

### 7.2 Human Intervention Process

```
Human Intervention Required
    │
    ├── Pause workflow
    │
    ├── Collect diagnostic information
    │   ├── Error details
    │   ├── Execution history
    │   ├── Current state
    │   └── Suggested actions
    │
    ├── Notify human
    │   ├── Send notification
    │   ├── Provide context
    │   └── Suggest options
    │
    ├── Wait for human response
    │   ├── Retry with changes
    │   ├── Skip step
    │   ├── Modify plan
    │   ├── Cancel workflow
    │   └── Timeout → use default
    │
    └── Execute human decision
```

---

## 8. Configuration

```yaml
recovery:
  # Step recovery
  step:
    max_retries: 3
    base_delay: 10s
    multiplier: 2.0
    
  # Workflow recovery
  workflow:
    max_retries: 2
    retry_from: checkpoint
    
  # Rollback
  rollback:
    enabled: true
    auto_rollback: true
    
  # Alternatives
  alternatives:
    enabled: true
    try_agents: true
    try_models: true
    try_approaches: true
    
  # Human intervention
  human:
    enabled: true
    timeout: 3600s
    default_action: skip
    
  # Monitoring
  monitoring:
    enabled: true
    log_recovery: true
```
