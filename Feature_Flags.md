# AIDA — Enterprise Feature Flag System

## 1. Design Philosophy

Feature flags — bu kod o'zgartirmasdan va qayta deploy qilmasdan imkoniyatlarni yoqish/o'chirish tizimi. AIDA flag tizimi 5 darajali granularity bilan ishlaydi:

```
Global Level       ─── barcha user/tenant larga ta'sir qiladi
Environment Level  ─── development / staging / production
Tenant Level       ─── per-organization (Enterprise multi-tenant)
User Level         ─── per-user (beta program, A/B testing)
Session Level      ─── per-request (eksperimentlar)
```

**Current Status**: Feature flag tizimi hali implementatsiya qilinmagan. Quyidagi dizayn implementatsiya uchun tayyor.

## 2. Flag Registry

### 2.1 Built-in Flags

```yaml
# aida/config/feature_flags.yaml
features:
  voice:
    description: "Voice input/output support"
    default: false
    type: boolean
    environments: [development, staging]
    owner: product-team
    stage: BETA

  vision:
    description: "Image recognition and processing"
    default: false
    type: boolean
    environments: [development, staging, production]
    owner: ml-team
    stage: BETA

  rag:
    description: "Retrieval-Augmented Generation"
    default: true
    type: boolean
    environments: [development, staging, production]
    owner: ml-team
    stage: GA

  memory:
    description: "Persistent conversation memory"
    default: true
    type: boolean
    environments: [development, staging, production]
    owner: core-team
    stage: GA

  agents:
    description: "Multi-agent orchestration"
    default: true
    type: boolean
    environments: [development, staging, production]
    owner: agents-team
    stage: GA

  docker:
    description: "Docker container management via AIDA"
    default: false
    type: boolean
    environments: [development, staging]
    owner: devops-team
    stage: ALPHA

  github:
    description: "GitHub integration (PR, issues, code review)"
    default: false
    type: boolean
    environments: [development, staging, production]
    owner: integrations-team
    stage: BETA

  internet_search:
    description: "Live internet search capability"
    default: false
    type: boolean
    environments: [development, staging, production]
    owner: search-team
    stage: BETA

  browser:
    description: "Headless browser automation"
    default: false
    type: boolean
    environments: [development, staging]
    owner: automation-team
    stage: ALPHA

  auto_mode:
    description: "Autonomous task execution mode"
    default: true
    type: boolean
    environments: [development, staging, production]
    owner: core-team
    stage: GA

  plugins:
    description: "Third-party plugin system"
    default: true
    type: boolean
    environments: [development, staging, production]
    owner: platform-team
    stage: GA

  streaming:
    description: "Real-time streaming responses"
    default: true
    type: boolean
    environments: [development, staging, production]
    owner: core-team
    stage: GA

  batch_processing:
    description: "Batch task processing"
    default: false
    type: boolean
    environments: [development, staging, production]
    owner: infra-team
    stage: BETA

  audit_logging:
    description: "Detailed audit logging"
    default: true
    type: boolean
    environments: [staging, production]
    owner: security-team
    stage: GA

  multi_tenant:
    description: "Multi-tenant isolation"
    default: false
    type: boolean
    environments: [production]
    owner: enterprise-team
    stage: ALPHA

  experimental_models:
    description: "Enable experimental/unstable models"
    default: false
    type: boolean
    environments: [development]
    owner: ml-team
    stage: ALPHA
```

### 2.2 Custom Flags

Plugins va modullar o'z flaglarini ro'yxatdan o'tkazadi:

```python
from aida.feature_flags import register_flag

register_flag(
    name="my_plugin_premium",
    description="Enable premium features in MyPlugin",
    default=False,
    type=bool,
    owner="plugin-team",
    stage="BETA",
)
```

## 3. Flag Evaluation Engine

### 3.1 Resolution Order

```
1. Session-level override        ← Request context (cookies, headers)
2. User-level override           ← User profile (database)
3. Tenant-level override         ← Tenant settings (database)
4. Environment-level override    ← config/{env}.yaml
5. Environment variables         ← FFLAG_* env vars
6. Global default                ← feature_flags.yaml
```

### 3.2 Evaluation API

```python
from aida.feature_flags import feature_flag

# Simple check
if feature_flag("rag", user=current_user):
    enable_rag_pipeline()

# With tenant context
if feature_flag("plugins", tenant=current_tenant):
    load_plugins()

# Decorator pattern
@feature_flag("streaming")
async def chat_handler(request):
    ...

# With context manager
with feature_flag.override("vision", True, session=request.session):
    process_image()
```

### 3.3 Caching Strategy

```python
# L1: In-memory cache (dict, < 1ms)
# L2: Redis cache (60s TTL, < 5ms)
# L3: Database (fallback)

cache_key = f"fflag:{tenant_id}:{user_id}:{flag_name}"

# L1 check
if cache_key in local_cache:
    return local_cache[cache_key]

# L2 check
result = redis.get(cache_key)
if result is not None:
    local_cache[cache_key] = result
    return result

# L3 evaluate
result = evaluate_flag(flag_name, tenant_id, user_id)
redis.set(cache_key, result, ex=60)
local_cache[cache_key] = result
return result
```

### 3.4 Performance Targets

| Metric | Target | Method |
|--------|--------|--------|
| Evaluation latency | < 1ms | L1 in-memory cache + L2 Redis |
| Cache hit rate | > 99% | 60s TTL, instant invalidation on change |
| Memory per flag | < 100 bytes | Compact struct |
| Concurrent evaluations | > 10,000/s | Lock-free reads (immutable flag state) |

