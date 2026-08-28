# AIDA — Enterprise Logging Architecture

## 1. Architectural Overview

AIDA logging tizimi 4 qatlamli arxitektura asosida ishlaydi. Har bir qatlam o'ziga xos log turlari, formatlari va handlerlariga ega.

```
┌─────────────────────────────────────────────────────────────┐
│                     LAYER 4: EXPORT                         │
│        CloudWatch · Loki · Elasticsearch · Datadog          │
├─────────────────────────────────────────────────────────────┤
│                     LAYER 3: AGGREGATION                    │
│        File · Console · JSON Stream · Syslog · Rsyslog      │
├─────────────────────────────────────────────────────────────┤
│                     LAYER 2: PROCESSING                     │
│   Formatter → Filter → Redacter → Router → Handler Dispatch │
├─────────────────────────────────────────────────────────────┤
│                     LAYER 1: COLLECTION                     │
│   System · AI · Agent · Tool · API · DB · Security · Audit  │
└─────────────────────────────────────────────────────────────┘
```

### 1.1 Current State Analysis

| Component | Status | Location |
|-----------|--------|----------|
| Structured JSON formatter | ✅ Active | `aidaos/infrastructure/logging/__init__.py:33` |
| Colored console formatter | ✅ Active | `aidaos/infrastructure/logging/__init__.py:61` |
| File rotation (10MB, 5 backups) | ✅ Active | `aidaos/infrastructure/logging/__init__.py:106` |
| Thread-local context propagation | ✅ Active | `aidaos/infrastructure/logging/__init__.py:15` |
| Django logging config | ✅ Active | `AIDA/settings.py:115` |
| AI/LLM request logging | ❌ Missing | No provider-level structured logs |
| Security audit logging | ❌ Missing | No auth/access logging |
| Agent execution logging | ❌ Missing | No per-agent lifecycle logs |
| Error tracking (structured) | ❌ Missing | No capture with severity/recovery |
| Performance metrics in logs | ❌ Missing | No CPU/RAM/GPU timings |

### 1.2 Target Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      LOG PRODUCERS                          │
│  ┌────────┐ ┌──────┐ ┌───────┐ ┌────┐ ┌─────┐ ┌─────────┐  │
│  │ System │ │ AI   │ │ Agent │ │Tool│ │ API │ │ Security │  │
│  │ Logs   │ │ Logs │ │ Logs  │ │Logs│ │Logs │ │ Logs     │  │
│  └────┬───┘ └──┬───┘ └───┬───┘ └──┬─┘ └──┬──┘ └────┬────┘  │
│       └────────┴─────────┴────────┴──────┴─────────┘       │
│                          │                                   │
│                          ▼                                   │
│              ┌─────────────────────┐                        │
│              │  LOG COLLECTOR      │                        │
│              │  (get_logger /      │                        │
│              │   logging.getLogger)│                        │
│              └─────────┬───────────┘                        │
│                        │                                     │
│                        ▼                                     │
│              ┌─────────────────────┐                        │
│              │  LOG PROCESSING     │                        │
│              │  ├─ JSONFormatter   │                        │
│              │  ├─ ColoredConsole  │                        │
│              │  ├─ SecretRedactor  │                        │
│              │  └─ ContextEnricher │                        │
│              └─────────┬───────────┘                        │
│                        │                                     │
│                        ▼                                     │
│              ┌─────────────────────┐                        │
│              │  LOG ROUTER         │                        │
│              │  ├─ ConsoleHandler  │                        │
│              │  ├─ FileHandler     │                        │
│              │  ├─ AuditHandler    │ (separate file)        │
│              │  └─ SecurityHandler │ (separate file)        │
│              └─────────┬───────────┘                        │
│                        │                                     │
│                        ▼                                     │
│              ┌─────────────────────┐                        │
│              │  LOG EXPORT         │                        │
│              │  ├─ Loki (Grafana)  │                        │
│              │  ├─ CloudWatch Logs │                        │
│              │  └─ Elasticsearch   │                        │
│              └─────────────────────┘                        │
└──────────────────────────────────────────────────────────────┘
```

## 2. Log Categories

### 2.1 Category Matrix

| Category | Prefix | Purpose | Separate File | JSON Schema |
|----------|--------|---------|---------------|-------------|
| **System** | `aida.system` | Infrastructure, startup, shutdown | `system.log` | `LogEntry` |
| **AI** | `aida.ai` | LLM requests, responses, tokens | `ai.log` | `AIEvent` |
| **Agent** | `aida.agent` | Agent lifecycle, tasks, decisions | `agent.log` | `AgentEvent` |
| **Tool** | `aida.tool` | Tool execution, I/O, duration | `tool.log` | `ToolEvent` |
| **API** | `aida.api` | HTTP requests, responses, status | `api.log` | `APIEvent` |
| **Database** | `aida.db` | Queries, connections, migrations | `db.log` | `DBEvent` |
| **Workflow** | `aida.workflow` | Workflow steps, transitions | `workflow.log` | `WorkflowEvent` |
| **Plugin** | `aida.plugin` | Plugin lifecycle, errors | `plugin.log` | `PluginEvent` |
| **Audit** | `aida.audit` | Config/admin changes (immutable) | `audit.log` | `AuditEvent` |
| **Security** | `aida.security` | Auth, tokens, access control | `security.log` | `SecurityEvent` |
| **Performance** | `aida.perf` | CPU, RAM, GPU, latency metrics | `perf.log` | `PerfEvent` |

### 2.2 Logger Naming Convention

Current logger naming has 3 conventions (`aida.*`, `aidaos.*`, `webapp.*`). Target unified convention:

```
aida.{category}.{module}.{class}

