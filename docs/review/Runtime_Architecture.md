# AIDA Runtime Engine Architecture

**Document:** Book 2, Chapter 2
**Version:** 1.0.0
**Date:** 2026-07-04
**Author:** Principal AI Systems Engineer / Distributed Runtime Architect

---

## 1. Vision

The Runtime Engine is the **universal execution environment** of AIDA. It receives tasks from the AI Kernel, manages worker pools, schedules execution, enforces resource limits, sandboxes untrusted code, and returns results. The Runtime must:

- **Execute any task type** — sync, async, streaming, background, distributed
- **Manage 1000+ concurrent workers** — across multiple machines
- **Enforce resource limits** — CPU, RAM, GPU, network, file system
- **Isolate untrusted code** — Docker, gVisor, seccomp sandboxes
- **Self-heal** — automatic recovery from worker crashes, timeouts, failures
- **Scale horizontally** — add workers dynamically based on load

---

## 2. Architecture Overview

### 2.1 Layer Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     AI KERNEL (Task Source)                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Task Submission
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                     RUNTIME ENGINE CORE                          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Execution   │  │  Scheduler   │  │   Queue      │          │
│  │  Manager     │  │              │  │   Manager    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                    │
│  ┌──────┴─────────────────┴─────────────────┴──────┐           │
│  │              RESOURCE MANAGER                     │           │
│  └──────┬─────────────────┬─────────────────┬──────┘           │
│         │                 │                 │                    │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐            │
│  │  Worker     │  │  Sandbox    │  │   State     │            │
│  │  Pool       │  │  Manager    │  │   Manager   │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                 │                 │                    │
│  ┌──────┴─────────────────┴─────────────────┴──────┐           │
│  │           RESULT AGGREGATOR                       │           │
│  └──────────────────────────────────────────────────┘           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
   ┌──────────┐    ┌──────────┐    ┌──────────┐
   │ General  │    │  Code    │    │   AI     │
   │ Workers  │    │ Workers  │    │ Workers  │
   └──────────┘    └──────────┘    └──────────┘
          ↓                ↓                ↓
   ┌──────────┐    ┌──────────┐    ┌──────────┐
   │ Terminal │    │ Browser  │    │ Sandbox  │
   │ Workers  │    │ Workers  │    │ Workers  │
   └──────────┘    └──────────┘    └──────────┘
```

### 2.2 Data Flow

```
Kernel → Task → Queue → Scheduler → Worker Pool → Sandbox → Execution → Result → Aggregator → Kernel
          ↕           ↕              ↕              ↕            ↕
       State DB   Redis Queue   Resource Mgr   Sandbox Mgr   Metrics
```

### 2.3 Component Relationship

```
ExecutionManager
  ├── uses → QueueManager (task queuing)
  ├── uses → Scheduler (task scheduling)
  ├── uses → WorkerPool (worker management)
  ├── uses → ResourceManager (resource allocation)
  ├── uses → SandboxManager (code isolation)
  ├── uses → StateManager (state tracking)
  └── uses → ResultAggregator (result collection)

QueueManager
  ├── backed by → Redis (primary queue)
  └── fallback → PostgreSQL (persistent queue)

WorkerPool
  ├── manages → General Workers
  ├── manages → Code Workers
  ├── manages → AI Workers
  ├── manages → Terminal Workers
  └── manages → Sandbox Workers

SandboxManager
  ├── creates → Docker Containers
  ├── creates → gVisor Sandboxes
  ├── creates → Python Subprocesses
  └── manages → Temp Workspaces
```

---

## 3. Execution Manager

### 3.1 Purpose

The Execution Manager is the **orchestrator** of the Runtime Engine. It receives tasks from the Kernel, coordinates all Runtime components, and returns results.

### 3.2 Interface

```python
class IExecutionManager:
    async def submit(task: Task) -> TaskHandle
    async def execute(task: Task) -> TaskResult
    async def cancel(task_id: UUID) -> CancelResult
    async def get_status(task_id: UUID) -> TaskStatus
    async def get_result(task_id: UUID) -> TaskResult
    async def list_tasks(filter: TaskFilter) -> list[TaskStatus]
