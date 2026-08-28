# AIDA Tool Routing

**Document:** Book 2, Chapter 9 - Tool Routing
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

Tool Routing automatically selects the **optimal tool** for each task based on task requirements, tool capabilities, availability, and performance characteristics.

---

## 2. Routing Rules

### 2.1 Task-to-Tool Mapping

| Task Pattern | Primary Tool | Fallback Tool |
|--------------|-------------|---------------|
| Git analysis | Git Tool | CLI Tool |
| Repository search | Filesystem Tool | CLI Tool |
| Web search | Browser Tool | REST API Tool |
| Docker build | Docker Tool | CLI Tool |
| Code execution | Sandbox Tool | Terminal Tool |
| Database query | Database Tool | CLI Tool |
| File operations | Filesystem Tool | CLI Tool |
| Cloud operations | Cloud Tool | REST API Tool |
| MCP operations | MCP Tool | REST API Tool |

### 2.2 Routing Algorithm

```
1. Parse task requirements
   - Required capabilities
   - Input/output types
   - Resource constraints
   - Security requirements

2. Filter available tools
   - Has required capabilities
   - Is healthy
   - Has required permissions
   - Within resource limits

3. Score remaining tools
   - Capability match: 0.4
   - Performance score: 0.3
   - Reliability score: 0.2
   - Cost score: 0.1

4. Select top scorer
   - If score > 0.7: select
   - If score 0.5-0.7: select with monitoring
   - If score < 0.5: request human input
```

---

## 3. Routing Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| Capability Match | Match task capabilities to tool | Default |
| Performance | Select fastest tool | Time-critical |
| Reliability | Select most reliable tool | Critical tasks |
| Cost | Select cheapest tool | Cost-sensitive |
| Round Robin | Distribute across tools | Load balancing |
| Weighted | Custom weights per criterion | Specialized |

---

## 4. Fallback Chain

```
Primary Tool fails
       |
       v
Alternative Tool available?
  Yes -> Use Alternative
  No  -> Check Fallback Chain
       |
       v
Fallback Tool available?
  Yes -> Use Fallback
  No  -> Check Manual Override
       |
       v
Request Human Input
```

---

## 5. Configuration

```yaml
tool_routing:
  enabled: true
  strategy: capability_match
  fallback: manual_selection
  
  scoring:
    capability_match: 0.4
    performance: 0.3
    reliability: 0.2
    cost: 0.1
  
  thresholds:
    auto_select: 0.7
    monitor: 0.5
    human_required: 0.3
```
