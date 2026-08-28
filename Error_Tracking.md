# AIDA — Enterprise Error Tracking System

## 1. Design Philosophy

Error tracking tizimi xatolarni **strukturaviy**, **kontekstli** va **harakatga keltiruvchi** tarzda qayd qiladi. Har bir xato:

- Kelib chiqish sababini aniqlaydi
- Qanday tuzatish mumkinligini ko'rsatadi
- Avtomatik ravishda severity bo'yicha klassifikatsiya qilinadi
- Kontekst (session, request, user, agent) bilan boyitiladi

**Current State**: Xatolar hozirda `logger.exception()` orqali oddiy text formatda yoziladi, structured capture mavjud emas.

## 2. Error Severity Classification

| Level | Numeric | Description | Response | Examples |
|-------|---------|-------------|----------|----------|
| **TRIVIAL** | 1 | No impact, cosmetic | Log only | Missing optional metadata, deprecated warning |
| **MINOR** | 2 | Minor impact, auto-recovered | Log + monitor | Rate limit reached (auto-retry), temporary timeout |
| **MODERATE** | 3 | Degraded experience | Alert + investigate | Feature unavailable, slow response |
| **MAJOR** | 4 | Critical feature broken | Immediate response | LLM provider down, database connection lost |
| **SEVERE** | 5 | System partially down | Escalate | Vector DB unavailable, queue backlog |
| **CRITICAL** | 6 | Full system failure | Pager/on-call | Application crash, data corruption |
| **CATASTROPHIC** | 7 | Data loss / security breach | Emergency | Data deletion, unauthorized access |

## 3. Error Event Schema

### 3.1 Standard Error Event

```json
{
  "error_id": "err_a1b2c3d4",
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "severity": "MAJOR",
  "severity_code": 4,
  "type": "LLMProviderError",
  "module": "openai_provider",
  "class": "OpenAIProvider",
  "function": "generate",
  "line": 142,

  "message": "OpenAI API call failed after 3 retries",
  "stack_trace": "Traceback (most recent call last):\n  File \".../providers/openai.py\", line 142, in generate\n    response = await client.chat.completions.create(...)\nopenai.RateLimitError: Rate limit exceeded for token sk-...",

  "input": {
    "model": "gpt-4o",
    "messages_count": 5,
    "total_prompt_tokens": 850,
    "temperature": 0.7
  },
  "expected_output": "Chat completion with choice",
  "actual_output": null,

  "context": {
    "request_id": "req_abc123",
    "session_id": "sess_def456",
    "user_id": "user_789",
    "agent_id": "agent_code_review",
    "task_id": "task_xyz"
  },

  "cause_analysis": {
    "primary_cause": "rate_limit_exceeded",
    "secondary_causes": ["no_retry_available", "quota_exceeded"],
    "is_recoverable": true,
    "auto_recovered": false
  },

  "recovery": {
    "suggestion": "Wait 60 seconds and retry. Consider upgrading OpenAI tier.",
    "auto_recovery_available": true,
    "auto_recovery_action": "retry_with_backoff",
    "retry_count": 3,
    "max_retries": 3
  },

  "system_state": {
    "cpu_percent": 45.2,
    "ram_mb": 256.0,
    "gpu_percent": 78.0,
    "gpu_memory_mb": 2048.0,
    "uptime_seconds": 86400
  },

  "tags": ["llm", "openai", "rate_limit", "retry_exhausted"]
}
```

### 3.2 Error Types Registry

| Error Type | Category | Default Severity | Auto-Recoverable |
|------------|----------|------------------|------------------|
| `LLMProviderError` | AI | MODERATE | Yes (retry + fallback) |
| `LLMRateLimitError` | AI | MINOR | Yes (exponential backoff) |
| `LLMTimeoutError` | AI | MINOR | Yes (retry) |
| `LLMAuthenticationError` | AI | MAJOR | No (invalid API key) |
| `DatabaseConnectionError` | Database | CRITICAL | Yes (connection pool retry) |
| `DatabaseQueryError` | Database | MODERATE | No |
| `DatabaseMigrationError` | Database | CRITICAL | Yes (rollback) |
| `RedisConnectionError` | Cache | MAJOR | Yes (fallback to memory) |
| `VectorDBConnectionError` | Vector | MAJOR | Yes (fallback to brute force) |
| `AgentExecutionError` | Agent | MODERATE | Yes (retry) |
| `ToolExecutionError` | Tool | MODERATE | No |
| `PluginLoadError` | Plugin | MEDIUM | No |
| `AuthenticationError` | Security | MAJOR | No |
| `AuthorizationError` | Security | MODERATE | No |
| `RateLimitExceeded` | Security | MINOR | Yes (wait + retry) |
| `FileSystemError` | System | MODERATE | No |
| `NetworkError` | System | MODERATE | Yes (retry) |
| `ConfigurationError` | System | CRITICAL | No (startup failure) |
| `ValidationError` | System | MINOR | No |

## 4. Error Capture Patterns

### 4.1 Current Pattern (Basic)

```python
# Current: unstructured, no context
try:
    response = await client.chat.completions.create(...)
except Exception as e:
    logger.exception("OpenAI API call failed: %s", e)  # No structure
```

### 4.2 Target Pattern (Structured)

