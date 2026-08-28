# AIDA Routing System

**Document:** Book 2, Chapter 1 — Routing System
**Version:** 1.0.0
**Date:** 2026-07-04

---

## Overview

The Routing System is the **decision engine** of the AI Kernel. It determines **which model**, **which agent**, and **which tools** should handle each task. All routing decisions are **declarative** (configuration-driven), not **imperative** (code-driven).

---

## 1. Model Routing

### 1.1 Architecture

```
Task → Capability Extractor → Model Filter → Model Scorer → Model Selector
                                          ↑
                                    Health Checker
                                          ↑
                                    Config Registry
```

### 1.2 Routing Decision Tree

```
Request
  │
  ├─ Has code? → code_generation capabilities
  │    ├─ Needs completion? → deepseek-coder (primary)
  │    ├─ Needs explanation? → qwen2.5 (primary)
  │    └─ Needs review? → gpt-4 (primary)
  │
  ├─ Has vision? → vision capabilities
  │    ├─ Image analysis? → gpt-4o (primary)
  │    ├─ OCR? → gemini-pro-vision (primary)
  │    └─ Diagram? → gpt-4o (primary)
  │
  ├─ Needs reasoning? → reasoning capabilities
  │    ├─ Math? → gpt-4 (primary)
  │    ├─ Logic? → deepseek-reasoner (primary)
  │    └─ Planning? → deepseek-reasoner (primary)
  │
  ├─ Conversation? → chat capabilities
  │    ├─ Quick answer? → qwen2.5-flash (primary)
  │    ├─ Detailed? → qwen2.5 (primary)
  │    └─ Creative? → gemini-pro (primary)
  │
  ├─ Needs embedding? → embedding capabilities
  │    └─ text-embedding-3-small (primary)
  │
  └─ Default → auto (Kernel selects best available)
```

### 1.3 Model Selection Algorithm

```python
def select_model(task: Task, context: ExecutionContext) -> ModelSelection:
    # Step 1: Extract required capabilities
    required_caps = extract_capabilities(task)
    
    # Step 2: Filter by capability
    candidates = filter_by_capability(required_caps)
    
    # Step 3: Filter by availability (health check)
    available = filter_by_health(candidates)
    
    # Step 4: Filter by user tier
    tier_allowed = filter_by_tier(available, context.user_tier)
    
    # Step 5: Score each candidate
    scored = []
    for model in tier_allowed:
        score = compute_score(model, task, context)
        scored.append((model, score))
    
    # Step 6: Sort by score (descending)
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # Step 7: Select top model + fallbacks
    primary = scored[0][0]
    fallbacks = [s[0] for s in scored[1:3]]
    
    return ModelSelection(
        primary=primary,
        fallbacks=fallbacks,
        config=get_model_config(primary, task)
    )
```

### 1.4 Scoring Formula

```
score = w1 × capability_match
      + w2 × health_score
      + w3 × speed_score
      + w4 × cost_efficiency
      + w5 × user_preference

Where:
  capability_match = len(matching_capabilities) / len(required_capabilities)
  health_score = success_rate_last_100_requests
  speed_score = 1 / (avg_latency / target_latency)
  cost_efficiency = 1 / (cost_per_1k_tokens / avg_cost)
  user_preference = 1.0 if preferred else 0.5
```

### 1.5 Model Configuration

```yaml
model_routing:
  rules:
    - match:
        task_type: code_generation
        sub_type: completion
      select:
        primary: deepseek-coder
        fallbacks: [qwen2.5-coder, gpt-4]
        config:
          temperature: 0.3
          max_tokens: 8192
          top_p: 0.95
          
    - match:
        task_type: code_generation
        sub_type: explanation
      select:
        primary: qwen2.5
        fallbacks: [gpt-4o, gemini-pro]
        config:
          temperature: 0.7
          max_tokens: 4096
          
    - match:
        task_type: vision
      select:
        primary: gpt-4o
        fallbacks: [gemini-pro-vision]
        config:
          max_tokens: 4096
          
    - match:
        task_type: embedding
      select:
        primary: text-embedding-3-small
        fallbacks: [bge-small]
        config:
          dimensions: 1536
```

