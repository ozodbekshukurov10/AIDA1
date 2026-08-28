# AIDA -- Enterprise Log Retention Policy

## 1. Policy Overview

Ushbu hujjat AIDA logging tizimining saqlash, arxivlash, compress qilish va o'chirish siyosatini belgilaydi. Har bir log kategoriyasi o'zining retention, rotation va compliance talablariga ega.

```
+------------------------------------------------------------+
|                    LOG LIFECYCLE                           |
|                                                            |
|  Generation -> Collection -> Processing -> Storage -> Archive
|                                                  -> Delete
|                                                  -> Comply
+------------------------------------------------------------+
```

**Current State**: Hozirda faqat RotatingFileHandler (10MB, 5 backups) mavjud. Retention siyosati mavjud emas.

## 2. Retention by Log Category

### 2.1 Application Logs

| Category | Hot Storage | Warm Storage | Cold Archive | Total | Compliance |
|----------|-------------|--------------|--------------|-------|------------|
| aida.log (main) | 7 days | 30 days | 90 days | 90 days | Internal |
| error.log | 30 days | 90 days | 1 year | 1 year | SOC 2 |
| system.log | 7 days | 30 days | 90 days | 90 days | Internal |
| db.log | 7 days | 30 days | 90 days | 90 days | Internal |
| api.log | 7 days | 30 days | 90 days | 90 days | Internal |
| perf.log | 1 day | 7 days | 30 days | 30 days | Internal |

### 2.2 AI Logs

| Category | Hot Storage | Warm Storage | Cold Archive | Total | Compliance |
|----------|-------------|--------------|--------------|-------|------------|
| llm.log | 7 days | 30 days | 90 days | 90 days | Internal |
| agent.log | 30 days | 90 days | 1 year | 1 year | Internal |
| tool.log | 7 days | 30 days | 90 days | 90 days | Internal |
| workflow.log | 30 days | 90 days | 1 year | 1 year | Internal |
| tokens.log | 90 days | 1 year | 3 years | 3 years | Billing |
| Full prompts | 1 day | 7 days | 30 days | 30 days | Internal |

### 2.3 Security Logs

| Category | Hot Storage | Warm Storage | Cold Archive | Total | Compliance |
|----------|-------------|--------------|--------------|-------|------------|
| security.log | 90 days | 1 year | 3 years | 3 years | SOC 2, PCI DSS |
| auth.log | 90 days | 1 year | 3 years | 3 years | SOC 2 |
| apikey.log | 1 year | 3 years | 7 years | 7 years | SOC 2, SOX |
| HIGH events | 1 year | 3 years | 7 years | 7 years | SOC 2 |
| CRITICAL events | 2 years | 5 years | 10 years | 10 years | All |

### 2.4 Audit Logs

| Category | Hot Storage | Warm Storage | Cold Archive | Total | Compliance |
|----------|-------------|--------------|--------------|-------|------------|
| audit.log | 90 days | 1 year | 7 years | 7 years | SOC 2, SOX |
| Config changes | 90 days | 1 year | 7 years | 7 years | SOC 2, ISO |
| Plugin changes | 90 days | 1 year | 7 years | 7 years | SOC 2 |
| Admin actions | 1 year | 3 years | 7 years | 7 years | SOC 2, SOX, HIPAA |
| Deployments | 30 days | 90 days | 1 year | 1 year | Internal |

## 3. Storage Tiers

### 3.1 Tier Definitions

| Tier | Storage Medium | Access Time | Cost | Retention Target |
|------|---------------|-------------|------|------------------|
| **Hot** | SSD / Local disk | < 10ms | High | Latest data |
| **Warm** | HDD / Network storage | < 100ms | Medium | Recent data |
| **Cold** | S3 / Glacier / Tape | > 1s | Low | Archived data |

### 3.2 Tier Transition

