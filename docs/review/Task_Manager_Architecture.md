# AIDA Intelligent Task Manager Architecture

**Document:** Book 2, Chapter 3 — Intelligent Task Manager Architecture
**Version:** 1.0.0
**Date:** 2026-07-04
**Author:** Principal AI Systems Architect / Multi-Agent Orchestration Engineer

---

## 1. Vision

The Intelligent Task Manager is the **Project Manager** of the AIDA platform. It independently understands user requests, decomposes them into optimal subtasks, assigns them to the right agents and models, manages dependencies and parallel execution, and assembles all results into a single coherent response.

### 1.1 Core Principles

| Principle | Description |
|-----------|-------------|
| **Intelligent Decomposition** | AI analyzes and splits complex tasks automatically |
| **Parallel Execution** | Independent tasks run simultaneously |
| **Dependency Awareness** | Dependent tasks wait for prerequisites |
| **Adaptive Routing** | Tasks are assigned to the best-suited agent/model |
| **Self-Healing** | Failures trigger automatic recovery |
| **Full Observability** | Every decision is logged and auditable |
| **Stateful Execution** | Checkpoints enable resume and rollback |

---

## 2. Architecture Overview

### 2.1 Layer Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER REQUEST                                  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    TASK MANAGER CORE                                 │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Request    │  │   Intent     │  │  Complexity  │              │
│  │   Analyzer   │→ │   Detector   │→ │   Analyzer   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│         ↓                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Task       │  │ Dependency   │  │  Priority    │              │
│  │  Decomposer  │→ │   Graph      │→ │   Engine     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│         ↓                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Resource   │  │    Task      │  │   Task       │              │
│  │   Planner    │→ │   Router     │→ │  Scheduler   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION ENGINE                               │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Execution   │  │  Parallel    │  │  Checkpoint  │              │
│  │   Manager    │→ │   Executor   │→ │   Manager    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│         ↓                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Failure    │  │  Result      │  │   Task       │              │
│  │   Handler    │→ │  Aggregator  │→ │   Memory     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
           ┌────────────────────┼────────────────────┐
           ↓                    ↓                    ↓
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │   Planner    │    │    Code      │    │  Security    │
    │   Agent      │    │    Agent     │    │   Agent      │
    └──────────────┘    └──────────────┘    └──────────────┘
           ↓                    ↓                    ↓
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │  Research    │    │  Testing     │    │   Deploy     │
    │   Agent      │    │   Agent      │    │   Agent      │
    └──────────────┘    └──────────────┘    └──────────────┘
```

### 2.2 Component Relationship

```
TaskManager
  ├── uses → RequestAnalyzer (parse user input)
  ├── uses → IntentDetector (understand user goal)
  ├── uses → ComplexityAnalyzer (assess difficulty)
  ├── uses → TaskDecomposer (split into subtasks)
  ├── uses → DependencyGraph (build dependency tree)
  ├── uses → PriorityEngine (assign priorities)
  ├── uses → ResourcePlanner (estimate resources)
  ├── uses → TaskRouter (assign to agents/models)
  └── uses → TaskScheduler (order execution)

OrchestrationEngine
  ├── uses → ExecutionManager (run tasks)
  ├── uses → ParallelExecutor (concurrent execution)
  ├── uses → CheckpointManager (save/restore state)
  ├── uses → FailureHandler (recover from errors)
  ├── uses → ResultAggregator (combine results)
  └── uses → TaskMemory (store history/metrics)
```

---

## 3. Request Analysis Pipeline

### 3.1 Pipeline Stages

```
User Request
    │
    ↓
┌─────────────────────────────────┐
│ Stage 1: Normalize              │
│ - Clean whitespace              │
│ - Detect language               │
│ - Extract code blocks           │
│ - Identify file references      │
└────────────────┬────────────────┘
                 │
                 ↓
┌─────────────────────────────────┐
│ Stage 2: Intent Detection       │
│ - User goal                     │
│ - Expected output               │
│ - Programming language          │
│ - Framework                     │
│ - Risk level                    │
└────────────────┬────────────────┘
                 │
                 ↓