## 4. Flag Lifecycle

```
PROPOSED  →  ALPHA  →  BETA  →  GA  →  SUNSET  →  REMOVED
```

| Stage | Default | Environment | Description |
|-------|---------|-------------|-------------|
| **PROPOSED** | `false` | — | Under discussion, not yet implemented |
| **ALPHA** | `false` | development | Internal testing, unstable |
| **BETA** | `false` | dev + staging | Limited external testing |
| **GA** | `true` | all environments | Stable, fully supported |
| **SUNSET** | `true` (with warning) | all | Deprecated, warning in logs |
| **REMOVED** | — | — | Code deleted |

## 5. Gradual Rollout

### 5.1 Percentage-Based Rollout

```yaml
flag:
  name: agents_v2
  rollout:
    percentage: 25           # 25% users for
    strategy: user_id_hash   # Deterministic per user
```

```python
def should_enable(flag, user_id):
    if flag.rollout.percentage >= 100:
        return True
    if flag.rollout.strategy == "user_id_hash":
        return (hash(user_id) % 100) < flag.rollout.percentage
    return False
```

### 5.2 A/B Testing

```yaml
flag:
  name: new_chat_ui
  experiments:
    - name: "v2-chat-ui"
      variants:
        control: {percentage: 50}
        treatment: {percentage: 50}
```

### 5.3 Targeted Rollout

```yaml
flag:
  name: premium_voice
  rules:
    - if: user.tier == "premium"
      then: true
    - if: user.tier == "free"
      then: false
```

## 6. Admin Interface

### 6.1 REST API

```
GET    /api/v1/admin/feature-flags              — List all flags with current values
GET    /api/v1/admin/feature-flags/:name         — Get flag details
PUT    /api/v1/admin/feature-flags/:name         — Set override (body: {value, level, reason})
DELETE /api/v1/admin/feature-flags/:name         — Remove override
POST   /api/v1/admin/feature-flags/:name/rollout — Set percentage rollout
```

### 6.2 CLI

```bash
# List all flags
aida feature-flags list

# Get flag status with context
aida feature-flags get rag --tenant acme --user bob

# Set global override
aida feature-flags set rag true --reason "GA release"

# Set user-level override
aida feature-flags set rag false --user bob --reason "beta opt-out"

# Gradual rollout
aida feature-flags rollout agents_v2 25 --strategy user_id_hash

# Environment comparison
aida feature-flags diff --from staging --to production
```

## 7. Audit & Monitoring

### 7.1 Evaluation Audit

```json
{
  "event": "feature_flag_evaluated",
  "flag": "rag",
  "result": true,
  "user": "user_abc",
  "tenant": "tenant_xyz",
  "request_id": "req-123",
  "timestamp": "2026-07-03T12:00:00Z"
}
```

### 7.2 Change Audit

```json
{
  "event": "feature_flag_changed",
  "flag": "agents",
  "old_value": false,
  "new_value": true,
  "level": "global",
  "changed_by": "admin@example.com",
  "reason": "GA release v2.1.0",
  "timestamp": "2026-07-03T12:00:00Z"
}
```

## 8. Code Integration Patterns

### 8.1 In Code

```python
from aida.feature_flags import feature_flag

# Feature-gated code path
if feature_flag("voice"):
    from aida.kernel.voice import VoiceProcessor
    voice = VoiceProcessor()
    result = voice.process(audio)

# Feature-gated view/endpoint
@router.post("/chat/stream")
@feature_flag("streaming")
async def stream_chat(request):
    ...

# Feature-gated import
import importlib

def get_agent_orchestrator():
    if feature_flag("agents", user=current_user):
        module = importlib.import_module("aida.kernel.agents")
        return module.AgentOrchestrator()
    return SimpleOrchestrator()
```

### 8.2 In Templates

```html
{% if feature_flag("voice", request) %}
  <button onclick="startVoice()">Voice Input</button>
{% endif %}
```

### 8.3 In Frontend

```typescript
// API returns active flags per session
const flags = await api.get('/api/v1/feature-flags');

if (flags.voice) {
    enableVoiceButton();
}
```

## 9. Storage Schema

### 9.1 Database Table

```sql
CREATE TABLE feature_flag_overrides (
    id UUID PRIMARY KEY,
    flag_name VARCHAR(128) NOT NULL,
    level VARCHAR(16) NOT NULL,       -- 'global', 'environment', 'tenant', 'user'
    level_id VARCHAR(64),             -- tenant_id, user_id, environment
    value BOOLEAN NOT NULL,
    reason TEXT,
    created_by VARCHAR(128),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,  -- TTL for temporary overrides
    UNIQUE(flag_name, level, level_id)
);
```

### 9.2 Redis Cache Keys

```
fflag:global:{flag_name}
fflag:env:{environment}:{flag_name}
fflag:tenant:{tenant_id}:{flag_name}
fflag:user:{user_id}:{flag_name}
fflag:session:{session_id}:{flag_name}
```

## 10. Flag Cleanup Policy

| Stage | Action | Timeline |
|-------|--------|----------|
| **SUNSET** | Log deprecation warning, allow override | 2 release cycles |
| **REMOVED** | Delete flag registry, remove code branches | After sunset period |
| **Hardcoded check** | Lint rule `FIXME-flag` warns | On every commit |

```python
# Example: flag approaching removal
@feature_flag("old_feature", sunset="2026-09-01")
def old_functionality():
    # TODO: Remove after sunset date
    pass
```
