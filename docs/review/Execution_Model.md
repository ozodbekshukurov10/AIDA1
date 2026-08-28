# AIDA Execution Model

**Document:** Book 2, Chapter 2 — Execution Model
**Version:** 1.0.0
**Date:** 2026-07-04

---

## Overview

The Execution Model defines how tasks are executed within the Runtime Engine. It supports **8 execution types**, each optimized for different workload characteristics.

---

## 1. Execution Types

### 1.1 Synchronous Execution

```
Client → Submit Task → Wait → Receive Result → Return
```

| Property | Value |
|----------|-------|
| Blocking | Yes |
| Timeout | 30s default |
| Use case | Simple queries, quick responses |
| Worker allocation | Dedicated until complete |

**Flow:**
```
1. Client sends request
2. Task submitted to queue
3. Worker picks up task
4. Worker executes task
5. Worker returns result
6. Result sent to client
7. Worker freed
```

### 1.2 Asynchronous Execution

```
Client → Submit Task → Receive TaskID → (Background) → Poll/Callback → Receive Result
```

| Property | Value |
|----------|-------|
| Blocking | No |
| Timeout | 300s default |
| Use case | Long-running tasks, complex analysis |
| Worker allocation | Released after submission |

**Flow:**
```
1. Client sends request
2. Task submitted to queue
3. Client receives task_id immediately
4. Worker picks up task (when available)
5. Worker executes task
6. Result stored in StateManager
7. Client polls or receives webhook callback
```

### 1.3 Background Execution

```
Client → Submit Task → Receive Ack → (Fire and Forget)
```

| Property | Value |
|----------|-------|
| Blocking | No |
| Timeout | 3600s default |
| Use case | Batch processing, reports, cleanup |
| Worker allocation | Minimal priority |

**Flow:**
```
1. Client sends request
2. Task submitted to background queue
3. Client receives immediate ACK
4. Scheduler assigns to background worker
5. Worker executes when resources available
6. Result stored (client can retrieve later)
7. No notification (unless configured)
```

### 1.4 Streaming Execution

```
Client → Submit Task → Receive Stream of Chunks → Stream Ends
```

| Property | Value |
|----------|-------|
| Blocking | Semi-blocking (stream) |
| Timeout | 300s default |
| Use case | LLM responses, real-time output |
| Worker allocation | Dedicated until stream ends |

**Flow:**
```
1. Client sends request
2. Task submitted to streaming queue
3. Worker picks up task
4. Worker begins execution
5. Worker yields chunks as they're produced
6. Chunks sent to client via SSE/WebSocket
7. Stream ends when task completes
8. Worker freed
```

### 1.5 Parallel Execution

```
Client → Submit Task → Split into Subtasks → Execute in Parallel → Merge Results → Return
```

| Property | Value |
|----------|-------|
| Blocking | Semi-blocking |
| Timeout | 120s per subtask |
| Use case | Independent subtasks, multi-perspective analysis |
| Worker allocation | Multiple workers simultaneously |

**Flow:**
```
1. Client submits complex task
2. Planner decomposes into N subtasks
3. Each subtask assigned to separate worker
4. Workers execute in parallel
5. Results collected as they complete
6. Results merged/aggregated
7. Final result sent to client
```

### 1.6 Distributed Execution

```
Client → Submit Task → Distributed across Nodes → Execute → Aggregate → Return
```

| Property | Value |
|----------|-------|
| Blocking | No |
| Timeout | 600s default |
| Use case | Large-scale analysis, multi-repo processing |
| Worker allocation | Multiple machines |

**Flow:**
```
1. Client submits task
2. Task split into distributed chunks
3. Chunks assigned to workers on different nodes
4. Workers execute independently
5. Partial results sent to aggregator
6. Aggregator assembles final result
7. Result sent to client
```

### 1.7 Scheduled Execution

```
Scheduler → Trigger → Execute Task → Store Result
```

| Property | Value |
|----------|-------|
| Blocking | No |
| Timeout | Configurable per schedule |
| Use case | Periodic monitoring, daily reports, cleanup |
| Worker allocation | On schedule |

**Schedule Types:**
```yaml
schedules:
  daily_report:
    cron: "0 9 * * *"  # 9 AM daily
    task: generate_daily_report
    
  health_check:
    cron: "*/5 * * * *"  # Every 5 minutes
    task: system_health_check
    
  cleanup:
    cron: "0 2 * * 0"  # 2 AM Sunday
    task: cleanup_expired_data
    
  model_refresh:
    interval: 3600  # Every hour
    task: refresh_model_health
```

### 1.8 Recursive Execution

```
Task → Execute → Produces New Tasks → Execute New Tasks → ... → Final Result
```

| Property | Value |
|----------|-------|
| Blocking | Semi-blocking |
| Timeout | Per level, max depth |
| Use case | Agent collaboration, multi-step reasoning |
| Worker allocation | Dynamic per level |

**Flow:**
```
1. Task executes and produces subtasks
2. Subtasks queued for execution
3. Each subtask may produce more subtasks
4. Recursion continues until:
   - Max depth reached
   - No more subtasks
   - Timeout
5. Results aggregated bottom-up
```

---

