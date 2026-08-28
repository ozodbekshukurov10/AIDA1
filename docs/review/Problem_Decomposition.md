# AIDA Problem Decomposition

**Document:** Book 2, Chapter 8 - Problem Decomposition
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

Problem Decomposition breaks complex goals into manageable components through a **7-level hierarchy**: Goal, Objectives, Modules, Tasks, Subtasks, Dependencies, and Validation Rules.

---

## 2. Decomposition Hierarchy

### 2.1 Seven Levels

```
Level 1: GOAL
  The high-level objective from the user
  Example: "Build authentication system"

Level 2: OBJECTIVES
  Measurable outcomes that achieve the goal
  Example: "User registration, login, logout, password reset"

Level 3: MODULES
  Logical components that implement objectives
  Example: "User model, Auth views, JWT service, Password service"

Level 4: TASKS
  Specific work items within modules
  Example: "Create User model with email field"

Level 5: SUBTASKS
  Granular steps within tasks
  Example: "Define fields, add validators, create migration"

Level 6: DEPENDENCIES
  Order and relationships between items
  Example: "User model must exist before Auth views"

Level 7: VALIDATION RULES
  Acceptance criteria for each level
  Example: "Email field must be unique, migration must succeed"
```

---

## 3. Decomposition Process

### 3.1 Algorithm

```
1. Parse Goal (Level 1)
   - Identify main objective
   - Extract constraints
   - Set success criteria

2. Generate Objectives (Level 2)
   - Break goal into measurable outcomes
   - Ensure each objective is SMART
   - Prioritize by importance

3. Identify Modules (Level 3)
   - Map objectives to logical components
   - Define module boundaries
   - Identify module interfaces

4. Create Tasks (Level 4)
   - Break modules into specific tasks
   - Estimate effort per task
   - Assign to agents if applicable

5. Define Subtasks (Level 5)
   - Break tasks into actionable steps
   - Ensure atomic (one action per subtask)
   - Estimate time per subtask

6. Map Dependencies (Level 6)
   - Identify blocking relationships
   - Create DAG (directed acyclic graph)
   - Find critical path

7. Set Validation Rules (Level 7)
   - Define acceptance criteria per level
   - Create test cases
   - Set quality gates
```

---

## 4. Decomposition Example

### 4.1 Goal: "Fix authentication bug"

```
GOAL: Fix authentication bug
|
+-- OBJECTIVES:
    |-- O1: Identify root cause
    |-- O2: Implement fix
    |-- O3: Verify fix works
    |-- O4: Prevent regression
|
+-- MODULES:
    |-- M1: Debug module
    |   +-- T1: Reproduce bug
    |   +-- T2: Analyze logs
    |   +-- T3: Identify root cause
    |-- M2: Fix module
    |   +-- T4: Implement fix
    |   +-- T5: Write tests
    |-- M3: Verification module
        +-- T6: Run existing tests
        +-- T7: Run new tests
        +-- T8: Manual verification
|
+-- DEPENDENCIES:
    |-- T1 -> T2 -> T3 (sequential)
    |-- T3 -> T4 (blocking)
    |-- T4 -> T5 (sequential)
    |-- T5 -> T6, T7, T8 (parallel)
|
+-- VALIDATION:
    |-- V1: Bug reproduced in test
    |-- V2: Root cause identified with evidence
    |-- V3: Fix passes all tests
    |-- V4: No regressions detected
```

---

## 5. Validation Rules

### 5.1 Rule Types

| Type | Description | Example |
|------|-------------|---------|
| Functional | Feature works correctly | Login returns JWT |
| Non-functional | Performance, security | Response < 200ms |
| Structural | Code quality | No lint errors |
| Integration | Components work together | API + DB connected |
| Regression | Existing features work | Old tests pass |

---

## 6. Configuration

```yaml
problem_decomposition:
  enabled: true
  
  levels:
    - goal
    - objectives
    - modules
    - tasks
    - subtasks
    - dependencies
    - validation
  
  task_estimation:
    enabled: true
    unit: minutes
    min: 5
    max: 480
  
  dependencies:
    auto_detect: true
    validate_dag: true
    find_critical_path: true
```
