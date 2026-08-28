# AIDA Prompt Lifecycle

**Document:** Book 2, Chapter 7 — Prompt Lifecycle
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Prompt Lifecycle defines the complete journey of a prompt from user request to learning. Every prompt passes through **14 stages**, each with specific inputs, processing logic, and outputs.

---

## 2. Lifecycle Stages

### 2.1 Complete Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PROMPT LIFECYCLE                              │
│                                                                      │
│  1. Receive Request                                                  │
│     ↓                                                                │
│  2. Intent Analysis                                                  │
│     ↓                                                                │
│  3. Task Analysis                                                    │
│     ↓                                                                │
│  4. Context Collection                                               │
│     ↓                                                                │
│  5. Memory Injection                                                 │
│     ↓                                                                │
│  6. Knowledge Injection                                              │
│     ↓                                                                │
│  7. Template Selection                                               │
│     ↓                                                                │
│  8. Prompt Assembly                                                  │
│     ↓                                                                │
│  9. Validation                                                       │
│     ↓                                                                │
│  10. Optimization                                                    │
│     ↓                                                                │
│  11. Execution                                                       │
│     ↓                                                                │
│  12. Response Analysis                                               │
│     ↓                                                                │
│  13. Learning                                                        │
│     ↓                                                                │
│  14. Archive                                                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Stage Details

### 3.1 Stage 1 — Receive Request

| Property | Value |
|----------|-------|
| Input | User message |
| Output | Parsed request |
| Duration | < 5ms |
| Failure | Return error |

**Processing:**
```
1. Receive user message
2. Parse message format
3. Extract content
4. Identify message type (text, code, file)
5. Create request object
```

---

### 3.2 Stage 2 — Intent Analysis

| Property | Value |
|----------|-------|
| Input | Parsed request |
| Output | Intent analysis |
| Duration | < 50ms |
| Failure | Return clarification |

**Processing:**
```
1. Analyze user intent
2. Determine goal category
3. Identify expected output type
4. Assess risk level
5. Create intent analysis
```

**Intent Categories:**
| Category | Description | Risk Level |
|----------|-------------|------------|
| `code_generation` | Write code | Low |
| `code_review` | Review code | Low |
| `debugging` | Fix errors | Low |
| `planning` | Plan approach | Low |
| `research` | Gather info | Low |
| `security` | Security analysis | Medium |
| `deployment` | Deploy code | High |
| `modification` | Modify existing | Medium |

---

### 3.3 Stage 3 — Task Analysis

| Property | Value |
|----------|-------|
| Input | Intent analysis |
| Output | Task analysis |
| Duration | < 50ms |
| Failure | Return error |

**Processing:**
```
1. Determine task type
2. Assess complexity
3. Estimate required context
4. Identify required tools
5. Create task analysis
```

---

### 3.4 Stage 4 — Context Collection

| Property | Value |
|----------|-------|
| Input | Task analysis |
| Output | Collected context |
| Duration | < 100ms |
| Failure | Use minimal context |

**Processing:**
```
1. Identify context sources
2. Collect repository context
3. Collect project context
4. Collect session context
5. Collect system context
6. Merge contexts
```

---

### 3.5 Stage 5 — Memory Injection

| Property | Value |
|----------|-------|
| Input | Collected context |
| Output | Context with memory |
| Duration | < 100ms |
| Failure | Skip memory |

**Processing:**
```
1. Query relevant memories
2. Rank memories by relevance
3. Select top memories
4. Inject into context
5. Update access counts
```

---

### 3.6 Stage 6 — Knowledge Injection

| Property | Value |
|----------|-------|
| Input | Context with memory |
| Output | Context with knowledge |
| Duration | < 100ms |
| Failure | Skip knowledge |

**Processing:**
```
1. Query knowledge base
2. Search documentation
3. Find relevant examples
4. Inject into context
```

---

### 3.7 Stage 7 — Template Selection

| Property | Value |
|----------|-------|
| Input | Task analysis + context |
| Output | Selected template |
| Duration | < 10ms |
| Failure | Use default template |

**Processing:**
```
1. Match task type to template
2. Load template
3. Validate template
4. Set template version
```

