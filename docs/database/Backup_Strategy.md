# AIDA Enterprise Database Architecture
## Backup Strategy

**Versiya:** 1.0.0
**Sana:** 2026-07-03
**Muallif:** AIDA Database Team

---

## 1. BACKUP ARXITEKTURASI

```
┌─────────────────────────────────────────────────────────────────┐
│                    AIDA BACKUP SYSTEM                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [PostgreSQL Primary]                                           │
│       │                                                         │
│       ├── WAL Streaming ──► [S3: wal-archive/] (real-time)     │
│       │                      Retention: 30 kun                  │
│       │                                                         │
│       ├── pg_basebackup ──► [S3: base-backups/] (haftalik)     │
│       │                      Retention: 4 hafta                 │
│       │                                                         │
│       ├── pg_dump ─────────► [S3: logical-dumps/] (haftalik)   │
│       │                      Retention: 12 hafta                │
│       │                                                         │
│       └── Snapshot ────────► [Cloud Snapshot] (soatlik)        │
│                               Retention: 48 soat               │
│                                                                 │
│  [Redis]                                                        │
│       ├── RDB Snapshot ──► [S3: redis-backups/] (soatlik)      │
│       └── AOF ───────────► [S3: redis-aof/] (real-time)        │
│                                                                 │
│  [S3 Primary] ────────────► [S3 DR Region] (cross-region)      │
│  (same region)               Replication                        │
│                                                                 │
│  [S3 DR Region] ──────────► [Glacier] (30 kundan keyin)        │
│                              Cold Archive                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. BACKUP TURLARI

### 2.1 WAL Continuous Archiving (Uzluksiz)

```
Tur:        Physical, real-time
Vosita:     pgBackRest / pg_receivewal
Interval:   Har 5 daqiqada S3'ga
Retention:  30 kun
RPO:        ≤ 5 daqiqa (oxirgi WAL segment)

Maqsad:
  Point-in-time recovery (PITR) imkoni beradi.
  "Kecha soat 14:37 dagi holatga qaytish" mumkin bo'ladi.

Saqlash joyi:
  s3://aida-backups/wal-archive/{yil}/{oy}/{kun}/

Verification:
  WAL fayllar checksum bilan tekshiriladi
  Har kecha 03:00 da WAL sequence uzilishini tekshirish
```

### 2.2 Base Backup (Haftalik Full)

```
Tur:        Physical, full
Vosita:     pgBackRest yoki pg_basebackup
Jadval:     Yakshanba 01:00 UTC
Retention:  4 hafta (4 ta full backup)
Hajm:       ~2-10 GB (compressed)

Jarayon:
  1. pg_basebackup --checkpoint=fast --wal-method=stream
  2. pgBackRest bilan compress + encrypt
  3. S3'ga yuklash
  4. Checksum verification
  5. Monitoring'ga muvaffaqiyat signal

Saqlash joyi:
  s3://aida-backups/base-backups/{YYYY-WW}/
```

### 2.3 Logical Backup (Haftalik pg_dump)

```
Tur:        Logical, full
Vosita:     pg_dump --format=custom
Jadval:     Shanba 02:00 UTC
Retention:  12 hafta (3 oy)
Hajm:       ~500MB-5GB (compressed)

Afzalliklari:
  - Alohida table restore mumkin
  - PostgreSQL versiyalar orasida portativ
  - Schema-only dump imkoni

Saqlash joyi:
  s3://aida-backups/logical-dumps/{YYYY-WW}/full.dump
  s3://aida-backups/logical-dumps/{YYYY-WW}/schema-only.dump
