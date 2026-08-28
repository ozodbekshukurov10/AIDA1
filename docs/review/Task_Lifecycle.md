# AIDA Task Lifecycle

**Document:** Book 2, Chapter 3 — Task Lifecycle
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Task Lifecycle defines the complete journey of a task from user request to final delivery. Every task passes through **14 stages**, each with specific inputs, processing logic, and outputs.

---

## 2. Lifecycle Stages

### 2.1 Complete Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TASK LIFECYCLE                                 │
│                                                                      │
│  1. Receive Request                                                  │
│     ↓                                                                │
│  2. Normalize Request                                                │
│     ↓                                                                │
│  3. Intent Detection                                                 │
│     ↓                                                                │
│  4. Complexity Analysis                                              │
│     ↓                                                                │
│  5. Dependency Analysis                                              │
│     ↓                                                                │
│  6. Task Decomposition                                               │
│     ↓                                                                │
│  7. Priority Assignment                                              │
│     ↓                                                                │
│  8. Agent Selection                                                  │
│     ↓                                                                │
│  9. Resource Allocation                                              │
│     ↓                                                                │
│  10. Execution                                                       │
│     ↓                                                                │
│  11. Validation                                                      │
│     ↓                                                                │
│  12. Aggregation                                                     │
│     ↓                                                                │
│  13. Final Review                                                    │
│     ↓                                                                │
│  14. Response Delivery                                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Stage Details

### 3.1 Stage 1 — Receive Request

| Property | Value |
|----------|-------|
| Input | Raw user message |
| Output | Parsed request object |
| Duration | < 10ms |
| Failure | Reject invalid requests |

**Processing:**
```
1. Receive HTTP/WebSocket message
2. Validate message format
3. Extract message content
4. Identify sender (user_id, session_id)
5. Create Request object
6. Log request receipt
```

**Request Object:**
```python
class ReceivedRequest:
    request_id: UUID
    user_id: UUID
    session_id: UUID
    content: str
    message_type: str  # text, code, file
    received_at: datetime
    metadata: dict
```

---

### 3.2 Stage 2 — Normalize Request

| Property | Value |
|----------|-------|
| Input | Parsed request object |
| Output | Normalized request |
| Duration | < 50ms |
| Failure | Return error to user |

**Processing:**
```
1. Clean whitespace (trim, normalize spaces)
2. Detect language (uz, en, ru, tr)
3. Extract code blocks (```...```)
4. Identify file references (/path/to/file)
5. Resolve abbreviations and shortcuts
6. Normalize to internal format
```

**Normalization Rules:**
```python
normalization_rules:
  whitespace:
    - trim_leading_trailing: true
    - normalize_spaces: true
    - remove_empty_lines: true
    
  language:
    - auto_detect: true
    - default: uz
    - translate_if_needed: false  # Keep original
    
  code:
    - extract_code_blocks: true
    - detect_language: true
    - preserve_formatting: true
    
  files:
    - extract_paths: true
    - resolve_relative: true
    - validate_exists: false  # Check later
```

---

### 3.3 Stage 3 — Intent Detection

| Property | Value |
|----------|-------|
| Input | Normalized request |
| Output | Intent analysis |
| Duration | < 200ms |
| Failure | Return clarification request |

**Processing:**
```
1. Analyze user goal
2. Determine expected output type
3. Detect programming language
4. Detect framework/library
5. Identify target repository
6. Determine risk level
7. Estimate time constraint
```

**Intent Analysis:**
```python
class IntentAnalysis:
    # User Goal
    user_goal: str                    # "Create a REST API for users"
    goal_category: str                # "coding"
    
    # Expected Output
    expected_output_type: str         # "code"
    expected_files: list[str]         # ["views.py", "serializers.py"]
    
    # Technical Context
    programming_language: str         # "python"
    framework: str                    # "django"
    repository: str                   # "my-project"
    
    # Risk Assessment
    risk_level: str                   # "medium"
    risk_factors: list[str]           # ["modifies production code"]
    
    # Constraints
    time_constraint: str              # "hours"
    quality_requirement: str          # "standard"
```

**Goal Categories:**
| Category | Description | Examples |
|----------|-------------|----------|
| coding | Write/modify code | "Create login page" |
| debugging | Fix errors | "Fix the crash" |
| research | Gather information | "What is Django?" |
| analysis | Analyze code/data | "Review this PR" |
| testing | Write/run tests | "Add unit tests" |
| documentation | Write docs | "Write API docs" |
| deployment | Deploy/release | "Deploy to production" |
| planning | Plan approach | "How to implement X?" |

---

### 3.4 Stage 4 — Complexity Analysis

| Property | Value |
|----------|-------|
| Input | Intent analysis |
| Output | Complexity assessment |
| Duration | < 100ms |
| Failure | N/A (always succeeds) |

**Processing:**
```
1. Estimate number of subtasks
2. Assess technical complexity
3. Determine skill requirements
4. Estimate total duration
5. Estimate resource requirements
6. Assign complexity level
```

