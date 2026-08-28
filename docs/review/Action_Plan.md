# AIDA Action Plan

**Generated:** 2026-07-04
**Target:** Book 2 (AI Core) Readiness
**Estimated Total Effort:** 40-50 days

---

## CRITICAL (Must Complete Before Book 2)

### C1. Security Fixes — 3-5 days
| Task | Effort | Owner |
|------|--------|-------|
| Remove hardcoded JWT secret; require env var | 0.5 day | Backend |
| Unify JWT secret source (settings.py + auth) | 0.5 day | Backend |
| Remove eval/exec from sandbox; use container | 1 day | Backend |
| Fix SQL injection in DatabaseTool | 0.5 day | Backend |
| Remove shell=True subprocess calls | 0.5 day | Backend |
| Add CORS configuration | 0.5 day | Backend |
| Enable HTTPS + security headers | 0.5 day | DevOps |
| Set DEBUG=false as default | 0.1 day | Backend |

### C2. Database Migration — 3-5 days
| Task | Effort | Owner |
|------|--------|-------|
| Install PostgreSQL locally | 0.5 day | DevOps |
| Create PostgreSQL settings config | 0.5 day | Backend |
| Migrate SQLite to PostgreSQL | 1 day | Backend |
| Unify 5 SQLite databases into 1 | 1 day | Backend |
| Add connection pooling | 0.5 day | Backend |
| Update memory system to use Django ORM | 1 day | Backend |

### C3. Caching Layer — 2-3 days
| Task | Effort | Owner |
|------|--------|-------|
| Install Redis locally | 0.5 day | DevOps |
| Configure Django CACHES with Redis | 0.5 day | Backend |
| Add provider health check caching (30s TTL) | 0.5 day | Backend |
| Add model status caching (5s TTL) | 0.5 day | Backend |
| Configure CHANNEL_LAYERS with Redis | 0.5 day | Backend |
| Add response caching for read endpoints | 0.5 day | Backend |

### C4. Test Suite — 5-7 days
| Task | Effort | Owner |
|------|--------|-------|
| Set up pytest + coverage | 0.5 day | Backend |
| Write auth flow tests (register, login, token) | 1 day | Backend |
| Write API endpoint tests (CRUD for all ViewSets) | 2 days | Backend |
| Write agent workflow tests | 1 day | AI |
| Write memory system tests | 0.5 day | Backend |
| Write LLM provider fallback tests | 0.5 day | AI |
| Achieve >50% coverage | 1 day | Backend |

---

## HIGH (Complete Within 2 Weeks)

### H1. Architecture Cleanup — 5-7 days
| Task | Effort | Owner |
|------|--------|-------|
| Decompose aida_controller.py into domain services | 3 days | Backend |
| Wire aidaos/ Clean Architecture into Django | 2 days | Backend |
| Remove duplicate knowledge stores | 0.5 day | Backend |
| Remove duplicate TF-IDF implementations | 0.5 day | Backend |
| Remove duplicate provider systems | 1 day | Backend |

### H2. CI/CD Pipeline — 2-3 days
| Task | Effort | Owner |
|------|--------|-------|
| Set up GitHub Actions workflow | 1 day | DevOps |
| Add linting (ruff) + formatting (black) | 0.5 day | Backend |
| Add test execution in CI | 0.5 day | DevOps |
| Add Docker build + push | 0.5 day | DevOps |
| Add deployment script | 0.5 day | DevOps |

### H3. Structured Logging — 1-2 days
| Task | Effort | Owner |
|------|--------|-------|
| Configure JSON logging format | 0.5 day | Backend |
| Add request ID to all logs | 0.5 day | Backend |
| Add log rotation (RotatingFileHandler) | 0.5 day | Backend |
| Add structured error logging | 0.5 day | Backend |

### H4. Agent Improvements — 3-5 days
| Task | Effort | Owner |
|------|--------|-------|
| Replace sleep-based dependency resolution | 1 day | AI |
| Wire WebSocket consumers to real agents | 2 days | AI |
| Add agent result caching | 0.5 day | AI |
| Implement parallel agent execution | 1 day | AI |

### H5. Monitoring — 2-3 days
| Task | Effort | Owner |
|------|--------|-------|
| Add Prometheus metrics export | 1 day | DevOps |
| Define SLI/SLO alerting rules | 0.5 day | SRE |
| Add request tracing with OpenTelemetry | 1 day | DevOps |
| Set up basic Grafana dashboard | 0.5 day | DevOps |

---

## MEDIUM (Complete Within 1 Month)

