# AIDA Workflow Lifecycle

**Document:** Book 2, Chapter 5 — Workflow Lifecycle
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Workflow Lifecycle defines the complete journey of a workflow from user request to final delivery. Every workflow passes through **12 stages**, each with specific inputs, processing logic, and outputs.

---

## 2. Lifecycle Stages

### 2.1 Complete Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        WORKFLOW LIFECYCLE                             │
│                                                                      │
│  1. Created                                                          │
│     ↓                                                                │
│  2. Validated                                                        │
│     ↓                                                                │
│  3. Planned                                                          │
│     ↓                                                                │
│  4. Scheduled                                                        │
│     ↓                                                                │
│  5. Running                                                          │
│     ↓                                                                │
│  6. Waiting (for dependency/approval)                                │
│     ↓                                                                │
│  7. Paused (by user/system)                                          │
│     ↓                                                                │
│  8. Resumed                                                          │
│     ↓                                                                │
│  9. Completed                                                        │
│     ↓                                                                │
│  10. Failed                                                          │
│     ↓                                                                │
│  11. Cancelled                                                       │
│     ↓                                                                │
│  12. Archived                                                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Stage Details

### 3.1 Stage 1 — Created

| Property | Value |
|----------|-------|
| Input | User request |
| Output | Workflow object |
| Duration | < 10ms |
| Failure | Reject request |

**Processing:**
```
1. Receive user request
2. Create workflow object
3. Set workflow_id (UUID)
4. Set status = "created"
5. Set created_at timestamp
6. Store in database
7. Log workflow creation
```

---

### 3.2 Stage 2 — Validated

| Property | Value |
|----------|-------|
| Input | Workflow object |
| Output | Validated workflow |
| Duration | < 100ms |
| Failure | Reject workflow |

**Processing:**
```
1. Validate request format
2. Check user permissions
3. Check resource availability
4. Validate against business rules
5. Check budget limits
6. Set status = "validated"
7. Log validation result
```

**Validation Rules:**
```yaml
validation:
  request:
    - required_fields: [user_id, request_type, content]
    - max_content_length: 100000
    
  permissions:
    - user_can_create_workflow: true
    - user_has_budget: true
    
  resources:
    - cpu_available: true
    - memory_available: true
    - gpu_available: true
    
  business_rules:
    - max_concurrent_workflows: 100
    - max_workflow_duration: 86400s
```

---

### 3.3 Stage 3 — Planned

| Property | Value |
|----------|-------|
| Input | Validated workflow |
| Output | Execution plan |
| Duration | 1-30s |
| Failure | Return error |

**Processing:**
```
1. Analyze user request
2. Determine workflow type
3. Decompose into steps
4. Identify dependencies
5. Assign agents and models
6. Estimate resources
7. Create execution plan
8. Set status = "planned"
9. Log plan creation
```

**Plan Output:**
```python
class WorkflowPlan:
    workflow_id: UUID
    workflow_type: str
    steps: list[Step]
    dependencies: list[Dependency]
    estimated_duration: int  # seconds
    estimated_cost: float
    estimated_resources: ResourcePlan
    parallel_groups: list[list[str]]
```

---

### 3.4 Stage 4 — Scheduled

| Property | Value |
|----------|-------|
| Input | Execution plan |
| Output | Scheduled workflow |
| Duration | < 1s |
| Failure | Queue for later |

**Processing:**
```
1. Check resource availability
2. Determine execution order
3. Schedule steps
4. Allocate resources
5. Set status = "scheduled"
6. Set scheduled_at timestamp
7. Log scheduling
```

---

### 3.5 Stage 5 — Running

| Property | Value |
|----------|-------|
| Input | Scheduled workflow |
| Output | Running workflow |
| Duration | Variable (1s — hours) |
| Failure | Trigger recovery |

**Processing:**
```
1. Start workflow execution
2. Execute steps (sequential/parallel)
3. Monitor progress
4. Handle decisions
5. Save checkpoints
6. Collect results
7. Update progress
8. Set status = "running"
9. Set started_at timestamp
```

---

### 3.6 Stage 6 — Waiting

| Property | Value |
|----------|-------|
| Input | Running workflow |
| Output | Waiting workflow |
| Duration | Variable |
| Failure | Timeout handling |

**Processing:**
```
1. Pause execution
2. Wait for trigger:
   - Dependency completion
   - Human approval
   - External event
   - Scheduled time
3. Set status = "waiting"
4. Set waiting_reason
5. Log waiting
```

---

### 3.7 Stage 7 — Paused

| Property | Value |
|----------|-------|
| Input | Running/waiting workflow |
| Output | Paused workflow |
| Duration | Variable |
| Failure | N/A |

**Processing:**
```
1. Pause execution
2. Save current state
3. Release resources (optional)
4. Set status = "paused"
5. Set paused_at timestamp
6. Log pause
```

