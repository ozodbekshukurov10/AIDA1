# AIDA — Enterprise Configuration Validation Rules

## 1. Validation Pipeline

Configuration validation startup vaqtida, hech qanday service ishga tushishidan oldin bajariladi. **Fail-fast** — agar kritik qoida bajarilmasa, process aniq xato xabari bilan to'xtaydi.

```
Raw Config  →  Schema Validation  →  Type Checking  →  Business Rules  →  Connection Checks  →  Frozen Config
```

## 2. Current Validation State

### 2.1 What Exists Today

| Validation | Status | Location |
|------------|--------|----------|
| Django SECRET_KEY auto-fallback | ✅ Active | `AIDA/settings.py:18` |
| Provider endpoint config | ✅ Active | `aidaos/infrastructure/config/settings.py` |
| Exposed secret detection | ✅ Active | `webapp/repo_analyzer/quality.py:184` |
| JSON Schema validation | ❌ Not implemented | Planned for `aida/config/schema.yaml` |
| Type checking | ❌ Not implemented | Planned |
| Connection checks | ❌ Not implemented | Planned |
| Business rules (prod checks) | ❌ Not implemented | Planned |

### 2.2 Validation Gaps

- Hech qanday schema validation mavjud emas
- Type checking `str` ga asoslangan (int/float/bool tekshirilmaydi)
- Majburiy maydonlar runtime da `AttributeError` yoki `None` bilan tugaydi
- Connection checks faqat runtime da, config load vaqtida emas

## 3. Schema Validation (JSON Schema)

### 3.1 Schema Definition

```yaml
# aida/config/schema.yaml
$schema: http://json-schema.org/draft-07/schema#
type: object
required: [app, database, redis, logging, security]
properties:
  app:
    type: object
    required: [name, version, debug]
    properties:
      name: {type: string, minLength: 1}
      version: {type: string, pattern: "^\\d+\\.\\d+\\.\\d+"}
      debug: {type: boolean}
      secret_key:
        type: string
        minLength: 32
        description: "Required in production. Generate: openssl rand -hex 32"
      port:
        type: integer
        minimum: 1024
        maximum: 65535
        default: 8000
      host:
        type: string
        default: "0.0.0.0"

  database:
    type: object
    required: [url]
    properties:
      url:
        type: string
        pattern: "^(sqlite|postgresql|mysql)://"
      pool_size:
        type: integer
        minimum: 1
        maximum: 100
        default: 5
      max_overflow:
        type: integer
        minimum: 0
        maximum: 200
        default: 10

  redis:
    type: object
    required: [url]
    properties:
      url:
        type: string
        pattern: "^redis://"
      socket_timeout:
        type: integer
        minimum: 1
        maximum: 60
        default: 5

  models:
    type: object
    properties:
      default_provider: {type: string}
      providers:
        type: object
        properties:
          openai:
            type: object
            properties:
              api_key:
                type: string
                pattern: "^sk-"
          anthropic:
            type: object
            properties:
              api_key:
                type: string
                pattern: "^sk-ant-"
          ollama:
            type: object
            properties:
              url:
                type: string
                format: uri

  security:
    type: object
    required: [jwt_secret]
    properties:
      jwt_secret:
        type: string
        minLength: 32
      cors_origins:
        type: array
        items: {type: string, format: uri}
      allowed_hosts:
        type: array
        items: {type: string}

  logging:
    type: object
    required: [level]
    properties:
      level:
        type: string
        enum: [DEBUG, INFO, WARNING, ERROR, CRITICAL]
      format:
        type: string
        enum: [json, text]
        default: json
```

## 4. Type Checking Rules

### 4.1 Core Type Map

| Config Key | Expected Type | Current | Validation | Error Message |
|------------|---------------|---------|------------|---------------|
| `app.debug` | `bool` | `str` | Must be `true`/`false` | `app.debug must be boolean (true/false)` |
| `app.port` | `int` | `str` | 1024 ≤ port ≤ 65535 | `app.port must be integer 1024-65535` |
| `database.pool_size` | `int` | `str` | ≥ 1 | `database.pool_size must be ≥ 1` |
| `database.url` | `str` | `str` | Valid scheme | `database.url must start with sqlite://, postgresql://, or mysql://` |
| `redis.url` | `str` | `str` | Must start with `redis://` | `redis.url must start with redis://` |
| `logging.level` | `str` | `str` | Enum check | `logging.level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL` |
| `security.cors_origins` | `list[str]` | `str` | URI validation | `security.cors_origins[0] is not a valid URI` |
| `models.providers.openai.api_key` | `str` | `str` | Pattern `^sk-` | `OpenAI API key must start with 'sk-'` |
| `ollama.timeout` | `int` | `str` | > 0 | `ollama.timeout must be positive integer` |
| `rate_limit` | `int` | `int` | > 0 | `rate_limit must be positive integer` |

