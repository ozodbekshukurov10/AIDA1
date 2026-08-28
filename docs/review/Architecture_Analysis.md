# AIDA Architecture Analysis

**Document:** Book 2, Chapter 10 - Architecture Analysis
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

Architecture Analysis automatically detects and evaluates the architectural style of a repository: Layered, Clean, Hexagonal, DDD, MVC, Microservice, or Monolith.

---

## 2. Architecture Styles

| Style | Key Characteristics | Detection Signals |
|-------|---------------------|-------------------|
| Layered | UI -> Business -> Data | controller/, service/, repository/ |
| Clean | Entities, Use Cases, Interface Adapters | domain/, application/, infrastructure/ |
| Hexagonal | Ports and Adapters | ports/, adapters/, core/ |
| DDD | Bounded Contexts, Aggregates | domain/, contexts/, aggregates/ |
| MVC | Model-View-Controller | models/, views/, controllers/ |
| Microservice | Independent services | services/, gateway/, shared/ |
| Monolith | Single deployment unit | Single codebase, no service split |

---

## 3. Detection Algorithm

```
1. Analyze folder structure
2. Map directories to patterns
3. Score against each architecture style
4. Select highest scoring style
5. Generate architecture report
```

### 3.1 Pattern Matching

| Pattern | Layered | Clean | Hex | DDD | MVC |
|---------|---------|-------|-----|-----|-----|
| controllers/ | 1.0 | 0.3 | 0.3 | 0.3 | 1.0 |
| services/ | 1.0 | 0.5 | 0.3 | 0.5 | 0.5 |
| repositories/ | 1.0 | 0.5 | 0.5 | 0.5 | 0.3 |
| domain/ | 0.3 | 1.0 | 0.5 | 1.0 | 0.0 |
| application/ | 0.3 | 1.0 | 0.3 | 0.5 | 0.0 |
| infrastructure/ | 0.5 | 1.0 | 1.0 | 0.5 | 0.3 |
| ports/ | 0.0 | 0.5 | 1.0 | 0.3 | 0.0 |
| adapters/ | 0.0 | 0.5 | 1.0 | 0.3 | 0.0 |
| models/ | 0.5 | 0.3 | 0.3 | 0.5 | 1.0 |
| views/ | 0.3 | 0.0 | 0.0 | 0.0 | 1.0 |
| services/ (micro) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

---

## 4. Architecture Report

```
ArchitectureReport:
  detected_style: string
  confidence: float
  layers: list[Layer]
  violations: list[Violation]
  recommendations: list[string]
  score: float (0-100)

Layer:
  name: string
  components: list[string]
  dependencies: list[string]
  violates_direction: list[string]
```

---

## 5. Violation Detection

| Violation | Description | Severity |
|-----------|-------------|----------|
| Layer Skip | UI directly accesses Data | High |
| Circular Dep | Module A depends on B, B on A | High |
| God Class | Class with > 500 lines | Medium |
| Feature Envy | Module uses other module heavily | Medium |
| Dead Code | Unreachable code | Low |

---

## 6. Configuration

```yaml
architecture_analysis:
  enabled: true
  auto_detect: true
  styles: [layered, clean, hexagonal, ddd, mvc, microservice, monolith]
  violation_detection: true
  min_confidence: 0.6
```
