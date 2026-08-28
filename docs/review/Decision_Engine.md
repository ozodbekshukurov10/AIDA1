# AIDA Decision Engine

**Document:** Book 2, Chapter 5 — Decision Engine
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Decision Engine enables the Workflow Engine to make autonomous decisions during execution. It evaluates conditions, applies rules, uses AI reasoning, and falls back to human approval when confidence is low.

---

## 2. Decision Types

### 2.1 Decision Categories

| Category | Description | Example |
|----------|-------------|---------|
| `conditional` | IF/ELSE branching | "If language is Python, use Django" |
| `switch` | Multi-way branching | "Route based on task type" |
| `rule` | Rule-based decisions | "Apply business rules" |
| `ai_decision` | AI-powered decisions | "Choose best approach" |
| `confidence` | Confidence-based | "If confidence < 0.7, ask human" |
| `fallback` | Default decisions | "Use default if no match" |

---

## 3. Decision Components

### 3.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DECISION ENGINE                                   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Condition Evaluator                        │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │   IF     │  │  ELSE    │  │  SWITCH  │  │  RULE    │    │   │
│  │  │ Evaluator│  │ Evaluator│  │ Evaluator│  │ Evaluator│    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    AI Decision Maker                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  �┌──────────┐    │   │
│  │  │ Context  │→ │ Analysis │→ │ Decision │→ │ Confidence│   │   │
│  │  │ Gatherer │  │ Engine   │  │ Maker    │  │ Scorer   │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Fallback Handler                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │ Default  │  │ Human    │  │ Retry    │  │ Skip     │    │   │
│  │  │ Action   │  │ Approval │  │ Decision │  │ Decision │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Condition Evaluation

### 4.1 IF/ELSE Conditions

```yaml
conditions:
  # Simple condition
  - type: if
    expression: "context.language == 'python'"
    true_action: use_django
    false_action: use_flask
    
  # Nested condition
  - type: if
    expression: "context.complexity == 'high'"
    true_action:
      - type: if
        expression: "context.budget > 100"
        true_action: use_pro_model
        false_action: use_flash_model
    false_action: use_flash_model
```

### 4.2 SWITCH Conditions

```yaml
switch:
  field: "context.task_type"
  cases:
    coding:
      action: code_generation
    testing:
      action: test_generation
    research:
      action: web_research
    documentation:
      action: doc_generation
  default:
    action: ai_general
```

### 4.3 RULE Conditions

```yaml
rules:
  - name: high_priority_routing
    conditions:
      - field: "context.priority"
        operator: ">="
        value: 80
    action: route_to_critical_queue
    
  - name: budget_check
    conditions:
      - field: "context.estimated_cost"
        operator: ">"
        value: "context.budget"
    action: request_budget_approval
```

---

## 5. AI Decision Making

### 5.1 AI Decision Flow

```
Decision Point Reached
    │
    ├── Gather Context
    │   ├── Current workflow state
    │   ├── Previous step results
    │   ├── Available options
    │   └── Constraints
    │
    ├── Analyze Options
    │   ├── Evaluate each option
    │   ├── Score each option
    │   └── Rank options
    │
    ├── Make Decision
    │   ├── Select best option
    │   ├── Generate reasoning
    │   └── Calculate confidence
    │
    ├── Confidence Check
    │   ├── Confidence >= 0.8 → Auto-execute
    │   ├── Confidence >= 0.5 → Execute with monitoring
    │   └── Confidence < 0.5 → Request human approval
    │
    └── Execute Decision
```

### 5.2 AI Decision Prompt

```python
AI_DECISION_PROMPT = """
You are making a decision for a workflow execution.

Current Context:
- Workflow: {workflow_name}
- Step: {step_name}
- Previous Results: {previous_results}
- Available Options: {options}
- Constraints: {constraints}

Make the best decision based on the context.

Output Format:
{{
  "decision": "selected_option",
  "reasoning": "Why this option was selected",
  "confidence": 0.85,
  "alternatives": ["option2", "option3"],
  "risks": ["risk1", "risk2"]
}}
"""
```

### 5.3 Confidence Scoring

```python
class ConfidenceScorer:
    def score(self, decision: Decision) -> float:
        factors = []
        
        # Context completeness
        context_completeness = self.score_context(decision.context)
        factors.append(context_completeness * 0.3)
        
        # Option clarity
        option_clarity = self.score_options(decision.options)
        factors.append(option_clarity * 0.2)
        
        # Historical success
        historical_success = self.score_history(decision.similar_decisions)
        factors.append(historical_success * 0.3)
        
        # Risk assessment
        risk_score = self.score_risks(decision.risks)
        factors.append(risk_score * 0.2)
        
        return sum(factors)
```

---

## 6. Fallback Decisions

### 6.1 Fallback Chain

```
Primary Decision (AI)
    │
    ├── Confidence >= 0.8
    │   └── Execute decision
    │
    ├── Confidence >= 0.5
    │   ├── Execute decision
    │   └── Monitor closely
    │
    ├── Confidence < 0.5
    │   ├── Request human approval
    │   │   ├── Approved → Execute
    │   │   ├── Rejected → Try alternative
    │   │   └── Timeout → Use default
    │   └── No human available → Use default
    │
    └── AI fails
        ├── Try rule-based decision
        │   ├── Success → Execute
        │   └── Failure → Use default
        └── Use default action
```

### 6.2 Default Actions

```yaml
default_actions:
  # When AI confidence is low
  low_confidence:
    action: request_human_approval
    timeout: 3600s
    fallback: use_default
    
  # When AI fails
  ai_failure:
    action: try_rule_based
    fallback: use_default
    
  # When rule-based fails
  rule_failure:
    action: use_default
    
  # Default action
  use_default:
    action: skip_step
    log_warning: true
```

---

## 7. Decision Configuration

```yaml
decision_engine:
  # AI Decisions
  ai_decisions:
    enabled: true
    model: pro
    timeout: 30s
    max_retries: 2
    
  # Confidence Thresholds
  confidence:
    auto_execute: 0.8
    monitor_execute: 0.5
    human_approval: 0.3
    
  # Fallback
  fallback:
    enabled: true
    chain:
      - ai_decision
      - rule_based
      - default_action
    
  # Human Approval
  human_approval:
    enabled: true
    timeout: 3600s
    default_action: reject
    
  # Monitoring
  monitoring:
    enabled: true
    log_decisions: true
    metrics_interval: 15s
```
