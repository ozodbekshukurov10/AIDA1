# AIDA Task Routing

**Document:** Book 2, Chapter 3 — Task Routing
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

Task Routing determines which agent and model should execute each task. It matches task requirements to agent capabilities, considers workload and availability, and selects the optimal combination for quality and performance.

---

## 2. Routing Architecture

### 2.1 Routing Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    TASK ROUTING PIPELINE                         │
│                                                                  │
│  Task Input                                                      │
│     │                                                            │
│     ↓                                                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Step 1: Task Analysis                                   │   │
│  │  - Task type detection                                    │   │
│  │  - Skill requirement extraction                          │   │
│  │  - Resource requirement estimation                       │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│     ↓                       │                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Step 2: Agent Matching                                  │   │
│  │  - Capability matching                                    │   │
│  │  - Availability check                                    │   │
│  │  - Workload assessment                                   │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│     ↓                       │                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Step 3: Model Selection                                 │   │
│  │  - Task-model compatibility                              │   │
│  │  - Performance requirements                              │   │
│  │  - Cost optimization                                     │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│     ↓                       │                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Step 4: Assignment                                      │   │
│  │  - Primary agent + model                                  │   │
│  │  - Fallback agent + model                                 │   │
│  │  - Resource allocation                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Output: RoutingDecision                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Agent Registry

### 3.1 Agent Capabilities

| Agent | Primary Skills | Task Types | Models |
|-------|---------------|------------|--------|
| `planner_agent` | Planning, architecture, estimation | planning, analysis | pro |
| `code_agent` | Programming, refactoring, debugging | coding, debugging | pro |
| `research_agent` | Web search, analysis, synthesis | research, analysis | pro, flash |
| `test_agent` | Testing, QA, test generation | testing | pro |
| `security_agent` | Security audit, vulnerability analysis | security | pro |
| `documentation_agent` | Technical writing, docs | documentation | flash |
| `monitoring_agent` | Monitoring, alerting, metrics | monitoring | flash |
| `deployment_agent` | CI/CD, deployment, DevOps | deployment | flash |
| `memory_agent` | Memory management, context | memory | flash |
| `debug_agent` | Debugging, error analysis | debugging | pro |

### 3.2 Agent Availability

```python
class AgentStatus:
    agent_id: str
    status: str  # available, busy, offline
    current_task: Optional[UUID]
    workload: float  # 0.0 - 1.0
    max_concurrent: int
    current_concurrent: int
    last_health_check: datetime
```

---

## 4. Task-Model Matching

### 4.1 Model Profiles

| Model | Context | Speed | Quality | Cost | Best For |
|-------|---------|-------|---------|------|----------|
| `pro` | 8192 tokens | Medium | High | High | Complex coding, reasoning |
| `flash` | 4096 tokens | Fast | Medium | Low | Simple tasks, classification |
| `low` | 4096 tokens | Slow | High | Low | Deep analysis, long context |

### 4.2 Task-Model Matrix

| Task Type | Primary Model | Fallback Model | Rationale |
|-----------|---------------|----------------|-----------|
| `code_generation` | pro | flash | Needs high quality code |
| `code_review` | pro | flash | Needs deep analysis |
| `debugging` | pro | flash | Needs reasoning |
| `planning` | pro | flash | Needs architecture thinking |
| `research` | pro | flash | Needs synthesis |
| `testing` | pro | flash | Needs test generation |
| `security` | pro | flash | Needs security knowledge |
| `documentation` | flash | pro | Simpler writing |
| `classification` | flash | pro | Simple classification |
| `summarization` | flash | pro | Simple summarization |
| `monitoring` | flash | pro | Simple monitoring |
| `deployment` | flash | pro | Simple deployment |

### 4.3 Model Selection Algorithm

