# AIDA Context Engine

**Document:** Book 2, Chapter 6 — Context Engine
**Version:** 1.0.0
**Date:** 2026-07-04
**Author:** Principal AI Memory Architect / Cognitive Systems Engineer

---

## 1. Vision

The Context Engine is the **long-term memory** of AIDA. It collects, normalizes, classifies, ranks, compresses, stores, retrieves, updates, archives, and deletes context from all sources. It provides the AI Kernel and Agents with the most relevant context in milliseconds.

### 1.1 Core Principles

| Principle | Description |
|-----------|-------------|
| **Automatic Collection** | Context gathered without human intervention |
| **Intelligent Ranking** | Most relevant context delivered first |
| **Efficient Compression** | Context fits within token limits |
| **Fast Retrieval** | Millisecond-level context retrieval |
| **Secure Access** | Context protected by access control |
| **Scalable** | Handles millions of context items |
| **Extensible** | Supports new context types |

---

## 2. Architecture Overview

### 2.1 Layer Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CONTEXT SOURCES                                   │
│                                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │  User    │ │Repository│ │  Agent   │ │  Task    │ │  System  │  │
│  │ Context  │ │ Context  │ │ Context  │ │ Context  │ │ Context  │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       │            │            │            │            │          │
└───────┼────────────┼────────────┼────────────┼────────────┼──────────┘
        │            │            │            │            │
        ↓            ↓            ↓            ↓            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    CONTEXT ENGINE CORE                               │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Context    │  │   Context    │  │   Context    │              │
│  │  Collector   │→ │  Classifier  │→ │   Ranker     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│         ↓                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Context    │  │   Context    │  │   Context    │              │
│  │  Compressor  │→ │   Store      │→ │  Retriever   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│         ↓                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Context    │  │   Context    │  │   Context    │              │
│  │  Updater     │→ │  Archiver    │→ │  Deleter     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    CONTEXT STORAGE                                   │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │  Redis   │  │PostgreSQL│  │  Vector  │  │    S3    │            │
│  │ (Cache)  │  │ (Meta)   │  │   (EMB)  │  │  (Raw)   │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    CONTEXT CONSUMERS                                 │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │   AI     │  │  Agent   │  │ Workflow │  │  RAG     │            │
│  │  Kernel  │  │ Manager  │  │  Engine  │  │  Engine  │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Relationship

```
ContextEngine
  ├── uses → ContextCollector (gather context from sources)
  ├── uses → ContextClassifier (classify context type)
  ├── uses → ContextRanker (rank by relevance)
  ├── uses → ContextCompressor (fit within token limits)
  ├── uses → ContextStore (persist context)
  ├── uses → ContextRetriever (retrieve relevant context)
  ├── uses → ContextUpdater (update existing context)
  ├── uses → ContextArchiver (archive old context)
  └── uses → ContextDeleter (delete expired context)

ContextStore
  ├── uses → RedisCache (fast cache)
  ├── uses → PostgreSQLMeta (metadata storage)
  ├── uses → VectorDB (embedding storage)
  └── uses → S3Raw (raw content storage)
```

---

## 3. Context Types

### 3.1 Context Categories

| Category | Description | Sources |
|----------|-------------|---------|
| `global` | System-wide context | Config, features, limits |
| `session` | Current session context | Session state, preferences |
| `conversation` | Current conversation | Messages, turns, topics |
| `repository` | Repository context | Code, docs, structure |
| `task` | Current task context | Task state, results |
| `workflow` | Current workflow | Steps, decisions, progress |
| `agent` | Agent context | Agent state, capabilities |
| `plugin` | Plugin context | Plugin state, config |
| `system` | System context | Health, metrics, alerts |

---

## 4. Context Lifecycle

### 4.1 Lifecycle Stages

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CONTEXT LIFECYCLE                                  │
│                                                                      │
│  1. Collect                                                          │
│     ↓                                                                │
│  2. Normalize                                                        │
│     ↓                                                                │
│  3. Classify                                                         │
│     ↓                                                                │
│  4. Rank                                                             │
│     ↓                                                                │
│  5. Compress                                                         │
│     ↓                                                                │
│  6. Store                                                            │
│     ↓                                                                │
│  7. Retrieve                                                         │
│     ↓                                                                │
│  8. Update                                                           │
│     ↓                                                                │
│  9. Archive                                                          │
│     ↓                                                                │
│  10. Delete                                                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Stage Details

