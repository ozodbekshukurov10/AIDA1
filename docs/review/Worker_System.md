# AIDA Worker System

**Document:** Book 2, Chapter 2 — Worker System
**Version:** 1.0.0
**Date:** 2026-07-04

---

## Overview

The Worker System manages a fleet of **specialized workers** that execute tasks. Each worker type is optimized for specific task categories, with appropriate resource allocations and security configurations.

---

## 1. Worker Type Definitions

### 1.1 General Worker

**Purpose:** Basic tasks — API calls, data transformation, simple logic.

```yaml
general_worker:
  description: Lightweight worker for simple tasks
  resources:
    cpu: 0.5 cores
    memory: 256MB
    gpu: none
    disk: 100MB
    network: enabled
  concurrency: 10
  timeout: 30s
  sandbox: none
  use_cases:
    - api_calls
    - data_transform
    - json_processing
    - text_processing
```

### 1.2 Code Worker

**Purpose:** Code generation, analysis, refactoring, review.

```yaml
code_worker:
  description: Specialized for code-related tasks
  resources:
    cpu: 2.0 cores
    memory: 2GB
    gpu: none
    disk: 5GB
    network: enabled
  concurrency: 5
  timeout: 120s
  sandbox: docker (for untrusted code)
  tools: [git, filesystem, terminal]
  use_cases:
    - code_generation
    - code_review
    - refactoring
    - debugging
    - test_generation
```

### 1.3 AI Worker

**Purpose:** LLM inference, reasoning, complex analysis.

```yaml
ai_worker:
  description: High-resource worker for LLM inference
  resources:
    cpu: 2.0 cores
    memory: 4GB
    gpu: 4GB VRAM (optional)
    disk: 1GB
    network: enabled
  concurrency: 3
  timeout: 60s
  sandbox: none
  use_cases:
    - llm_inference
    - reasoning
    - planning
    - summarization
    - translation
```

### 1.4 Planning Worker

**Purpose:** Task decomposition, project planning, estimation.

```yaml
planning_worker:
  description: Specialized for planning and decomposition
  resources:
    cpu: 1.0 core
    memory: 1GB
    gpu: none
    disk: 500MB
    network: disabled
  concurrency: 5
  timeout: 30s
  sandbox: none
  use_cases:
    - task_decomposition
    - project_planning
    - estimation
    - roadmap_creation
```

### 1.5 Research Worker

**Purpose:** Web search, information gathering, summarization.

```yaml
research_worker:
  description: Web research and information gathering
  resources:
    cpu: 1.0 core
    memory: 2GB
    gpu: none
    disk: 1GB
    network: enabled (10MB/s limit)
  concurrency: 8
  timeout: 120s
  sandbox: docker (for web scraping)
  tools: [browser, rest_api]
  use_cases:
    - web_search
    - documentation_lookup
    - api_research
    - trend_analysis
```

### 1.6 Security Worker

**Purpose:** Vulnerability scanning, security audit, code review.

```yaml
security_worker:
  description: Security analysis and vulnerability scanning
  resources:
    cpu: 2.0 cores
    memory: 2GB
    gpu: none
    disk: 2GB
    network: enabled
  concurrency: 5
  timeout: 180s
  sandbox: docker
  tools: [git, filesystem, database]
  use_cases:
    - vulnerability_scan
    - security_audit
    - dependency_check
    - secrets_detection
```

### 1.7 Browser Worker

**Purpose:** Web automation, screenshot capture, form filling.

```yaml
browser_worker:
  description: Browser automation and web interaction
  resources:
    cpu: 2.0 cores
    memory: 4GB
    gpu: optional (for rendering)
    disk: 2GB
    network: enabled (10MB/s)
  concurrency: 3
  timeout: 120s
  sandbox: docker (with Chromium)
  use_cases:
    - web_automation
    - screenshot_capture
    - form_filling
    - web_testing
```

### 1.8 Terminal Worker

**Purpose:** Shell commands, system operations, build processes.

```yaml
terminal_worker:
  description: Shell command execution
  resources:
    cpu: 1.0 core
    memory: 512MB
    gpu: none
    disk: 1GB
    network: enabled
  concurrency: 10
  timeout: 60s
  sandbox: docker
  tools: [terminal, filesystem]
  use_cases:
    - shell_commands
    - build_processes
    - git_operations
    - system_administration
```

### 1.9 Sandbox Worker

**Purpose:** Untrusted code execution with maximum isolation.

```yaml
sandbox_worker:
  description: Maximum isolation for untrusted code
  resources:
    cpu: 1.0 core
    memory: 1GB
    gpu: none
    disk: 5GB
    network: disabled (default)
  concurrency: 1
  timeout: 60s
  sandbox: gvisor (maximum isolation)
  security:
    read_only_rootfs: true
    no_network: true
    max_processes: 50
    max_open_files: 256
  use_cases:
    - untrusted_code_execution
    - user_submitted_scripts
    - plugin_execution
```

### 1.10 Streaming Worker

**Purpose:** Real-time streaming responses (SSE, WebSocket).

```yaml
streaming_worker:
  description: Real-time streaming output
  resources:
    cpu: 0.5 cores
    memory: 256MB
    gpu: none
    disk: 100MB
    network: enabled
  concurrency: 20
  timeout: 300s
  sandbox: none
  use_cases:
    - llm_streaming
    - real_time_output
    - progress_reporting
```

---

## 2. Worker Manager

### 2.1 Interface

```python
class IWorkerManager:
    async def get_worker(worker_type: WorkerType) -> Worker
    async def release_worker(worker: Worker) -> None
    async def scale_pool(worker_type: WorkerType, target_count: int) -> None
    async def get_pool_status() -> PoolStatus
    async def get_worker_metrics(worker_id: str) -> WorkerMetrics
    async def health_check_all() -> dict[str, HealthStatus]
```