### 4.2 Conversion Rules

Current system `str` formatda env var larni o'qiydi. Target type conversion:

```python
# aida/config/validator.py
TYPE_CONVERTERS = {
    bool: lambda v: str(v).lower() in ("true", "1", "yes"),
    int: lambda v: int(v),
    float: lambda v: float(v),
    str: lambda v: str(v),
    list: lambda v: [x.strip() for x in v.split(",") if x.strip()],
}

def convert_and_validate(key: str, value: str, target_type: type) -> Any:
    try:
        return TYPE_CONVERTERS[target_type](value)
    except (ValueError, TypeError):
        raise ValidationError(
            id="TYPE-001",
            key=key,
            message=f"Cannot convert '{value}' to {target_type.__name__}",
        )
```

## 5. Business Rules

### 5.1 Production Rules (PROD)

```yaml
rules:
  - id: PROD-001
    severity: CRITICAL
    description: "Secret key must be set and >= 32 characters"
    check: |
      len(config.app.secret_key) >= 32
    error: |
      [PROD-001] app.secret_key is not set or too short.
      Generate: openssl rand -hex 32
      Set in: .env.production or vault

  - id: PROD-002
    severity: CRITICAL
    description: "Debug mode must be disabled"
    check: |
      config.app.debug is False
    error: |
      [PROD-002] app.debug must be False in production.
      Set APP_DEBUG=false in your production environment.

  - id: PROD-003
    severity: CRITICAL
    description: "Database must be PostgreSQL in production"
    check: |
      config.database.url.startswith("postgresql")
    error: |
      [PROD-003] Production requires PostgreSQL.
      Current: {config.database.url}
      Set DATABASE_URL to a PostgreSQL connection string.

  - id: PROD-004
    severity: CRITICAL
    description: "JWT secret must be set and >= 32 characters"
    check: |
      len(config.security.jwt_secret) >= 32
    error: |
      [PROD-004] JWT secret is not set or too short.
      Generate: openssl rand -hex 32
      Set JWT_SECRET in vault.

  - id: PROD-005
    severity: HIGH
    description: "At least one model provider API key must be configured"
    check: |
      config.models.providers.openai.api_key is not None or
      config.models.providers.anthropic.api_key is not None
    error: |
      [PROD-005] No model provider API keys configured.
      Set at least: OPENAI_API_KEY or ANTHROPIC_API_KEY.

  - id: PROD-006
    severity: MEDIUM
    description: "Redis must be configured (not in-memory cache)"
    check: |
      config.cache.provider == "redis"
    error: |
      [PROD-006] Production requires Redis cache.
      Set CACHE_PROVIDER=redis and REDIS_URL.

  - id: PROD-007
    severity: MEDIUM
    description: "Allowed hosts must be restricted"
    check: |
      len(config.security.allowed_hosts) > 0 and
      "*" not in config.security.allowed_hosts
    error: |
      [PROD-007] Allowed hosts must be restricted in production.
      Set ALLOWED_HOSTS to specific domain(s).

  - id: PROD-008
    severity: HIGH
    description: "Vector DB must be configured for production"
    check: |
      config.vector_db.url is not None
    error: |
      [PROD-008] Vector DB URL not configured.
      Set VECTOR_DB_URL for production.
```

### 5.2 Security Rules (SEC)

