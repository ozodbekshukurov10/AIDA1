# AIDA Code Search

**Document:** Book 2, Chapter 10 - Code Search
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

Code Search provides **7 search modes**: semantic search, symbol search, reference search, implementation search, usage search, regex search, and natural language search across the entire codebase.

---

## 2. Search Modes

| Mode | Description | Input | Use Case |
|------|-------------|-------|----------|
| Semantic | Find similar code | Code snippet | Find related code |
| Symbol | Find by symbol name | Function/class name | Direct lookup |
| Reference | Find all references | Symbol name | Impact analysis |
| Implementation | Find implementations | Interface name | Find concrete code |
| Usage | Find usage patterns | API/feature name | Usage examples |
| Regex | Pattern matching | Regex pattern | Flexible search |
| Natural Language | English description | Natural language query | Intuitive search |

---

## 3. Search Pipeline

```
Search Query
     |
     v
+---------------------+
| Query Parser        |
| - Detect mode       |
| - Parse query       |
+----------+----------+
           |
           v
+---------------------+
| Index Query         |
| - Symbol index      |
| - Semantic index    |
| - Regex index       |
+----------+----------+
           |
           v
+---------------------+
| Result Ranker       |
| - Relevance score   |
| - File distance     |
+----------+----------+
           |
           v
Ranked Results
```

---

## 4. Search Index

| Index | Content | Update |
|-------|---------|--------|
| Symbol Index | All symbols (classes, functions, variables) | On change |
| Semantic Index | Code embeddings | On change |
| Reference Index | All references | On change |
| Usage Index | API usage patterns | On change |

---

## 5. Ranking Algorithm

```
Score = relevance * 0.5 + recency * 0.2 + proximity * 0.2 + importance * 0.1

Where:
  relevance = match quality (0-1)
  recency = file modification time (0-1)
  proximity = distance from query context (0-1)
  importance = symbol centrality (0-1)
```

---

## 6. Configuration

```yaml
code_search:
  enabled: true
  modes: [semantic, symbol, reference, implementation, usage, regex, natural_language]
  max_results: 50
  indexing:
    auto_update: true
    semantic_embeddings: true
  ranking:
    relevance: 0.5
    recency: 0.2
    proximity: 0.2
    importance: 0.1
```
