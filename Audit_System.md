# AIDA — Enterprise Audit System

## 1. Design Principles

Audit tizimi AIDA'dagi barcha muhim o'zgarishlarni **append-only**, **tamper-evident** va **immutable** tarzda qayd qiladi.

```
┌──────────────────────────────────────────────────────────┐
│                  AUDIT PRINCIPLES                         │
│                                                          │
│  ✅ Append-only — hech qachon o'chirilmaydi              │
│  ✅ Immutable — bir marta yozilgan, o'zgartirilmaydi     │
│  ✅ Tamper-evident — har qanday o'zgartirish aniqlanadi  │
│  ✅ Timestamped — har bir yozuvda aniq vaqt              │
│  ✅ Actor-tracked — kim o'zgartirgani ma'lum             │
│  ✅ Reason-required — nima uchun o'zgartirilgani ma'lum  │
│  ✅ Verifiable — audit chain tekshirilishi mumkin         │
└──────────────────────────────────────────────────────────┘
```

**Current Status**: Audit tizimi hali implementatsiya qilinmagan. Hech qanday audit logging mavjud emas.

## 2. Audit Event Categories

### 2.1 Configuration Changes

Har bir konfiguratsiya o'zgarishi audit qilinadi:

| Event | Description | Severity |
|-------|-------------|----------|
| `config.key.changed` | Config key qiymati o'zgartirildi | MEDIUM |
| `config.key.deleted` | Config key o'chirildi | HIGH |
| `config.file.reloaded` | Config fayl qayta yuklandi | MEDIUM |
| `config.env.override` | Environment override qo'llandi | LOW |
| `config.secret.rotated` | Secret key rotatsiya qilindi | CRITICAL |

```json
{
  "event": "config.key.changed",
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "actor": {
    "user_id": "user_admin_001",
    "username": "admin@example.com",
    "ip_address": "192.168.1.100",
    "session_id": "sess_abc123"
  },
  "target": {
    "key": "models.openai.api_key",
    "previous_value": null,
    "new_value": "[REDACTED]"
  },
  "source": "admin_api",
  "reason": "Initial configuration setup",
  "request_id": "req_xyz789"
}
```

### 2.2 Plugin Lifecycle

| Event | Description | Severity |
|-------|-------------|----------|
| `plugin.installed` | Yangi plugin o'rnatildi | HIGH |
| `plugin.removed` | Plugin o'chirildi | HIGH |
| `plugin.enabled` | Plugin yoqildi | MEDIUM |
| `plugin.disabled` | Plugin o'chirildi | MEDIUM |
| `plugin.updated` | Plugin yangilandi | MEDIUM |
| `plugin.permission.changed` | Plugin ruxsatlari o'zgartirildi | HIGH |

```json
{
  "event": "plugin.installed",
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "actor": {
    "user_id": "user_admin_001",
    "username": "admin@example.com"
  },
  "target": {
    "plugin_name": "custom-code-analyzer",
    "plugin_version": "1.2.0",
    "source": "registry.example.com",
    "checksum": "sha256:a1b2c3..."
  },
  "permissions": [
    "filesystem.read",
    "network.http"
  ],
  "source": "admin_api",
  "reason": "Security audit requirement"
}
```

### 2.3 Agent Changes

| Event | Description | Severity |
|-------|-------------|----------|
| `agent.created` | Yangi agent yaratildi | LOW |
| `agent.deleted` | Agent o'chirildi | MEDIUM |
| `agent.config.changed` | Agent konfiguratsiyasi o'zgartirildi | LOW |
| `agent.model.changed` | Agent modeli o'zgartirildi | MEDIUM |
| `agent.tools.changed` | Agent tool lari o'zgartirildi | MEDIUM |
| `agent.prompt.updated` | Agent system prompti o'zgartirildi | HIGH |

