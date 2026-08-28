# AIDA Confidence Scoring

**Document:** Book 2, Chapter 8 - Confidence Scoring
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

Confidence Scoring quantifies certainty in every decision. It combines evidence strength, missing information analysis, and uncertainty measurement.

---

## 2. Confidence Formula

Confidence = (evidence * 0.30) + (past_success * 0.25) + (completeness * 0.20) + (consistency * 0.15) + (clarity * 0.10)

### Components

| Component | Weight | Description |
|-----------|--------|-------------|
| Evidence | 0.30 | Supporting facts available |
| Past Success | 0.25 | Similar decisions succeeded |
| Completeness | 0.20 | Information completeness |
| Consistency | 0.15 | Agreement across paths |
| Clarity | 0.10 | Unambiguity of conclusion |

---

## 3. Confidence Levels

| Score | Level | Action |
|-------|-------|--------|
| 0.90-1.00 | Very High | Execute immediately |
| 0.80-0.89 | High | Execute |
| 0.70-0.79 | Medium | Execute with monitoring |
| 0.60-0.69 | Low | Request more info |
| 0.50-0.59 | Very Low | Human review |
| 0.00-0.49 | Minimal | Human required |

---

## 4. Evidence Analysis

| Type | Strength | Example |
|------|----------|---------|
| Direct proof | 1.0 | Code compiles and tests pass |
| Strong evidence | 0.8 | Multiple sources confirm |
| Moderate evidence | 0.6 | Single reliable source |
| Weak evidence | 0.4 | Indirect indication |
| Anecdotal | 0.2 | Single data point |
| No evidence | 0.0 | No supporting data |

---

## 5. Missing Information Impact

| Gap Type | Impact | Mitigation |
|----------|--------|------------|
| Critical missing | -0.3 | Request information |
| Important missing | -0.2 | Use defaults |
| Nice-to-have missing | -0.1 | Continue |
| Optional missing | 0.0 | Ignore |

---

## 6. Uncertainty Handling (when confidence < 0.7)

1. Identify specific uncertainty source
2. Determine if resolvable
3. If resolvable: request info, research, validate
4. If not: present options with probabilities, explain uncertainty

---

## 7. Configuration

```yaml
confidence_scoring:
  enabled: true
  weights:
    evidence: 0.30
    past_success: 0.25
    completeness: 0.20
    consistency: 0.15
    clarity: 0.10
  thresholds:
    auto_execute: 0.70
    require_approval: 0.50
    require_human: 0.30
```