## 2. Execution Context

Every task execution receives a rich context:

```python
class ExecutionContext:
    # Task info
    task_id: UUID
    task_type: str
    priority: int
    
    # User context
    user_id: str
    user_tier: str
    session_id: str
    
    # Resource context
    allocated_cpu: float
    allocated_memory_mb: int
    allocated_gpu: Optional[GpuAllocation]
    timeout: int
    
    # Sandbox context
    sandbox_id: Optional[str]
    workspace_path: Optional[str]
    
    # State context
    checkpoint: Optional[Checkpoint]
    previous_results: list[TaskResult]
    
    # Configuration
    model_config: dict
    agent_config: dict
    tool_config: dict
```

---

## 3. Execution Pipeline

### 3.1 Pre-Execution

```
1. Validate task (schema, permissions, rate limits)
2. Check resource availability
3. Select worker type
4. Allocate resources
5. Create/assign sandbox
6. Load checkpoint (if resuming)
7. Prepare execution environment
```

### 3.2 Execution

```
1. Send task to worker
2. Worker initializes environment
3. Worker loads task code/config
4. Worker executes with timeout
5. Worker monitors resource usage
6. Worker yields results (if streaming)
7. Worker captures logs
```

### 3.3 Post-Execution

```
1. Validate result (schema, completeness)
2. Apply content filters
3. Store result in StateManager
4. Release resources
5. Destroy sandbox (if auto-destroy)
6. Update metrics
7. Notify completion (if async)
8. Trigger next step (if workflow)
```

---

## 4. Execution Constraints

### 4.1 Timeout Rules

```yaml
timeouts:
  per_task:
    sync: 30s
    async: 300s
    background: 3600s
    streaming: 300s
    distributed: 600s
    
  per_step:
    default: 60s
    code_generation: 120s
    repository_analysis: 600s
    llm_inference: 60s
    web_scraping: 120s
    
  per_workflow:
    simple: 300s
    complex: 1800s
    background: 7200s
```

### 4.2 Resource Limits

```yaml
resource_limits:
  per_task:
    max_cpu: 4.0
    max_memory: 8GB
    max_gpu_vram: 8GB
    max_disk: 10GB
    max_network: 100MB/s
    max_duration: 3600s
    
  per_worker:
    max_concurrent_tasks: 10
    max_memory: 16GB
    max_cpu: 8.0
    
  per_user:
    max_concurrent_tasks: 5
    max_daily_tasks: 1000
    max_daily_tokens: 1000000
```

### 4.3 Concurrency Limits

```yaml
concurrency:
  global:
    max_concurrent_tasks: 1000
    max_concurrent_workflows: 100
    max_concurrent_streaming: 50
    
  per_worker:
    general: 10
    code: 5
    ai: 3
    terminal: 10
    sandbox: 1
    
  per_user:
    free: 2
    premium: 5
    enterprise: 20
```

---

## 5. Execution Monitoring

### 5.1 Per-Task Metrics

```python
class TaskMetrics:
    task_id: UUID
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: int
    
    # Resource usage
    cpu_time_ms: int
    memory_peak_mb: int
    gpu_time_ms: int
    disk_read_mb: float
    disk_write_mb: float
    network_sent_mb: float
    network_received_mb: float
    
    # Execution details
    worker_id: str
    worker_type: str
    sandbox_id: Optional[str]
    model_used: Optional[str]
    tokens_used: Optional[int]
    
    # Quality
    success: bool
    retry_count: int
    error_message: Optional[str]
```

### 5.2 Real-time Monitoring Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│                    RUNTIME DASHBOARD                          │
│                                                              │
│  Tasks: ████░░░░░░ 45/100 running                           │
│  Queue: ███░░░░░░░ 1,234 pending                            │
│  Workers: ████████░ 18/20 active                            │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ CPU: 45% │ │ RAM: 62% │ │ GPU: 30% │ │Disk: 25% │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│                                                              │
│  Recent Tasks:                                               │
│  ✓ task_001  CodeGen    2.3s   deepseek-coder              │
│  ✓ task_002  Research   5.1s   gemini-pro                  │
│  ⏳ task_003  Planning   3.2s   (running)                   │
│  ✗ task_004  Debug      1.0s   TIMEOUT (retrying)          │
│  ✓ task_005  Chat       0.8s   qwen2.5                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Execution Events

| Event | Publisher | Subscribers |
|-------|-----------|-------------|
| TaskSubmitted | ExecutionManager | QueueManager, MetricsCollector |
| TaskQueued | QueueManager | Scheduler |
| TaskScheduled | Scheduler | WorkerPool |
| TaskAssigned | WorkerPool | ResourceManager, StateManager |
| TaskStarted | Worker | StateManager, MetricsCollector |
| TaskProgress | Worker | StateManager |
| TaskCompleted | Worker | ResultAggregator, StateManager, MetricsCollector |
| TaskFailed | Worker | RecoveryManager, StateManager, MetricsCollector |
| TaskCancelled | ExecutionManager | Worker, StateManager |
| TaskRetried | RecoveryManager | QueueManager |
| ResourceAllocated | ResourceManager | Worker |
| ResourceReleased | ResourceManager | WorkerPool |