```

### 3.3 Execution Flow

```
submit(task)
    ↓
validate(task)
    ↓
assign_priority(task)
    ↓
enqueue(task) → QueueManager
    ↓
schedule(task) → Scheduler
    ↓
assign_worker(task) → WorkerPool
    ↓
allocate_resources(task) → ResourceManager
    ↓
sandbox(task) → SandboxManager
    ↓
execute(task, worker, sandbox) → Worker
    ↓
monitor(task) → StateManager
    ↓
collect_result(task) → ResultAggregator
    ↓
release_resources(task) → ResourceManager
    ↓
return_result(task) → Kernel
```

### 3.4 Task State Machine

```
SUBMITTED → VALIDATED → QUEUED → SCHEDULED → ASSIGNED →
ALLOCATED → RUNNING → COMPLETED → DELIVERED
                ↓           ↓
            PAUSED      FAILED → RETRYING → QUEUED
                ↓           ↓
            RESUMED    CANCELLED
```

---

## 4. Scheduler

### 4.1 Purpose

The Scheduler determines **when** and **where** tasks should execute. It considers worker availability, resource constraints, task priorities, and dependencies.

### 4.2 Scheduling Algorithms

| Algorithm | Use Case | Description |
|-----------|----------|-------------|
| FIFO | Simple tasks | First in, first out |
| Priority | Mixed workloads | Higher priority first |
| Fair Share | Multi-tenant | Equal resource distribution |
| Deadline | Time-sensitive | Earliest deadline first |
| Affinity | Specialized tasks | Match task requirements to worker capabilities |
| Load Balancing | Distributed | Distribute across workers evenly |

### 4.3 Scheduling Decision

```python
class SchedulingDecision:
    task_id: UUID
    worker_id: str
    queue_name: str
    scheduled_at: datetime
    estimated_start: datetime
    estimated_duration: int
    priority: int
    reason: str  # Why this decision was made
```

### 4.4 Multi-Queue Scheduling

```
┌─────────────────────────────────────────────┐
│              SCHEDULER                        │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Critical │  │   High   │  │ Standard │  │
│  │  Queue   │  │  Queue   │  │  Queue   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │             │             │          │
│  ┌────┴─────────────┴─────────────┴────┐    │
│  │     Worker Availability Checker      │    │
│  └────┬─────────────┬─────────────┬────┘    │
│       │             │             │          │
│  ┌────┴─────┐  ┌────┴─────┐  ┌───┴──────┐  │
│  │ Worker 1 │  │ Worker 2 │  │ Worker N │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────┘
```

### 4.5 Scheduler Configuration

```yaml
scheduler:
  algorithm: priority_with_fair_share
  
  queues:
    critical:
      priority: 100
      max_workers: 10
      max_wait: 5s
      
    high:
      priority: 80
      max_workers: 20
      max_wait: 30s
      
    standard:
      priority: 50
      max_workers: 50
      max_wait: 60s
      
    background:
      priority: 20
      max_workers: 30
      max_wait: 300s
      
  fair_share:
    enabled: true
    min_share_per_tenant: 10%
    max_share_per_tenant: 50%
    
  rebalance_interval: 30s