**Complexity Levels:**
| Level | Tasks | Duration | Skills Required |
|-------|-------|----------|-----------------|
| Simple | 1-2 | < 30 min | Basic |
| Medium | 3-5 | 30 min — 2h | Intermediate |
| Complex | 6-15 | 2h — 8h | Advanced |
| Critical | 16+ | 8h+ | Expert + multiple |

**Complexity Factors:**
```python
complexity_factors:
  code_changes:
    files_modified: 1-3 → simple
    files_modified: 4-10 → medium
    files_modified: 11-30 → complex
    files_modified: 30+ → critical
    
  dependencies:
    new_dependencies: 0 → simple
    new_dependencies: 1-3 → medium
    new_dependencies: 4-7 → complex
    new_dependencies: 8+ → critical
    
  integration:
    no_integration → simple
    single_integration → medium
    multiple_integrations → complex
    external_systems → critical
    
  security:
    no_security_impact → simple
    authentication → medium
    authorization → complex
    encryption → critical
```

---

### 3.5 Stage 5 — Dependency Analysis

| Property | Value |
|----------|-------|
| Input | Intent analysis + Complexity |
| Output | Dependency graph |
| Duration | < 100ms |
| Failure | N/A |

**Processing:**
```
1. Identify file dependencies
2. Identify module dependencies
3. Identify service dependencies
4. Identify external API dependencies
5. Build dependency graph
6. Detect cycles
7. Calculate critical path
```

**Dependency Types:**
| Type | Description | Example |
|------|-------------|---------|
| `file_read` | Needs to read file | "Modify views.py" |
| `file_write` | Needs to write file | "Create test.py" |
| `module_import` | Needs module | "Use pandas" |
| `service_call` | Needs service | "Call payment API" |
| `database` | Needs DB access | "Query users table" |
| `external_api` | Needs external API | "Call OpenAI API" |

---

### 3.6 Stage 6 — Task Decomposition

| Property | Value |
|----------|-------|
| Input | Intent + Complexity + Dependencies |
| Output | Task tree |
| Duration | < 500ms |
| Failure | Return error, suggest manual decomposition |

**Processing:**
```
1. Create task hierarchy (Epic → Feature → Task → Subtask)
2. Assign task types to each task
3. Define acceptance criteria
4. Estimate duration per task
5. Assign prerequisites
6. Create execution plan
```

**Decomposition Example:**
```
User Request: "Create a user authentication system"

Epic: User Authentication System
├── Feature: User Registration
│   ├── Task: Create User model
│   ├── Task: Create registration API endpoint
│   └── Task: Create registration form
├── Feature: User Login
│   ├── Task: Create login API endpoint
│   ├── Task: Create JWT token service
│   └── Task: Create login form
├── Feature: Password Reset
│   ├── Task: Create password reset API
│   └── Task: Create email service
└── Feature: Testing
    ├── Task: Write unit tests
    └── Task: Write integration tests
```

---

### 3.7 Stage 7 — Priority Assignment

| Property | Value |
|----------|-------|
| Input | Task tree + dependencies |
| Output | Tasks with priorities |
| Duration | < 50ms |
| Failure | N/A |

**Processing:**
```
1. Calculate base priority from user request
2. Apply urgency factor (deadline)
3. Apply impact factor (affected users)
4. Apply dependency factor (blocking others)
5. Apply effort factor (small tasks get boost)
6. Normalize to 0-100 scale
```

**Priority Matrix:**
| Urgency \ Impact | High | Medium | Low |
|------------------|------|--------|-----|
| **Immediate** | 100 | 90 | 80 |
| **Hours** | 90 | 70 | 60 |
| **Days** | 70 | 50 | 40 |
| **None** | 60 | 40 | 20 |

---

### 3.8 Stage 8 — Agent Selection

| Property | Value |
|----------|-------|
| Input | Task tree + priorities |
| Output | Agent assignments |
| Duration | < 100ms |
| Failure | Select fallback agent |

**Processing:**
```
1. Match task type to agent capabilities
2. Check agent availability
3. Check agent workload
4. Select best agent (capability + availability)
5. Assign fallback agent
6. Create agent-task mapping
```

**Selection Algorithm:**
```python
def select_agent(task: Task) -> AgentAssignment:
    # Get capable agents
    capable = agent_pool.get_capable_agents(task.required_skills)
    
    # Score each agent
    scored = []
    for agent in capable:
        score = 0.0
        
        # Capability match (0-40 points)
        score += capability_score(agent, task) * 0.4
        
        # Availability (0-30 points)
        score += availability_score(agent) * 0.3
        
        # Workload (0-20 points) - lower = better
        score += (1.0 - agent.workload) * 0.2
        
        # Historical performance (0-10 points)
        score += performance_score(agent, task.type) * 0.1
        
        scored.append((agent, score))
    
    # Sort by score
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return AgentAssignment(
        primary=scored[0][0],
        fallback=scored[1][0] if len(scored) > 1 else None
    )
```

---

### 3.9 Stage 9 — Resource Allocation

