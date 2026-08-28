# AIDA Reflection Engine

**Document:** Book 2, Chapter 8 - Reflection Engine
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Reflection Engine reviews every completed task to identify what went well, what went wrong, how to improve, and how to apply lessons to future tasks. It is the self-improvement mechanism of the Reasoning Engine.

---

## 2. Reflection Lifecycle

### 2.1 Flow

```
Task Completed
       |
       v
+---------------------+
| Result Analyzer     |
| - Compare vs goal   |
| - Identify gaps     |
+----------+----------+
           |
           v
+---------------------+
| Success Evaluator   |
| - What worked       |
| - What failed       |
+----------+----------+
           |
           v
+---------------------+
| Improvement Finder  |
| - Root cause analysis|
| - Better approaches |
+----------+----------+
           |
           v
+---------------------+
| Lesson Extractor    |
| - Generalize lessons|
| - Store in memory   |
+----------+----------+
           |
           v
Reflection Report
```

---

## 3. Reflection Components

### 3.1 Reflection Report Structure

```
ReflectionReport:
  task_id: string
  task_description: string
  goal: string
  result: string
  success: boolean
  
  what_went_well: list[string]
  what_went_wrong: list[string]
  root_causes: list[string]
  
  improvements: list[Improvement]
  lessons_learned: list[Lesson]
  
  time_spent: int (seconds)
  tokens_used: int
  accuracy_score: float (0-1)
  efficiency_score: float (0-1)
```

### 3.2 Improvement Structure

```
Improvement:
  area: string (code|planning|testing|communication)
  description: string
  suggestion: string
  priority: string (high|medium|low)
  expected_impact: float (0-1)
```

### 3.3 Lesson Structure

```
Lesson:
  category: string
  description: string
  context: string (when to apply)
  confidence: float (0-1)
  source_task_id: string
```

---

## 4. Analysis Dimensions

### 4.1 What Went Well

| Dimension | Evaluation Criteria |
|-----------|---------------------|
| Goal Achievement | All objectives met |
| Efficiency | Time/token optimization |
| Quality | No bugs, clean code |
| Communication | Clear explanation |
| Strategy | Good approach selection |

### 4.2 What Went Wrong

| Dimension | Detection Method |
|-----------|------------------|
| Missed Requirements | Compare vs acceptance criteria |
| Inefficiency | Compare actual vs optimal time |
| Quality Issues | Bugs, errors, poor style |
| Wrong Strategy | Better alternatives available |
| Missing Context | Incomplete information used |

---

## 5. Root Cause Analysis

### 5.1 Analysis Methods

| Method | Description | When to Use |
|--------|-------------|-------------|
| 5 Whys | Ask why repeatedly | Simple failures |
| Fishbone | Categorize causes | Complex failures |
| Pareto | 80/20 analysis | Multiple issues |
| Timeline | Sequence events | Timing issues |

---

## 6. Learning Integration

### 6.1 Learning Process

```
1. Extract lessons from reflection
2. Validate lesson quality
3. Store in Reasoning Memory:
   a. Update decision patterns
   b. Update success/failure rates
   c. Update risk assessments
4. Apply to future tasks:
   a. Prefer strategies with high success
   b. Avoid strategies with high failure
   c. Adjust confidence based on history
```

### 6.2 Learning Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Improvement Rate | Tasks showing improvement | > 30% |
| Error Reduction | Errors decreasing over time | > 20% |
| Efficiency Gain | Time/tokens decreasing | > 15% |
| Lesson Application | Lessons applied successfully | > 50% |

---

## 7. Configuration

```yaml
reflection_engine:
  enabled: true
  auto_reflect: true
  
  analysis:
    root_cause: true
    improvement_suggestions: true
    lesson_extraction: true
  
  learning:
    store_lessons: true
    apply_to_future: true
    update_patterns: true
  
  metrics:
    track_improvement: true
    track_efficiency: true
```