---

## 2. Agent Routing

### 2.1 Architecture

```
Task → Capability Matcher → Agent Filter → Agent Scorer → Agent Selector
                                        ↑
                                  Agent Registry
```

### 2.2 Agent Capability Matrix

| Agent | Capabilities | Best For |
|-------|-------------|----------|
| Planner | planning, decomposition, estimation | Complex task breakdown |
| Code | code_generation, refactoring, review | Writing/modifying code |
| Debug | debugging, error_analysis, fixing | Finding/fixing bugs |
| Research | research, web_search, summarization | Information gathering |
| Test | test_generation, coverage_analysis | Writing tests |
| Security | security_audit, vulnerability_scan | Security review |
| Documentation | documentation, explanation, tutorial | Writing docs |
| Memory | knowledge_management, fact_retrieval | Knowledge operations |
| Monitoring | metrics, health_check, alerting | System monitoring |
| Deployment | deployment, docker, kubernetes | DevOps tasks |

### 2.3 Agent Selection Algorithm

```python
def select_agent(task: Task, plan: ExecutionPlan) -> AgentSelection:
    # Step 1: Determine required capabilities
    required_caps = plan.required_capabilities
    
    # Step 2: Find agents with matching capabilities
    candidates = registry.find_by_capabilities(required_caps)
    
    # Step 3: Filter by availability
    available = [a for a in candidates if a.health_status == HEALTHY]
    
    # Step 4: Score by capability match + success rate
    scored = []
    for agent in available:
        cap_score = len(set(required_caps) & set(agent.capabilities)) / len(required_caps)
        success_score = agent.success_rate
        score = 0.6 * cap_score + 0.4 * success_score
        scored.append((agent, score))
    
    # Step 5: Select best
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0] if scored else None
```

### 2.4 Agent Orchestration Patterns

**Pattern 1: Sequential**
```
Agent A → Agent B → Agent C → Result
```
Use: Linear workflows (research → plan → code)

**Pattern 2: Parallel**
```
Agent A ─┐
Agent B ─┼→ Merge → Result
Agent C ─┘
```
Use: Independent tasks (code + tests in parallel)

**Pattern 3: Fan-out / Fan-in**
```
        ┌→ Agent A₁ ─┐
Plan ───┼→ Agent A₂ ─┼→ Synthesize → Result
        └→ Agent A₃ ─┘
```
Use: Complex analysis (multiple perspectives)

**Pattern 4: Pipeline**
```
Agent A → Transform → Agent B → Transform → Agent C
```
Use: Data processing (extract → analyze → report)

**Pattern 5: Debate**
```
Agent A (FOR) ──┐
                ├→ Judge → Result
Agent B (AGAINST)┘
```
Use: Quality assurance (pros vs cons analysis)

**Pattern 6: Hierarchical**
```
Coordinator Agent
  ├→ Sub-Agent A
  ├→ Sub-Agent B
  └→ Sub-Agent C
```
Use: Complex projects (coordinator delegates)

### 2.5 Orchestration Configuration

```yaml
agent_routing:
  orchestration_patterns:
    full_project:
      pattern: hierarchical
      coordinator: planner
      sub_agents: [research, code, test, security, documentation]
      dependency: sequential
      
    code_review:
      pattern: parallel
      agents: [code, security, test]
      merge: weighted_average
      
    bug_fix:
      pattern: sequential
      agents: [debug, test, code]
      
    research:
      pattern: fan_out_fan_in
      fan_out: [web_search, academic_search, code_search]
      fan_in: synthesizer
```

---

## 3. Tool Routing

### 3.1 Architecture

```
Agent Request → Tool Matcher → Permission Check → Tool Selector → Executor
                                           ↑
                                     Tool Registry
                                           ↑
                                     Sandbox Manager
```

### 3.2 Tool Capability Matrix

