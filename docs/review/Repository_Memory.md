# AIDA Repository Memory

**Document:** Book 2, Chapter 6 — Repository Memory
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

Repository Memory stores knowledge specific to code repositories, including architecture patterns, dependencies, coding standards, and project history.

---

## 2. Repository Memory Structure

### 2.1 Memory Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `architecture` | System architecture | Module structure, patterns |
| `dependencies` | Package dependencies | Libraries, frameworks |
| `standards` | Coding standards | Style, conventions |
| `patterns` | Code patterns | Design patterns, idioms |
| `issues` | Known issues | Bugs, workarounds |
| `history` | Project history | Decisions, changes |
| `documentation` | Project docs | README, guides |

---

## 3. Repository Memory Data

### 3.1 Architecture Memory

```python
class ArchitectureMemory:
    repository_id: UUID
    
    # Module structure
    modules: list[ModuleInfo]
    
    # Design patterns
    patterns: list[PatternInfo]
    
    # Data flow
    data_flow: dict
    
    # Dependencies
    dependencies: list[DependencyInfo]
    
    # Architecture decisions
    decisions: list[ArchitectureDecision]
```

### 3.2 Coding Standards Memory

```python
class CodingStandardsMemory:
    repository_id: UUID
    
    # Style guide
    style: dict
    
    # Naming conventions
    naming: dict
    
    # Import conventions
    imports: dict
    
    # File organization
    organization: dict
    
    # Custom rules
    custom_rules: list[Rule]
```

### 3.3 Known Issues Memory

```python
class KnownIssuesMemory:
    repository_id: UUID
    
    # Active issues
    active_issues: list[Issue]
    
    # Workarounds
    workarounds: list[Workaround]
    
    # Fixed issues
    fixed_issues: list[Issue]
```

---

## 4. Repository Analysis

### 4.1 Analysis Process

```
Repository Analysis
    │
    ├── Scan Structure
    │   ├── Directory tree
    │   ├── File types
    │   └── Configuration files
    │
    ├── Analyze Code
    │   ├── AST parsing
    │   ├── Dependency extraction
    │   └── Pattern detection
    │
    ├── Extract Knowledge
    │   ├── Architecture patterns
    │   ├── Coding standards
    │   └── Common patterns
    │
    └── Store in Memory
        ├── Create memory entries
        ├── Generate embeddings
        └── Index for search
```

---

## 5. Configuration

```yaml
repository_memory:
  enabled: true
  
  # Analysis
  analysis:
    auto_analyze: true
    analyze_on_clone: true
    analyze_on_change: true
    
  # Categories
  categories:
    architecture: true
    dependencies: true
    standards: true
    patterns: true
    issues: true
    history: true
    documentation: true
    
  # Retention
  retention:
    max_age: permanent
    max_size: unlimited
    
  # Search
  search:
    vector_search: true
    keyword_search: true
```