```

---

## 5. Queue Manager

### 5.1 Purpose

The Queue Manager manages all task queues, providing reliable, durable, and prioritized task storage.

### 5.2 Queue Types

| Queue | Purpose | Storage | Durability |
|-------|---------|---------|------------|
| FIFO | Standard processing | Redis List | AOF |
| Priority | Multi-priority processing | Redis Sorted Set | AOF |
| Delayed | Scheduled execution | Redis Sorted Set + Timer | AOF |
| Retry | Failed task retry | Redis List | AOF |
| Dead Letter | Permanently failed tasks | PostgreSQL | Durable |
| Scheduled | Cron-like execution | Redis Sorted Set | AOF |
| Stream | Real-time streaming | Redis Stream | AOF |

### 5.3 Queue Interface

```python
class IQueueManager:
    async def enqueue(queue: str, task: Task, priority: int) -> QueuePosition
    async def dequeue(queue: str) -> Optional[Task]
    async def peek(queue: str, count: int) -> list[Task]
    async def size(queue: str) -> int
    async def move(task_id: UUID, from_queue: str, to_queue: str) -> bool
    async def delay(task_id: UUID, delay_seconds: int) -> bool
    async def dead_letter(task_id: UUID, error: Exception) -> bool
    async def retry(task_id: UUID) -> bool
    async def purge(queue: str) -> int
```

### 5.4 Queue Topology

```
                    ┌─────────────┐
                    │   Incoming   │
                    │    Tasks     │
                    └──────┬──────┘
                           ↓
                    ┌─────────────┐
                    │  Priority    │
                    │  Router      │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
   │  Critical   │ │   Standard  │ │ Background  │
   │   Queue     │ │   Queue     │ │   Queue     │
   └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
          │                │                │
          ↓                ↓                ↓
   ┌──────────────────────────────────────────────┐
   │              Worker Pool                      │
   └──────────────────────────────────────────────┘
          │                │                │
          ↓                ↓                ↓
   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
   │   Retry     │ │ Dead Letter │ │  Scheduled  │
   │   Queue     │ │   Queue     │ │   Queue     │
   └─────────────┘ └─────────────┘ └─────────────┘
```

### 5.5 Queue Configuration

```yaml
queues:
  redis:
    host: localhost
    port: 6379
    db: 0
    password_env: REDIS_PASSWORD
    
  defaults:
    max_size: 100000
    message_ttl: 86400
    visibility_timeout: 300
    
  retry:
    max_retries: 3
    retry_delays: [10, 60, 300]
    dead_letter_after: 3
    
  delayed:
    check_interval: 1s
    batch_size: 100
```

---

## 6. Worker Pool

### 6.1 Purpose

The Worker Pool manages a fleet of **specialized workers** that execute tasks. Workers are categorized by type, each optimized for specific task categories.

### 6.2 Worker Types

| Worker Type | Purpose | Resources | Concurrency |
|-------------|---------|-----------|-------------|
| General | Basic tasks, API calls | Low CPU, Low RAM | 10 |
| Code | Code generation, analysis | Medium CPU, Medium RAM | 5 |
| AI | LLM inference, reasoning | Low CPU, High RAM, GPU | 3 |
| Planning | Task decomposition | Medium CPU, Medium RAM | 5 |
| Research | Web search, scraping | Low CPU, Medium RAM | 8 |
| Security | Vulnerability scanning | Medium CPU, Medium RAM | 5 |
| Browser | Web automation | Medium CPU, High RAM | 3 |
| Terminal | Shell commands | Low CPU, Low RAM | 10 |
| Sandbox | Untrusted code | Isolated (Docker) | 1 per container |
| Streaming | Real-time responses | Low CPU, Low RAM | 20 |

### 6.3 Worker Interface

```python
class IWorker:
    worker_id: str
    worker_type: WorkerType
    status: WorkerStatus
    
    async def start() -> None
    async def stop() -> None
    async def execute(task: Task) -> TaskResult
    async def cancel(task_id: UUID) -> bool
    async def health_check() -> HealthStatus
    async def get_metrics() -> WorkerMetrics
```

### 6.4 Worker Lifecycle

```
CREATED → INITIALIZING → READY → BUSY → IDLE → BUSY → ...
              ↓            ↓       ↓
          FAILED       STOPPING  CRASHED
              ↓            ↓       ↓
           DEAD        STOPPED  RESTARTING → INITIALIZING