```json
{
  "event": "agent.model.changed",
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "actor": {
    "user_id": "user_dev_042",
    "username": "developer@example.com"
  },
  "target": {
    "agent_id": "agent_code_review",
    "agent_name": "Code Review Agent",
    "previous_model": "gpt-4",
    "new_model": "gpt-4o",
    "previous_provider": "openai",
    "new_provider": "openai"
  },
  "source": "web_ui",
  "reason": "Performance upgrade"
}
```

### 2.4 Model Changes

| Event | Description | Severity |
|-------|-------------|----------|
| `model.provider.added` | Yangi model provider qo'shildi | MEDIUM |
| `model.provider.removed` | Provider o'chirildi | HIGH |
| `model.default.changed` | Default model o'zgartirildi | MEDIUM |
| `model.parameters.updated` | Model parametrlari o'zgartirildi | LOW |

### 2.5 Database Migrations

| Event | Description | Severity |
|-------|-------------|----------|
| `db.migration.applied` | Migratsiya qo'llanildi | HIGH |
| `db.migration.reverted` | Migratsiya qaytarildi | CRITICAL |
| `db.backup.created` | Backup yaratildi | MEDIUM |
| `db.backup.restored` | Backup tiklandi | CRITICAL |
| `db.schema.changed` | Schema o'zgartirildi | HIGH |

```json
{
  "event": "db.migration.applied",
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "actor": {
    "user_id": "system",
    "username": "deployment-pipeline"
  },
  "target": {
    "migration_id": "0042_add_vector_index",
    "previous_revision": "0041_add_user_preferences",
    "new_revision": "0042_add_vector_index"
  },
  "source": "alembic",
  "duration_ms": 1234,
  "reason": "Scheduled deployment v2.3.1"
}
```

### 2.6 Deployments

| Event | Description | Severity |
|-------|-------------|----------|
| `deployment.started` | Deploy boshlandi | HIGH |
| `deployment.completed` | Deploy muvaffaqiyatli tugadi | HIGH |
| `deployment.failed` | Deploy muvaffaqiyatsiz tugadi | CRITICAL |
| `deployment.rolled_back` | Deploy orqaga qaytarildi | CRITICAL |
| `deployment.health_check.failed` | Health check o'tmadi | CRITICAL |

```json
{
  "event": "deployment.completed",
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "actor": {
    "user_id": "system",
    "username": "ci-cd-pipeline"
  },
  "target": {
    "version": "2.3.1",
    "commit": "a1b2c3d4e5f6...",
    "branch": "main",
    "environment": "production"
  },
  "changes": [
    "feat: add vector search indexing",
    "fix: rate limiting for streaming endpoints"
  ],
  "duration_ms": 45678
}
```

### 2.7 Admin Actions

| Event | Description | Severity |
|-------|-------------|----------|
| `admin.user.created` | Yangi admin foydalanuvchi yaratildi | HIGH |
| `admin.user.deleted` | Admin foydalanuvchi o'chirildi | CRITICAL |
| `admin.user.role.changed` | Admin roli o'zgartirildi | HIGH |
| `admin.user.suspended` | Admin hisobi bloklandi | CRITICAL |
| `admin.user.unsuspended` | Admin hisobi tiklandi | HIGH |
| `admin.api_key.generated` | API key generatsiya qilindi | HIGH |
| `admin.api_key.revoked` | API key bekor qilindi | HIGH |

```json
{
  "event": "admin.user.role.changed",
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "actor": {
    "user_id": "user_superadmin_001",
    "username": "superadmin@example.com"
  },
  "target": {
    "user_id": "user_dev_042",
    "previous_role": "developer",
    "new_role": "admin"
  },
  "source": "admin_ui",
  "reason": "Promotion to team lead",
  "request_id": "req_admin_456"
}
```

### 2.8 Feature Flag Changes

| Event | Description | Severity |
|-------|-------------|----------|
| `feature_flag.created` | Yangi feature flag yaratildi | LOW |
| `feature_flag.enabled` | Feature flag yoqildi | MEDIUM |
| `feature_flag.disabled` | Feature flag o'chirildi | MEDIUM |
| `feature_flag.rollout.changed` | Rollout foizi o'zgartirildi | MEDIUM |
| `feature_flag.deleted` | Feature flag o'chirildi | LOW |

