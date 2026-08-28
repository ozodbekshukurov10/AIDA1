# AIDA — Enterprise Health Check System

## 1. Design Philosophy

Health checks — AIDA servislarining holatini aniqlash va nosozliklarni erta aniqlash uchun ishlatiladi. Har bir health check:

- **Deterministic** — har safar bir xil natija qaytaradi
- **Lightweight** — 5 soniyadan oshmaydi
- **Independent** — boshqa servislarga bog'liq emas (dependency check alohida)
- **Versioned** — `/health` va `/health/v2` kabi versiyalanadi

**Current State**: Faqat `webapp/api/status.py:8` orqali `GET /api/v2/status/` mavjud. Standart Kubernetes health check endpointlari (`/health`, `/ready`, `/livez`) mavjud emas.

## 2. Health Check Endpoints

### 2.1 Standard Endpoints

| Endpoint | Type | Purpose | Kubernetes Probe |
|----------|------|---------|------------------|
| `GET /health` | Liveness | Service is alive | `livenessProbe` |
| `GET /ready` | Readiness | Service is ready to serve | `readinessProbe` |
| `GET /livez` | Liveness | Same as `/health` (K8s convention) | `livenessProbe` |
| `GET /readyz` | Readiness | Detailed dependency check | `startupProbe` |
| `GET /health/db` | Database | Database connectivity | — |
| `GET /health/redis` | Cache | Redis connectivity | — |
| `GET /health/vector` | VectorDB | Vector database connectivity | — |
| `GET /health/llm` | AI | LLM provider connectivity | — |
| `GET /health/all` | Composite | All dependencies summary | — |
| `GET /metrics` | Metrics | Prometheus metrics endpoint | — |

### 2.2 Current Status Endpoint

```json
// GET /api/v2/status/  (existing)
{
  "status": "ok",
  "version": "2.1.0",
  "platform": "AIDA Agentic Platform",
  "active_provider": "ollama",
  "providers": {"ollama": {"available": true, "model": "llama3"}},
  "agents": {
    "code_agent": {"name": "Code Agent", "status": "idle", "metrics": {"calls": 1234, "errors": 5}}
  }
}
```

### 2.3 Target Health Endpoints

```json
// GET /health
{
  "status": "healthy",
  "version": "2.1.0",
  "commit": "a1b2c3d4",
  "uptime_seconds": 123456,
  "timestamp": "2026-07-03T12:00:00Z"
}

// GET /ready
{
  "status": "ready",
  "dependencies": {
    "database": {"status": "up", "latency_ms": 3},
    "redis": {"status": "up", "latency_ms": 1},
    "vector_db": {"status": "up", "latency_ms": 12},
    "llm_provider": {"status": "degraded", "message": "Ollama unreachable, using fallback"}
  },
  "checks": {
    "total": 4,
    "passed": 3,
    "failed": 0,
    "degraded": 1
  }
}

// GET /health/all  (detailed)
{
  "service": "aida-api",
  "version": "2.1.0",
  "uptime_seconds": 123456,
  "status": "degraded",
  "checks": [
    {
      "name": "database",
      "status": "healthy",
      "type": "connectivity",
      "target": "postgresql://db.internal:5432/aida",
      "latency_ms": 3,
      "last_success": "2026-07-03T12:00:00Z",
      "last_failure": null,
      "consecutive_failures": 0
    },
    {
      "name": "redis",
      "status": "healthy",
      "type": "ping",
      "target": "redis://redis:6379/0",
      "latency_ms": 1,
      "last_success": "2026-07-03T12:00:00Z"
    },
    {
      "name": "llm_openai",
      "status": "healthy",
      "type": "api",
      "target": "openai",
      "models_available": ["gpt-4o", "gpt-4-turbo"],
      "rate_limit_remaining": 4500
    },
    {
      "name": "llm_ollama",
      "status": "unhealthy",
      "type": "api",
      "target": "http://ollama:11434",
      "error": "Connection refused",
      "consecutive_failures": 3
    }
  ]
}
```

## 3. Health Check Registry

### 3.1 Built-in Checks

| Check Name | Implementation | Timeout | Critical |
|------------|---------------|---------|----------|
| `database` | `connection.execute("SELECT 1")` | 3s | Yes |
| `redis` | `redis_client.ping()` | 2s | No (cache only) |
| `vector_db` | `qdrant_client.health_check()` | 5s | No (fallback) |
| `llm_openai` | `openai.Model.list()` | 5s | Conditional |
| `llm_ollama` | `requests.get(OLLAMA_URL)` | 3s | Conditional |
| `llm_anthropic` | SDK health ping | 5s | Conditional |
| `queue` | `redis.ping()` + queue length | 2s | No |
| `plugin_system` | Plugin registry status | 2s | No |
| `disk_space` | `shutil.disk_usage()` | 1s | Yes if >90% |
| `memory` | `psutil.virtual_memory()` | 1s | Yes if >95% |

