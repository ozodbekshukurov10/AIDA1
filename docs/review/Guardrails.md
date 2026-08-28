# AIDA Prompt Guardrails

**Document:** Book 2, Chapter 7 - Guardrails
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Guardrails system protects the Prompt Engine against prompt injection, sensitive data leakage, policy violations, and unsafe requests. It operates as a **security layer** between user input and model execution.

---

## 2. Threat Categories

| Threat | Description | Severity | Detection |
|--------|-------------|----------|-----------|
| Prompt Injection | Malicious instructions in user input | Critical | Pattern matching + ML |
| Sensitive Data | PII, secrets, credentials in prompt | Critical | Regex + NER |
| Policy Violations | Content against platform rules | High | Classification |
| Unsafe Requests | Dangerous code, harmful content | High | Rule engine |
| Token Overflow | Exceeding token limits | Medium | Token counting |
| Instruction Leakage | Extracting system prompts | Medium | Pattern detection |

---

## 3. Guardrail Pipeline

### 3.1 Pipeline Flow

`
User Input
    |
    v
+---------------------------+
| Input Sanitizer           |
| - Remove control chars    |
| - Normalize unicode       |
| - Trim whitespace         |
+-----------+---------------+
            |
            v
+---------------------------+
| Injection Detector        |
| - Pattern matching        |
| - ML classification       |
| - Heuristic analysis      |
+-----------+---------------+
            |
            v
+---------------------------+
| Sensitive Data Scanner    |
| - PII detection           |
| - Secret detection        |
| - Credential detection    |
+-----------+---------------+
            |
            v
+---------------------------+
| Policy Checker            |
| - Content policy          |
| - Usage policy            |
| - Safety policy           |
+-----------+---------------+
            |
            v
+---------------------------+
| Safe Prompt               |
+---------------------------+
`

### 3.2 Post-Generation Check

`
Model Response
    |
    v
+---------------------------+
| Output Sanitizer          |
| - Remove sensitive data   |
| - Filter harmful content  |
| - Validate format         |
+-----------+---------------+
            |
            v
+---------------------------+
| Instruction Leakage Check |
| - Detect system prompt    |
| - Detect instructions     |
| - Detect internal config  |
+-----------+---------------+
            |
            v
+---------------------------+
| Safe Output               |
+---------------------------+
`

---

## 4. Injection Detection

### 4.1 Pattern Rules

| Pattern | Action | Confidence |
|---------|--------|------------|
| Ignore previous instructions | Block | 0.95 |
| You are now X | Block | 0.90 |
| System: ... | Block | 0.85 |
| Forget everything | Block | 0.90 |
| New instructions | Block | 0.80 |
| Override system | Block | 0.95 |
| Pretend you are | Block | 0.85 |
| Role play as | Warn | 0.70 |
| Ignore safety | Block | 0.95 |
| DAN mode | Block | 0.99 |
| Jailbreak | Block | 0.99 |

### 4.2 ML Detection

`
Features:
- Token probability distribution
- Instruction vs query ratio
- Semantic similarity to known attacks
- Structural anomalies
- Encoding patterns

Model: Fine-tuned classifier
Training: 10K+ attack examples
Accuracy: 94%
False Positive Rate: 2%
`

### 4.3 Heuristic Rules

`
Rule 1: Multiple language switches in single message -> Warn
Rule 2: Base64 encoded content -> Scan
Rule 3: Excessive special characters -> Warn
Rule 4: Instruction-like phrasing in user role -> Block
Rule 5: Nested role markers -> Block
Rule 6: Unicode confusables in keywords -> Warn
Rule 7: Prompt concatenation patterns -> Block
`

---

## 5. Sensitive Data Detection

### 5.1 PII Patterns