```yaml
rules:
  - id: SEC-001
    severity: CRITICAL
    description: "Secret key is not the default value"
    check: |
      config.app.secret_key not in [None, "change-me", "dev-secret-key-not-for-production", "default"]
    error: |
      [SEC-001] Default/placeholder secret key detected.
      Generate: openssl rand -hex 32

  - id: SEC-002
    severity: CRITICAL
    description: "API keys are not exposed in URL"
    check: |
      "api_key" not in str(config.database.url).lower()
    error: |
      [SEC-002] API key found in database URL.
      Use secrets vault or environment variables instead.

  - id: SEC-003
    severity: HIGH
    description: "CORS origins are restricted"
    check: |
      "*" not in config.security.cors_origins or config.app.debug
    error: |
      [SEC-003] CORS origins set to wildcard in non-debug mode.
      Restrict to specific origins.

  - id: SEC-004
    severity: HIGH
    description: "JWT algorithm is not 'none'"
    check: |
      config.security.jwt_algorithm.lower() != "none"
    error: |
      [SEC-004] JWT algorithm set to 'none'. Signature verification disabled.

  - id: SEC-005
    severity: MEDIUM
    description: "Vector DB API key is configured for cloud providers"
    check: |
      if config.vector_db.provider in ["pinecone", "weaviate"]:
        config.vector_db.api_key is not None
      else:
        True
    error: |
      [SEC-005] {config.vector_db.provider} requires API key.
      Set VECTOR_DB_API_KEY.

  - id: SEC-006
    severity: HIGH
    description: "Rate limiting is enabled in production"
    check: |
      config.rate_limits.enabled is not False
    error: |
      [SEC-006] Rate limiting is disabled.
      Set RATE_LIMIT_ENABLED=true in production.

  - id: SEC-007
    severity: LOW
    description: "HTTPS redirect is enabled"
    check: |
      config.security.ssl_redirect or config.app.debug
    error: |
      [SEC-007] SSL redirect not enabled. Consider setting SECURE_SSL_REDIRECT=true.
```

### 5.3 Connection Rules (CONN)

```yaml
rules:
  - id: CONN-001
    severity: CRITICAL
    description: "Database is reachable"
    check: can_connect(config.database.url, timeout=5)
    error: |
      [CONN-001] Cannot connect to database.
      URL: {redact(config.database.url)}
      Check: Is the database running? Is the URL correct?

  - id: CONN-002
    severity: HIGH
    description: "Redis is reachable"
    check: can_connect(config.redis.url, timeout=3)
    error: |
      [CONN-002] Cannot connect to Redis.
      URL: {redact(config.redis.url)}
      Check: Is Redis running? Is the URL correct?

  - id: CONN-003
    severity: HIGH
    description: "Vector DB is reachable"
    check: can_connect(config.vector_db.url, timeout=5)
    error: |
      [CONN-003] Cannot connect to Vector DB.
      Provider: {config.vector_db.provider}
      URL: {redact(config.vector_db.url)}

  - id: CONN-004
    severity: MEDIUM
    description: "Default model provider is reachable"
    check: can_connect_to_model_provider(config.models.default_provider)
    error: |
      [CONN-004] Cannot connect to model provider.
      Provider: {config.models.default_provider}

  - id: CONN-005
    severity: LOW
    description: "Ollama is reachable (if enabled)"
    condition: config.models.providers.ollama.enabled
    check: can_connect(config.models.providers.ollama.url, timeout=5)
    error: |
      [CONN-005] Cannot connect to Ollama.
      URL: {config.models.providers.ollama.url}
```

### 5.4 Cross-Config Rules (CROSS)

```yaml
rules:
  - id: CROSS-001
    severity: HIGH
    description: "Embedding dimension matches vector DB"
    check: |
      config.embedding.dimension == config.vector_db.embedding_dim
    error: |
      [CROSS-001] Embedding dimension mismatch.
      Embedding: {config.embedding.dimension}
      Vector DB: {config.vector_db.embedding_dim}
      They must be equal.

  - id: CROSS-002
    severity: MEDIUM
    description: "Default provider has corresponding configuration"
    check: |
      provider = config.models.default_provider
      provider_config = config.models.providers.get(provider)
      provider_config is not None and (
        not provider_config.api_key or
        provider_config.url
      )
    error: |
      [CROSS-002] Default model provider '{config.models.default_provider}' is not configured.
      Check that the provider's URL and/or API key are set.

  - id: CROSS-003
    severity: LOW
    description: "Cache provider matches available infrastructure"
    check: |
      if config.cache.provider == "redis":
        config.redis.url is not None
      else:
        True
    error: |
      [CROSS-003] Cache provider set to 'redis' but Redis URL not configured.
      Set REDIS_URL or change CACHE_PROVIDER to 'memory'.

  - id: CROSS-004
    severity: MEDIUM
    description: "RAG requires vector DB configuration"
    check: |
      if config.rag.enabled:
        config.vector_db.url is not None
      else:
        True
    error: |
      [CROSS-004] RAG is enabled but Vector DB is not configured.
      Set VECTOR_DB_URL or disable RAG (RAG_ENABLED=false).
```

