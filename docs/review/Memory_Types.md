# AIDA Memory Types

**Document:** Book 2, Chapter 6 — Memory Types
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

AIDA uses 10 distinct memory types, each optimized for specific use cases. This document defines each memory type, its purpose, storage, and access patterns.

---

## 2. Memory Type Definitions

### 2.1 Working Memory

| Property | Value |
|----------|-------|
| **Purpose** | Current task context |
| **TTL** | 30 minutes |
| **Capacity** | 100 items |
| **Access** | Read/Write (frequent) |
| **Storage** | Redis |
| **Use Case** | Active task state, intermediate results |

```yaml
working_memory:
  description: "Current task context - what AI is actively working on"
  max_items: 100
  ttl: 1800s
  eviction: LRU
  persistence: redis
  
  contents:
    - current_task
    - intermediate_results
    - active_variables
    - pending_actions
    - recent_decisions
```

### 2.2 Short-Term Memory

| Property | Value |
|----------|-------|
| **Purpose** | Recent interactions |
| **TTL** | 24 hours |
| **Capacity** | 1000 items |
| **Access** | Read/Write |
| **Storage** | Redis + PostgreSQL |
| **Use Case** | Conversation history, recent events |

```yaml
short_term_memory:
  description: "Recent interactions and events"
  max_items: 1000
  ttl: 86400s
  eviction: LRU
  persistence: redis + postgresql
  
  contents:
    - conversation_history
    - recent_messages
    - recent_actions
    - recent_decisions
    - session_state
```

### 2.3 Long-Term Memory

| Property | Value |
|----------|-------|
| **Purpose** | Persistent knowledge |
| **TTL** | Permanent |
| **Capacity** | Unlimited |
| **Access** | Read/Write |
| **Storage** | PostgreSQL + VectorDB |
| **Use Case** | Learned knowledge, user preferences |

```yaml
long_term_memory:
  description: "Persistent knowledge and learned patterns"
  max_items: unlimited
  ttl: permanent
  persistence: postgresql + vectordb
  
  contents:
    - learned_knowledge
    - user_preferences
    - project_patterns
    - successful_strategies
    - error_patterns
```

### 2.4 Semantic Memory

| Property | Value |
|----------|-------|
| **Purpose** | Meaning-based knowledge |
| **TTL** | Permanent |
| **Capacity** | Unlimited |
| **Access** | Read (vector search) |
| **Storage** | VectorDB |
| **Use Case** | Concept relationships, knowledge graph |

```yaml
semantic_memory:
  description: "Meaning-based knowledge and concept relationships"
  max_items: unlimited
  ttl: permanent
  persistence: vectordb
  
  contents:
    - concept_definitions
    - concept_relationships
    - knowledge_graph
    - semantic_patterns
    - meaning_embeddings
```

### 2.5 Episodic Memory

| Property | Value |
|----------|-------|
| **Purpose** | Event experiences |
| **TTL** | 30 days |
| **Capacity** | 10000 items |
| **Access** | Read/Write |
| **Storage** | PostgreSQL |
| **Use Case** | Past events, experiences, outcomes |

```yaml
episodic_memory:
  description: "Past events and experiences"
  max_items: 10000
  ttl: 2592000s  # 30 days
  persistence: postgresql
  
  contents:
    - past_events
    - event_outcomes
    - event_context
    - event_learnings
    - event_patterns
```

### 2.6 Procedural Memory

| Property | Value |
|----------|-------|
| **Purpose** | How-to knowledge |
| **TTL** | Permanent |
| **Capacity** | Unlimited |
| **Access** | Read |
| **Storage** | PostgreSQL |
| **Use Case** | Procedures, workflows, how-to guides |

```yaml
procedural_memory:
  description: "How-to knowledge and procedures"
  max_items: unlimited
  ttl: permanent
  persistence: postgresql
  
  contents:
    - procedures
    - workflows
    - how_to_guides
    - best_practices
    - step_by_step_instructions
```

### 2.7 Project Memory

| Property | Value |
|----------|-------|
| **Purpose** | Project-specific knowledge |
| **TTL** | Project lifetime |
| **Capacity** | Unlimited |
| **Access** | Read/Write |
| **Storage** | PostgreSQL |
| **Use Case** | Project context, decisions, history |

