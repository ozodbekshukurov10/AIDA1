# AIDA Decision Framework

**Document:** Book 2, Chapter 8 - Decision Framework
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Decision Framework evaluates hypotheses across **9 technical dimensions** to select the optimal strategy. It uses weighted scoring, multi-criteria analysis, and trade-off evaluation.

---

## 2. Decision Dimensions

### 2.1 Core Criteria

| # | Criterion | Weight | Description |
|---|-----------|--------|-------------|
| 1 | Accuracy | 0.20 | Correctness of solution |
| 2 | Complexity | 0.10 | Implementation complexity |
| 3 | Performance | 0.15 | Runtime performance impact |
| 4 | Maintainability | 0.15 | Long-term maintainability |
| 5 | Scalability | 0.10 | Growth potential |
| 6 | Security | 0.15 | Security implications |
| 7 | Reliability | 0.10 | Failure resistance |
| 8 | Token Cost | 0.05 | Token/monetary cost |
| 9 | Execution Time | 0.05 | Time to completion |

### 2.2 Scoring Scale

| Score | Meaning |
|-------|---------|
| 1.0 | Excellent - Best possible |
| 0.8 | Good - Meets requirements well |
| 0.6 | Acceptable - Meets minimum requirements |
| 0.4 | Poor - Below requirements |
| 0.2 | Bad - Significant issues |
| 0.0 | Unacceptable - Cannot proceed |

---

## 3. Scoring Algorithm

### 3.1 Weighted Score Calculation

`
DecisionScore(hypothesis) = SUM(weight_i * score_i) for i in 1..9

Where:
  weight_i = weight of criterion i
  score_i = score of hypothesis on criterion i (0-1)
`

### 3.2 Example Calculation

`
Hypothesis: Refactor controller into services

Criterion        Weight  Score  Weighted
Accuracy         0.20    0.9    0.180
Complexity       0.10    0.5    0.050
Performance      0.15    0.8    0.120
Maintainability  0.15    0.9    0.135
Scalability      0.10    0.8    0.080
Security         0.15    0.7    0.105
Reliability      0.10    0.8    0.080
Token Cost       0.05    0.6    0.030
Execution Time   0.05    0.5    0.025
----------------------------------------
TOTAL                   0.805
Grade: B+ (Good)
`

---

## 4. Decision Matrix

### 4.1 Hypothesis Comparison

| Criterion | H1: Refactor | H2: Patch | H3: Rewrite |
|-----------|-------------|-----------|-------------|
| Accuracy | 0.9 | 0.7 | 0.95 |
| Complexity | 0.5 | 0.9 | 0.3 |
| Performance | 0.8 | 0.6 | 0.85 |
| Maintainability | 0.9 | 0.4 | 0.85 |
| Scalability | 0.8 | 0.3 | 0.9 |
| Security | 0.7 | 0.5 | 0.8 |
| Reliability | 0.8 | 0.6 | 0.7 |
| Token Cost | 0.6 | 0.9 | 0.3 |
| Execution Time | 0.5 | 0.9 | 0.2 |
| **Score** | **0.805** | **0.585** | **0.725** |

### 4.2 Decision

`
Winner: H1 (Refactor)
Reason: Best balance of quality and feasibility
Runner-up: H3 (Rewrite) - higher quality but higher risk
`

---

## 5. Trade-Off Analysis

### 5.1 Common Trade-Offs

| Trade-Off | Left | Right | Resolution |
|-----------|------|-------|------------|
| Speed vs Quality | Fast delivery | Thorough solution | Quality wins |
| Cost vs Quality | Low cost | High quality | Balance |
| Simplicity vs Flexibility | Simple | Flexible | Context-dependent |
| Security vs Usability | Maximum security | Easy to use | Security first |
| Short-term vs Long-term | Quick fix | Sustainable | Long-term wins |

### 5.2 Pareto Optimization

`
1. Score all hypotheses on all criteria
2. Find Pareto-optimal set (no hypothesis dominated by another)
3. From Pareto set, select based on:
   a. Highest overall weighted score
   b. No critical dimension below threshold
   c. Best risk-adjusted score
`

---

## 6. Decision Rules

### 6.1 Hard Constraints

`
Rule 1: Security score must be >= 0.6
Rule 2: Accuracy score must be >= 0.7
Rule 3: No single dimension can be 0.0
Rule 4: If confidence < 0.5, request more information
`

### 6.2 Soft Constraints

`
Rule 5: Prefer maintainability over performance (long-term)
Rule 6: Prefer reliability over speed
Rule 7: Prefer security over usability
Rule 8: Prefer simplicity when all else equal
`

---

## 7. Decision Output

### 7.1 Decision Report Structure

`
DecisionReport:
  goal: string
  hypotheses_evaluated: int
  selected_hypothesis: Hypothesis
  score: float
  grade: string
  reasoning: string
  trade_offs: list[TradeOff]
  risks: list[Risk]
  confidence: float
  alternatives: list[Hypothesis]
  timestamp: datetime
`

---

## 8. Configuration

`yaml
decision_framework:
  enabled: true
  
  criteria:
    accuracy:
      weight: 0.20
      min_score: 0.7
    complexity:
      weight: 0.10
      preference: low
    performance:
      weight: 0.15
      min_score: 0.5
    maintainability:
      weight: 0.15
      min_score: 0.5
    scalability:
      weight: 0.10
    security:
      weight: 0.15
      min_score: 0.6
    reliability:
      weight: 0.10
    token_cost:
      weight: 0.05
    execution_time:
      weight: 0.05
  
  grading:
    A: 0.90
    B: 0.80
    C: 0.70
    D: 0.60
    F: 0.00
  
  constraints:
    hard:
      - security_min: 0.6
      - accuracy_min: 0.7
    soft:
      - prefer_maintainability
      - prefer_reliability
      - prefer_security
      - prefer_simplicity
`
