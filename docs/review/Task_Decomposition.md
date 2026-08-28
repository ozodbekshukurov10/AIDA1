# AIDA Task Decomposition

**Document:** Book 2, Chapter 3 — Task Decomposition
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

Task Decomposition is the process of breaking complex user requests into manageable, atomic subtasks. The decomposition engine uses AI-powered analysis to create optimal task hierarchies that minimize dependencies and maximize parallelism.

---

## 2. Decomposition Hierarchy

### 2.1 Level Definitions

```
Level 0: Epic
  ├── Major feature or project
  ├── Duration: days to weeks
  └── Example: "Build user authentication system"

Level 1: Feature
  ├── Specific capability within epic
  ├── Duration: hours to days
  └── Example: "User registration with email verification"

Level 2: Module
  ├── Functional unit within feature
  ├── Duration: 1-4 hours
  └── Example: "Email verification service"

Level 3: Component
  ├── Smaller unit within module
  ├── Duration: 30 min — 2 hours
  └── Example: "Send verification email"

Level 4: Task
  ├── Atomic work item
  ├── Duration: 15 min — 1 hour
  └── Example: "Create email template"

Level 5: Subtask
  ├── Step within task
  ├── Duration: 5-15 min
  └── Example: "Design email header"

Level 6: Action
  ├── Single operation
  ├── Duration: 1-5 min
  └── Example: "Add logo to header"
```

### 2.2 Hierarchy Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECOMPOSITION HIERARCHY                       │
│                                                                  │
│  Level 0: EPIC                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Build User Authentication System                        │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│  Level 1: FEATURE           │                                    │
│  ┌──────────────────────┐   │   ┌──────────────────────┐        │
│  │  User Registration   │   │   │  User Login          │        │
│  └──────────┬───────────┘   │   └──────────┬───────────┘        │
│             │               │              │                     │
│  Level 2: MODULE           │              │                     │
│  ┌────────────────┐        │   ┌────────────────┐               │
│  │  Email Service │        │   │  JWT Service   │               │
│  └───────┬────────┘        │   └───────┬────────┘               │
│          │                 │           │                         │
│  Level 3: COMPONENT        │           │                         │
│  ┌────────────────┐        │   ┌────────────────┐               │
│  │  Send Email    │        │   │  Token Generate│               │
│  └───────┬────────┘        │   └───────┬────────┘               │
│          │                 │           │                         │
│  Level 4: TASK             │           │                         │
│  ┌────────────────┐        │   ┌────────────────┐               │
│  │  Create Template│       │   │  Token Validate│               │
│  └───────┬────────┘        │   └───────┬────────┘               │
│          │                 │           │                         │
│  Level 5: SUBTASK          │           │                         │
│  ┌────────────────┐        │   ┌────────────────┐               │
│  │  Design Header │        │   │  Parse JWT     │               │
│  └───────┬────────┘        │   └────────────────┘               │
│          │                 │                                     │
│  Level 6: ACTION           │                                     │
│  ┌────────────────┐        │                                     │
│  │  Add Logo      │        │                                     │
│  └────────────────┘        │                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Decomposition Rules

### 3.1 Core Rules

| # | Rule | Description | Violation Example |
|---|------|-------------|-------------------|
| 1 | **Single Responsibility** | Each task does exactly one thing | "Create user system and add login" |
| 2 | **Estimable** | Task duration can be estimated | "Fix everything" |
| 3 | **Testable** | Task has clear completion criteria | "Make it better" |
| 4 | **Independent** | Minimize dependencies between tasks | Circular dependencies |
| 5 | **Right-Sized** | 15 min — 4 hours per task | 1 minute or 3 day tasks |
| 6 | **Complete** | Task description is self-contained | "Do the thing" |
| 7 | **Acceptable** | Task has acceptance criteria | "Write code" |

### 3.2 Size Guidelines

| Duration | Level | Example |
|----------|-------|---------|
| 1-5 min | Action | "Add import statement" |
| 5-15 min | Subtask | "Create function signature" |
| 15-60 min | Task | "Implement function logic" |
| 1-4 hours | Component | "Create API endpoint" |
| 4-8 hours | Module | "Create service layer" |
| 8-40 hours | Feature | "Create user registration" |
| 40+ hours | Epic | "Build auth system" |

---

## 4. Decomposition Strategies

### 4.1 Vertical Decomposition (Feature-Based)