### 3.2 Check Registration

```python
from aida.monitoring.health import register_check, HealthCheckResult

@register_check(
    name="database",
    timeout=3.0,
    critical=True,
    tags=["core", "storage"],
)
def check_database() -> HealthCheckResult:
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
            if row and row[0] == 1:
                return HealthCheckResult(status="healthy", latency_ms=...)
        return HealthCheckResult(status="unhealthy", error="SELECT 1 failed")
    except Exception as e:
        return HealthCheckResult(status="unhealthy", error=str(e))
```

## 4. Status Computation

### 4.1 Status Values

| Status | HTTP Code | Meaning | Action |
|--------|-----------|---------|--------|
| `healthy` | 200 | All checks pass | Normal operation |
| `degraded` | 200 | Non-critical check failed | Continue, investigate |
| `unhealthy` | 503 | Critical check failed | Stop serving |
| `maintenance` | 503 | Planned downtime | Return Retry-After |
| `starting` | 503 | Still initializing | Startup probe |

### 4.2 Status Algorithm

```python
def compute_overall_status(checks: list[HealthCheckResult]) -> str:
    for check in checks:
        if check.critical and check.status == "unhealthy":
            return "unhealthy"
    for check in checks:
        if check.status == "unhealthy":
            return "degraded"
    return "healthy"
```

## 5. Health Check Cache

Health check natijalari cache'lanadi. `check_all_health()` already has a `_health_cache` with 30s TTL.

```python
class HealthCheckRunner:
    def __init__(self):
        self._cache: dict[str, tuple[float, HealthCheckResult]] = {}
        self._cache_ttl = 30.0  # seconds

    def run_check(self, name: str) -> HealthCheckResult:
        now = time.monotonic()
        if name in self._cache:
            cached_time, cached_result = self._cache[name]
            if now - cached_time < self._cache_ttl:
                return cached_result

        result = self._registry[name].fn()
        self._cache[name] = (now, result)
        return result

    def invalidate_cache(self):
        self._cache.clear()
```

## 6. Kubernetes Probe Integration

### 6.1 Deployment Configuration

```yaml
# k8s/deployment.yaml
spec:
  containers:
    - name: aida
      ports:
        - containerPort: 8000
          name: http
      livenessProbe:
        httpGet:
          path: /livez
          port: http
        initialDelaySeconds: 30
        periodSeconds: 15
        timeoutSeconds: 5
        failureThreshold: 3
      readinessProbe:
        httpGet:
          path: /readyz
          port: http
        initialDelaySeconds: 5
        periodSeconds: 10
        timeoutSeconds: 3
        failureThreshold: 2
      startupProbe:
        httpGet:
          path: /readyz
          port: http
        initialDelaySeconds: 0
        periodSeconds: 5
        failureThreshold: 30  # 150 seconds max startup
```

### 6.2 Docker Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

## 7. Health Check Monitoring

### 7.1 Metrics

```
# Health check metrics (Prometheus)
aida_health_check_status{check="database"} 1  # 1=healthy, 0=unhealthy
aida_health_check_duration_ms{check="redis"} 2.3
aida_health_check_failures_total{check="ollama"} 7
aida_overall_status 1  # 1=healthy, 0=unhealthy
```

### 7.2 Alert Rules

```yaml
groups:
  - name: aida-health
    rules:
      - alert: AIDADown
        expr: aida_overall_status == 0
        for: 1m
        labels: {severity: critical}
        annotations:
          summary: "AIDA is down"

      - alert: DatabaseUnhealthy
        expr: aida_health_check_status{check="database"} == 0
        for: 30s
        labels: {severity: critical}
        annotations:
          summary: "Database connection lost"

      - alert: LLMProviderDown
        expr: aida_health_check_status{check=~"llm_.*"} == 0
        for: 2m
        labels: {severity: warning}
        annotations:
          summary: "LLM provider {{ $labels.check }} is down"
```

## 8. Implementation Priority

| Phase | Component | Priority | Effort |
|-------|-----------|----------|--------|
| P0 | `/health` liveness endpoint | CRITICAL | Small |
| P0 | `/ready` readiness with deps | CRITICAL | Small |
| P0 | Database health check | CRITICAL | Small |
| P0 | Docker HEALTHCHECK directive | CRITICAL | Small |
| P1 | Redis health check | HIGH | Small |
| P1 | Vector DB health check | HIGH | Small |
| P1 | LLM provider health check (existing) | HIGH | Small |
| P1 | Plugin system health check | MEDIUM | Small |
| P2 | `/livez` + `/readyz` K8s endpoints | MEDIUM | Small |
| P2 | Disk/memory health check | MEDIUM | Small |
| P2 | Health check Prometheus metrics | MEDIUM | Medium |
| P2 | K8s probe YAML in k8s/ directory | MEDIUM | Small |
| P3 | Health check dashboard panel | LOW | Medium |
