# AIDA Checkpoint System

**Document:** Book 2, Chapter 5 — Checkpoint System
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Checkpoint System saves workflow state at regular intervals, enabling pause, resume, and rollback. It ensures long-running workflows can survive failures and continue from the last saved state.

---

## 2. Checkpoint Architecture

### 2.1 Layer Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CHECKPOINT SYSTEM                                  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Checkpoint Manager                         │   │
│  │  - Create checkpoints                                         │   │
│  │  - Restore checkpoints                                        │   │
│  │  - Manage checkpoint lifecycle                                │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│     ↓                       │                                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Checkpoint Storage                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │  Redis   │  │PostgreSQL│  │   S3     │  │  Local   │    │   │
│  │  │ (Active) │  │(Durable) │  │ (Backup) │  │  (Temp)  │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Checkpoint Types                           │   │
│  │  - Manual Checkpoint                                          │   │
│  │  - Auto Checkpoint                                            │   │
│  │  - Milestone Checkpoint                                       │   │
│  │  - Recovery Checkpoint                                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Checkpoint Types

### 3.1 Type Definitions

| Type | Trigger | Frequency | Purpose |
|------|---------|-----------|---------|
| `manual` | User request | On demand | User-initiated save |
| `auto` | Time-based | 60s | Regular state save |
| `milestone` | Step completion | Per milestone | Key progress save |
| `recovery` | Error/failure | On error | Recovery point |
| `pre_step` | Before step | Per step | Rollback point |
| `post_step` | After step | Per step | Progress save |

---

## 4. Checkpoint Data

### 4.1 Checkpoint Object

```python
class Checkpoint:
    checkpoint_id: UUID
    workflow_id: UUID
    
    # Type
    checkpoint_type: str  # manual, auto, milestone, recovery, pre_step, post_step
    
    # State
    workflow_state: dict
    step_states: dict[str, StepState]
    context: dict
    
    # Results
    completed_steps: list[str]
    step_results: dict[str, StepResult]
    
    # Metadata
    created_at: datetime
    step_id: Optional[str]  # Current step
    progress: float  # 0.0 - 1.0
    
    # Size
    size_bytes: int
    compressed: bool
```

### 4.2 Checkpoint Data Structure

```python
class CheckpointData:
    # Workflow state
    workflow_status: str
    workflow_started_at: datetime
    workflow_context: dict
    
    # Step states
    step_statuses: dict[str, str]
    step_results: dict[str, Any]
    step_errors: dict[str, str]
    
    # Resources
    allocated_resources: ResourceAllocation
    resource_usage: ResourceUsage
    
    # Decisions
    decisions_made: list[Decision]
    decision_context: dict
    
    # Variables
    variables: dict[str, Any]
    
    # Metadata
    version: str
    checksum: str
```

---

## 5. Checkpoint Operations

### 5.1 Create Checkpoint

```python
class CheckpointManager:
    async def create_checkpoint(
        self,
        workflow: Workflow,
        checkpoint_type: str,
        step_id: Optional[str] = None
    ) -> Checkpoint:
        """Create a new checkpoint."""
        
        # Serialize workflow state
        state = self.serialize_state(workflow)
        
        # Calculate checksum
        checksum = self.calculate_checksum(state)
        
        # Create checkpoint
        checkpoint = Checkpoint(
            checkpoint_id=uuid4(),
            workflow_id=workflow.id,
            checkpoint_type=checkpoint_type,
            workflow_state=state,
            step_states=self.get_step_states(workflow),
            context=workflow.context,
            completed_steps=workflow.completed_steps,
            step_results=workflow.step_results,
            created_at=datetime.utcnow(),
            step_id=step_id,
            progress=workflow.progress,
            size_bytes=len(state),
            compressed=False
        )
        
        # Store checkpoint
        await self.store.save(checkpoint)
        
        # Log checkpoint creation
        logger.info("checkpoint_created",
            checkpoint_id=checkpoint.checkpoint_id,
            workflow_id=workflow.id,
            type=checkpoint_type
        )
        
        return checkpoint
```

