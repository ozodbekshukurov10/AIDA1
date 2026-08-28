# AIDA Reasoning Memory

**Document:** Book 2, Chapter 8 - Reasoning Memory
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

Reasoning Memory stores **decision history, reasoning chains, lessons learned, successful plans, failed plans, and risk reports** to enable continuous improvement and informed future decisions.

---

## 2. Memory Types

| Type | Description | Retention | Access Pattern |
|------|-------------|-----------|----------------|
| Decision History | All past decisions | Permanent | Query by context |
| Reasoning Chains | Step-by-step reasoning | Permanent | Query by problem |
| Lessons Learned | Extracted insights | Permanent | Query by category |
| Successful Plans | Plans that worked | Long-term | Query by similarity |
| Failed Plans | Plans that failed | Long-term | Query to avoid |
| Risk Reports | Risk assessments | Medium-term | Query by risk type |

---

## 3. Memory Structure

### 3.1 Decision Record

```
DecisionRecord:
  decision_id: string
  timestamp: datetime
  goal: string
  context: dict
  hypotheses: list[Hypothesis]
  selected: Hypothesis
  confidence: float
  result: string
  success: boolean
  lessons: list[string]
```

### 3.2 Reasoning Chain

```
ReasoningChain:
  chain_id: string
  steps: list[ReasoningStep]
  conclusion: string
  confidence: float
  validated: boolean

ReasoningStep:
  step_number: int
  reasoning_type: string
  premise: string
  inference: string
  confidence: float
  evidence: list[string]
```

### 3.3 Lesson Record

```
LessonRecord:
  lesson_id: string
  category: string
  description: string
  context: string (when to apply)
  confidence: float
  source_task_id: string
  times_applied: int
  success_rate: float
```

---

## 4. Memory Operations

### 4.1 Store

```
1. Create memory record
2. Set metadata (timestamp, type, tags)
3. Calculate importance score
4. Store in appropriate memory tier
5. Index for retrieval
```

### 4.2 Retrieve

```
1. Parse retrieval query
2. Search relevant memory tier
3. Rank by relevance and recency
4. Return top-K results
5. Update access counts
```

### 4.3 Consolidate

```
1. Periodically review memories
2. Merge similar memories
3. Remove outdated memories
4. Update importance scores
5. Recompute indexes
```

---

## 5. Memory Retrieval Algorithm

### 5.1 Query Process

```
Query:
  1. Parse query into keywords and context
  2. Search by keywords (BM25)
  3. Search by semantic similarity (embedding)
  4. Combine results (hybrid)
  5. Filter by relevance threshold
  6. Sort by: relevance * 0.5 + recency * 0.3 + importance * 0.2
  7. Return top results
```

---

## 6. Memory Tiers

| Tier | Content | TTL | Max Size |
|------|---------|-----|----------|
| Working | Current session decisions | Session | 100 |
| Short-term | Recent decisions | 7 days | 1000 |
| Long-term | Important decisions | Permanent | 10000 |
| Archive | Old decisions | 90 days | Unlimited |

---

## 7. Configuration

```yaml
reasoning_memory:
  enabled: true
  
  tiers:
    working:
      max_size: 100
      ttl: session
    short_term:
      max_size: 1000
      ttl: 7d
    long_term:
      max_size: 10000
      ttl: permanent
    archive:
      ttl: 90d
  
  retrieval:
    algorithm: hybrid
    top_k: 10
    min_relevance: 0.5
  
  consolidation:
    enabled: true
    frequency: daily
    merge_threshold: 0.9
```
