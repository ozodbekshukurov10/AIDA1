# AIDA Refactoring Engine

**Document:** Book 2, Chapter 10 - Refactoring Engine
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Refactoring Engine automatically suggests and applies code improvements: rename, extract method, extract class, move file, split module, simplify logic, and dead code removal.

---

## 2. Refactoring Types

| Type | Description | Risk | Impact |
|------|-------------|------|--------|
| Rename | Rename symbol | Low | Readability |
| Extract Method | Extract code to function | Low | Maintainability |
| Extract Class | Extract to new class | Medium | SRP |
| Move File | Move to different location | Medium | Organization |
| Split Module | Split large module | High | Modularity |
| Simplify Logic | Reduce complexity | Low | Readability |
| Dead Code Removal | Remove unused code | Low | Cleanliness |

---

## 3. Detection Process

```
1. Analyze code quality metrics
2. Identify code smells:
   - Long method (>50 lines)
   - Large class (>500 lines)
   - Long parameter list (>5 params)
   - Duplicated code
   - Dead code
   - Feature envy
   - God class
   - Data clumps
3. Map smells to refactoring types
4. Estimate effort and risk
5. Prioritize by impact
6. Generate refactoring plan
```

---

## 4. Refactoring Plan

```
RefactoringPlan:
  target_file: string
  refactorings: list[Refactoring]
  estimated_effort: string
  risk_level: string
  expected_improvement: string

Refactoring:
  type: string
  description: string
  location: Location
  before: string (current code)
  after: string (refactored code)
  tests_required: list[string]
```

---

## 5. Safety Rules

```
Rule 1: Never refactor without tests
Rule 2: One refactoring at a time
Rule 3: Run tests after each change
Rule 4: Keep behavior identical
Rule 5: Version control before refactoring
```

---

## 6. Configuration

```yaml
refactoring_engine:
  enabled: true
  auto_suggest: true
  types: [rename, extract_method, extract_class, move_file, split_module, simplify, dead_code]
  safety:
    require_tests: true
    require_review: true
    max_risk: medium
```