| Property | Value |
|----------|-------|
| Input | Task tree + agent assignments |
| Output | Resource plans |
| Duration | < 100ms |
| Failure | Reduce allocation, continue |

**Processing:**
```
1. Estimate CPU requirements
2. Estimate memory requirements
3. Estimate GPU requirements (if needed)
4. Estimate duration
5. Check resource availability
6. Allocate resources
7. Set resource limits
```

**Resource Allocation Table:**
| Task Type | CPU | RAM | GPU | Duration |
|-----------|-----|-----|-----|----------|
| code_generation | 2.0 | 2GB | No | 30s |
| code_review | 2.0 | 2GB | No | 60s |
| testing | 2.0 | 2GB | No | 180s |
| security_scan | 4.0 | 4GB | No | 300s |
| llm_inference | 2.0 | 4GB | Yes (4GB) | 30s |

---

### 3.10 Stage 10 — Execution

| Property | Value |
|----------|-------|
| Input | Resource plans + agent assignments |
| Output | Task results |
| Duration | Variable (1s — 4h) |
| Failure | Trigger recovery |

**Processing:**
```
1. Submit task to queue
2. Schedule task execution
3. Assign worker to task
4. Allocate sandbox (if needed)
5. Execute task
6. Monitor progress
7. Collect results
8. Release resources
```

**Execution Strategies:**
| Strategy | When | Description |
|----------|------|-------------|
| Sequential | Dependent tasks | Execute one by one |
| Parallel | Independent tasks | Execute simultaneously |
| Pipeline | Multi-stage | Stages overlap |
| DAG | Complex dependencies | Respect graph order |

---

### 3.11 Stage 11 — Validation

| Property | Value |
|----------|-------|
| Input | Task results |
| Output | Validation report |
| Duration | < 30s |
| Failure | Return to execution |

**Processing:**
```
1. Check completion criteria
2. Validate output format
3. Run tests (if applicable)
4. Check security constraints
5. Verify quality standards
6. Generate validation report
```

**Validation Checks:**
```python
validation_checks:
  completion:
    - all_acceptance_criteria_met: true
    - no_pending_subtasks: true
    
  format:
    - output_type_matches_expected: true
    - output_size_within_limits: true
    
  tests:
    - unit_tests_pass: true
    - integration_tests_pass: true
    - no_test_failures: true
    
  security:
    - no_hardcoded_secrets: true
    - no_sql_injection: true
    - no_xss_vulnerabilities: true
    
  quality:
    - code_review_passed: true
    - documentation_complete: true
    - no_lint_errors: true
```

---

### 3.12 Stage 12 — Aggregation

| Property | Value |
|----------|-------|
| Input | Validated task results |
| Output | Aggregated result |
| Duration | < 5s |
| Failure | Return error, retry aggregation |

**Processing:**
```
1. Collect all task results
2. Merge code changes
3. Combine documentation
4. Consolidate test results
5. Merge metrics
6. Create unified result
```

**Aggregation Strategies:**
| Strategy | Use Case | Description |
|----------|----------|-------------|
| Concat | Sequential steps | Append results in order |
| Merge | Parallel steps | Combine independent results |
| Reduce | Summary tasks | Aggregate into summary |
| Vote | Quality assurance | Majority vote from agents |

---

### 3.13 Stage 13 — Final Review

| Property | Value |
|----------|-------|
| Input | Aggregated result |
| Output | Reviewed result |
| Duration | < 10s |
| Failure | Return to specific task |

**Processing:**
```
1. Overall quality check
2. Consistency verification
3. Completeness check
4. Security review
5. Performance review
6. Final approval
```

---

### 3.14 Stage 14 — Response Delivery

| Property | Value |
|----------|-------|
| Input | Reviewed result |
| Output | User response |
| Duration | < 1s |
| Failure | Log and retry delivery |

**Processing:**
```
1. Format response for user
2. Include execution summary
3. Include metrics
4. Send via appropriate channel (HTTP/WS)
5. Log delivery
6. Update task memory
```

---

## 4. Timing Summary

| Stage | Min | Average | Max |
|-------|-----|---------|-----|
| 1. Receive | 1ms | 5ms | 10ms |
| 2. Normalize | 10ms | 30ms | 50ms |
| 3. Intent | 100ms | 200ms | 500ms |
| 4. Complexity | 50ms | 100ms | 200ms |
| 5. Dependencies | 50ms | 100ms | 200ms |
| 6. Decomposition | 200ms | 500ms | 2s |
| 7. Priority | 10ms | 30ms | 50ms |
| 8. Agent Selection | 50ms | 100ms | 200ms |
| 9. Resource Allocation | 50ms | 100ms | 200ms |
| 10. Execution | 1s | 30s | 4h |
| 11. Validation | 5s | 30s | 60s |
| 12. Aggregation | 100ms | 1s | 5s |
| 13. Final Review | 1s | 5s | 10s |
| 14. Delivery | 100ms | 500ms | 1s |
| **Total (simple)** | **2s** | **5s** | **10s** |
| **Total (complex)** | **30s** | **5min** | **4h** |