Examples:
  aida.ai.providers.ollama
  aida.agent.orchestrator
  aida.tool.registry
  aida.api.views
  aida.db.migrations
  aida.security.auth
  aida.audit.config
  aida.workflow.executor
  aida.plugin.loader
  aida.system.startup
  aida.perf.monitor
```

## 3. Log Levels

| Level | Numeric | Usage | Production |
|-------|---------|-------|------------|
| **TRACE** | 5 | Detailed step-by-step execution, LLM raw token flow, function entry/exit | DISABLED |
| **DEBUG** | 10 | Development debugging, variable dumps, detailed state | DISABLED |
| **INFO** | 20 | Normal operation events, service start/stop, successful operations | ENABLED |
| **SUCCESS** | 22 | Successful completion of important operations (deploy, migration, batch job) | ENABLED |
| **WARNING** | 30 | Potential issues, deprecated usage, rate limit nearing, fallback activated | ENABLED |
| **ERROR** | 40 | Operation failure, service degradation, API call failure | ENABLED |
| **CRITICAL** | 50 | System-wide failure, data loss risk, component unavailable | ENABLED |
| **FATAL** | 60 | Unrecoverable error, immediate shutdown required | ENABLED |

### 3.1 Level Semantics

```python
# TRACE — Detailed execution flow (development only)
logger.log(TRACE, "Entering function process_message with args=%s", args)

# DEBUG — Context-rich debugging
logger.debug("Vector search: query=%s top_k=%d threshold=%.2f", query, top_k, threshold)

# INFO — Normal operational events
logger.info("Chat session=%s provider=%s model=%s", session_id, provider, model)

# SUCCESS — Important milestones
logger.log(SUCCESS, "Deployment version=%s completed in %.2fs", version, duration)

# WARNING — Non-critical issues
logger.warning("Rate limit at 80%% for API key %s", key_id)

# ERROR — Operation failures
logger.error("LLM call failed after %d retries: %s", retries, exc_info)

# CRITICAL — System-level failures
logger.critical("Database connection lost. Retry %d/5", retry_count)