### 2.2 Pool Status

```python
class PoolStatus:
    total_workers: int
    active_workers: int
    idle_workers: int
    busy_workers: int
    failed_workers: int
    
    by_type: dict[WorkerType, TypeStatus]
    
class TypeStatus:
    worker_type: WorkerType
    total: int
    active: int
    idle: int
    busy: int
    avg_cpu: float
    avg_memory: float
    avg_task_duration: float
```

---

## 3. Worker Lifecycle

### 3.1 Startup Sequence

```
1. Worker process starts
2. Load configuration
3. Initialize runtime environment
4. Register with WorkerManager
5. Perform self-test
6. Signal READY
7. Wait for task assignment
```

### 3.2 Task Execution Sequence

```
1. Receive task from WorkerManager
2. Update status → BUSY
3. Allocate resources
4. Initialize execution environment
5. Execute task
6. Capture result
7. Capture logs
8. Release resources
9. Update status → IDLE
10. Return result to WorkerManager
```

### 3.3 Shutdown Sequence

```
1. Receive shutdown signal
2. Stop accepting new tasks
3. Complete current task (if any)
4. Flush logs
5. Release all resources
6. Unregister from WorkerManager
7. Process exit
```

---

## 4. Worker Health Monitoring

### 4.1 Health Check Protocol

```
WorkerManager → HealthCheck → Worker
Worker → HealthReport → WorkerManager

HealthReport includes:
  - status: healthy | degraded | unhealthy
  - cpu_usage: float
  - memory_usage: float
  - active_tasks: int
  - last_task_duration: int
  - error_count: int
  - uptime: int
```

### 4.2 Health States

| State | Criteria | Action |
|-------|----------|--------|
| HEALTHY | All checks pass | Normal operation |
| DEGRADED | High resource usage | Reduce task assignment |
| UNHEALTHY | Check failures > threshold | Stop assigning tasks |
| DEAD | No response to health check | Restart worker |

### 4.3 Auto-Restart

```yaml
auto_restart:
  enabled: true
  max_restart_attempts: 5
  restart_delay: [5, 10, 30, 60, 120]  # seconds, exponential
  reset_after: 300s  # Reset restart count after 5 min of health
```

---

## 5. Worker Communication

### 5.1 In-Process Communication

For single-node deployment, workers communicate via in-memory queues:

```
WorkerManager ↔ [InMemory Queue] ↔ Workers
```

### 5.2 Redis Communication

For multi-node deployment, workers communicate via Redis:

```
WorkerManager ↔ [Redis Queue] ↔ Workers (on different nodes)
```

### 5.3 gRPC Communication

For high-performance distributed deployment:

```
WorkerManager ↔ [gRPC] ↔ Workers (on different nodes)
```

---

## 6. Worker Pool Scaling

### 6.1 Scale-Up Rules

```yaml
scale_up:
  trigger: avg_cpu > 80% OR queue_depth > 100
  increment: 2 workers
  cooldown: 60s
  max_scale_up_per_hour: 10
```

### 6.2 Scale-Down Rules

```yaml
scale_down:
  trigger: avg_cpu < 30% AND queue_depth < 10
  decrement: 1 worker
  cooldown: 300s
  min_idle_time: 300s  # Worker must be idle for 5 min before removal
  max_scale_down_per_hour: 5
```

### 6.3 Scaling Decision

```python
def should_scale(pool: WorkerPool) -> ScalingDecision:
    metrics = pool.get_metrics()
    
    # Scale up conditions
    if metrics.avg_cpu > 0.8 or metrics.queue_depth > 100:
        return ScalingDecision(action="scale_up", count=2)
    
    # Scale down conditions
    if metrics.avg_cpu < 0.3 and metrics.queue_depth < 10:
        idle_workers = [w for w in pool.workers if w.idle_time > 300]
        if idle_workers:
            return ScalingDecision(action="scale_down", count=1)
    
    return ScalingDecision(action="none")
```

---

## 7. Worker Assignment Strategies

### 7.1 Round Robin

```
Task 1 → Worker 1
Task 2 → Worker 2
Task 3 → Worker 3
Task 4 → Worker 1 (wraps around)
```

**Use case:** Uniform tasks, equal worker capacity.

### 7.2 Least Loaded

```
Task → Worker with lowest CPU/RAM usage
```

**Use case:** Mixed workloads, varying task complexity.

### 7.3 Affinity-Based

```
Task requiring GPU → Worker with GPU
Task requiring Docker → Worker with Docker
Task requiring Git → Worker with Git
```

**Use case:** Specialized tasks, resource matching.

### 7.4 Weighted

```
Task → Worker selected by weighted random
Weight = worker_capacity × (1 - worker_load)
```

**Use case:** Heterogeneous workers, capacity-aware routing.

---

## 8. Worker Configuration

```yaml
workers:
  general:
    count: {min: 5, max: 50}
    resources: {cpu: 0.5, memory: 256MB}
    concurrency: 10
    timeout: 30s
    
  code:
    count: {min: 3, max: 20}
    resources: {cpu: 2.0, memory: 2GB}
    concurrency: 5
    timeout: 120s
    
  ai:
    count: {min: 2, max: 10}
    resources: {cpu: 2.0, memory: 4GB, gpu: 4GB}
    concurrency: 3
    timeout: 60s
    
  terminal:
    count: {min: 5, max: 30}
    resources: {cpu: 1.0, memory: 512MB}
    concurrency: 10
    timeout: 60s
    
  sandbox:
    count: {min: 2, max: 20}
    resources: {cpu: 1.0, memory: 1GB}
    concurrency: 1
    timeout: 60s
    sandbox_type: gvisor
```