```

### 6.5 Worker Pool Architecture

```
┌────────────────────────────────────────────────────────┐
│                    WORKER POOL MANAGER                   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Worker Registry                     │   │
│  │  worker_1: General, IDLE, cpu=10%, ram=20%      │   │
│  │  worker_2: Code, BUSY, cpu=80%, ram=60%         │   │
│  │  worker_3: AI, IDLE, cpu=5%, ram=40%, gpu=30%   │   │
│  │  worker_4: Sandbox, IDLE, docker=ready           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Health Monitor                       │   │
│  │  - Check worker health every 10s                 │   │
│  │  - Restart unhealthy workers                     │   │
│  │  - Scale pool based on load                      │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Load Balancer                        │   │
│  │  - Round-robin for same-type workers             │   │
│  │  - Resource-aware for mixed workloads            │   │
│  │  - Affinity-based for specialized tasks          │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

### 6.6 Worker Configuration

```yaml
worker_pool:
  min_workers:
    general: 5
    code: 3
    ai: 2
    terminal: 5
    sandbox: 2
    
  max_workers:
    general: 50
    code: 20
    ai: 10
    terminal: 30
    sandbox: 20
    
  scaling:
    scale_up_threshold: 0.8
    scale_down_threshold: 0.3
    scale_up_cooldown: 60s
    scale_down_cooldown: 300s
    
  health_check:
    interval: 10s
    timeout: 5s
    max_failures: 3
    
  auto_restart: true
  max_restart_attempts: 5
```

---

## 7. Resource Manager

### 7.1 Purpose

The Resource Manager tracks and enforces resource limits for every task and worker, preventing resource abuse and ensuring fair distribution.

### 7.2 Resource Types

| Resource | Unit | Enforcement |
|----------|------|-------------|
| CPU | cores / millicores | cgroup / process affinity |
| RAM | MB / GB | cgroup / memory limit |
| GPU | VRAM MB | CUDA / MPS |
| Disk | MB / GB | Filesystem quota |
| Network | MB/s | Traffic shaping |
| Open Files | count | ulimit |
| Processes | count | ulimit |
| Time | seconds | Timeout |

### 7.3 Resource Allocation

```python
class ResourceAllocation:
    task_id: UUID
    worker_id: str
    cpu: CpuAllocation
    memory: MemoryAllocation
    gpu: Optional[GpuAllocation]
    disk: DiskAllocation
    network: NetworkAllocation
    timeout: int
    
class CpuAllocation:
    cores: float          # 0.5 = half core, 2.0 = 2 cores
    shares: int           # cgroup CPU shares
    quota: int            # cgroup CPU quota (microseconds)
    
class MemoryAllocation:
    limit_mb: int         # Hard limit
    reservation_mb: int   # Soft limit / guarantee
    swap_mb: int          # Swap limit
    
class GpuAllocation:
    device_id: int        # GPU device
    vram_mb: int          # VRAM limit
    compute_share: float  # GPU compute share (0.0-1.0)
```

### 7.4 Resource Limits Per Task Type

```yaml
resource_limits:
  simple_chat:
    cpu: 0.5
    memory: 256MB
    timeout: 30s
    
  code_generation:
    cpu: 2.0
    memory: 2GB
    timeout: 120s
    
  repository_analysis:
    cpu: 4.0
    memory: 8GB
    disk: 10GB
    timeout: 600s
    
  llm_inference:
    cpu: 2.0
    memory: 4GB
    gpu: 4GB VRAM
    timeout: 60s
    
  sandbox_execution:
    cpu: 1.0
    memory: 1GB
    disk: 5GB
    timeout: 60s
    network: disabled
    
  browser_automation:
    cpu: 2.0
    memory: 4GB
    timeout: 120s
    network: 10MB/s
```

### 7.5 Resource Monitoring

```
Resource Usage Timeline (per worker):
  CPU:    [████████░░░░░░░░] 50%
  RAM:    [██████░░░░░░░░░░] 37%
  GPU:    [██░░░░░░░░░░░░░░] 12%
  Disk:   [████░░░░░░░░░░░░] 25%
  Network:[█░░░░░░░░░░░░░░░] 6%

Alerts:
  CPU > 90% for 60s → WARNING
  RAM > 85% → WARNING
  RAM > 95% → CRITICAL (kill task)
  GPU > 90% → WARNING
  Disk > 80% → WARNING
```