```
Day 0-7:     HOT   - SSD, immediate query
Day 8-30:    WARM  - HDD, queryable with index
Day 31-365:  COLD  - S3/Glacier, compressed, manual restore
Day 365+:    DEEP  - Glacier Deep Archive, compliance only
```

## 4. Log Rotation

### 4.1 Current Rotation (Active)

```python
# aidaos/infrastructure/logging/__init__.py
RotatingFileHandler(
    maxBytes=10 * 1024 * 1024,   # 10 MB per file
    backupCount=5,                 # 5 rotated backups
    encoding="utf-8",
)
```

### 4.2 Target Rotation by Category

| Category | Rotation Trigger | Max Size | Backup Count | Format |
|----------|-----------------|----------|--------------|--------|
| aida.log | Size | 100 MB | 10 | JSON |
| error.log | Size | 100 MB | 20 | JSON |
| security.log | Daily | 50 MB | 30 | JSON |
| audit.log | Daily | 50 MB | 90 | JSONL |
| ai/llm.log | Size | 200 MB | 5 | JSON |
| ai/agent.log | Size | 100 MB | 10 | JSON |
| ai/tokens.log | Daily | 10 MB | 365 | JSON |
| perf.log | Hourly | 50 MB | 24 | JSON |

### 4.3 Size-Based Rotation (Current)

```python
# Active: size-based with RotatingFileHandler
# Target: size + time hybrid
class HybridRotatingHandler:
    """Rotates by size OR time, whichever comes first."""
    def __init__(self, max_bytes=100*1024*1024, when='midnight', backup_count=10):
        self.size_handler = RotatingFileHandler(maxBytes=max_bytes, backupCount=backup_count)
        self.time_handler = TimedRotatingFileHandler(when=when, backupCount=backup_count)
```

## 5. Compression

### 5.1 Compression Strategy

| Stage | Format | Tool | Ratio | Action |
|-------|--------|------|-------|--------|
| Warm archive | gzip | gzip | 10:1 | Auto-compress on transition |
| Cold archive | gzip | pigz (parallel) | 12:1 | Manual or scheduled |
| Deep archive | zstd | zstd | 15:1 | Compliance only |

### 5.2 Compression Schedule

```bash
# Daily compression of previous day's logs
0 3 * * *  find /var/log/aida/ -name '*.log' -mtime +7 -exec gzip {} \;

# Weekly compression of warm logs
0 4 * * 0  find /var/log/aida/ -name '*.jsonl' -mtime +30 -exec pigz {} \;

# Monthly archive to cold storage
0 5 1 * *  tar czf /archive/aida/logs-$(date +%Y-%m).tar.gz /var/log/aida/archive/
```

## 6. Archive Structure

```
archive/
+-- aida/
�   +-- application/
�   �   +-- 2026/
�   �   �   +-- Q1/
�   �   �   �   +-- aida.2026-01.tar.gz
�   �   �   �   +-- aida.2026-02.tar.gz
�   �   �   �   +-- aida.2026-03.tar.gz
�   �   �   +-- Q2/
�   �   �   +-- ...
�   �   +-- 2027/
�   +-- security/
�   �   +-- 2026/
�   �       +-- security.2026-01.tar.gz (encrypted)
�   �       +-- ...
�   +-- audit/
�   �   +-- 2026/
�   �       +-- audit.2026-01.tar.gz (encrypted)
�   �       +-- ...
�   +-- ai/
�       +-- 2026/
�           +-- llm.2026-01.tar.gz
�           +-- tokens.2026-01.tar.gz
+-- index.json                           # Archive manifest
```

## 7. Encryption

| Stage | Encryption | Standard | Key Management |
|-------|------------|----------|----------------|
| At rest (hot) | AES-256-GCM | SOC 2 | OS-level (LUKS) |
| At rest (warm) | AES-256-GCM | FIPS 140-2 | LUKS / BitLocker |
| In archive | AES-256-GCM | FIPS 140-2 | KMS / Vault |
| In transit | TLS 1.3 | PCI DSS | Auto (HTTPS) |