| Tool | Capabilities | Sandbox | Permissions |
|------|-------------|---------|-------------|
| git | version_control, diff, log, blame | none | read, write |
| github | pull_request, issue, code_review | none | read, write |
| python | code_execution, data_analysis | docker | execute |
| docker | container_management | host | execute |
| browser | web_browsing, screenshot | docker | network |
| filesystem | file_read, file_write | chroot | read, write |
| database | query, schema, migrate | readonly | read |
| terminal | command_execution | docker | execute |
| rest_api | http_request, api_call | none | network |

### 3.3 Tool Selection Algorithm

```python
def select_tools(agent: Agent, task: Task) -> list[ToolSelection]:
    # Step 1: Get agent's required tools
    required_tools = agent.required_tools
    
    # Step 2: Filter by availability
    available = [t for t in required_tools if registry.is_available(t)]
    
    # Step 3: Check permissions
    permitted = [t for t in available if check_permissions(t, agent)]
    
    # Step 4: Configure sandbox
    selections = []
    for tool in permitted:
        sandbox = sandbox_manager.get_config(tool)
        selections.append(ToolSelection(
            tool=tool,
            sandbox=sandbox,
            timeout=tool.default_timeout
        ))
    
    return selections
```

### 3.4 Tool Configuration

```yaml
tool_routing:
  tools:
    git:
      executable: /usr/bin/git
      sandbox: none
      permissions: [read, write]
      timeout: 30s
      
    python:
      executable: python3
      sandbox:
        type: docker
        image: python:3.14-slim
        network: none
        volumes:
          - /tmp/sandbox:/workspace
      permissions: [execute]
      timeout: 60s
      max_memory: 512MB
      max_cpu: 1.0
      
    database:
      type: readonly
      connection: sqlite:///aida.db
      permissions: [read]
      timeout: 10s
      max_rows: 1000
      
    browser:
      sandbox:
        type: docker
        image: chromium:latest
        network: allowed
        domains: [github.com, docs.python.org]
      permissions: [network]
      timeout: 60s
```

---

## 4. Routing Rules Engine

### 4.1 Rule Format

All routing rules follow a unified format:

```yaml
routing_rule:
  name: rule_name
  priority: 100
  
  match:
    # Conditions (ALL must match)
    task_type: code_generation
    sub_type: completion
    user_tier: [premium, enterprise]
    capabilities_required: [code, function_calling]
    
  select:
    # Selection strategy
    strategy: capability_match
    
    # Candidates
    candidates:
      - id: deepseek-coder
        priority: 1
        config:
          temperature: 0.3
          
      - id: qwen2.5-coder
        priority: 2
        config:
          temperature: 0.5
          
    # Fallback
    fallback:
      - id: gpt-4
        config:
          temperature: 0.5
          
  # Constraints
  constraints:
    max_cost_per_request: 0.10
    max_latency_ms: 30000
    require_availability: true
```

### 4.2 Rule Evaluation

```python
def evaluate_rules(task: Task, context: ExecutionContext) -> RoutingDecision:
    # Get all matching rules (sorted by priority)
    matching_rules = [
        rule for rule in all_rules
        if rule.matches(task, context)
    ]
    matching_rules.sort(key=lambda r: r.priority)
    
    # Apply first matching rule
    if matching_rules:
        return matching_rules[0].select(task, context)
    
    # Default routing
    return default_routing(task, context)
```

### 4.3 Rule hot-reloading

Routing rules can be updated without restarting the Kernel:

```
Config File Change → File Watcher → Rule Parser → Rule Validator → Registry Update → Hot Reload
```

---

## 5. Health-Aware Routing

### 5.1 Health Check System

```python
class HealthChecker:
    """Checks health of all registered modules."""
    
    async def check_model(model_id: str) -> HealthStatus:
        # Try a minimal request
        start = time.time()
        try:
            await model.ping()
            latency = time.time() - start
            return HealthStatus(
                status="healthy",
                latency_ms=latency * 1000,
                last_check=datetime.now()
            )
        except Exception as e:
            return HealthStatus(
                status="unhealthy",
                error=str(e),
                last_check=datetime.now()
            )
```