---

## 8. Sandbox Manager

### 8.1 Purpose

The Sandbox Manager creates **isolated execution environments** for untrusted code, preventing damage to the host system and other tasks.

### 8.2 Sandbox Types

| Type | Isolation Level | Performance | Use Case |
|------|----------------|-------------|----------|
| Python Subprocess | LOW | Fast | Simple scripts |
| Docker Container | HIGH | Medium | Untrusted code |
| gVisor (runsc) | VERY HIGH | Slower | Maximum security |
| Firecracker | VERY HIGH | Fast | MicroVM workloads |
| Temp Workspace | LOW | Fast | File operations |

### 8.3 Sandbox Interface

```python
class ISandboxManager:
    async def create(config: SandboxConfig) -> Sandbox
    async def destroy(sandbox_id: str) -> None
    async def execute(sandbox_id: str, code: str) -> ExecutionResult
    async def copy_to(sandbox_id: str, path: str, content: bytes) -> None
    async def copy_from(sandbox_id: str, path: str) -> bytes
    async def list_files(sandbox_id: str, path: str) -> list[FileInfo]
    async def get_metrics(sandbox_id: str) -> SandboxMetrics
```

### 8.4 Docker Sandbox Configuration

```yaml
docker_sandbox:
  image: python:3.14-slim
  
  resources:
    cpus: 1.0
    memory: 1GB
    pids_limit: 100
    
  security:
    read_only_rootfs: true
    no_new_privileges: true
    drop_capabilities: [ALL]
    add_capabilities: [NET_BIND_SERVICE]
    seccomp_profile: default
    
  filesystem:
    volumes:
      - type: tmpfs
        target: /tmp
        size: 512MB
      - type: tmpfs
        target: /workspace
        size: 1GB
        
  network:
    enabled: false
    # If enabled:
    # dns: [8.8.8.8]
    # allowed_domains: [github.com, pypi.org]
    # blocked_ports: [22, 25, 445]
    
  timeout: 60s
  auto_destroy: true
```

### 8.5 Sandbox Isolation Layers

```
Layer 1: Process Isolation
  - Separate PID namespace
  - Separate user namespace
  - Resource limits (cgroup)

Layer 2: Filesystem Isolation
  - Read-only root filesystem
  - OverlayFS for writes
  - No access to host filesystem

Layer 3: Network Isolation
  - No network (default)
  - Or: Bridge network with filtering
  - Or: Host network (trusted only)

Layer 4: System Call Filtering
  - Seccomp profile
  - Allow only safe syscalls
  - Block: mount, reboot, kexec_load

Layer 5: Capability Dropping
  - Drop ALL capabilities
  - Add only what's needed
  - No: SYS_ADMIN, NET_ADMIN, SYS_PTRACE
```

---

## 9. State Manager

### 9.1 Purpose

The State Manager tracks the state of every task, worker, and resource in the Runtime Engine.

### 9.2 State Storage

| State Type | Storage | TTL | Purpose |
|------------|---------|-----|---------|
| Task state | Redis + PostgreSQL | 24h / permanent | Current task status |
| Worker state | Redis | 60s | Worker health/status |
| Resource state | Redis | 30s | Resource allocation |
| Checkpoint | Redis + S3 | 1h / permanent | Workflow checkpoints |
| Metrics | Redis + Prometheus | 1h / permanent | Performance data |

### 9.3 State Interface

```python
class IStateManager:
    async def set_task_state(task_id: UUID, state: TaskState) -> None
    async def get_task_state(task_id: UUID) -> TaskState
    async def update_task_progress(task_id: UUID, progress: float) -> None
    async def add_task_log(task_id: UUID, log: LogEntry) -> None
    async def save_checkpoint(task_id: UUID, checkpoint: Checkpoint) -> None
    async def load_checkpoint(task_id: UUID) -> Optional[Checkpoint]
    async def set_worker_state(worker_id: str, state: WorkerState) -> None
    async def get_worker_state(worker_id: str) -> WorkerState
```