## 8. Deletion Policy

### 8.1 Deletion Schedule

| Tier | Retention Period | Action | Authorization |
|------|-----------------|--------|---------------|
| Hot | As per category table | Auto-delete (cold storage promotes) | System |
| Warm | As per category table | Auto-delete after archive confirmed | System |
| Cold | As per compliance table | Manual purge | Security team |
| Deep | 10+ years | Legal hold only | Legal + Security |

### 8.2 Deletion Process

```python
# aida/logs/retention/cleanup.py
def apply_retention_policy():
    for category in LOG_CATEGORIES:
        cutoff = datetime.now() - category.retention_delta

        # 1. Compress warm logs
        compress_logs(category, days_old=7)

        # 2. Move to cold storage
        archive_to_s3(category, days_old=30)

        # 3. Verify archive integrity
        verify_archive_checksum(category)

        # 4. Delete local files
        delete_local_logs(category, older_than=category.retention_delta)

        # 5. Log the cleanup
        logger.info("Retention applied: %s deleted logs older than %s",
                    category.name, cutoff)
```

### 8.3 Legal Hold

Muayyan loglar sud/qonun talabi bilan saqlanishi kerak:

```python
# aida/logs/retention/legal_hold.py
LEGAL_HOLDS = {
    "case-2026-001": {
        "holder": "Legal Department",
        "date_from": "2026-01-01",
        "date_to": "2026-06-30",
        "categories": ["audit", "security", "auth"],
        "expires": "2028-01-01"
    }
}
```

## 9. Backup Strategy

### 9.1 Backup Schedule

| Data | Frequency | Retention | Type | Location |
|------|-----------|-----------|------|----------|
| Hot logs | Real-time (sync) | 24 hours | Mirror | Secondary SSD |
| Warm logs | Daily | 7 days | Snapshot | Network storage |
| Cold archive | Weekly | 1 month | Full copy | S3 (different region) |
| Audit logs | Real-time | 1 year | WORM copy | Immutable bucket |

### 9.2 Backup Verification

```bash
# Verify archive checksums weekly
aida logs verify --archive 2026-Q1

# Test restore monthly
aida logs restore --from archive/2026/03 --to /tmp/test-restore

# Backup integrity report
aida logs backup --status
```

## 10. Compliance Matrix

| Standard | Retention Requirement | AIDA Policy |
|----------|----------------------|-------------|
| SOC 2 | 6 months - 1 year | 1-3 years (security/audit) |
| GDPR | Right to deletion | Deletion supported with legal hold |
| HIPAA | 6 years | 7 years audit, 10 years critical |
| PCI DSS | 1 year | 3 years security, 7 years apikey |
| SOX | 7 years | 7 years audit |
| ISO 27001 | Defined policy | Compliant per category |
| FINRA | 7 years | 7 years audit + security |

## 11. Monitoring & Alerts

| Alert Condition | Severity | Action |
|----------------|----------|--------|
| Disk usage > 80% | WARNING | Compress oldest logs |
| Disk usage > 90% | CRITICAL | Emergency rotation |
| Archive sync failed | HIGH | Retry + notify DevOps |
| Archive integrity check failed | CRITICAL | Restore from backup |
| Legal hold conflict | HIGH | Notify security team |
| Retention policy not applied | MEDIUM | Run cleanup manually |

## 12. Implementation Priority

| Phase | Component | Priority | Effort |
|-------|-----------|----------|--------|
| P0 | Category-based log file separation | CRITICAL | Medium |
| P0 | Daily log rotation for audit/security | CRITICAL | Small |
| P1 | Log compression for warm storage | HIGH | Medium |
| P1 | Archive management (S3 backup) | HIGH | Large |
| P2 | Retention policy automation | MEDIUM | Medium |
| P2 | Archive encryption | MEDIUM | Medium |
| P3 | Legal hold system | LOW | Medium |
| P3 | Compliance reporting | LOW | Large |