---

### 3.8 Stage 8 — Resumed

| Property | Value |
|----------|-------|
| Input | Paused workflow |
| Output | Running workflow |
| Duration | < 1s |
| Failure | N/A |

**Processing:**
```
1. Restore state from checkpoint
2. Reallocate resources
3. Resume execution
4. Set status = "running"
5. Set resumed_at timestamp
6. Log resume
```

---

### 3.9 Stage 9 — Completed

| Property | Value |
|----------|-------|
| Input | Running workflow |
| Output | Completed workflow |
| Duration | < 1s |
| Failure | N/A |

**Processing:**
```
1. Validate all steps completed
2. Aggregate results
3. Generate final response
4. Release all resources
5. Set status = "completed"
6. Set completed_at timestamp
7. Calculate metrics
8. Log completion
```

---

### 3.10 Stage 10 — Failed

| Property | Value |
|----------|-------|
| Input | Running workflow |
| Output | Failed workflow |
| Duration | < 1s |
| Failure | N/A |

**Processing:**
```
1. Stop execution
2. Collect error information
3. Attempt recovery (if configured)
4. If recovery fails:
   - Rollback changes
   - Release resources
   - Set status = "failed"
   - Set failed_at timestamp
   - Set error information
5. Log failure
6. Alert operator (if configured)
```

---

### 3.11 Stage 11 — Cancelled

| Property | Value |
|----------|-------|
| Input | Any active state |
| Output | Cancelled workflow |
| Duration | < 1s |
| Failure | N/A |

**Processing:**
```
1. Stop execution
2. Rollback changes (if configured)
3. Release resources
4. Set status = "cancelled"
5. Set cancelled_at timestamp
6. Set cancelled_by
7. Log cancellation
```

---

### 3.12 Stage 12 — Archived

| Property | Value |
|----------|-------|
| Input | Terminal state |
| Output | Archived workflow |
| Duration | < 1s |
| Failure | N/A |

**Processing:**
```
1. Move to archive storage
2. Compress data
3. Set status = "archived"
4. Set archived_at timestamp
5. Log archival
```

---

## 4. State Diagram

```
                                    ┌─────────────────────────────────┐
                                    │                                 │
                                    ↓                                 │
┌─────────┐   validate  ┌──────────┐   plan   ┌──────────┐          │
│ created │────────────→│validated │─────────→│ planned  │          │
└─────────┘             └──────────┘          └────┬────┘          │
     │                                              │ schedule      │
     │ invalid                                      ↓               │
     ↓                                         ┌──────────┐          │
┌─────────┐                                   │scheduled │          │
│ rejected│                                   └────┬────┘          │
└─────────┘                                        │ start          │
                                                   ↓               │
                                              ┌──────────┐         │
                              ┌──────────────→│ running  │←────┐   │
                              │               └────┬────┘     │   │
                              │                    │          │   │
                              │           ┌────────┼────────┐ │   │
                              │           ↓        ↓        ↓ │   │
                              │      ┌────────┐ ┌────────┐ ┌────────┐
                              │      │waiting │ │paused  │ │ failed │
                              │      └────┬───┘ └────┬───┘ └────────┘
                              │           │          │
                              │           │ resume   │
                              │           └──────────┘
                              │
                         ┌──────────┐
                         │completed │
                         └──────────┘
```

---

## 5. Timing Summary

| Stage | Min | Average | Max |
|-------|-----|---------|-----|
| 1. Created | 1ms | 5ms | 10ms |
| 2. Validated | 10ms | 50ms | 100ms |
| 3. Planned | 1s | 5s | 30s |
| 4. Scheduled | 100ms | 500ms | 1s |
| 5. Running | 1s | 300s | 86400s |
| 6. Waiting | 1s | 60s | 86400s |
| 7. Paused | 1s | 1s | 1s |
| 8. Resumed | 100ms | 500ms | 1s |
| 9. Completed | 100ms | 500ms | 1s |
| 10. Failed | 100ms | 500ms | 1s |
| 11. Cancelled | 100ms | 500ms | 1s |
| 12. Archived | 100ms | 1s | 5s |

---

## 6. Configuration

```yaml
workflow_lifecycle:
  # Validation
  validation:
    enabled: true
    strict_mode: false
    
  # Planning
  planning:
    ai_planning: true
    max_steps: 50
    planning_timeout: 60s
    
  # Scheduling
  scheduling:
    auto_schedule: true
    max_queue_size: 1000
    
  # Execution
  execution:
    max_concurrent: 10
    step_timeout: 3600s
    workflow_timeout: 86400s
    
  # Waiting
  waiting:
    max_wait_time: 86400s
    timeout_action: fail
    
  # Archival
  archival:
    enabled: true
    retention:
      completed: 30d
      failed: 90d
      cancelled: 30d
```