```
User Request: "Create user registration"

Feature: User Registration
├── Task: Design registration form
│   ├── Subtask: Create form layout
│   ├── Subtask: Add form fields
│   └── Subtask: Add validation
├── Task: Create registration API
│   ├── Subtask: Create endpoint
│   ├── Subtask: Add validation
│   └── Subtask: Add error handling
├── Task: Create email service
│   ├── Subtask: Create email template
│   ├── Subtask: Send verification email
│   └── Subtask: Verify email
└── Task: Add tests
    ├── Subtask: Unit tests
    └── Subtask: Integration tests
```

### 4.2 Horizontal Decomposition (Layer-Based)

```
User Request: "Create user registration"

Layer: Data
├── Task: Create User model
├── Task: Create migration
└── Task: Create repository

Layer: Business Logic
├── Task: Create registration service
├── Task: Create validation service
└── Task: Create email service

Layer: API
├── Task: Create registration endpoint
├── Task: Add serialization
└── Task: Add error handling

Layer: Frontend
├── Task: Create registration form
├── Task: Add form validation
└── Task: Add success message

Layer: Testing
├── Task: Unit tests
├── Task: Integration tests
└── Task: E2E tests
```

### 4.3 Priority-Based Decomposition

```
User Request: "Create user registration"

Phase 1: MVP (Minimum Viable Product)
├── Task: Create User model (MUST)
├── Task: Create registration API (MUST)
└── Task: Create basic form (MUST)

Phase 2: Core Features
├── Task: Add email verification (SHOULD)
├── Task: Add form validation (SHOULD)
└── Task: Add error handling (SHOULD)

Phase 3: Enhanced Features
├── Task: Add password strength check (COULD)
├── Task: Add rate limiting (COULD)
└── Task: Add analytics (COULD)
```

---

## 5. Decomposition Algorithm

### 5.1 AI-Powered Decomposition

```python
class TaskDecomposer:
    async def decompose(self, request: UserRequest) -> TaskTree:
        # Step 1: Analyze request
        analysis = await self.analyze_request(request)
        
        # Step 2: Determine decomposition strategy
        strategy = self.select_strategy(analysis)
        
        # Step 3: Generate task tree
        tree = await self.generate_tree(analysis, strategy)
        
        # Step 4: Validate tree
        validated = self.validate_tree(tree)
        
        # Step 5: Optimize tree
        optimized = self.optimize_tree(validated)
        
        return optimized
    
    def select_strategy(self, analysis: RequestAnalysis) -> str:
        if analysis.complexity == "simple":
            return "vertical"
        elif analysis.complexity == "medium":
            return "vertical"
        elif analysis.complexity == "complex":
            return "horizontal"
        else:
            return "priority_based"
```

### 5.2 Decomposition Prompt

```python
DECOMPOSITION_PROMPT = """
Analyze the following user request and decompose it into tasks.

User Request: {request}

Context:
- Programming Language: {language}
- Framework: {framework}
- Repository: {repository}
- Complexity: {complexity}

Rules:
1. Each task must have a single responsibility
2. Each task must be estimable (15 min — 4 hours)
3. Each task must have clear completion criteria
4. Minimize dependencies between tasks
5. Maximize parallelism opportunities

Output Format:
{{
  "epic": {{
    "title": "Epic title",
    "description": "Epic description"
  }},
  "features": [
    {{
      "title": "Feature title",
      "description": "Feature description",
      "tasks": [
        {{
          "title": "Task title",
          "description": "Task description",
          "type": "coding|testing|documentation|research",
          "estimated_duration": "30m",
          "acceptance_criteria": ["criterion1", "criterion2"],
          "dependencies": ["task_id_1", "task_id_2"]
        }}
      ]
    }}
  ]
}}
"""
```

---

## 6. Task Template

### 6.1 Task Object

```python
@dataclass
class Task:
    id: UUID
    title: str
    description: str
    task_type: TaskType
    
    # Hierarchy
    parent_id: Optional[UUID]
    children: list[UUID]
    depth: int
    
    # Classification
    priority: int
    complexity: str
    
    # Dependencies
    depends_on: list[UUID]
    blocks: list[UUID]
    
    # Assignment
    assigned_agent: Optional[str]
    assigned_model: Optional[str]
    
    # Resources
    estimated_duration: int  # seconds
    estimated_cpu: float
    estimated_memory_mb: int
    
    # Acceptance Criteria
    acceptance_criteria: list[str]
    
    # Status
    status: TaskStatus
    progress: float  # 0.0 - 1.0
    
    # Timestamps
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
```