```

### 2.4 Incremental Backup (Kunlik)

```
Tur:        Physical, incremental
Vosita:     pgBackRest --type=incr
Jadval:     Har kecha 02:00 UTC (Yakshanba tashqari)
Retention:  7 kun
Hajm:       ~50-500MB (faqat o'zgargan bloklar)

Saqlash joyi:
  s3://aida-backups/incremental/{YYYY-MM-DD}/
```

### 2.5 Cloud Snapshot (Soatlik)

```
Tur:        Block-level snapshot (cloud managed)
Vosita:     AWS EBS Snapshot / GCP Persistent Disk Snapshot
Jadval:     Har soatda
Retention:  48 soat
Tezlik:     RTO ~5 daqiqa (snapshot'dan restore)

Afzallik: Cloud provider boshqaradi, avtomatik
```

---

## 3. BACKUP JADVALI UMUMIY KO'RINISH

```
┌─────────────┬──────────────┬────────────────────┬────────────────┐
│ Backup Turi │ Jadval       │ Retention          │ RPO / RTO      │
├─────────────┼──────────────┼────────────────────┼────────────────┤
│ WAL Archive │ Real-time    │ 30 kun             │ RPO: ≤5 min    │
│ Snapshot    │ Soatlik      │ 48 soat            │ RTO: ~5 min    │
│ Incremental │ Kecha 02:00  │ 7 kun              │ RTO: ~15 min   │
│ Full (base) │ Yakshanba    │ 4 hafta            │ RTO: ~30 min   │
│ Logical dump│ Shanba 02:00 │ 12 hafta           │ RTO: ~1 soat   │
│ Monthly     │ Har oy 1-si  │ 12 oy             │ Archive        │
│ Redis RDB   │ Soatlik      │ 7 kun              │ RPO: ~1 soat   │
│ Redis AOF   │ Real-time    │ 3 kun              │ RPO: ~1 sek    │
└─────────────┴──────────────┴────────────────────┴────────────────┘
```

---

## 4. SAQLASH JOYLARI (GEO-REDUNDANCY)

```
PRIMARY STORAGE:
  Provider:   AWS S3 / MinIO
  Region:     eu-central-1 (yoki asosiy region)
  Bucket:     aida-db-backups-primary
  Versioning: ENABLED
  Encryption: SSE-S3 (server-side)

SECONDARY STORAGE (DR):
  Provider:   AWS S3
  Region:     eu-west-1 (boshqa region)
  Bucket:     aida-db-backups-dr
  Replication: S3 Cross-Region Replication (CRR)
  Lag:        ~1-5 daqiqa

COLD ARCHIVE:
  Provider:   AWS Glacier / S3 Glacier Deep Archive
  Trigger:    30 kundan eski backuplar avtomatik lifecycle policy
  Cost:       ~$0.004/GB/oy
  Retrieval:  3-12 soat (Glacier), 12-48 soat (Deep Archive)
```

---

## 5. BACKUP TEKSHIRISH (VERIFICATION)

```
Avtomatik tekshirish jadvali:

KUNLIK (har kecha 04:00):
  [ ] WAL sequence uzilishini tekshirish
  [ ] Oxirgi backup checksum verification
  [ ] S3 bucket accessibility check
  [ ] Backup fayl hajmi anomaliyasini tekshirish (±30% threshold)

HAFTALIK (Dushanba 05:00):
  [ ] Incremental backup'dan to'liq restore (test muhit)
  [ ] Row count validation (asosiy jadvallarda)
  [ ] Schema integrity check
  [ ] Application smoke test (10 ta muhim query)

OYLIK:
  [ ] Full backup'dan to'liq restore (staging muhit)
  [ ] DR regiondan restore testi
  [ ] PITR (point-in-time recovery) testi — random vaqt tanlash
  [ ] RTO vaqtini o'lchash va hujjatlashtirish

Verification natijasi monitoring'ga yuboriladi:
  aida_backup_last_success_timestamp → Prometheus metric
  aida_backup_verification_status    → Grafana dashboard
```

---

## 6. DISASTER RECOVERY (DR)

### 6.1 RPO va RTO Maqsadlari

```
RPO (Recovery Point Objective):
  Kritik data:    ≤ 5 daqiqa   (WAL streaming bilan)
  Normal data:    ≤ 1 soat     (snapshot bilan)

RTO (Recovery Time Objective):
  Snapshot restore:  ≤ 15 daqiqa
  Base backup:       ≤ 45 daqiqa
  Full rebuild:      ≤ 2 soat
```

### 6.2 DR Runbook — Qadamba-qadam

```
HOLAT: Primary database server ishlamayapti

QADAM 1: Holatni tasdiqlash (0-5 daqiqa)
  □ Prometheus: aida_health_check_status{service="database"} == 0
  □ SSH orqali serverga ulanishga urinish
  □ Cloud provider console'da instance statusini tekshirish
  □ Read replica ishlayaptimi tekshirish

QADAM 2: Read Replica'ni Promote qilish (5-10 daqiqa)
  □ Read replica'da: SELECT pg_promote();
     yoki: pg_ctl promote -D /var/lib/postgresql/data
  □ Replica endi primary bo'ldi
  □ Application connection string'ni yangilash
  □ HAProxy/Patroni avtomatik failover (agar sozlangan)

QADAM 3: Application'ni yangi Primary'ga yo'naltirish (10-15 daqiqa)
  □ DNS/VIP o'zgartirish: DB_HOST env variable
  □ PgBouncer'ni reload: pgbouncer -R
  □ Django server restart (connection pool yangilash uchun)
  □ Health check endpoint tekshirish: GET /api/health/

QADAM 4: Monitoring va Verification (15-30 daqiqa)
  □ Write queries ishlayaptimi tekshirish
  □ Error rate normal darajaga tushdimi
  □ WAL archiving yangi primary'da boshlandimi
  □ Incident log yozish

QADAM 5: Yangi Replica yaratish (keyingi 2 soatda)
  □ Yangi server provision
  □ pg_basebackup orqali current primary'dan replica
  □ Streaming replication sozlash
  □ Patroni/Sentinel'ga qo'shish
```

### 6.3 Failback Jarayoni (Primary tiklanganida)

```
QADAM 1: Eski primary'ni to'ldirish
  □ pgBackRest restore --type=standby orqali current data bilan sync

QADAM 2: Eski primary'ni yangi replica sifatida ulash
  □ recovery.conf / standby.signal sozlash
  □ Replication lag monitoring (0'ga yetguncha kutish)

QADAM 3: Agar kerak bo'lsa — swap back
  □ Maintenance window e'lon qilish
  □ pg_promote eski primary'da
  □ Connection string qayta o'zgartirish
  □ Verify + smoke test
```

---

## 7. REDIS BACKUP

```
RDB Snapshot:
  save 900 1      (900 sek = 15 min, 1 ta o'zgarish)
  save 300 10     (300 sek = 5 min, 10 ta o'zgarish)
  save 60 10000   (60 sek, 10000 ta o'zgarish)
  Saqlash: S3'ga soatlik upload

AOF (Append Only File):
  appendonly yes
  appendfsync everysec   (har sekundda fsync)
  Saqlash: S3'ga kunlik upload

Redis Cluster DR:
  Primary cluster down → replica promote (Sentinel avtomatik)
  RTO: ~30 saniya
```

---

## 8. VECTOR DATABASE BACKUP (pgvector)

```
pgvector PostgreSQL'da saqlangani uchun:
  → Barcha yuqoridagi PostgreSQL backup'lar embeddings'ni ham qamrab oladi

Alohida muammo:
  embeddings jadvali juda katta bo'lishi mumkin (GB'lab vektor)
  pg_dump --table=embeddings alohida bajarilishi mumkin

Re-indexing:
  Embedding vektorlar yo'qolsa — knowledge manbalaridan qayta generatsiya qilish mumkin
  Bu mahal AI model chaqiriqlari talab qilinadi (cost va vaqt hisobi)
  Shuning uchun embedding backup alohida muhim
```

---

## 9. BACKUP MONITORING VA ALERTLAR

```
Prometheus Metrics:
  aida_backup_last_success_timestamp{type="wal"}         → Gauge
  aida_backup_last_success_timestamp{type="full"}        → Gauge
  aida_backup_size_bytes{type="incremental", date="..."}  → Gauge
  aida_backup_duration_seconds{type="full"}               → Gauge
  aida_backup_verification_success{type="weekly"}         → Gauge

Alert Qoidalari:
  WAL backup 10 daqiqadan ortiq kelmasa        → P2 HIGH
  Daily backup muvaffaqiyatsiz bo'lsa          → P2 HIGH
  Weekly verification muvaffaqiyatsiz bo'lsa   → P1 CRITICAL
  Backup hajmi 50% kamaysa (anomaliya)         → P2 HIGH
  DR region replication lag > 1 soat          → P2 HIGH
```

---

## 10. XARAJAT OPTIMALLASHTIRISH

```
S3 Storage Classes:
  0–7 kun:    S3 Standard       (~$0.023/GB/oy)
  7–30 kun:   S3 Standard-IA    (~$0.0125/GB/oy)  ← Infrequent Access
  30–90 kun:  S3 Glacier IR     (~$0.004/GB/oy)
  90+ kun:    S3 Glacier DA     (~$0.00099/GB/oy) ← Deep Archive

Lifecycle Policy (S3 Bucket):
  Day 7:   Transition to Standard-IA
  Day 30:  Transition to Glacier Instant Retrieval
  Day 90:  Transition to Glacier Deep Archive
  Day 365: Delete (agar compliance talab qilmasa)

Taxminiy oylik xarajat (100GB database):
  WAL archive (30 kun): ~$3/oy
  Backups (all types):  ~$5/oy
  DR region:            ~$5/oy (replication)
  JAMI:                 ~$13/oy
```

---

## 11. COMPLIANCE VA DATA RETENTION

```
GDPR Article 17 (Right to Erasure):
  Foydalanuvchi o'chirish so'rovi → 30 kun ichida bajarilishi kerak
  Backup'lardagi ma'lumotlar: backup retention tugaguncha qoladi
  GDPR bo'yicha bu qonuniy (Article 17(3)(b))
  Yozma ravishda foydalanuvchiga xabar beriladi

Data Retention Siyosati:
  Session data:      30 kun
  Audit logs:        365 kun (compliance uchun)
  System logs:       90 kun
  Chat messages:     Foydalanuvchi o'chirishicha (unlimited)
  Embedding vectors: Knowledge bilan birga

Backup Immutability (S3 Object Lock):
  Audit log backup'lari: COMPLIANCE mode, 365 kun
  O'chirib bo'lmaydi — forensics uchun zarur
```

---

*Hujjat AIDA Development Bible — Book 1, Chapter 8 asosida tayyorlangan.*