# FATAL — Unrecoverable
logger.log(FATAL, "Corrupt state detected. Shutting down.")
```

## 4. Log Format

### 4.1 Standard Log Entry (JSON)

Current `JSONFormatter` output (already active via `AIDA_LOG_FORMAT=json`):

```json
{
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "level": "INFO",
  "logger": "aida.services.chat",
  "message": "Chat response generated",
  "module": "chat_service",
  "function": "chat",
  "line": 66,
  "context": {
    "session_id": "sess_abc123",
    "request_id": "req_def456"
  },
  "exception": null,
  "extra": null
}
```

### 4.2 Target Enhanced Format

```json
{
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "level": "INFO",
  "logger": "aida.ai.providers.openai",
  "service": "aida-api",
  "environment": "production",
  "hostname": "node-3",
  "pid": 12345,
  "module": "openai_provider",
  "class": "OpenAIProvider",
  "function": "generate",
  "line": 142,
  "request_id": "req_abc123",
  "session_id": "sess_def456",
  "user_id": "user_789",
  "agent_id": "agent_code",
  "task_id": "task_xyz",
  "execution_time_ms": 1234.56,
  "message": "LLM generation completed",
  "exception": null,
  "metadata": {
    "model": "gpt-4o",
    "provider": "openai",
    "prompt_tokens": 450,
    "completion_tokens": 120,
    "total_tokens": 570,
    "response_time_ms": 1234
  },
  "performance": {
    "cpu_percent": 45.2,
    "ram_mb": 256.0,
    "gpu_percent": 78.0,
    "gpu_memory_mb": 2048.0
  },
  "tags": ["llm", "chat", "production"]
}
```

### 4.3 Required Fields for Each Category

| Field | System | AI | Agent | Tool | API | Security | Audit |
|-------|--------|----|-------|------|-----|----------|-------|
| timestamp | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| level | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| logger | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| service | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| environment | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| request_id | - | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| session_id | - | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| user_id | - | ✓ | ✓ | - | ✓ | ✓ | ✓ |
| agent_id | - | - | ✓ | - | - | - | - |
| task_id | - | - | ✓ | ✓ | - | - | - |
| execution_time_ms | ✓ | ✓ | ✓ | ✓ | ✓ | - | - |
| metadata | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| exception | ✓ | ✓ | ✓ | ✓ | ✓ | - | - |
| performance | ✓ | ✓ | ✓ | ✓ | ✓ | - | - |

## 5. Log Handlers

### 5.1 Current Handlers

```python
# aidaos/infrastructure/logging/__init__.py:106
# Handler 1: RotatingFileHandler → logs/aida.log (10MB, 5 backups)
# Handler 2: StreamHandler → stdout (console)

# AIDA/settings.py:122
# Handler 1: StreamHandler (console) with verbose text format
# Handler 2: FileHandler → logs/aida.log with verbose text format
```

### 5.2 Target Handlers

| Handler | Destination | Format | Category | Enabled |
|---------|-------------|--------|----------|---------|
| ConsoleHandler | stdout | Colored (dev) / JSON (prod) | All | Always |
| FileHandler | `logs/{category}.log` | JSON | All | Always |
| AuditHandler | `logs/audit.log` | JSON (append-only) | `aida.audit.*` | Always |
| SecurityHandler | `logs/security.log` | JSON (immutable) | `aida.security.*` | Always |
| AIHandler | `logs/ai.log` | JSON | `aida.ai.*` | When AI logging enabled |
| ErrorHandler | `logs/error.log` | JSON | ERROR+ from all | Always |
| PerformanceHandler | `logs/perf.log` | JSON | `aida.perf.*` | When monitoring enabled |
| SyslogHandler | `/var/log/aida/` | JSON | All | Linux production |
| LokiHandler | Grafana Loki | JSON | All | Cloud production |

### 5.3 Audit Handler (Special)

Audit logs append-only. Hech qachon o'chirilmaydi yoki o'zgartirilmaydi.

```python
class AuditLogHandler(logging.Handler):
    """Append-only audit log handler. Never rotates — uses daily files."""
    def __init__(self, path: Path):
        super().__init__(level=logging.INFO)
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, record: logging.LogRecord):
        # Always append, never truncate
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(self.format(record) + "\n")
```

## 6. Log Processing Pipeline

### 6.1 Secret Redaction

Log yozilishidan oldin barcha maxfiy ma'lumotlar avtomatik redacted qilinadi:

```python
# Redacted patterns (applied in Formatter.format())
SECRET_PATTERNS = [
    (r'(api_key["\']?\s*[:=]\s*["\']?)[^"\'\s,}]+', r'\1***REDACTED***'),
    (r'(sk-[a-zA-Z0-9]{20,})', 'sk-***REDACTED***'),
    (r'(sk-ant-[a-zA-Z0-9]{20,})', 'sk-ant-***REDACTED***'),
    (r'(AIza[0-9A-Za-z\-_]{35})', '***REDACTED***'),
    (r'(ghp_[0-9a-zA-Z]{36})', '***REDACTED***'),
    (r'(password["\']?\s*[:=]\s*["\']?)[^"\'\s,}]+', r'\1***REDACTED***'),
    (r'(secret["\']?\s*[:=]\s*["\']?)[^"\'\s,}]+', r'\1***REDACTED***'),
    (r'(token["\']?\s*[:=]\s*["\']?)[^"\'\s,}]+', r'\1***REDACTED***'),
]
```

### 6.2 Context Enrichment

Har bir log record ga quyidagi global kontekstlar avtomatik qo'shiladi:
- `request_id` (per-request UUID)
- `session_id` (active session)
- `user_id` (authenticated user)
- `agent_id` (active agent)
- `task_id` (active task)

Current `set_context()` mechanism already supports this.

### 6.3 Filter Chain

```
Raw Record → SeverityFilter → CategoryFilter → RedactionFilter → RateLimitFilter → Output
```

## 7. Logger Migration Path

### 7.1 Current → Target Mapping

| Current Logger | Target Logger | Status |
|----------------|---------------|--------|
| `aida.*` | `aida.{category}.*` | ✅ Already migrating |
| `aidaos.*` | `aida.{category}.*` | Need migration |
| `webapp.*` | `aida.{category}.*` | Need migration |
| `scripts.*` | `aida.system.*` | Need migration |

### 7.2 Migration Strategy

```
Phase 1: Create aida.{category}.get_logger() helpers
Phase 2: Migrate aidaos.* → aida.{category}.* (backward compat)
Phase 3: Migrate webapp.* → aida.{category}.*
Phase 4: Remove old logger names, activate category-based file handlers
```

## 8. Performance Considerations

| Metric | Current | Target |
|--------|---------|--------|
| JSON serialization | Per-record | Per-record (cached formatters) |
| File I/O | Sync writes | Async queue + batch writes |
| Context propagation | thread-local | thread-local (async local for asyncio) |
| Redaction | None | O(1) regex per record |
| Handler count | 2 per logger | 3-5 per logger (category-dependent) |

### 8.1 Async Log Queue (Target)

```python
# aida/infrastructure/logging/async_handler.py
import asyncio
from collections import deque