```python
def select_model(task: Task, agents: list[Agent]) -> ModelAssignment:
    """Select optimal model for task."""
    
    # Get compatible models
    compatible = [
        model for model in self.models
        if model.supports_task_type(task.task_type)
        and model.context_window >= task.estimated_tokens
    ]
    
    # Score each model
    scored = []
    for model in compatible:
        score = 0.0
        
        # Quality score (0-40 points)
        score += model.quality_score * 0.4
        
        # Speed score (0-30 points)
        score += model.speed_score * 0.3
        
        # Cost score (0-20 points)
        score += (1.0 - model.cost_score) * 0.2
        
        # Availability score (0-10 points)
        score += model.availability_score * 0.1
        
        scored.append((model, score))
    
    # Sort by score
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return ModelAssignment(
        primary=scored[0][0],
        fallback=scored[1][0] if len(scored) > 1 else None
    )
```

---

## 5. Routing Strategies

### 5.1 Capability-Based Routing

```python
def capability_routing(task: Task) -> AgentAssignment:
    """Route based on task requirements and agent capabilities."""
    
    # Extract required skills
    required_skills = task.required_skills
    
    # Find agents with matching capabilities
    capable_agents = [
        agent for agent in self.agents
        if agent.has_skills(required_skills)
    ]
    
    if not capable_agents:
        raise NoAgentAvailableError(task.id)
    
    # Score agents
    scored = []
    for agent in capable_agents:
        score = self.score_agent(agent, task)
        scored.append((agent, score))
    
    # Select best agent
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return AgentAssignment(
        primary=scored[0][0],
        fallback=scored[1][0] if len(scored) > 1 else None
    )
```

### 5.2 Load-Balanced Routing

```python
def load_balanced_routing(task: Task) -> AgentAssignment:
    """Route to least loaded capable agent."""
    
    capable = self.get_capable_agents(task)
    
    # Sort by workload (ascending)
    capable.sort(key=lambda a: a.workload)
    
    return AgentAssignment(
        primary=capable[0],
        fallback=capable[1] if len(capable) > 1 else None
    )
```

### 5.3 Affinity-Based Routing

```python
def affinity_routing(task: Task) -> AgentAssignment:
    """Route based on historical performance."""
    
    capable = self.get_capable_agents(task)
    
    # Score by historical success rate
    scored = []
    for agent in capable:
        history = self.get_agent_history(agent.id, task.task_type)
        success_rate = history.success_rate if history else 0.5
        avg_duration = history.avg_duration if history else 300
        
        score = success_rate * 0.7 + (1.0 - min(avg_duration / 600, 1.0)) * 0.3
        scored.append((agent, score))
    
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return AgentAssignment(
        primary=scored[0][0],
        fallback=scored[1][0] if len(scored) > 1 else None
    )
```

### 5.4 Cost-Optimized Routing

```python
def cost_optimized_routing(task: Task) -> AgentAssignment:
    """Route to minimize cost while meeting quality requirements."""
    
    capable = self.get_capable_agents(task)
    
    # Score by cost efficiency
    scored = []
    for agent in capable:
        model = agent.preferred_model
        cost_per_token = model.cost_per_token
        quality = model.quality_score
        
        # Cost efficiency = quality / cost
        efficiency = quality / max(cost_per_token, 0.001)
        scored.append((agent, efficiency))
    
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return AgentAssignment(
        primary=scored[0][0],
        fallback=scored[1][0] if len(scored) > 1 else None
    )
```

---

## 6. Routing Configuration

### 6.1 Routing Rules

```yaml
routing_rules:
  # Task type → Agent mapping
  task_type_routing:
    planning:
      primary: planner_agent
      fallback: code_agent
      model: pro
      
    coding:
      primary: code_agent
      fallback: planner_agent
      model: pro
      
    debugging:
      primary: debug_agent
      fallback: code_agent
      model: pro
      
    research:
      primary: research_agent
      fallback: planner_agent
      model: pro
      
    testing:
      primary: test_agent
      fallback: code_agent
      model: pro
      
    security:
      primary: security_agent
      fallback: code_agent
      model: pro
      
    documentation:
      primary: documentation_agent
      fallback: code_agent
      model: flash
      
    monitoring:
      primary: monitoring_agent
      fallback: planner_agent
      model: flash
      
    deployment:
      primary: deployment_agent
      fallback: code_agent
      model: flash
      
    memory:
      primary: memory_agent
      fallback: planner_agent
      model: flash
```