### 5.2 Restore Checkpoint

```python
async def restore_checkpoint(self, checkpoint_id: UUID) -> Workflow:
    """Restore workflow from checkpoint."""
    
    # Load checkpoint
    checkpoint = await self.store.get(checkpoint_id)
    if not checkpoint:
        raise CheckpointNotFoundError(checkpoint_id)
    
    # Deserialize state
    state = self.deserialize_state(checkpoint.workflow_state)
    
    # Restore workflow
    workflow = Workflow.from_checkpoint(state)
    
    # Restore step states
    for step_id, step_state in checkpoint.step_states.items():
        workflow.set_step_state(step_id, step_state)
    
    # Restore context
    workflow.context = checkpoint.context
    
    # Restore results
    workflow.completed_steps = checkpoint.completed_steps
    workflow.step_results = checkpoint.step_results
    
    # Log restoration
    logger.info("checkpoint_restored",
        checkpoint_id=checkpoint_id,
        workflow_id=workflow.id
    )
    
    return workflow
```

### 5.3 Delete Checkpoint

```python
async def delete_checkpoint(self, checkpoint_id: UUID) -> bool:
    """Delete a checkpoint."""
    
    # Check if checkpoint exists
    checkpoint = await self.store.get(checkpoint_id)
    if not checkpoint:
        return False
    
    # Delete from storage
    await self.store.delete(checkpoint_id)
    
    # Log deletion
    logger.info("checkpoint_deleted", checkpoint_id=checkpoint_id)
    
    return True
```

---

## 6. Checkpoint Triggers

### 6.1 Auto-Checkpoint Rules

```yaml
auto_checkpoint:
  enabled: true
  
  # Time-based
  time_interval: 60s
  
  # Step-based
  before_each_step: true
  after_each_step: true
  
  # Progress-based
  on_progress_milestone: [0.25, 0.5, 0.75]
  
  # Error-based
  on_error: true
  
  # State-based
  on_state_change: true
```

### 6.2 Checkpoint Policy

```yaml
checkpoint_policy:
  # Maximum checkpoints per workflow
  max_checkpoints: 100
  
  # Checkpoint retention
  retention:
    active: 24h
    completed: 7d
    failed: 30d
    
  # Compression
  compression:
    enabled: true
    threshold: 10KB
    algorithm: gzip
    
  # Backup
  backup:
    enabled: true
    to_s3: true
    interval: 3600s
```

---

## 7. Rollback

### 7.1 Rollback Process

```
Rollback Triggered
    │
    ├── Find latest checkpoint
    │
    ├── Validate checkpoint integrity
    │
    ├── Restore workflow state
    │
    ├── Restore step states
    │
    ├── Restore context
    │
    ├── Resume execution
    │
    └── Log rollback event
```

### 7.2 Rollback Configuration

```yaml
rollback:
  enabled: true
  
  # Auto-rollback on failure
  auto_rollback: true
  
  # Maximum rollback attempts
  max_attempts: 3
  
  # Rollback timeout
  timeout: 60s
  
  # Rollback strategy
  strategy: latest_checkpoint  # latest_checkpoint | specific_checkpoint | step_back
```

---

## 8. Configuration

```yaml
checkpoint:
  # Manager
  manager:
    enabled: true
    
  # Storage
  storage:
    primary: redis
    backup: postgresql
    s3_backup: false
    
  # Auto-checkpoint
  auto_checkpoint:
    enabled: true
    interval: 60s
    before_step: true
    after_step: true
    
  # Retention
  retention:
    active: 24h
    completed: 7d
    failed: 30d
    
  # Compression
  compression:
    enabled: true
    algorithm: gzip
    
  # Rollback
  rollback:
    enabled: true
    auto_rollback: true
    max_attempts: 3
    
  # Monitoring
  monitoring:
    enabled: true
    log_checkpoints: true
```