class AsyncLogHandler(logging.Handler):
    """Non-blocking log handler with batch writes."""
    def __init__(self, target_handler, batch_size=100, flush_interval=1.0):
        self._queue = deque()
        self._batch_size = batch_size
        self._flush_interval = flush_interval

    def emit(self, record):
        self._queue.append(record)
        if len(self._queue) >= self._batch_size:
            self._flush()

    async def _flush(self):
        batch = list(self._queue)
        self._queue.clear()
        # Batch write to file/network
```

## 9. Logging Configuration

### 9.1 Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `AIDA_LOG_LEVEL` | `INFO` | Root log level |
| `AIDA_LOG_FORMAT` | `text` | `json` or `text` |
| `AIDA_LOG_DIR` | `logs/` | Log directory |
| `AIDA_LOG_MAX_BYTES` | `10485760` | Max file size (10MB) |
| `AIDA_LOG_BACKUP_COUNT` | `5` | Rotated files to keep |
| `AIDA_LOG_ASYNC` | `false` | Enable async logging |
| `AIDA_LOG_AI_ENABLED` | `true` | Enable AI-specific logging |
| `AIDA_LOG_PERF_ENABLED` | `false` | Enable performance metrics |
| `AIDA_LOG_REDACT_SECRETS` | `true` | Enable secret redaction |
| `AIDA_AUDIT_ENABLED` | `true` | Enable audit trail |

### 9.2 Log Level by Environment

| Environment | Root Level | AI Logs | Security | Audit | Performance |
|-------------|------------|---------|----------|-------|-------------|
| Development | DEBUG | DEBUG | INFO | INFO | DISABLED |
| Testing | INFO | INFO | INFO | INFO | DISABLED |
| Staging | INFO | INFO | INFO | INFO | ENABLED |
| Production | WARNING | INFO | INFO | INFO | ENABLED |

## 10. Log Storage Layout

```
logs/
├── aida.log              # Main log (all categories, rotated)
├── error.log             # ERROR+ only (all categories, rotated)
├── ai.log                # AI/LLM operations
├── agent.log             # Agent lifecycle
├── tool.log              # Tool execution
├── api.log               # HTTP API calls
├── db.log                # Database operations
├── workflow.log          # Workflow execution
├── plugin.log            # Plugin lifecycle
├── system.log            # System/startup
├── audit.log             # Audit trail (append-only, daily)
├── security.log          # Security events (append-only, daily)
├── perf.log              # Performance metrics (rotated)
└── archive/              # Compressed archives
    ├── 2026/
    │   ├── Q1/           # Quarterly archives
    │   ├── Q2/
    │   ├── Q3/
    │   └── Q4/
    └── 2027/
        └── ...
```