┌─────────────────────────────────┐
│ Stage 3: Complexity Analysis    │
│ - Task count estimation         │
│ - Skill requirements            │
│ - Time estimation               │
│ - Resource requirements         │
└────────────────┬────────────────┘
                 │
                 ↓
┌─────────────────────────────────┐
│ Stage 4: Classification         │
│ - Task type                     │
│ - Priority level                │
│ - Required agents               │
│ - Required tools                │
└─────────────────────────────────┘
```

### 3.2 Intent Detection Model

```python
class IntentDetection:
    user_goal: str              # What the user wants to achieve
    expected_output: str        # Expected result format
    programming_language: str   # python, javascript, etc.
    framework: str              # django, react, etc.
    repository: str             # Target repository
    environment: str            # production, staging, development
    required_tools: list[str]   # Tools needed
    risk_level: str             # low, medium, high, critical
    time_constraint: str        # immediate, hours, days
    quality_requirement: str    # quick, standard, thorough
```

---

## 4. Task Decomposition Engine

### 4.1 Decomposition Hierarchy

```
Epic (Major feature / project)
  └── Feature (Specific capability)
        └── Module (Functional unit)
              └── Component (Smaller unit)
                    └── Task (Atomic work item)
                          └── Subtask (Task step)
                                └── Action (Single operation)
```

### 4.2 Decomposition Rules

| Rule | Description | Example |
|------|-------------|---------|
| Single Responsibility | Each task does one thing | "Create User model" not "Build auth system" |
| Estimable | Task can be estimated | Not "fix everything" |
| Testable | Task has clear completion criteria | Tests pass, feature works |
| Independent | Minimize dependencies | Avoid circular dependencies |
| Right-sized | 15 min — 4 hours per task | Not 1 minute, not 3 days |

### 4.3 Task Template

```python
class Task:
    id: UUID
    title: str
    description: str
    task_type: str           # coding, testing, research, etc.
    priority: int            # 0-100
    status: str              # lifecycle state
    
    # Decomposition
    parent_id: Optional[UUID]
    children: list[UUID]
    depth: int               # 0=epic, 1=feature, etc.
    
    # Dependencies
    depends_on: list[UUID]
    blocks: list[UUID]
    
    # Assignment
    assigned_agent: str
    assigned_model: str
    
    # Resources
    estimated_cpu: float
    estimated_memory_mb: int
    estimated_duration: int  # seconds
    required_tools: list[str]
    
    # Execution
    checkpoints: list[Checkpoint]
    results: list[TaskResult]
    errors: list[TaskError]
    
    # Metadata
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: str
```

---

## 5. Dependency Graph Engine

### 5.1 Dependency Types

| Type | Description | Example |
|------|-------------|---------|
| `finish_to_start` | B starts after A finishes | Test after code |
| `finish_to_finish` | B finishes after A finishes | Docs with code |
| `start_to_start` | B starts when A starts | Parallel features |
| `start_to_finish` | B finishes when A starts | Handoff tasks |

### 5.2 Graph Operations

```
Operations:
  - Topological sort (execution order)
  - Cycle detection (prevent deadlocks)
  - Critical path (longest dependency chain)
  - Parallel groups (independent tasks)
  - Bottleneck identification
```

### 5.3 Critical Path Analysis

```
Critical Path = Longest path through dependency graph

Example:
  Task A (2h) → Task B (1h) → Task D (3h) = 6 hours (CRITICAL)
  Task A (2h) → Task C (1h) → Task D (3h) = 6 hours (CRITICAL)
  Task A (2h) → Task E (30m)              = 2.5 hours (slack)