## 6. Validation Error Format

```json
{
  "status": "FAILED",
  "environment": "production",
  "timestamp": "2026-07-03T12:00:00Z",
  "errors": [
    {
      "id": "PROD-001",
      "severity": "CRITICAL",
      "key": "app.secret_key",
      "message": "Secret key is not set or too short",
      "expected": "string >= 32 characters",
      "actual": "None",
      "remediation": "Generate with: openssl rand -hex 32\nSet APP_SECRET_KEY in your environment or vault"
    },
    {
      "id": "PROD-003",
      "severity": "CRITICAL",
      "key": "database.url",
      "message": "Database must be PostgreSQL in production",
      "expected": "postgresql://...",
      "actual": "sqlite:///data/aida.db",
      "remediation": "Set DATABASE_URL to a PostgreSQL connection string"
    }
  ],
  "summary": {
    "total": 6,
    "critical": 2,
    "high": 1,
    "medium": 2,
    "low": 1,
    "passed": 12
  }
}
```

## 7. Startup Behavior by Severity

| Severity | Development | Testing | Staging | Production |
|----------|-------------|---------|---------|------------|
| **CRITICAL** | WARN + continue | FAIL + exit | FAIL + exit | FAIL + exit |
| **HIGH** | WARN + continue | WARN + continue | FAIL + exit | FAIL + exit |
| **MEDIUM** | WARN + continue | WARN + continue | WARN + continue | FAIL + exit |
| **LOW** | WARN + continue | WARN + continue | WARN + continue | WARN + continue |

## 8. Validation Hook Registration

Modules can register custom validation hooks:

```python
from aida.config.validator import register_validation_hook

@register_validation_hook(severity="HIGH", order=100)
def validate_agent_config(config):
    """Validates agent-specific configuration."""
    max_concurrent = config.get("agents.max_concurrent", 10)
    if max_concurrent < 1:
        return ValidationError(
            id="AGENT-001",
            key="agents.max_concurrent",
            message="Must be at least 1",
            actual=max_concurrent,
        )
    if max_concurrent > 100 and not config.get("app.debug"):
        return ValidationError(
            id="AGENT-002",
            key="agents.max_concurrent",
            message="Cannot exceed 100 in production",
            actual=max_concurrent,
        )
    return None
```

## 9. CLI Validation Commands

```bash
# Full validation
aida config validate

# Validate specific environment
aida config validate --environment production

# Validate a specific key
aida config validate --key database.url

# Dry run (don't exit on failure)
aida config validate --dry-run

# Output as JSON
aida config validate --format json

# Compare two configurations
aida config diff --from staging --to production --validate

# Show current config (redacted)
aida config show --format yaml
```

## 10. Relaxation for Development

Development mode validation **permissive**:

```python
def validate(config, rules):
    if config.app.debug:
        # Skip connection checks
        rules = [r for r in rules if not r.id.startswith("CONN-")]
        # Downgrade production rules to warnings
        for rule in rules:
            if rule.id.startswith("PROD-"):
                rule.severity = "WARNING"
    return validator.validate(config, rules)
```

## 11. Complete Validation Checklist

```
[ ] Schema validation (JSON Schema)
[ ] Type checking (every key)
[ ] Required field presence
[ ] String length constraints
[ ] Enum value constraints
[ ] Numeric range constraints
[ ] URL format validation
[ ] Production-specific rules (PROD-*)
[ ] Security rules (SEC-*)
[ ] Connection checks (CONN-*)
[ ] Cross-config consistency (CROSS-*)
[ ] Business logic rules
[ ] Custom module hooks
[ ] Embedding dimension matches vector DB
[ ] Default provider has configuration
[ ] Cache-Redis consistency
[ ] RAG-VectorDB dependency
```

## 12. Implementation Priority

| Rule Group | Priority | Effort | Depends On |
|------------|----------|--------|------------|
| Type checking | P0 | Small | None (env vars already read) |
| Production rules | P0 | Small | APP_ENV detection |
| Security rules | P1 | Small | None |
| Cross-config rules | P1 | Medium | Full config schema |
| Connection checks | P2 | Medium | Service health endpoints |
| JSON Schema | P2 | Medium | YAML config files |
| Custom hooks | P3 | Large | Full validator framework |