| Type | Pattern | Action |
|------|---------|--------|
| Email | [a-z0-9]+@[a-z]+\.[a-z]+ | Mask |
| Phone | \+?[0-9]{10,15} | Mask |
| SSN | [0-9]{3}-[0-9]{2}-[0-9]{4} | Block |
| Credit Card | [0-9]{4} [0-9]{4} [0-9]{4} [0-9]{4} | Block |
| Name | NER detection | Mask |
| Address | NER detection | Mask |
| IP Address | [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+ | Mask |

### 5.2 Secret Patterns

| Type | Pattern | Action |
|------|---------|--------|
| API Key | api[_-]?key[_-]?=.+ | Block |
| AWS Key | AKIA[0-9A-Z]{16} | Block |
| Private Key | -----BEGIN.*PRIVATE KEY----- | Block |
| Password | password[_-]?=.+ | Block |
| Token | token[_-]?=.+ | Block |
| JWT | eyJ[A-Za-z0-9]+.eyJ | Block |

### 5.3 Detection Actions

`
Block: Reject input, return error to user
Mask: Replace with [REDACTED], continue processing
Warn: Log warning, continue processing
Scan: Run deeper analysis before deciding
`

---

## 6. Policy Rules

### 6.1 Content Policy

`
Rule 1: No harmful content generation
Rule 2: No illegal activity instructions
Rule 3: No hate speech or discrimination
Rule 4: No explicit content
Rule 5: No violence promotion
Rule 6: No self-harm instructions
Rule 7: No misinformation generation
`

### 6.2 Usage Policy

`
Rule 1: No unauthorized system access
Rule 2: No data exfiltration
Rule 3: No resource abuse
Rule 4: No commercial misuse
Rule 5: No impersonation
`

### 6.3 Safety Policy

`
Rule 1: No dangerous code execution
Rule 2: No system modification without auth
Rule 3: No network access without permission
Rule 4: No file deletion without confirmation
Rule 5: No irreversible operations without warning
`

---

## 7. Response Validation

### 7.1 Output Checks

| Check | Description | Action |
|-------|-------------|--------|
| System Prompt Leak | Response contains system instructions | Block |
| Instruction Leak | Response reveals internal logic | Block |
| Sensitive Data | Response contains PII/secrets | Mask |
| Harmful Content | Response is harmful | Block |
| Format Violation | Response breaks expected format | Retry |
| Length Violation | Response too long/short | Truncate |

### 7.2 Leakage Detection

`
Heuristics:
1. Response contains phrases from system prompt
2. Response contains instruction-like structures
3. Response references internal configuration
4. Response includes template variables
5. Response reveals model identity details

Actions:
- Block complete response
- Remove leaked portions
- Regenerate with adjusted prompt
`

---

## 8. Guardrail Rules Engine

### 8.1 Rule Structure

`
Rule:
  id: string
  name: string
  category: string
  severity: critical|high|medium|low
  pattern: string (regex)
  action: block|warn|mask|scan
  confidence: float (0-1)
  enabled: boolean
  exceptions: list[string]
`

### 8.2 Rule Evaluation

`
1. Load all enabled rules
2. Sort by severity (critical first)
3. For each rule:
   a. Match pattern against input
   b. Calculate confidence
   c. If confidence >= threshold:
      - Execute action
      - Log result
      - Continue to next rule
4. If any critical block triggered: reject input
5. If warnings only: log and continue
`

---

## 9. Monitoring

### 9.1 Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| blocks_total | Total blocked attempts | > 100/hour |
| injection_attempts | Injection detection count | > 50/hour |
| sensitive_data_blocks | Sensitive data blocks | > 30/hour |
| policy_violations | Policy violation count | > 20/hour |
| false_positives | False positive rate | > 5% |
| avg_detection_time | Detection latency | > 100ms |

### 9.2 Logging

`
All guardrail events logged with:
- Timestamp
- Rule ID
- Category
- Severity
- Action taken
- Confidence score
- Input hash (not content)
- User ID (anonymized)
`

---

## 10. Configuration

`yaml
guardrails:
  enabled: true
  
  injection_detection:
    enabled: true
    ml_model: injection_classifier_v1
    pattern_rules: true
    heuristic_rules: true
    threshold: 0.8
    
  sensitive_data:
    enabled: true
    pii_detection: true
    secret_detection: true
    action: mask
    
  policy:
    enabled: true
    content_policy: true
    usage_policy: true
    safety_policy: true
    
  output_validation:
    enabled: true
    leakage_detection: true
    format_validation: true
    
  logging:
    enabled: true
    level: info
    anonymize: true
    
  alerts:
    enabled: true
    channels: [log, webhook]
    threshold: critical
`