### M1. Performance Optimization — 3-5 days
| Task | Effort | Owner |
|------|--------|-------|
| Add GZip compression | 0.5 day | Backend |
| Implement async views for I/O-bound endpoints | 2 days | Backend |
| Add prompt caching (Redis) | 1 day | AI |
| Add response caching for deterministic queries | 1 day | AI |
| Implement token counting (tiktoken) | 0.5 day | AI |

### M2. AI System Improvements — 5-7 days
| Task | Effort | Owner |
|------|--------|-------|
| Implement ChainCollaborationProvider | 2 days | AI |
| Replace TF-IDF with sentence-transformers | 2 days | AI |
| Add FAISS vector index | 1 day | AI |
| Implement request batching for LLM | 1 day | AI |
| Add circuit breaker pattern for providers | 1 day | AI |

### M3. API Improvements — 2-3 days
| Task | Effort | Owner |
|------|--------|-------|
| Enable API versioning | 0.5 day | Backend |
| Remove unnecessary @csrf_exempt | 1 day | Backend |
| Add API documentation UI (Swagger) | 0.5 day | Backend |
| Add request/response logging | 0.5 day | Backend |

### M4. Code Quality — 2-3 days
| Task | Effort | Owner |
|------|--------|-------|
| Add ruff + black configuration | 0.5 day | Backend |
| Add pre-commit hooks | 0.5 day | Backend |
| Fix code style inconsistencies | 1 day | Backend |
| Add type hints to critical paths | 1 day | Backend |

---

## LOW (Complete Within Quarter)

### L1. Documentation — 2-3 days
| Task | Effort | Owner |
|------|--------|-------|
| Archive root-level markdown files | 0.5 day | Tech Writer |
| Write operational runbook | 1 day | SRE |
| Write incident response playbook | 1 day | SRE |
| Update API documentation | 0.5 day | Backend |

### L2. Infrastructure — 2-3 days
| Task | Effort | Owner |
|------|--------|-------|
| Add log rotation | 0.5 day | DevOps |
| Add automated database backups | 1 day | DevOps |
| Add .env to .gitignore verification | 0.1 day | Backend |
| Remove empty directories | 0.1 day | Backend |
| Add pre-commit .gitignore check | 0.1 day | Backend |

### L3. Frontend — 5-7 days
| Task | Effort | Owner |
|------|--------|-------|
| Set up ESLint + Prettier | 0.5 day | Frontend |
| Add state management (Zustand) | 2 days | Frontend |
| Add API integration tests | 1 day | Frontend |
| Add E2E tests (Playwright) | 2 days | Frontend |
| Add error boundaries | 0.5 day | Frontend |

---

## Effort Summary

| Priority | Tasks | Effort (days) | Dependencies |
|----------|-------|---------------|--------------|
| CRITICAL | 20 | 13-20 | None |
| HIGH | 15 | 13-20 | CRITICAL |
| MEDIUM | 12 | 12-18 | HIGH |
| LOW | 10 | 9-13 | MEDIUM |
| **TOTAL** | **57** | **47-71** | |

---

## Milestone Plan

### Milestone 1: Security Hardening (Week 1)
- [ ] All CRITICAL security fixes
- [ ] PostgreSQL migration
- [ ] Redis caching layer

### Milestone 2: Quality Foundation (Week 2-3)
- [ ] Test suite >50% coverage
- [ ] CI/CD pipeline
- [ ] Structured logging

### Milestone 3: Architecture Cleanup (Week 3-4)
- [ ] Controller decomposition
- [ ] Duplicate elimination
- [ ] Agent improvements

### Milestone 4: Production Readiness (Week 5-6)
- [ ] Monitoring + alerting
- [ ] Performance optimization
- [ ] API improvements

### Milestone 5: Book 2 Ready (Week 7-8)
- [ ] All HIGH items complete
- [ ] MEDIUM items in progress
- [ ] Documentation updated
- [ ] Final review

---

## Go/No-Go Criteria for Book 2

| Criterion | Required | Current Status |
|-----------|----------|----------------|
| PostgreSQL database | YES | NOT MET |
| Redis caching | YES | NOT MET |
| Test coverage >50% | YES | NOT MET |
| CI/CD pipeline | YES | NOT MET |
| No CRITICAL security vulns | YES | NOT MET |
| CORS configured | YES | NOT MET |
| HTTPS enforced | YES | NOT MET |
| Structured logging | RECOMMENDED | NOT MET |

**Current Status: NO-GO**

**Estimated Date Ready:** 2-3 weeks from start