Total project duration = 6 hours (critical path)
Slack for Task E = 6 - 2.5 = 3.5 hours
```

---

## 6. Priority Engine

### 6.1 Priority Levels

| Level | Value | Description | Examples |
|-------|-------|-------------|----------|
| Emergency | 100 | System down, security breach | Production outage |
| Critical | 90 | Blocking other work | Core feature broken |
| High | 80 | Important, near deadline | Active user request |
| Normal | 50 | Standard work | Feature development |
| Low | 30 | Nice to have | UI improvements |
| Idle | 10 | When nothing else to do | Tech debt cleanup |

### 6.2 Priority Calculation

```python
def calculate_priority(task: Task) -> int:
    base = task.base_priority
    
    # Urgency factor
    if task.deadline:
        hours_left = (task.deadline - now()).total_seconds() / 3600
        if hours_left < 1:
            urgency = 50
        elif hours_left < 4:
            urgency = 30
        elif hours_left < 24:
            urgency = 15
        else:
            urgency = 0
    else:
        urgency = 0
    
    # Impact factor
    impact = task.affected_users * 2
    
    # Effort factor (smaller tasks get priority boost)
    if task.estimated_duration < 1800:  # < 30 min
        effort_boost = 10
    else:
        effort_boost = 0
    
    # Dependency factor (tasks blocking others get priority)
    dependency_boost = len(task.blocks) * 5
    
    return min(100, base + urgency + impact + effort_boost + dependency_boost)
```

---

## 7. Resource Planning

### 7.1 Resource Estimation

```python
class ResourcePlan:
    task_id: UUID
    
    cpu_cores: float
    memory_mb: int
    gpu_required: bool
    gpu_vram_mb: int
    
    estimated_duration: int  # seconds
    
    required_agents: list[str]
    required_models: list[str]
    required_tools: list[str]
    
    estimated_cost: float  # API cost estimate
```

### 7.2 Resource Estimation Rules

| Task Type | CPU | RAM | GPU | Duration |
|-----------|-----|-----|-----|----------|
| simple_chat | 0.5 | 256 | No | 5s |
| code_generation | 2.0 | 2GB | No | 30s |
| code_review | 2.0 | 2GB | No | 60s |
| repository_analysis | 4.0 | 8GB | No | 300s |
| llm_inference | 2.0 | 4GB | Yes (4GB) | 30s |
| browser_automation | 2.0 | 4GB | No | 120s |
| security_scan | 4.0 | 4GB | No | 300s |
| testing | 2.0 | 2GB | No | 180s |

---

## 8. Task Routing

### 8.1 Agent-Task Matching

| Task Type | Primary Agent | Fallback Agent |
|-----------|---------------|----------------|
| planning | planner_agent | code_agent |
| coding | code_agent | planner_agent |
| debugging | debug_agent | code_agent |
| research | research_agent | planner_agent |
| testing | test_agent | code_agent |
| security | security_agent | code_agent |
| documentation | documentation_agent | code_agent |
| monitoring | monitoring_agent | planner_agent |
| deployment | deployment_agent | code_agent |
| memory | memory_agent | planner_agent |

### 8.2 Model-Task Matching

| Task Type | Primary Model | Fallback Model |
|-----------|---------------|----------------|
| simple_chat | flash (small) | pro (large) |
| code_generation | pro (large) | flash (small) |
| reasoning | pro (large) | flash (small) |
| analysis | pro (large) | flash (small) |
| classification | flash (small) | pro (large) |
| summarization | flash (small) | pro (large) |

---

## 9. Orchestration Engine

### 9.1 Execution Strategies

| Strategy | When to Use | Description |
|----------|-------------|-------------|
| Sequential | Dependent tasks | Execute one by one |
| Parallel | Independent tasks | Execute simultaneously |
| Pipeline | Multi-stage processing | Stages run in parallel |
| MapReduce | Large datasets | Split, process, merge |
| DAG | Complex dependencies | Respect dependency graph |

### 9.2 Parallel Execution Engine

```python
class ParallelExecutor:
    async def execute_group(self, group: list[Task]) -> list[TaskResult]:
        """Execute independent tasks in parallel."""
        
        # Validate all tasks are independent
        for task in group:
            assert not task.depends_on, f"Task {task.id} has dependencies"
        
        # Create coroutines
        coroutines = [self.execute_task(task) for task in group]
        
        # Execute with concurrency limit
        results = await asyncio.gather(
            *coroutines,
            return_exceptions=True,
            max_concurrent=self.max_parallel_tasks
        )
        
        return results