### 5.2 Health Status Levels

| Status | Criteria | Action |
|--------|----------|--------|
| HEALTHY | success_rate > 95%, latency < target | Use normally |
| DEGRADED | success_rate > 80%, latency < 2×target | Use with caution |
| UNHEALTHY | success_rate ≤ 80% OR latency > 2×target | Skip, use fallback |
| DOWN | Connection failed OR timeout | Skip, alert SRE |

### 5.3 Health Cache

```
Health check results cached for 30 seconds:
  - Avoids hammering providers with health checks
  - Fresh enough to detect issues quickly
  - Configurable per provider
```

---

## 6. Fallback Strategy

### 6.1 Fallback Chain

```
Primary Model
  ↓ (failure)
Fallback Model 1
  ↓ (failure)
Fallback Model 2
  ↓ (failure)
Local Model (rule-based)
  ↓ (failure)
Error Response
```

### 6.2 Fallback Rules

| Error Type | Fallback Strategy |
|------------|-------------------|
| Model timeout | Try next model in chain |
| Model rate limit | Try next model (different provider) |
| Model unavailable | Try next model |
| All models down | Use local rule-based response |
| Network error | Retry with backoff, then fallback |

### 6.3 Cost-Aware Fallback

```yaml
fallback_strategy:
  # Prefer same capability, lower cost
  cost_aware: true
  
  # Maximum cost increase for fallback
  max_cost_multiplier: 3.0
  
  # Example chain:
  # DeepSeek ($0.001/1k) → Qwen Local ($0) → GPT-4 ($0.03/1k)
  # Fallback stops at Qwen (cost increase > 3×)
```

---

## 7. Routing Observability

### 7.1 Metrics

```yaml
routing_metrics:
  model_selection:
    - aida_routing_model_selection_total (counter, labels: model, task_type)
    - aida_routing_model_fallback_total (counter, labels: from_model, to_model, reason)
    - aida_routing_model_health_status (gauge, labels: model, status)
    
  agent_selection:
    - aida_routing_agent_selection_total (counter, labels: agent, task_type)
    - aida_routing_agent_fallback_total (counter, labels: from_agent, to_agent)
    
  tool_selection:
    - aida_routing_tool_selection_total (counter, labels: tool, agent)
    - aida_routing_tool_unavailable_total (counter, labels: tool, reason)
```

### 7.2 Tracing

Every routing decision is traced:
```
Span: model_routing
  Attributes:
    task_type: code_generation
    required_capabilities: [code, function_calling]
    candidates_evaluated: 5
    selected_model: deepseek-coder
    fallback_models: [qwen2.5-coder, gpt-4]
    selection_latency_ms: 15
    health_check_cached: true
```

---

## 8. Configuration Hot-Reload

### 8.1 Reload Flow

```
Config File Change
  → FileWatcher detects change
  → Parse YAML
  → Validate schema
  → Diff with current config
  → Apply changes (atomic swap)
  → Emit ConfigReloaded event
  → Log change
```

### 8.2 Atomic Config Swap

```python
class ConfigManager:
    """Thread-safe configuration management."""
    
    def __init__(self):
        self._config = AtomicReference(initial_config)
    
    def get_config(self) -> Config:
        return self._config.get()
    
    def reload(self, new_config: Config):
        old = self._config.get()
        self._config.set(new_config)
        logger.info("Config reloaded", diff=diff(old, new_config))
```

---

## 9. Future: AGI-Ready Routing

### 9.1 Self-Improving Routing

The routing system will eventually support:
- **Reinforcement learning:** Learn optimal routing from user feedback
- **A/B testing:** Automatically test new models/agents
- **Cost optimization:** Dynamically adjust routing based on cost/quality tradeoffs
- **Capability discovery:** Auto-discover new capabilities from module descriptors

### 9.2 Dynamic Capability Discovery

```yaml
# Future: Modules register capabilities at runtime
capability_discovery:
  enabled: true
  scan_interval: 300s
  auto_register: true
  require_approval: false
```