## 3. Audit Log Schema

### 3.1 Base Audit Event

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "audit_id",
    "event",
    "timestamp",
    "actor",
    "target",
    "source"
  ],
  "properties": {
    "audit_id": {
      "type": "string",
      "description": "Unique audit event ID (UUID v4)"
    },
    "event": {
      "type": "string",
      "pattern": "^[a-z]+\\.[a-z]+\\.[a-z]+$",
      "description": "Event type in dot notation"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 with microseconds"
    },
    "actor": {
      "type": "object",
      "required": ["user_id", "username"],
      "properties": {
        "user_id": {"type": "string"},
        "username": {"type": "string"},
        "ip_address": {"type": "string", "format": "ip"},
        "session_id": {"type": "string"},
        "roles": {"type": "array", "items": {"type": "string"}}
      }
    },
    "target": {
      "type": "object",
      "description": "What was changed (event-specific)"
    },
    "source": {
      "type": "string",
      "enum": ["admin_api", "admin_ui", "cli", "web_ui", "system", "plugin", "migration", "ci-cd"]
    },
    "reason": {
      "type": "string",
      "description": "Why the change was made"
    },
    "request_id": {
      "type": "string",
      "description": "Correlating request ID"
    },
    "fingerprint": {
      "type": "string",
      "description": "SHA-256 of previous entry + current entry (tamper evidence)"
    }
  }
}
```

### 3.2 Tamper-Evident Chain

Har bir audit entry oldingi entry ning hashini o'z ichiga oladi:

```python
# aida/audit/chain.py
import hashlib
import json

class AuditChain:
    def __init__(self, chain_file: str):
        self.chain_file = chain_file
        self._previous_hash = self._get_last_hash()

    def _get_last_hash(self) -> str:
        try:
            with open(self.chain_file, "r") as f:
                for line in f:
                    pass
                last_entry = json.loads(line)
                return last_entry.get("fingerprint", "")
        except (FileNotFoundError, json.JSONDecodeError):
            return "0" * 64  # Genesis block

    def append(self, entry: dict) -> dict:
        entry["fingerprint"] = hashlib.sha256(
            (self._previous_hash + json.dumps(entry, sort_keys=True)).encode()
        ).hexdigest()
        self._previous_hash = entry["fingerprint"]
        return entry
```

## 4. Audit Log Storage

### 4.1 File Structure

```
logs/audit/
├── 2026/
│   ├── 07/
│   │   ├── audit.2026-07-01.jsonl      # Daily audit files
│   │   ├── audit.2026-07-02.jsonl
│   │   ├── audit.2026-07-03.jsonl
│   │   └── ...
│   └── ...
└── current -> 2026/07/audit.2026-07-03.jsonl  # Symlink to current
```

### 4.2 Storage Characteristics

| Property | Value |
|----------|-------|
| Format | JSONL (JSON Lines, append-only) |
| Rotation | Daily |
| Compression | gzip after 30 days |
| Archive | Yearly to cold storage |
| Encryption | AES-256-GCM at rest |
| Access | Read-only for auditors, append-only for logger |
| Immutability | WORM (Write Once Read Many) filesystem |

### 4.3 Audit Retention

| Period | Storage Type | Retention | Action |
|--------|-------------|-----------|--------|
| Current month | Hot (SSD) | 90 days | Immediate query |
| Past 3 months | Warm (HDD) | 1 year | Compressed, queryable |
| Past years | Cold (S3/Glacier) | 7 years | Archived, manual restore |
| Compliance | Glacier Deep Archive | 10 years | Regulatory only |

## 5. Audit API

### 5.1 Query Endpoints

```
GET    /api/v1/admin/audit                          — List audit events (paginated)
GET    /api/v1/admin/audit?event=config.key.changed  — Filter by event type
GET    /api/v1/admin/audit?actor=user_admin_001       — Filter by actor
GET    /api/v1/admin/audit?from=2026-07-01&to=2026-07-03  — Date range
GET    /api/v1/admin/audit/:audit_id                  — Single event detail
GET    /api/v1/admin/audit/chain/verify               — Verify chain integrity
GET    /api/v1/admin/audit/stats                      — Audit volume statistics
```

### 5.2 CLI

```bash
# Query audit log
aida audit list --event config.key.changed --from 2026-07-01