```python
# Target: structured capture with context
from aida.infrastructure.errors import capture_error, ErrorSeverity

try:
    response = await client.chat.completions.create(...)
except openai.RateLimitError as e:
    capture_error(
        error=e,
        severity=ErrorSeverity.MINOR,
        error_type="LLMRateLimitError",
        input={"model": model, "messages_count": len(messages)},
        recovery={
            "auto_recovery_available": True,
            "auto_recovery_action": "retry_with_backoff",
            "suggestion": "Upgrade API tier or reduce request rate"
        }
    )
    # Auto-recovery
    await asyncio.sleep(backoff)
    response = await client.chat.completions.create(...)
```

### 4.3 Decorator Pattern

```python
from aida.infrastructure.errors import capture_errors

@capture_errors(
    error_type="LLMProviderError",
    severity=ErrorSeverity.MODERATE,
    auto_recovery="retry_with_fallback",
    max_retries=3
)
async def generate_chat(messages: list, model: str):
    response = await client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response
```

### 4.4 Context Manager Pattern

```python
from aida.infrastructure.errors import ErrorCapture

with ErrorCapture(
    error_type="DatabaseConnectionError",
    severity=ErrorSeverity.CRITICAL,
    context={"query": query_name, "database": db_name}
) as capture:
    result = await db.execute(query)
    if capture.has_error:
        # Fallback logic
        result = await fallback_db.execute(query)
```

## 5. Error Aggregation & Deduplication

### 5.1 Fingerprinting

Har bir xato unikal `fingerprint` orqali deduplicate qilinadi:

```python
def compute_fingerprint(error: Exception, context: dict) -> str:
    """Create a unique fingerprint for error deduplication."""
    key_parts = [
        type(error).__name__,
        context.get("module", ""),
        context.get("function", ""),
        str(error)[:200],  # First 200 chars of error message
    ]
    return hashlib.sha256(":".join(key_parts).encode()).hexdigest()
```

### 5.2 Grouping

O'xshash xatolar guruhlanadi:

```json
{
  "group_id": "group_llm_timeout",
  "fingerprint": "a1b2c3d4...",
  "count": 47,
  "first_seen": "2026-07-03T10:00:00Z",
  "last_seen": "2026-07-03T12:00:00Z",
  "affected_users": 12,
  "affected_sessions": 34,
  "status": "investigating",
  "assigned_to": "ml-team"
}
```

## 6. Recovery Suggestions Database

Har bir error type uchun oldindan tayyorlangan recovery suggestion:

| Error Pattern | Auto-Recovery | Suggestion |
|---------------|--------------|------------|
| LLM timeout | Retry (3x, exponential backoff) | "Consider reducing max_tokens or switching to faster model" |
| LLM rate limit | Retry with backoff | "Upgrade API tier. Current rate: 60 req/min" |
| LLM auth error | None | "Check OPENAI_API_KEY is valid and not expired" |
| DB connection lost | Connection pool retry (5x) | "Check database is running and network is stable" |
| DB query timeout | None | "Optimize query with index. Current duration: 30s" |
| Redis connection failed | Fallback to memory cache | "Check Redis service is running on REDIS_URL" |
| Vector DB unavailable | Fallback to brute-force search | "Check Qdrant service and VECTOR_DB_URL" |
| Agent execution failed | Retry (2x) | "Check agent configuration and available tools" |
| Plugin load failed | None | "Check plugin compatibility with current AIDA version" |
| Filesystem full | None | "Free up disk space in data/ directory. Current: 95% full" |
| Config validation error | None | "Run 'aida config validate' for detailed error report" |

## 7. Error Log Storage

### 7.1 File Structure

```
logs/errors/
├── errors.2026-07-03.jsonl        # All errors (JSONL, daily)
├── critical.2026-07-03.jsonl      # CRITICAL+ only (real-time alerting)
├── groups.json                    # Deduplicated error groups
└── archive/
    └── errors.2026-06.jsonl.gz    # Monthly compressed archives
```

### 7.2 Error Dashboard

```bash
# CLI error viewer
aida errors list --severity MAJOR --from 2026-07-01

# Error details
aida errors get err_a1b2c3d4

# Error groups
aida errors groups --status investigating

# Error statistics
aida errors stats --period 7d

# Acknowledge error
aida errors acknowledge err_a1b2c3d4 --assignee "ml-team"
```

## 8. Error Notification Routing

| Severity | Notification Channel | Response Time | Escalation |
|----------|---------------------|---------------|------------|
| TRIVIAL | None (log only) | — | — |
| MINOR | Log + metrics increment | — | — |
| MODERATE | Slack #alerts | 1 hour | After 3 occurrences |
| MAJOR | Slack + Email | 15 minutes | After 30 min |
| SEVERE | PagerDuty + SMS | 5 minutes | After 10 min |
| CRITICAL | PagerDuty + Phone | Immediate | After 5 min |
| CATASTROPHIC | All channels + Exec | Immediate | SEC + Legal |

## 9. Implementation Priority

| Phase | Component | Priority | Effort |
|-------|-----------|----------|--------|
| P0 | Structured error capture function | CRITICAL | Small |
| P0 | Error severity classification | CRITICAL | Small |
| P0 | Stack trace + context enrichment | CRITICAL | Medium |
| P1 | Error type registry | HIGH | Small |
| P1 | Recovery suggestions | HIGH | Medium |
| P1 | Auto-recovery patterns (retry, fallback) | HIGH | Medium |
| P2 | Error fingerprinting & deduplication | MEDIUM | Medium |
| P2 | Error groups & aggregation | MEDIUM | Large |
| P3 | Error dashboard CLI | LOW | Medium |
| P3 | Notification routing | LOW | Large |