### 6.2 Routing Strategy Selection

```yaml
routing_strategies:
  default: capability_based
  
  strategies:
    capability_based:
      description: Match task requirements to agent capabilities
      use_case: General purpose
      
    load_balanced:
      description: Distribute load evenly across agents
      use_case: High throughput scenarios
      
    affinity_based:
      description: Route based on historical performance
      use_case: Quality-critical tasks
      
    cost_optimized:
      description: Minimize cost while meeting quality
      use_case: Cost-sensitive workloads
```

---

## 7. Fallback Chain

### 7.1 Fallback Strategy

```
Primary Agent + Primary Model
    │
    ├── Fails? → Primary Agent + Fallback Model
    │              │
    │              ├── Fails? → Fallback Agent + Primary Model
    │              │              │
    │              │              ├── Fails? → Fallback Agent + Fallback Model
    │              │              │              │
    │              │              │              └── Fails? → Manual Review
    │              │              │
    │              │              └── Success → Return Result
    │              │
    │              └── Success → Return Result
    │
    └── Success → Return Result
```

### 7.2 Fallback Configuration

```yaml
fallback:
  enabled: true
  max_attempts: 4
  
  chain:
    - agent: primary
      model: primary
    - agent: primary
      model: fallback
    - agent: fallback
      model: primary
    - agent: fallback
      model: fallback
    
  escalation:
    after_max_attempts: manual_review
    alert_operator: true
```

---

## 8. Routing Metrics

### 8.1 Key Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Routing Accuracy | Correct agent/model selection | > 95% |
| First-Attempt Success | Success without fallback | > 90% |
| Average Routing Time | Time to make routing decision | < 100ms |
| Agent Utilization | Agent busy time / total time | 60-80% |
| Cost Efficiency | Quality achieved / cost incurred | Maximize |

### 8.2 Monitoring Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│                  TASK ROUTING DASHBOARD                           │
│                                                                  │
│  Agent Workload:                                                │
│  planner:      [██████░░░░] 60%  (3/5 tasks)                   │
│  code:         [████████░░] 80%  (4/5 tasks)                   │
│  research:     [████░░░░░░] 40%  (2/5 tasks)                   │
│  test:         [███░░░░░░░] 30%  (1.5/5 tasks)                 │
│  security:     [██░░░░░░░░] 20%  (1/5 tasks)                   │
│  documentation:[█░░░░░░░░░] 10%  (0.5/5 tasks)                 │
│                                                                  │
│  Routing Decisions (last hour):                                  │
│  Total: 156                                                     │
│  Primary agent: 142 (91%)                                       │
│  Fallback agent: 14 (9%)                                        │
│  Manual review: 0 (0%)                                          │
│                                                                  │
│  Model Distribution:                                            │
│  pro: 89 (57%)                                                  │
│  flash: 67 (43%)                                                │
│                                                                  │
│  Cost (last hour): $12.45                                       │
│  Avg cost per task: $0.08                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Configuration

```yaml
task_routing:
  # Default strategy
  default_strategy: capability_based
  
  # Agent selection
  agent_selection:
    max_workload: 0.9
    health_check_interval: 30s
    min_availability_score: 0.3
    
  # Model selection
  model_selection:
    prefer_quality: true
    max_cost_per_task: 0.50
    fallback_enabled: true
    
  # Fallback
  fallback:
    enabled: true
    max_attempts: 4
    escalate_after_max: true
    
  # Monitoring
  monitoring:
    enabled: true
    metrics_interval: 15s
    log_routing_decisions: true
```