# Verify audit chain integrity
aida audit verify --chain logs/audit/2026/07/audit.2026-07-03.jsonl

# Export audit events
aida audit export --from 2026-01-01 --to 2026-07-03 --format json

# Audit statistics
aida audit stats --period 30d
```

## 6. Code Integration

### 6.1 Audit Logger

```python
# aida/infrastructure/audit/__init__.py
from aida.infrastructure.logging import get_logger

audit_logger = get_logger("audit")

def audit_event(event: str, actor: dict, target: dict, source: str, reason: str = ""):
    """Log an audit event with standardized schema."""
    audit_logger.info(
        "Audit: %s by %s on %s — %s",
        event,
        actor.get("username", "unknown"),
        target.get("key", str(target)),
        reason,
        extra={
            "audit_id": generate_uuid(),
            "event": event,
            "actor": actor,
            "target": target,
            "source": source,
            "reason": reason,
        }
    )
```

### 6.2 Decorator

```python
# aida/infrastructure/audit/decorators.py
from functools import wraps

def audit_log(event_type: str, source: str = "system"):
    """Decorator that automatically logs audit events for function calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            audit_event(
                event=event_type,
                actor={"user_id": get_current_user(), "username": get_current_username()},
                target={"function": func.__name__, "args": sanitize_args(kwargs)},
                source=source,
                reason=kwargs.get("reason", "No reason provided")
            )
            return result
        return wrapper
    return decorator

# Usage
@audit_log("plugin.installed", source="admin_api")
def install_plugin(plugin_name: str, reason: str = ""):
    ...
```

### 6.3 Context Manager

```python
# aida/infrastructure/audit/context.py
from contextlib import contextmanager

@contextmanager
def audit_context(event: str, actor: dict, target: dict, source: str):
    """Context manager that logs start and end of an operation."""
    try:
        audit_event(f"{event}.started", actor, target, source)
        yield
        audit_event(f"{event}.completed", actor, target, source)
    except Exception as e:
        audit_event(f"{event}.failed", actor, {**target, "error": str(e)}, source)
        raise
```

## 7. Compliance Requirements

| Standard | Audit Requirement | AIDA Implementation |
|----------|------------------|---------------------|
| SOC 2 | Access control audit | All admin actions logged |
| SOC 2 | Change management | Config + deployment audit |
| GDPR | Data access logging | User data access audit |
| HIPAA | Access and disclosure | All PHI access logged |
| PCI DSS | Track all access to cardholder data | Payment-related audit |
| SOX | Financial controls | Configuration change audit |
| ISO 27001 | Audit logging | Full event coverage |

## 8. Implementation Priority

| Phase | Component | Priority | Effort |
|-------|-----------|----------|--------|
| P0 | Basic audit logger (`audit_event()`) | CRITICAL | Small |
| P0 | Admin action audit events | CRITICAL | Small |
| P1 | Config change audit events | HIGH | Small |
| P1 | Plugin lifecycle audit | HIGH | Small |
| P1 | Separate audit log file (JSONL) | HIGH | Medium |
| P2 | Deployment audit events | MEDIUM | Small |
| P2 | Database migration audit | MEDIUM | Medium |
| P3 | Tamper-evident chain (SHA-256) | LOW | Medium |
| P3 | Audit query API | LOW | Large |
| P3 | Audit chain verification CLI | LOW | Medium |
