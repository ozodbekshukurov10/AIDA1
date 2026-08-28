# AIDA Prompt Versioning

**Document:** Book 2, Chapter 7 - Prompt Versioning
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

Prompt Versioning provides **full lifecycle management** for prompt templates and configurations, enabling rollback, A/B testing, performance comparison, and audit trails.

---

## 2. Version Control Architecture

### 2.1 Storage Model

`
+-------------------+
| Prompt Registry   |
|                   |
| +-------------+  |
| | Template    |  |
| | - id        |  |
| | - name      |  |
| | - versions  |--+---> Version Store
| | - current   |  |     +----------------+
| +-------------+  |     | v1.0.0 - blob  |
+-------------------+     | v1.1.0 - blob  |
                          | v1.2.0 - blob  |
                          +----------------+
`

### 2.2 Version Structure

`
PromptVersion:
  version_id: string (uuid)
  template_id: string
  version: string (semver)
  author: string
  created_at: datetime
  modified_at: datetime
  content: dict
  metadata: dict
  performance_score: float
  is_active: boolean
  changelog: string
  parent_version: string (nullable)
`

---

## 3. Semantic Versioning

### 3.1 Version Format

`
MAJOR.MINOR.PATCH

MAJOR: Breaking changes (new template structure)
MINOR: Feature additions (new variables, conditions)
PATCH: Bug fixes (typos, corrections)
`

### 3.2 Version Rules

| Change Type | Version Bump | Example |
|-------------|--------------|---------|
| New template | 1.0.0 | Initial release |
| Add variable | 1.1.0 | Add user_context |
| Add condition | 1.2.0 | Add security check |
| Fix typo | 1.2.1 | Fix spelling |
| Restructure | 2.0.0 | New layout |
| Deprecate | 2.1.0 | Mark old as deprecated |

---

## 4. Version Operations

### 4.1 Create Version

`
1. Load current version
2. Apply changes
3. Generate version number
4. Validate new version
5. Store new version
6. Update registry
7. Log creation event
`

### 4.2 Activate Version

`
1. Validate version exists
2. Check compatibility
3. Deactivate current version
4. Activate new version
5. Update routing
6. Notify consumers
7. Log activation event
`

### 4.3 Rollback Version

`
1. Identify target version
2. Check rollback target valid
3. Deactivate current version
4. Activate target version
5. Validate rollback
6. Notify consumers
7. Log rollback event
`

### 4.4 Compare Versions

`
1. Load both versions
2. Diff content structure
3. Diff variables
4. Diff conditions
5. Diff performance metrics
6. Generate comparison report
`

---

## 5. Version History

### 5.1 History Tracking

| Event | Data Stored |
|-------|-------------|
| Created | Version, author, initial content |
| Modified | Changes, diff, author |
| Activated | Version, timestamp, reason |
| Deactivated | Version, timestamp, reason |
| Rolled back | From version, to version, reason |
| Performance updated | Score, metrics, timestamp |

### 5.2 Audit Trail

`
AuditEntry:
  entry_id: string
  timestamp: datetime
  action: string
  version_id: string
  author: string
  details: dict
  ip_address: string
  user_agent: string
`

---

## 6. Rollback Strategy

### 6.1 Automatic Rollback

`
Trigger: Performance score drops below threshold
  - Current score < 0.6
  - Score drop > 20% from previous
  - Error rate > 10%

Process:
1. Detect performance degradation
2. Identify last good version
3. Automatic rollback
4. Notify author
5. Create incident report
`

### 6.2 Manual Rollback

`
1. Author requests rollback
2. Select target version
3. Confirm rollback
4. Execute rollback
5. Validate result
6. Log rollback
`

---

## 7. A/B Testing Support

### 7.1 Test Configuration

`
ABTest:
  test_id: string
  name: string
  variants:
    - version_id: string
      weight: float (0-1)
      description: string
  duration: int (hours)
  metrics: list[string]
  min_sample: int
  confidence_level: float (0.95)
`

### 7.2 Test Execution

`
1. Create test with variants
2. Split traffic by weight
3. Collect metrics per variant
4. Calculate statistical significance
5. Determine winner
6. Auto-promote winner (optional)
7. Generate test report
`

---

## 8. Version Metadata

### 8.1 Required Fields

| Field | Type | Description |
|-------|------|-------------|
| version_id | string | Unique identifier |
| template_id | string | Parent template |
| version | string | Semantic version |
| author | string | Creator name |
| created_at | datetime | Creation time |
| content | dict | Template content |
| is_active | boolean | Currently active |

### 8.2 Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| changelog | string | Change description |
| parent_version | string | Previous version |
| performance_score | float | Quality score |
| test_results | dict | A/B test results |
| tags | list[string] | Classification tags |
| notes | string | Author notes |

---

## 9. Configuration

`yaml
prompt_versioning:
  enabled: true
  
  storage:
    backend: database
    max_versions_per_template: 50
    
  versioning:
    strategy: semantic
    auto_version: true
    
  rollback:
    enabled: true
    auto_rollback: true
    threshold: 0.6
    
  ab_testing:
    enabled: true
    min_sample: 100
    confidence: 0.95
    
  audit:
    enabled: true
    retention_days: 365
`