### 6.2 Task Types

| Type | Description | Required Skills |
|------|-------------|-----------------|
| `coding` | Write/modify code | Programming, architecture |
| `testing` | Write/run tests | Testing, QA |
| `research` | Gather information | Analysis, web search |
| `analysis` | Analyze code/data | Code review, metrics |
| `documentation` | Write docs | Technical writing |
| `planning` | Plan approach | Architecture, estimation |
| `security` | Security review | Security, OWASP |
| `deployment` | Deploy/release | DevOps, CI/CD |
| `debugging` | Fix errors | Debugging, analysis |
| `design` | Design UI/UX | Design, UX |

---

## 7. Decomposition Examples

### 7.1 Example 1: Simple Task

```
User Request: "Fix the login bug"

Decomposition:
Task: Fix Login Bug
├── Task: Identify bug cause
│   ├── Type: debugging
│   ├── Duration: 15 min
│   └── Acceptance: Bug root cause identified
├── Task: Implement fix
│   ├── Type: coding
│   ├── Duration: 30 min
│   ├── Depends on: "Identify bug cause"
│   └── Acceptance: Fix implemented
├── Task: Test fix
│   ├── Type: testing
│   ├── Duration: 15 min
│   ├── Depends on: "Implement fix"
│   └── Acceptance: Tests pass
└── Task: Deploy fix
    ├── Type: deployment
    ├── Duration: 10 min
    ├── Depends on: "Test fix"
    └── Acceptance: Fix deployed
```

### 7.2 Example 2: Complex Task

```
User Request: "Create a real-time chat application"

Decomposition:
Epic: Real-Time Chat Application
├── Feature: User Authentication
│   ├── Task: Create User model
│   ├── Task: Create registration API
│   ├── Task: Create login API
│   ├── Task: Create JWT service
│   ├── Task: Create auth middleware
│   └── Task: Add tests
├── Feature: Chat Rooms
│   ├── Task: Create Room model
│   ├── Task: Create room API
│   ├── Task: Create room management
│   └── Task: Add tests
├── Feature: Real-Time Messaging
│   ├── Task: Create WebSocket service
│   ├── Task: Create message model
│   ├── Task: Create message API
│   ├── Task: Create real-time handler
│   └── Task: Add tests
├── Feature: UI
│   ├── Task: Create chat layout
│   ├── Task: Create room list
│   ├── Task: Create message list
│   ├── Task: Create message input
│   └── Task: Add responsive design
└── Feature: Deployment
    ├── Task: Create Docker config
    ├── Task: Create CI/CD pipeline
    ├── Task: Deploy to production
    └── Task: Monitor deployment
```

---

## 8. Optimization Rules

### 8.1 Parallelism Optimization

```python
def optimize_parallelism(tree: TaskTree) -> TaskTree:
    """Optimize task tree for maximum parallelism."""
    
    for task in tree.all_tasks():
        # Find tasks that can run in parallel
        independent = find_independent_tasks(task, tree)
        
        if len(independent) > 1:
            # Create parallel group
            parallel_group = ParallelGroup(
                tasks=independent,
                strategy="parallel"
            )
            tree.add_group(parallel_group)
    
    return tree
```

### 8.2 Dependency Minimization

```python
def minimize_dependencies(tree: TaskTree) -> TaskTree:
    """Minimize dependencies between tasks."""
    
    for task in tree.all_tasks():
        unnecessary = []
        
        for dep_id in task.depends_on:
            dep = tree.get_task(dep_id)
            
            # Check if dependency is truly necessary
            if not is_truly_necessary(task, dep, tree):
                unnecessary.append(dep_id)
        
        # Remove unnecessary dependencies
        for dep_id in unnecessary:
            task.depends_on.remove(dep_id)
    
    return tree
```

---

## 9. Validation Rules

```yaml
decomposition_validation:
  hierarchy:
    - max_depth: 7
    - min_tasks_per_level: 1
    - max_tasks_per_level: 20
    
  task_size:
    - min_duration: 300  # 5 min
    - max_duration: 14400  # 4 hours
    
  dependencies:
    - no_circular_dependencies: true
    - max_dependencies_per_task: 10
    - no_self_dependencies: true
    
  completeness:
    - all_tasks_have_acceptance_criteria: true
    - all_tasks_have_estimates: true
    - all_tasks_have_types: true
```
