# AIDA Semantic Code Graph

**Document:** Book 2, Chapter 10 - Semantic Code Graph
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Semantic Code Graph is a **unified knowledge representation** of the entire codebase. It captures function calls, dependencies, data flow, control flow, module relations, and API usage as a graph structure.

---

## 2. Graph Structure

### 2.1 Node Types

| Node Type | Properties | Example |
|-----------|------------|---------|
| File | path, language, size | src/auth.py |
| Class | name, parent, methods | UserService |
| Function | name, params, return_type | login() |
| Variable | name, type, scope | user_id |
| Module | name, exports | auth module |
| API | method, path, params | POST /api/login |
| Config | key, value | DATABASE_URL |

### 2.2 Edge Types

| Edge Type | From | To | Description |
|-----------|------|-----|-------------|
| calls | Function | Function | Function call |
| imports | File | Module | Import statement |
| inherits | Class | Class | Inheritance |
| uses | Function | Variable | Variable usage |
| provides | Module | API | API endpoint |
| depends_on | Module | Module | Dependency |
| contains | File | Class/Function | Containment |
| overrides | Class | Class | Method override |

---

## 3. Graph Construction

```
1. Parse all source files (AST)
2. Extract nodes (classes, functions, variables)
3. Extract edges (calls, imports, inherits)
4. Build graph data structure
5. Index nodes and edges
6. Compute graph metrics
```

---

## 4. Graph Metrics

| Metric | Description | Importance |
|--------|-------------|------------|
| Centrality | Most connected nodes | Key components |
| Coupling | Inter-module dependencies | Modularity |
| Cohesion | Intra-module connections | Module quality |
| Complexity | Graph density | Maintenance cost |
| Depth | Inheritance depth | Design quality |

---

## 5. Query Operations

| Query | Description | Example |
|-------|-------------|---------|
| Find callers | Who calls this function? | callers(login) |
| Find callees | What does this call? | callees(process) |
| Find path | Path between two nodes | path(A, B) |
| Find cycles | Circular dependencies | cycles() |
| Find roots | Entry points | roots() |
| Find leaves | Terminal nodes | leaves() |

---

## 6. Configuration

```yaml
semantic_code_graph:
  enabled: true
  auto_build: true
  incremental_update: true
  
  nodes: [file, class, function, variable, module, api, config]
  edges: [calls, imports, inherits, uses, provides, depends_on, contains]
  
  metrics:
    centrality: true
    coupling: true
    cohesion: true
```
