# AIDA Context Injection

**Document:** Book 2, Chapter 7 - Context Injection
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

Context Injection automatically enriches prompts with relevant information from multiple sources, ensuring the model has all necessary context to generate high-quality responses.

---

## 2. Context Sources

| Source | Description | Priority | Max Tokens |
|--------|-------------|----------|------------|
| Repository | Code structure, files | High | 2000 |
| Memory | User/session memory | High | 1000 |
| Knowledge | Documentation | Medium | 1500 |
| Project | Project metadata | Medium | 500 |
| Task | Current task info | High | 500 |
| User | User preferences | Medium | 300 |
| System | System config | Low | 200 |
| History | Chat history | Medium | 1000 |
| Examples | Few-shot examples | Medium | 1000 |
| Plugin | Plugin context | Low | 500 |

---

## 3. Injection Pipeline

### 3.1 Pipeline Flow

`
User Request
    |
    v
+-------------------+
| Request Analyzer   |
| - Parse request    |
| - Detect intent    |
| - Determine needs  |
+---------+---------+
          |
          v
+-------------------+
| Source Selector    |
| - Select sources   |
| - Set priorities   |
| - Set limits       |
+---------+---------+
          |
          v
+-------------------+
| Context Collector  |
| - Query sources    |
| - Collect data     |
| - Handle errors    |
+---------+---------+
          |
          v
+-------------------+
| Context Ranker     |
| - Rank relevance   |
| - Deduplicate      |
| - Merge            |
+---------+---------+
          |
          v
+-------------------+
| Context Injector   |
| - Inject into      |
|   prompt           |
| - Validate size    |
| - Format output    |
+-------------------+
          |
          v
Enriched Prompt
`

### 3.2 Source Selection Logic

`
1. Parse user request
2. Detect task type:
   code -> repository, memory, project, task
   debug -> repository, memory, task, history
   planning -> project, memory, task, knowledge
   research -> knowledge, memory, project
   security -> repository, knowledge, task
3. Set priority weights
4. Calculate token budget per source
5. Select top sources within budget
`

---

## 4. Context Types

### 4.1 Repository Context

`
Structure:
- File tree (top 2 levels)
- Key files (README, config, main)
- Recent changes
- Active branches
- Open issues

Token Budget: 2000
Priority: High (for code tasks)
`

### 4.2 Memory Context

`
Structure:
- Working memory (current session)
- Short-term memory (recent sessions)
- Long-term memory (user history)
- Episodic memory (past interactions)
- Procedural memory (learned patterns)

Token Budget: 1000
Priority: High
`

### 4.3 Knowledge Context

`
Structure:
- Relevant documentation
- API references
- Best practices
- Design patterns
- Common solutions

Token Budget: 1500
Priority: Medium
`

### 4.4 Project Context

`
Structure:
- Project name and description
- Tech stack
- Team size
- Status and phase
- Key decisions

Token Budget: 500
Priority: Medium
`

### 4.5 Task Context

`
Structure:
- Task description
- Requirements
- Constraints
- Acceptance criteria
- Dependencies

Token Budget: 500
Priority: High
`

### 4.6 User Context

`
Structure:
- User preferences
- Communication style
- Technical level
- Language preference
- History patterns

Token Budget: 300
Priority: Medium
`

### 4.7 System Context

`
Structure:
- Platform info
- Available tools
- Environment config
- Security rules
- Rate limits

Token Budget: 200
Priority: Low
`

### 4.8 History Context

`
Structure:
- Last N messages
- Key decisions made
- Files modified
- Errors encountered
- Progress tracked

Token Budget: 1000
Priority: Medium
`

### 4.9 Examples Context

`
Structure:
- Few-shot examples
- Similar past tasks
- Successful patterns
- Common mistakes

Token Budget: 1000
Priority: Medium
`

### 4.10 Plugin Context

`
Structure:
- Active plugins
- Plugin capabilities
- Plugin state
- Plugin outputs

Token Budget: 500
Priority: Low
`

---

## 5. Context Ranking

### 5.1 Ranking Algorithm

`
For each context item:
  score = (relevance * 0.4) + (recency * 0.3) + (importance * 0.3)
  
Where:
  relevance = cosine_similarity(item, request)
  recency = 1.0 / (1 + age_in_hours)
  importance = priority_weight * usage_frequency

Sort by score descending
Take top N items within token budget
`

### 5.2 Relevance Scoring

| Factor | Weight | Calculation |
|--------|--------|-------------|
| Keyword Match | 0.3 | TF-IDF similarity |
| Semantic Match | 0.3 | Embedding cosine similarity |
| Recency | 0.2 | Time decay function |
| Importance | 0.2 | Priority level |

---

## 6. Context Formatting

### 6.1 Format Templates

`
Repository Context:
  # Repository: {name}
  ## Structure
  {file_tree}
  ## Recent Changes
  {recent_changes}

Memory Context:
  # Xotira konteksti
  ## Joriy sessiya
  {working_memory}
  ## Oxirgi interactiya
  {short_term_memory}

Knowledge Context:
  # Bilimlar bazasi
  ## Hujjatlar
  {documents}
  ## Eng yaxshi amaliyotlar
  {best_practices}

Task Context:
  # Vazifa
  ## Tavsif
  {description}
  ## Talablar
  {requirements}
`

---

## 7. Token Budget Management

### 7.1 Budget Allocation

| Total Budget | Repository | Memory | Knowledge | Project | Task | User | System |
|-------------|------------|--------|-----------|---------|------|------|--------|
| 4096 | 2000 | 1000 | 1500 | 500 | 500 | 300 | 200 |
| 2048 | 800 | 500 | 600 | 200 | 300 | 150 | 100 |
| 1024 | 400 | 200 | 300 | 50 | 150 | 75 | 50 |

### 7.2 Overflow Handling

`
1. Calculate total context size
2. If within budget: inject all
3. If over budget:
   a. Rank by priority
   b. Truncate low-priority items
   c. Summarize medium-priority items
   d. Keep high-priority items full
4. Validate total size
5. Inject into prompt
`

---

## 8. Configuration

`yaml
context_injection:
  enabled: true
  auto_inject: true
  
  sources:
    repository:
      enabled: true
      max_tokens: 2000
      priority: high
    memory:
      enabled: true
      max_tokens: 1000
      priority: high
    knowledge:
      enabled: true
      max_tokens: 1500
      priority: medium
    project:
      enabled: true
      max_tokens: 500
      priority: medium
    task:
      enabled: true
      max_tokens: 500
      priority: high
    user:
      enabled: true
      max_tokens: 300
      priority: medium
    system:
      enabled: true
      max_tokens: 200
      priority: low
    history:
      enabled: true
      max_tokens: 1000
      priority: medium
    examples:
      enabled: true
      max_tokens: 1000
      priority: medium
    plugin:
      enabled: true
      max_tokens: 500
      priority: low
      
  ranking:
    algorithm: weighted
    weights:
      relevance: 0.4
      recency: 0.3
      importance: 0.3
      
  formatting:
    style: markdown
    language: uz
    
  budget:
    total: 4096
    overflow: truncate_then_summarize
`
