# AIDA RAG Architecture

**Document:** Book 2, Chapter 6 — RAG Architecture
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The RAG (Retrieval Augmented Generation) Architecture enables AIDA to retrieve relevant information from various sources and augment AI responses with accurate, up-to-date knowledge.

---

## 2. RAG Pipeline

### 2.1 Pipeline Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RAG PIPELINE                                      │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  1. Query Processing                                         │   │
│  │  - Parse query                                               │   │
│  │  - Extract keywords                                          │   │
│  │  - Generate query embedding                                  │   │
│  │  - Expand query                                              │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│     ↓                       │                                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  2. Retrieval                                                │   │
│  │  - Vector search                                             │   │
│  │  - Keyword search                                            │   │
│  │  - Hybrid search                                             │   │
│  │  - Metadata filtering                                        │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│     ↓                       │                                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  3. Ranking                                                  │   │
│  │  - Relevance scoring                                         │   │
│  │  - Re-ranking                                                │   │
│  │  - Deduplication                                             │   │
│  │  - Selection                                                 │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│     ↓                       │                                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  4. Augmentation                                             │   │
│  │  - Context assembly                                          │   │
│  │  - Citation generation                                       │   │
│  │  - Token budget management                                   │   │
│  │  - Prompt construction                                       │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│     ↓                       │                                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  5. Generation                                               │   │
│  │  - Send to LLM                                               │   │
│  │  - Generate response                                         │   │
│  │  - Validate response                                         │   │
│  │  - Return with citations                                     │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Search Types

### 3.1 Search Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `vector` | Semantic similarity | Conceptual queries |
| `keyword` | Exact keyword match | Specific terms |
| `hybrid` | Vector + keyword | General queries |
| `metadata` | Filter by metadata | Filtered searches |
| `graph` | Knowledge graph traversal | Relationship queries |

### 3.2 Hybrid Search

```python
class HybridSearch:
    async def search(self, query: str, limit: int) -> list[SearchResult]:
        """Perform hybrid search."""
        
        # Vector search
        vector_results = await self.vector_search(query, limit * 2)
        
        # Keyword search
        keyword_results = await self.keyword_search(query, limit * 2)
        
        # Merge results
        merged = self.merge_results(vector_results, keyword_results)
        
        # Re-rank
        reranked = self.rerank(merged, query)
        
        return reranked[:limit]
```

---

## 4. Search Sources

### 4.1 Source Types

| Source | Description | Search Method |
|--------|-------------|---------------|
| Documents | Uploaded documents | Vector + Keyword |
| Repository | Code repositories | Vector + AST |
| Knowledge Base | Knowledge articles | Vector + Keyword |
| Memory | Stored memories | Vector + Metadata |
| Web | Web pages | Vector + Keyword |
| Database | Structured data | SQL + Vector |

---

## 5. Ranking

### 5.1 Ranking Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| `relevance` | 0.40 | Semantic similarity |
| `keyword_match` | 0.25 | Keyword presence |
| `recency` | 0.15 | How recent |
| `authority` | 0.10 | Source authority |
| `popularity` | 0.10 | Access frequency |

### 5.2 Re-ranking

```python
class ReRanker:
    def rerank(self, results: list[SearchResult], query: str) -> list[SearchResult]:
        """Re-rank search results."""
        
        for result in results:
            # Cross-encoder scoring
            cross_score = self.cross_encoder.score(query, result.content)
            
            # Combine with original score
            result.score = result.score * 0.5 + cross_score * 0.5
        
        # Sort by combined score
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
```

---

## 6. Citation Support

### 6.1 Citation Format

```python
class Citation:
    citation_id: str
    source: str
    source_type: str
    title: str
    url: Optional[str]
    excerpt: str
    relevance_score: float
```

### 6.2 Citation Generation

```yaml
citation_generation:
  enabled: true
  
  format: "[{source_id}]"
  
  include:
    - source_title
    - source_url
    - excerpt
    - relevance_score
```

---

## 7. Configuration

```yaml
rag:
  # Query Processing
  query_processing:
    expand_query: true
    max_query_length: 500
    
  # Retrieval
  retrieval:
    default_limit: 10
    max_limit: 50
    search_timeout: 5s
    
  # Ranking
  ranking:
    algorithm: weighted
    weights:
      relevance: 0.40
      keyword_match: 0.25
      recency: 0.15
      authority: 0.10
      popularity: 0.10
      
  # Re-ranking
  reranking:
    enabled: true
    model: cross_encoder
    
  # Citation
  citation:
    enabled: true
    format: "[{source_id}]"
    
  # Token Budget
  token_budget:
    max_context_tokens: 4096
    reserve_for_response: 2048
```
