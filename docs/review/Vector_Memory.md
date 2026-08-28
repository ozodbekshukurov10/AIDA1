# AIDA Vector Memory

**Document:** Book 2, Chapter 6 — Vector Memory
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

Vector Memory provides semantic search capabilities using embeddings. It enables finding similar content, concepts, and patterns based on meaning rather than exact keywords.

---

## 2. Vector Memory Architecture

### 2.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    VECTOR MEMORY                                     │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Embedding Service                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │  Text    │  │  Code    │  │  Multi-  │  │  Custom  │    │   │
│  │  │ Embedder │  │ Embedder │  │  Modal   │  │ Embedder │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Vector Store                               │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │  Index   │  │  Vector  │  │ Metadata │  │  Query   │    │   │
│  │  │ Manager  │  │  Store   │  │  Store   │  │  Engine  │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Optimization                               │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │  HNSW    │  │  IVF     │  │  PQ      │  │  Scalar  │    │   │
│  │  │  Index   │  │  Index   │  │  Quantize│  │  Quantize│    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Embedding Strategy

### 3.1 Embedding Models

| Model | Dimension | Speed | Quality | Use Case |
|-------|-----------|-------|---------|----------|
| `text-embedding-3-small` | 1536 | Fast | Good | General text |
| `text-embedding-3-large` | 3072 | Slow | Best | Critical search |
| `code-embedding` | 768 | Fast | Good | Code search |
| `custom` | Variable | Variable | Variable | Domain-specific |

### 3.2 Embedding Configuration

```yaml
embedding:
  # Default model
  default_model: text-embedding-3-small
  
  # Models by content type
  models:
    text: text-embedding-3-small
    code: code-embedding
    documentation: text-embedding-3-small
    
  # Dimension
  dimension: 1536
  
  # Batch processing
  batch_size: 100
  
  # Caching
  cache_enabled: true
  cache_ttl: 86400s
```

---

## 4. Chunk Strategy

### 4.1 Chunking Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| `fixed_size` | Fixed token count | Simple documents |
| `sentence` | Sentence-level | Natural language |
| `paragraph` | Paragraph-level | Structured docs |
| `semantic` | Semantic boundaries | Mixed content |
| `code` | AST-based | Code files |

### 4.2 Chunk Configuration

```yaml
chunking:
  # Default strategy
  default_strategy: semantic
  
  # Strategies by content type
  strategies:
    text:
      strategy: paragraph
      max_tokens: 512
      overlap: 50
      
    code:
      strategy: code
      max_tokens: 1024
      overlap: 0
      
    documentation:
      strategy: semantic
      max_tokens: 512
      overlap: 100
```

---

## 5. Similarity Threshold

### 5.1 Threshold Configuration

```yaml
similarity:
  # Default threshold
  default_threshold: 0.7
  
  # Thresholds by use case
  thresholds:
    exact_match: 0.95
    high_similarity: 0.85
    medium_similarity: 0.70
    low_similarity: 0.50
    
  # Minimum results
  min_results: 1
  max_results: 50
```

---

## 6. Index Strategy

### 6.1 Index Types

| Index | Description | Use Case |
|-------|-------------|----------|
| `HNSW` | Hierarchical Navigable Small World | General purpose |
| `IVF` | Inverted File Index | Large datasets |
| `Flat` | Exact search | Small datasets |

### 6.2 Index Configuration

```yaml
index:
  # Default index
  default_type: HNSW
  
  # HNSW parameters
  hnsw:
    m: 16
    ef_construction: 200
    ef_search: 100
    
  # IVF parameters
  ivf:
    nlist: 100
    nprobe: 10
```

---

## 7. Re-ranking

### 7.1 Re-ranking Strategy

```yaml
reranking:
  enabled: true
  
  # Cross-encoder model
  cross_encoder: ms-marco-MiniLM-L-6-v2
  
  # Top-k re-ranking
  top_k: 20
  
  # Score combination
  combine_with_original: true
  original_weight: 0.5
  rerank_weight: 0.5
```

---

## 8. Configuration

```yaml
vector_memory:
  # Embedding
  embedding:
    model: text-embedding-3-small
    dimension: 1536
    batch_size: 100
    
  # Chunking
  chunking:
    strategy: semantic
    max_tokens: 512
    overlap: 50
    
  # Index
  index:
    type: HNSW
    m: 16
    ef_construction: 200
    
  # Similarity
  similarity:
    threshold: 0.7
    max_results: 50
    
  # Re-ranking
  reranking:
    enabled: true
    model: cross_encoder
    
  # Storage
  storage:
    provider: pgvector
    table: vector_memory
```