---

### 3.8 Stage 8 — Prompt Assembly

| Property | Value |
|----------|-------|
| Input | Template + context |
| Output | Assembled prompt |
| Duration | < 20ms |
| Failure | Return error |

**Processing:**
```
1. Fill template variables
2. Inject context
3. Add examples
4. Add rules and constraints
5. Set expected output format
6. Assemble final prompt
```

---

### 3.9 Stage 9 — Validation

| Property | Value |
|----------|-------|
| Input | Assembled prompt |
| Output | Validated prompt |
| Duration | < 10ms |
| Failure | Fix or reject |

**Processing:**
```
1. Validate prompt structure
2. Check token count
3. Check for injection attempts
4. Check for sensitive data
5. Validate completeness
```

---

### 3.10 Stage 10 — Optimization

| Property | Value |
|----------|-------|
| Input | Validated prompt |
| Output | Optimized prompt |
| Duration | < 20ms |
| Failure | Use original |

**Processing:**
```
1. Reduce tokens
2. Compress context
3. Remove duplicates
4. Optimize instruction order
5. Select best examples
```

---

### 3.11 Stage 11 — Execution

| Property | Value |
|----------|-------|
| Input | Optimized prompt |
| Output | Model response |
| Duration | 1-30s |
| Failure | Retry or fallback |

**Processing:**
```
1. Send to model
2. Wait for response
3. Handle streaming
4. Collect response
5. Validate response
```

---

### 3.12 Stage 12 — Response Analysis

| Property | Value |
|----------|-------|
| Input | Model response |
| Output | Analysis report |
| Duration | < 100ms |
| Failure | Log and continue |

**Processing:**
```
1. Analyze response quality
2. Check completeness
3. Check accuracy
4. Check format
5. Generate analysis report
```

---

### 3.13 Stage 13 — Learning

| Property | Value |
|----------|-------|
| Input | Analysis report |
| Output | Learning updates |
| Duration | < 50ms |
| Failure | Skip learning |

**Processing:**
```
1. Update prompt statistics
2. Record success/failure
3. Update model performance
4. Update template effectiveness
5. Generate improvement suggestions
```

---

### 3.14 Stage 14 — Archive

| Property | Value |
|----------|-------|
| Input | Prompt + response |
| Output | Archived prompt |
| Duration | < 10ms |
| Failure | Log warning |

**Processing:**
```
1. Store prompt
2. Store response
3. Store metadata
4. Store analysis
5. Set retention
```

---

## 4. Timing Summary

| Stage | Min | Average | Max |
|-------|-----|---------|-----|
| 1. Receive | 1ms | 3ms | 5ms |
| 2. Intent | 10ms | 30ms | 50ms |
| 3. Task | 10ms | 30ms | 50ms |
| 4. Context | 20ms | 50ms | 100ms |
| 5. Memory | 20ms | 50ms | 100ms |
| 6. Knowledge | 20ms | 50ms | 100ms |
| 7. Template | 1ms | 5ms | 10ms |
| 8. Assembly | 5ms | 10ms | 20ms |
| 9. Validation | 2ms | 5ms | 10ms |
| 10. Optimization | 5ms | 10ms | 20ms |
| 11. Execution | 1s | 5s | 30s |
| 12. Response | 10ms | 50ms | 100ms |
| 13. Learning | 5ms | 20ms | 50ms |
| 14. Archive | 2ms | 5ms | 10ms |
| **Total (pre-execution)** | **83ms** | **268ms** | **525ms** |
| **Total (with execution)** | **1.1s** | **5.3s** | **30.5s** |

---

## 5. Configuration

```yaml
prompt_lifecycle:
  # Stages
  stages:
    intent_analysis: true
    task_analysis: true
    context_collection: true
    memory_injection: true
    knowledge_injection: true
    template_selection: true
    prompt_assembly: true
    validation: true
    optimization: true
    response_analysis: true
    learning: true
    archival: true
    
  # Timeouts
  timeouts:
    intent: 100ms
    context: 200ms
    assembly: 50ms
    execution: 30s
    
  # Retry
  retry:
    max_retries: 2
    retry_delay: 1s
```