```

### 9.3 Checkpoint System

```python
class Checkpoint:
    task_id: UUID
    checkpoint_id: int
    timestamp: datetime
    state: TaskState
    progress: float  # 0.0 - 1.0
    data: dict       # Serialized task state
    parent_checkpoint: Optional[int]
```

---

## 10. Failure Recovery

### 10.1 Recovery Strategies

| Strategy | When | Description |
|----------|------|-------------|
| Retry | Transient failure | Retry same agent/model |
| Alternative Agent | Agent unavailable | Try different agent |
| Alternative Model | Model unavailable | Try different model |
| Alternative Tool | Tool unavailable | Try different tool |
| Rollback | Wrong direction | Revert to checkpoint |
| Manual Review | Unknown failure | Alert human operator |
| Skip | Non-critical task | Skip and continue |
| Degrade | Resource exhaustion | Reduce quality |

### 10.2 Recovery Flow

```
Task Failed
    │
    ├── Check retry count < max_retries?
    │   ├── YES → Retry (same agent, same model)
    │   └── NO → Continue
    │
    ├── Try alternative agent?
    │   ├── YES → Execute with alternative
    │   └── NO → Continue
    │
    ├── Try alternative model?
    │   ├── YES → Execute with alternative
    │   └── NO → Continue
    │
    ├── Has checkpoint?
    │   ├── YES → Rollback to checkpoint
    │   └── NO → Continue
    │
    ├── Is task critical?
    │   ├── YES → Alert operator
    │   └── NO → Skip task
    │
    └── Mark task as FAILED
```

---

## 11. Task Memory

### 11.1 Memory Structure

```python
class TaskMemory:
    task_id: UUID
    
    # History
    execution_history: list[ExecutionRecord]
    decision_history: list[DecisionRecord]
    
    # Outputs
    intermediate_results: list[TaskResult]
    final_result: Optional[TaskResult]
    
    # Errors
    errors: list[TaskError]
    recovery_attempts: list[RecoveryAttempt]
    
    # Files
    created_files: list[FileInfo]
    modified_files: list[FileInfo]
    
    # Logs
    execution_logs: list[LogEntry]
    
    # Metrics
    metrics: TaskMetrics
```

### 11.2 Memory Retention

```yaml
task_memory:
  active_tasks:
    retention: until_completed
    
  completed_tasks:
    retention: 7d
    
  failed_tasks:
    retention: 30d
    
  archived_tasks:
    retention: 90d
```

---

## 12. Configuration

```yaml
task_manager:
  # Request Analysis
  analysis:
    normalize_language: true
    detect_code_blocks: true
    extract_file_references: true
    
  # Decomposition
  decomposition:
    max_depth: 6
    min_task_duration: 300  # 5 min
    max_task_duration: 14400  # 4 hours
    auto_decompose: true
    
  # Dependency Graph
  dependency:
    max_dependencies: 20
    cycle_detection: true
    critical_path_analysis: true
    
  # Priority
  priority:
    algorithm: composite
    weights:
      urgency: 0.4
      impact: 0.3
      effort: 0.1
      dependency: 0.2
      
  # Resource Planning
  resource:
    estimation_method: historical
    buffer_percent: 20
    
  # Orchestration
  orchestration:
    max_parallel_tasks: 10
    checkpoint_interval: 60s
    max_retries: 3
    timeout_per_task: 3600s
    
  # Recovery
  recovery:
    auto_retry: true
    auto_alternative_agent: true
    auto_alternative_model: true
    auto_rollback: true
    alert_on_failure: true
    
  # Memory
  memory:
    enabled: true
    retention:
      active: until_completed
      completed: 7d
      failed: 30d
```