---

## 10. Result Aggregator

### 10.1 Purpose

The Result Aggregator collects results from multiple steps/workers and assembles them into a final response.

### 10.2 Aggregation Strategies

| Strategy | Use Case | Description |
|----------|----------|-------------|
| Concat | Sequential steps | Append results in order |
| Merge | Parallel steps | Combine independent results |
| Reduce | Summary tasks | Aggregate into summary |
| Vote | Quality assurance | Majority vote from multiple agents |
| Weighted | Mixed quality | Weight by confidence/quality |

### 10.3 Result Interface

```python
class IResultAggregator:
    async def aggregate(results: list[TaskResult], strategy: str) -> AggregatedResult
    async def merge(results: list[TaskResult]) -> AggregatedResult
    async def reduce(results: list[TaskResult], reducer: str) -> AggregatedResult
    async def vote(results: list[TaskResult]) -> AggregatedResult
```

---

## 11. Plugin Runtime

### 11.1 Purpose

The Plugin Runtime manages third-party plugins that extend the Runtime Engine's capabilities.

### 11.2 Plugin Lifecycle

```
DISCOVERED → DOWNLOADED → VERIFIED → INSTALLED → INITIALIZED → READY → RUNNING → STOPPED
                ↓              ↓           ↓            ↓          ↓
            REJECTED       CORRUPTED   FAILED      FAILED     FAILED
```

### 11.3 Plugin Security

```yaml
plugin_security:
  verification:
    require_signature: true
    trusted_publishers: [aida-team]
    
  sandboxing:
    default: docker
    trusted: none
    untrusted: gvisor
    
  permissions:
    - network_access
    - file_read
    - file_write
    - code_execution
    - database_access
  require_explicit_grant: true
  
  resource_limits:
    max_cpu: 2.0
    max_memory: 4GB
    max_network: 10MB/s
    max_duration: 300s
```

---

## 12. Configuration

```yaml
runtime:
  engine:
    max_concurrent_tasks: 1000
    task_timeout: 300
    default_queue: standard
    
  scheduler:
    algorithm: priority_with_fair_share
    rebalance_interval: 30s
    
  queues:
    backend: redis
    redis_url: redis://localhost:6379/0
    
  worker_pool:
    min_workers: 10
    max_workers: 100
    auto_scale: true
    
  resource_manager:
    enabled: true
    enforcement: strict
    
  sandbox:
    default_type: docker
    auto_destroy: true
    max_concurrent: 50
    
  state:
    backend: redis
    checkpoint_store: redis+postgresql
    
  monitoring:
    enabled: true
    metrics_interval: 15s
    health_check_interval: 10s
```

---

## 13. Migration from Current Architecture

### Phase 1: Basic Runtime (Week 1-2)
- Implement ExecutionManager + QueueManager (Redis)
- Implement basic WorkerPool (in-process)
- No sandboxing yet

### Phase 2: Worker System (Week 3-4)
- Implement specialized workers
- Add ResourceManager
- Add StateManager

### Phase 3: Sandbox (Week 5-6)
- Implement Docker sandbox
- Add SandboxManager
- Security hardening

### Phase 4: Scaling (Week 7-8)
- Distributed worker pool
- Auto-scaling
- Load testing

---

## Appendix: Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Queue | Redis Lists + Sorted Sets | Fast, reliable, supports priorities |
| State | Redis + PostgreSQL | Fast cache + durable storage |
| Sandbox | Docker + gVisor | Industry standard + strong isolation |
| Worker Pool | Python asyncio + multiprocessing | Async I/O + CPU parallelism |
| Monitoring | Prometheus + Grafana | Industry standard |
| Logging | structlog + JSON | Structured, filterable |
| Config | YAML + Pydantic | Declarative, validated |
