# AIDA Memory Architecture

**Document:** Book 2, Chapter 6 — Memory Architecture
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Memory Architecture defines how AIDA stores, manages, and retrieves different types of memory. It provides a unified interface for working memory, short-term memory, long-term memory, and specialized memory types.

---

## 2. Memory Layer Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MEMORY ARCHITECTURE                               │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Memory Manager                             │   │
│  │  - Unified memory interface                                   │   │
│  │  - Memory routing                                             │   │
│  │  - Memory lifecycle management                                │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│     ↓                       │                                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Memory Types                               │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │ Working  │  │ Short-   │  │  Long-   │  │Semantic  │    │   │
│  │  │ Memory   │  │  Term    │  │  Term    │  │ Memory   │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │Episodic  │  │Procedural│  │ Project  │  │Repository│    │   │
│  │  │ Memory   │  │ Memory   │  │ Memory   │  │ Memory   │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │
│  │  ┌──────────┐  ┌──────────┐                                 │   │
│  │  │  User    │  │  Shared  │                                 │   │
│  │  │ Memory   │  │  Agent   │                                 │   │
│  │  └──────────┘  └──────────┘                                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Storage Backends                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │  Redis   │  │PostgreSQL│  │  Vector  │  │    S3    │    │   │
│  │  │ (Cache)  │  │ (Meta)   │  │   (EMB)  │  │  (Raw)   │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Memory Types Overview

| Type | Description | TTL | Capacity | Access Pattern |
|------|-------------|-----|----------|----------------|
| Working | Current task context | 30 min | 100 items | Read/Write |
| Short-Term | Recent interactions | 24 hours | 1000 items | Read/Write |
| Long-Term | Persistent knowledge | Permanent | Unlimited | Read/Write |
| Semantic | Meaning-based knowledge | Permanent | Unlimited | Read/Write |
| Episodic | Event experiences | 30 days | 10000 items | Read/Write |
| Procedural | How-to knowledge | Permanent | Unlimited | Read |
| Project | Project-specific | Project lifetime | Unlimited | Read/Write |
| Repository | Repository-specific | Repository lifetime | Unlimited | Read/Write |
| User | User-specific | User lifetime | Unlimited | Read/Write |
| Shared Agent | Cross-agent sharing | 24 hours | 1000 items | Read/Write |

---

## 4. Memory Interface

### 4.1 Core Operations

```python
class IMemoryManager:
    # Store
    async def store(memory_type: str, key: str, value: dict, metadata: dict) -> MemoryEntry
    
    # Retrieve
    async def retrieve(memory_type: str, key: str) -> Optional[MemoryEntry]
    
    # Search
    async def search(memory_type: str, query: str, limit: int) -> list[MemoryEntry]
    
    # Update
    async def update(memory_type: str, key: str, value: dict) -> bool
    
    # Delete
    async def delete(memory_type: str, key: str) -> bool
    
    # List
    async def list(memory_type: str, filter: dict) -> list[MemoryEntry]
    
    # Consolidate
    async def consolidate(memory_type: str) -> ConsolidationResult
```

### 4.2 Memory Entry

```python
class MemoryEntry:
    entry_id: UUID
    memory_type: str
    key: str
    value: dict
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    accessed_at: datetime
    access_count: int
    
    # Scoring
    importance: float  # 0.0 - 1.0
    relevance: float   # 0.0 - 1.0
    
    # Embedding
    embedding: Optional[list[float]]
    
    # TTL
    expires_at: Optional[datetime]
    
    # Source
    source: str
    source_id: Optional[str]
```

---

## 5. Storage Backends

### 5.1 Backend Selection

| Backend | Use Case | Latency | Durability |
|---------|----------|---------|------------|
| Redis | Cache, working memory | < 1ms | Low |
| PostgreSQL | Metadata, long-term | < 10ms | High |
| VectorDB | Embeddings, semantic search | < 50ms | High |
| S3 | Raw content, archives | < 100ms | Very High |

### 5.2 Backend Configuration

```yaml
storage_backends:
  redis:
    url: redis://localhost:6379/0
    pool_size: 20
    timeout: 5s
    
  postgresql:
    url: postgresql://localhost:5432/aida_memory
    pool_size: 10
    timeout: 10s
    
  vectordb:
    provider: pgvector
    url: postgresql://localhost:5432/aida_vectors
    dimension: 1536
    
  s3:
    bucket: aida-memory
    region: us-east-1
```

---

## 6. Memory Consolidation

### 6.1 Consolidation Process

```
Memory Consolidation
    │
    ├── Duplicate Detection
    │   ├── Find similar memories
    │   ├── Merge duplicates
    │   └── Keep most recent
    │
    ├── Importance Scoring
    │   ├── Calculate access frequency
    │   ├── Calculate recency
    │   ├── Calculate relevance
    │   └── Update importance score
    │
    ├── Conflict Resolution
    │   ├── Detect conflicting memories
    │   ├── Resolve based on recency
    │   ├── Resolve based on source
    │   └── Keep most reliable
    │
    ├── Summarization
    │   ├── Summarize long memories
    │   ├── Extract key points
    │   └── Create compact version
    │
    └── Garbage Collection
        ├── Remove expired memories
        ├── Remove low-importance
        └── Compress old memories
```

---

## 7. Configuration

```yaml
memory:
  # Working Memory
  working:
    enabled: true
    max_items: 100
    ttl: 1800s
    
  # Short-Term Memory
  short_term:
    enabled: true
    max_items: 1000
    ttl: 86400s
    
  # Long-Term Memory
  long_term:
    enabled: true
    max_items: unlimited
    ttl: permanent
    
  # Consolidation
  consolidation:
    enabled: true
    interval: 3600s
    duplicate_threshold: 0.9
    importance_threshold: 0.3
    
  # Storage
  storage:
    default_backend: redis
    cache_ttl: 3600s
    
  # Monitoring
  monitoring:
    enabled: true
    metrics_interval: 15s
```
