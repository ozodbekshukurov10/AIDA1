# AIDA Patch Engine

**Document:** Book 2, Chapter 10 - Patch Engine
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Patch Engine generates **minimal, safe patches** with rollback support, diff preview, and conflict detection. Patches are atomic changes that can be applied, reviewed, and reverted cleanly.

---

## 2. Patch Properties

| Property | Description | Requirement |
|----------|-------------|-------------|
| Minimal | Smallest possible change | Required |
| Safe | No breaking changes | Required |
| Atomic | Single logical change | Required |
| Reversible | Can be rolled back | Required |
| Testable | Includes test verification | Recommended |
| Documented | Includes change description | Recommended |

---

## 3. Patch Generation Pipeline

```
Change Request
     |
     v
+---------------------+
| Impact Analysis     |
| - Affected files    |
| - Affected tests    |
+----------+----------+
           |
           v
+---------------------+
| Patch Generator     |
| - Generate diff     |
| - Validate minimal  |
+----------+----------+
           |
           v
+---------------------+
| Safety Validator    |
| - Check no breakage |
| - Check no side effects|
+----------+----------+
           |
           v
+---------------------+
| Conflict Detector   |
| - Check merge conflicts|
| - Check dependencies|
+----------+----------+
           |
           v
Patch File
```

---

## 4. Patch Structure

```
Patch:
  patch_id: string
  description: string
  author: string
  created_at: datetime
  files: list[PatchFile]
  tests: list[string]
  rollback_command: string
  risk_level: string
  conflicts: list[Conflict]

PatchFile:
  path: string
  action: string (add|modify|delete)
  diff: string (unified diff)
  lines_added: int
  lines_removed: int
```

---

## 5. Diff Preview

```
--- a/src/auth.py
+++ b/src/auth.py
@@ -10,7 +10,7 @@
 def login(username, password):
-    if user is None:
-        return None
+    if user is None:
+        raise AuthError("User not found")
```

---

## 6. Configuration

```yaml
patch_engine:
  enabled: true
  auto_generate: true
  
  properties:
    minimal: true
    safe: true
    atomic: true
    reversible: true
  
  validation:
    run_tests: true
    check_conflicts: true
    require_approval: true
  
  rollback:
    enabled: true
    auto_rollback_on_failure: true
```