```yaml
project_memory:
  description: "Project-specific knowledge and context"
  max_items: unlimited
  ttl: project_lifetime
  persistence: postgresql
  
  contents:
    - project_context
    - project_decisions
    - project_history
    - project_patterns
    - project_preferences
```

### 2.8 Repository Memory

| Property | Value |
|----------|-------|
| **Purpose** | Repository-specific knowledge |
| **TTL** | Repository lifetime |
| **Capacity** | Unlimited |
| **Access** | Read/Write |
| **Storage** | PostgreSQL + VectorDB |
| **Use Case** | Code patterns, architecture, dependencies |

```yaml
repository_memory:
  description: "Repository-specific knowledge"
  max_items: unlimited
  ttl: repository_lifetime
  persistence: postgresql + vectordb
  
  contents:
    - architecture_patterns
    - code_patterns
    - dependencies
    - coding_standards
    - known_issues
    - completed_tasks
    - open_tasks
    - documentation
```

### 2.9 User Memory

| Property | Value |
|----------|-------|
| **Purpose** | User-specific knowledge |
| **TTL** | User lifetime |
| **Capacity** | Unlimited |
| **Access** | Read/Write |
| **Storage** | PostgreSQL |
| **Use Case** | Preferences, style, frequently used |

```yaml
user_memory:
  description: "User-specific knowledge and preferences"
  max_items: unlimited
  ttl: user_lifetime
  persistence: postgresql
  
  contents:
    - preferences
    - coding_style
    - frameworks
    - languages
    - frequently_used_tools
    - pinned_knowledge
    - custom_rules
```

### 2.10 Shared Agent Memory

| Property | Value |
|----------|-------|
| **Purpose** | Cross-agent sharing |
| **TTL** | 24 hours |
| **Capacity** | 1000 items |
| **Access** | Read/Write |
| **Storage** | Redis |
| **Use Agent Coordination** |

```yaml
shared_agent_memory:
  description: "Shared context between agents"
  max_items: 1000
  ttl: 86400s
  persistence: redis
  
  contents:
    - plans
    - intermediate_results
    - observations
    - warnings
    - decisions
    - progress
```

---

## 3. Memory Relationships

### 3.1 Memory Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MEMORY HIERARCHY                                  │
│                                                                      │
│  Level 0: Working Memory (active task)                              │
│     │                                                                │
│     ↓ (promote)                                                     │
│  Level 1: Short-Term Memory (recent)                                │
│     │                                                                │
│     ↓ (consolidate)                                                 │
│  Level 2: Long-Term Memory (persistent)                             │
│     │                                                                │
│     ↓ (specialize)                                                  │
│  Level 3: Semantic / Episodic / Procedural                          │
│     │                                                                │
│     ↓ (organize)                                                    │
│  Level 4: Project / Repository / User / Shared                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Memory Promotion

```yaml
promotion_rules:
  working_to_short_term:
    trigger: task_completed
    criteria:
      - importance > 0.5
      - access_count > 2
      
  short_term_to_long_term:
    trigger: daily_consolidation
    criteria:
      - importance > 0.7
      - access_count > 5
      - relevance > 0.6
      
  long_term_to_semantic:
    trigger: knowledge_extraction
    criteria:
      - type: concept
      - relationships > 3
```

---

## 4. Configuration

```yaml
memory_types:
  working:
    enabled: true
    max_items: 100
    ttl: 1800s
    
  short_term:
    enabled: true
    max_items: 1000
    ttl: 86400s
    
  long_term:
    enabled: true
    max_items: unlimited
    ttl: permanent
    
  semantic:
    enabled: true
    max_items: unlimited
    ttl: permanent
    
  episodic:
    enabled: true
    max_items: 10000
    ttl: 2592000s
    
  procedural:
    enabled: true
    max_items: unlimited
    ttl: permanent
    
  project:
    enabled: true
    max_items: unlimited
    
  repository:
    enabled: true
    max_items: unlimited
    
  user:
    enabled: true
    max_items: unlimited
    
  shared_agent:
    enabled: true
    max_items: 1000
    ttl: 86400s
```
  