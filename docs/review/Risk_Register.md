# AIDA Risk Register

**Assessment Date:** 2026-07-04
**Total Risks Identified:** 50
**Critical:** 8 | **High:** 15 | **Medium:** 18 | **Low:** 9

---

## CRITICAL RISKS (8)

| # | Risk | Probability | Impact | Priority | Solution |
|---|------|-------------|--------|----------|----------|
| 1 | JWT token forgery via hardcoded secret | HIGH | CRITICAL | P0 | Remove hardcoded fallback; require env var |
| 2 | Remote code execution via eval/exec in sandbox | HIGH | CRITICAL | P0 | Container-based sandboxing; no bare eval/exec |
| 3 | SQL injection in DatabaseTool | MEDIUM | CRITICAL | P0 | Parameterized queries only; query whitelist |
| 4 | Command injection via shell=True | MEDIUM | CRITICAL | P0 | Never use shell=True with user input |
| 5 | SQLite failure under concurrent writes | HIGH | CRITICAL | P0 | Migrate to PostgreSQL |
| 6 | No CORS configuration enables cross-origin abuse | HIGH | HIGH | P0 | Install django-cors-headers; configure origins |
| 7 | DEBUG=true in production .env | MEDIUM | HIGH | P0 | Default to false; environment-specific configs |
| 8 | No test suite — changes cannot be verified | HIGH | HIGH | P0 | Write critical path tests (>50% coverage) |

---

## HIGH RISKS (15)

| # | Risk | Probability | Impact | Priority | Solution |
|---|------|-------------|--------|----------|----------|
| 9 | CSRF protection disabled (19+ endpoints) | HIGH | HIGH | P1 | Token-based auth; validate Origin header |
| 10 | No CI/CD pipeline — manual deployment | MEDIUM | HIGH | P1 | GitHub Actions or GitLab CI |
| 11 | In-memory rate limiting — lost on restart | MEDIUM | HIGH | P1 | Redis-backed rate limiting |
| 12 | No caching layer — every request hits DB/LLM | HIGH | HIGH | P1 | Add Redis caching |
| 13 | Monolithic controller (4,400+ lines) | HIGH | HIGH | P1 | Decompose into domain services |
| 14 | SECRET_KEY regenerated on restart | MEDIUM | HIGH | P1 | Persist in environment |
| 15 | Custom JWT implementation bugs | MEDIUM | HIGH | P1 | Migrate to PyJWT |
| 16 | subprocess with shell=True in multiple files | MEDIUM | HIGH | P1 | Use subprocess with list args |
| 17 | No HTTPS enforcement | HIGH | HIGH | P1 | Enable SECURE_SSL_REDIRECT |
| 18 | No structured logging | MEDIUM | HIGH | P1 | Implement JSON logging |
| 19 | WebSocket consumers not wired to real agents | MEDIUM | MEDIUM | P1 | Connect to agent MessageBus |
| 20 | Duplicate knowledge stores (data silos) | MEDIUM | MEDIUM | P1 | Unify to single store |
| 21 | No monitoring dashboards | MEDIUM | MEDIUM | P1 | Add Prometheus + Grafana |
| 22 | SQLite file locks block concurrent reads | HIGH | HIGH | P1 | PostgreSQL migration |
| 23 | In-memory agent status lost on restart | MEDIUM | MEDIUM | P1 | Redis-backed status |

---

## MEDIUM RISKS (18)

| # | Risk | Probability | Impact | Priority | Solution |
|---|------|-------------|--------|----------|----------|
| 24 | TF-IDF rebuilds on every query | MEDIUM | MEDIUM | P2 | Incremental updates + caching |
| 25 | No prompt caching for LLM | MEDIUM | MEDIUM | P2 | Redis prompt cache |
| 26 | Sleep-based agent dependency resolution | MEDIUM | MEDIUM | P2 | Event-driven resolution |
| 27 | Two TF-IDF implementations | LOW | MEDIUM | P2 | Consolidate |
| 28 | Two provider systems (legacy + plugin) | MEDIUM | MEDIUM | P2 | Migrate to plugin system |
| 29 | No API versioning active | LOW | MEDIUM | P2 | Enable versioning middleware |
| 30 | Rate limiter trusts X-Forwarded-For | MEDIUM | MEDIUM | P2 | Configure trusted proxy |
| 31 | No database connection pooling | MEDIUM | MEDIUM | P2 | PgBouncer or Django pools |
| 32 | File read tool lacks path sandboxing | MEDIUM | MEDIUM | P2 | Whitelist allowed directories |
| 33 | Shell command blocking is keyword-based | MEDIUM | MEDIUM | P2 | Use seccomp or container |
| 34 | No token counting for LLM costs | LOW | MEDIUM | P2 | Implement tiktoken |
| 35 | No request batching for LLM | LOW | MEDIUM | P2 | Implement batch API |
| 36 | Character hash embeddings are weak | MEDIUM | MEDIUM | P2 | Use sentence-transformers |
| 37 | No distributed tracing | MEDIUM | MEDIUM | P2 | OpenTelemetry |
| 38 | Information leakage in error responses | LOW | MEDIUM | P2 | Sanitize error messages |
| 39 | Login password has no max_length | LOW | LOW | P2 | Add max_length constraint |
| 40 | API key prefix collision risk | LOW | LOW | P2 | Use full hash lookup |
| 41 | No backup automation | MEDIUM | MEDIUM | P2 | Automated PostgreSQL backups |

---

## LOW RISKS (9)

| # | Risk | Probability | Impact | Priority | Solution |
|---|------|-------------|--------|----------|----------|
| 42 | 30+ markdown files at root level | LOW | LOW | P3 | Archive to docs/ |
| 43 | Empty directories (code_workspace, projects) | LOW | LOW | P3 | Remove or document |
| 44 | Root-level orphaned Python files | LOW | LOW | P3 | Move to appropriate packages |
| 45 | No linting/formatting configuration | LOW | LOW | P3 | Add ruff + black |
| 46 | No pre-commit hooks | LOW | LOW | P3 | Add pre-commit config |
| 47 | Inconsistent code style between apps | LOW | LOW | P3 | Enforce with linter |
| 48 | Missing type hints in some files | LOW | LOW | P3 | Add gradually |
| 49 | server.log grows unbounded | LOW | LOW | P3 | Add log rotation |
| 50 | .aida_runtime.json committed | LOW | LOW | P3 | Add to .gitignore |

---

## Risk Summary

| Severity | Count | Total Priority |
|----------|-------|----------------|
| CRITICAL | 8 | P0 — Fix immediately |
| HIGH | 15 | P1 — Fix this week |
| MEDIUM | 18 | P2 — Fix this month |
| LOW | 9 | P3 — Fix this quarter |
| **TOTAL** | **50** | |

---

## Risk Heat Map

```
Impact →    LOW    MEDIUM   HIGH    CRITICAL
Probability
HIGH        |      |  22   | 9,12, |  1
            |      |       | 24    |
MEDIUM      |      | 25-41 | 7,14, | 3,4
            |      |       | 16,17 |
LOW         |42-50 |       |       |
            |      |       |       |
```

---

## Risk Trends

| Category | Risks | Primary Concern |
|----------|-------|-----------------|
| Security | 12 | Code execution, injection, auth |
| Architecture | 8 | Monolith, duplicates, no scaling |
| Infrastructure | 10 | SQLite, no cache, no CI/CD |
| AI System | 7 | No caching, weak embeddings |
| Operations | 6 | No monitoring, no alerts |
| Code Quality | 7 | No tests, style inconsistency |