| Stage | Description | Duration |
|-------|-------------|----------|
| Collect | Gather context from sources | < 100ms |
| Normalize | Standardize format | < 10ms |
| Classify | Determine context type | < 10ms |
| Rank | Score relevance | < 50ms |
| Compress | Fit within token limits | < 20ms |
| Store | Persist to storage | < 50ms |
| Retrieve | Find relevant context | < 100ms |
| Update | Refresh existing context | < 50ms |
| Archive | Move to cold storage | < 100ms |
| Delete | Remove expired context | < 50ms |

---

## 5. Context Retrieval

### 5.1 Retrieval Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `most_relevant` | Highest relevance score | General queries |
| `most_recent` | Newest context first | Recent events |
| `highest_priority` | Highest priority first | Critical tasks |
| `semantic_similarity` | Vector similarity | Similar content |
| `task_dependency` | Related to current task | Task context |
| `user_preference` | User's preferred context | Personalized |
| `repository_match` | Repository-specific | Code context |

### 5.2 Retrieval Flow

```
Context Request
    │
    ├── Parse request
    │   ├── Query text
    │   ├── Context type
    │   ├── Max items
    │   └── Token budget
    │
    ├── Search context
    │   ├── Cache lookup (Redis)
    │   ├── Metadata search (PostgreSQL)
    │   ├── Vector search (VectorDB)
    │   └── Hybrid search
    │
    ├── Rank results
    │   ├── Relevance score
    │   ├── Recency score
    │   ├── Priority score
    │   └── Combined score
    │
    ├── Compress results
    │   ├── Truncate if needed
    │   ├── Summarize if needed
    │   └── Fit within token budget
    │
    └── Return context
```

---

## 6. Context Ranking

### 6.1 Ranking Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| `relevance` | 0.35 | Semantic similarity to query |
| `recency` | 0.25 | How recent the context is |
| `priority` | 0.20 | Assigned priority level |
| `frequency` | 0.10 | How often context is used |
| `user_preference` | 0.10 | User's preference score |

### 6.2 Ranking Algorithm

```python
def rank_context(
    context: Context,
    query: str,
    user_preferences: dict
) -> float:
    """Calculate context ranking score."""
    
    # Relevance (semantic similarity)
    relevance = cosine_similarity(
        context.embedding,
        encode(query)
    )
    
    # Recency (exponential decay)
    age_hours = (now() - context.created_at).total_seconds() / 3600
    recency = math.exp(-0.1 * age_hours)
    
    # Priority (normalized)
    priority = context.priority / 100.0
    
    # Frequency (normalized)
    frequency = min(context.access_count / 100, 1.0)
    
    # User preference
    user_pref = user_preferences.get(context.type, 0.5)
    
    # Weighted sum
    score = (
        relevance * 0.35 +
        recency * 0.25 +
        priority * 0.20 +
        frequency * 0.10 +
        user_pref * 0.10
    )
    
    return score
```

---

## 7. Configuration

```yaml
context_engine:
  # Collection
  collection:
    enabled: true
    auto_collect: true
    batch_size: 100
    
  # Classification
  classification:
    enabled: true
    auto_classify: true
    
  # Ranking
  ranking:
    enabled: true
    algorithm: weighted
    weights:
      relevance: 0.35
      recency: 0.25
      priority: 0.20
      frequency: 0.10
      user_preference: 0.10
      
  # Compression
  compression:
    enabled: true
    max_tokens: 8192
    strategy: truncate_then_summarize
    
  # Storage
  storage:
    cache_ttl: 3600s
    retention:
      active: 24h
      archived: 30d
      
  # Retrieval
  retrieval:
    max_items: 50
    timeout: 100ms
    
  # Monitoring
  monitoring:
    enabled: true
    metrics_interval: 15s
```
