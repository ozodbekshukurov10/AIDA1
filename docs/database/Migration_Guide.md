# AIDA Enterprise Database Architecture
## Migration Guide

**Versiya:** 1.0.0
**Sana:** 2026-07-03
**Muallif:** AIDA Database Team

---

## 1. MIGRATION ARXITEKTURASI

```
┌─────────────────────────────────────────────────────────────────┐
│                   AIDA MIGRATION PIPELINE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Developer]                                                    │
│      │ python manage.py makemigrations                         │
│      ▼                                                          │
│  [Migration File]  ←── git commit                               │
│      │                                                          │
│      ▼                                                          │
│  [CI Pipeline]                                                  │
│      ├── migrate --check  (pending migrations bor?)            │
│      ├── Unit tests                                             │
│      └── Integration tests                                      │
│      │                                                          │
│      ▼                                                          │
│  [Staging Deploy]                                               │
│      ├── Pre-migration backup                                   │
│      ├── python manage.py migrate                               │
│      ├── Smoke tests                                            │
│      └── Row count validation                                   │
│      │                                                          │
│      ▼ (manual approval for production)                        │
│  [Production Deploy]                                            │
│      ├── Pre-migration backup (mandatory)                       │
│      ├── python manage.py migrate                               │
│      ├── Health check                                           │
│      └── Rollback if health check fails                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. VERSIONING STRATEGIYASI

### 2.1 Migration Fayl Nomlash

```
Format:  NNNN_verb_description.py
         NNNN = 4 raqamli ketma-ket raqam

Misollar:
  0001_initial.py
  0002_add_user_avatar_url.py
  0003_create_organization_members_table.py
  0004_alter_messages_add_token_count.py
  0005_add_embeddings_hnsw_index.py

Qoidalar:
  ✅ Tushunarli tavsif (verb + noun)
  ✅ Lowercase, underscore
  ✅ Django app bo'yicha ajratilgan
  ❌ Vaqt tamg'asi migration nomida (git tarixi yetarli)
  ❌ "fix" yoki "update" kabi noaniq nomlar
```

### 2.2 App Strukturasi

```
AIDA Django Apps va ularning migrationlari:

apps/
  users/migrations/          0001..NNNN
  organizations/migrations/  0001..NNNN
  projects/migrations/       0001..NNNN
  chats/migrations/          0001..NNNN
  agents/migrations/         0001..NNNN
  knowledge/migrations/      0001..NNNN
  system/migrations/         0001..NNNN (audit_logs, system_logs, config)
```

### 2.3 Branch Merging Muammolari

```
Muammo: Ikki developer parallel migration yaratdi

Developer A:  0005_add_user_phone.py
Developer B:  0005_create_notifications.py   ← CONFLICT!

Yechim:
  1. Developer B migration'ini 0006 ga rename qiladi
  2. B'ning migration'ida dependencies:
     dependencies = [('users', '0005_add_user_phone')]
  3. Linear history saqlash uchun squash kerak bo'lsa:
     python manage.py squashmigrations app 0001 0005

Qoida: Merge'dan oldin migration raqamlarini tekshiring!
```

### 2.4 Squash Migrations

```
Qachon squash kerakl:
  - 50+ migration bo'lganda (startup sekinlashadi)
  - Major release oldidan
  - Database'ni scratch'dan qayta o'rnatish tez bo'lishi uchun

Qachon squash QILINMAYDI:
  - Production'da deploy qilingan migrationlar (ishlaydigan tizimlarda)
  - Boshqalar branch'larida pull qilmagan migrationlar

Jarayon:
  python manage.py squashmigrations myapp 0001 0020
  → 0001_squashed_0020_description.py yaratiladi
  → Eski migrationlar replaces = [...] bilan belgilanadi
  → Barcha muhitlar yangi migration bilan o'tgach eski fayllar o'chiriladi
```

---

## 3. MIGRATION TURLARI

### 3.1 Schema Migration (DDL)

```
Nima: Jadval yaratish, ustun qo'shish/o'chirish, index, constraint

Reversible misol:
  def up():   ALTER TABLE users ADD COLUMN phone VARCHAR(20)
  def down(): ALTER TABLE users DROP COLUMN phone

Irreversible misol:
  def up():   DROP TABLE old_sessions
  def down(): pass  # Qaytarib bo'lmaydi

Irreversible migration qoidasi:
  ✅ Faqat bitta shart ostida ruxsat: ma'lumot boshqa joyga ko'chirilgan
  ✅ Majburiy: "# IRREVERSIBLE — data migrated to X" comment
  ✅ Majburiy: Pre-migration backup
  ❌ Ma'lumot yo'qoladi — hech qachon ruxsat berilmaydi
```

### 3.2 Data Migration (DML)

```
Nima: Mavjud ma'lumotlarni transform qilish, ko'chirish, to'ldirish

Qoida: HECH QACHON schema va data migration bir faylda!
Sabab: Schema migration tez, data migration sekin (million rows)

Misol: User'larni org'ga ko'chirish
  # Faza 1: Schema migration (0010_add_org_id_to_users.py)
  #   ADD COLUMN org_id NULLABLE
  # Faza 2: Data migration (0011_populate_org_id.py)
  #   UPDATE users SET org_id = default_org.id
  # Faza 3: Schema migration (0012_make_org_id_required.py)
  #   ALTER COLUMN org_id SET NOT NULL

Django data migration pattern:
  def migrate_data(apps, schema_editor):
      User = apps.get_model('users', 'User')
      Org = apps.get_model('organizations', 'Organization')
      default_org = Org.objects.get(slug='default')
      # Chunked update (1000 ta bir vaqtda)
      User.objects.filter(org__isnull=True).update(org=default_org)

  class Migration(migrations.Migration):
      operations = [migrations.RunPython(migrate_data, migrations.RunPython.noop)]
```

---

## 4. ZERO-DOWNTIME MIGRATION

### 4.1 Expand-Contract Pattern

```
Muammo: users.full_name ustunini first_name + last_name ga bo'lish
         Eski kod full_name'ni ishlatadi, yangi kod ikkisini ishlatadi

Yechim (3 deploy):

DEPLOY 1 — Expand:
  Migration: ADD COLUMN first_name, ADD COLUMN last_name
  Kod: full_name'ni yoza oladi, first_name + last_name ham yoza oladi
  Application: Hali full_name'ni o'qiydi

DEPLOY 2 — Migrate data:
  Migration: UPDATE SET first_name = split_part(full_name, ' ', 1)
  Kod: first_name + last_name'ni o'qiydi, full_name'ga ham yozadi
  Application: Yangi ustunlar asosiy

DEPLOY 3 — Contract:
  Migration: DROP COLUMN full_name
  Kod: Faqat first_name + last_name
```

### 4.2 Backward-Compatible O'zgarishlar

```
✅ SAFE (zero-downtime):
  ADD COLUMN (nullable yoki default bilan)
  ADD INDEX CONCURRENTLY
  ADD TABLE
  ADD CONSTRAINT (NOT VALID avval, keyin VALIDATE)
  RENAME TABLE → CREATE VIEW eski nom bilan

⚠️ EHTIYOTKORLIK BILAN:
  ADD COLUMN NOT NULL (default kerak)
  ADD FOREIGN KEY (DEFERRABLE INITIALLY DEFERRED)
  ADD UNIQUE (CREATE UNIQUE INDEX CONCURRENTLY avval)

❌ XAVFLI (downtime kerak):
  DROP COLUMN (avval kod'dan olib tashlash)
  RENAME COLUMN (avval alias yaratish)
  ALTER COLUMN TYPE (murakkab type conversion)
  DROP TABLE
```

### 4.3 Online DDL (Katta Jadvallar uchun)

```
Muammo: messages jadvali (100M+ rows) ga index qo'shish
         Oddiy CREATE INDEX → full table lock!

Yechim: CREATE INDEX CONCURRENTLY
  Afzalligi: Lock olmaydi, foydalanuvchilar davom etadi
  Kamchiligi: 2-3x sekin, vacuum bilan parallel ishlaydi

Misol:
  CREATE INDEX CONCURRENTLY idx_messages_chat_time
  ON messages(chat_id, created_at DESC);

Constraint qo'shish (katta jadvalda):
  -- Avval NOT VALID bilan qo'shing (mavjud datacha tekshirmaydi)
  ALTER TABLE orders ADD CONSTRAINT fk_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    NOT VALID;

  -- Keyin background'da validate qiling (ShareRowExclusiveLock faqat)
  ALTER TABLE orders VALIDATE CONSTRAINT fk_user;
```

---

## 5. ROLLBACK STRATEGIYASI

### 5.1 Avtomatik Rollback

```
Django migrate muvaffaqiyatsiz bo'lsa:
  - DDL: PostgreSQL atomic transaction ichida → avtomatik rollback
  - Django: migration atomically bajariladi (postgresql'da)
  - Natija: Qisman o'zgarish qolmaydi

Ammo:
  CREATE INDEX, CREATE TABLE — ba'zi DDL transactional emas!
  Bunday holatlarda qo'lda tozalash kerak.
```

### 5.2 Manual Rollback Procedure

```
QADAM 1: Muammoni aniqlash
  □ manage.py showmigrations → qaysi migration muvaffaqiyatsiz
  □ PostgreSQL logs'dan xato xabarini topish
  □ Lock kutib turgan querylar bormi: pg_stat_activity

QADAM 2: Rollback bajarish
  □ python manage.py migrate app_name 0004
     (0005 dan oldingi holatga qaytish)
  □ Migrate failed bo'lganda:
     python manage.py migrate app_name 0004 --fake
     (agar qo'lda undo qilgan bo'lsangiz)

QADAM 3: Tekshirish
  □ python manage.py showmigrations (barcha checked?)
  □ Health check endpoint
  □ Asosiy querylar ishlayaptimi

QADAM 4: Hujjatlashtirish
  □ Post-mortem yozish
  □ Migration'ni tuzatish
```

### 5.3 Data Migration Rollback

```
Data migration rollback murakkab — shuning uchun:

Qoida 1: Har data migration uchun reverse function yozing
  def rollback_data(apps, schema_editor):
      # Teskari amal
      ...

  migrations.RunPython(migrate_data, rollback_data)

Qoida 2: Katta data migration'dan oldin snapshot backup

Qoida 3: Idempotent qiling
  UPDATE users SET org_id = X WHERE org_id IS NULL
  -- Qayta ishga tushsa xato bermaydi
```

---

## 6. PRE/POST MIGRATION CHECKLIST

### 6.1 Pre-Migration (Deploy oldidan)

```
[ ] Backup mavjud va tekshirilgan (oxirgi 1 soatda)
[ ] Staging'da migration muvaffaqiyatli o'tdi
[ ] manage.py migrate --check (pending migrations soni mos)
[ ] Disk space yetarli (migration uchun 2x jadval hajmi kerak bo'lishi mumkin)
[ ] Active connections soni normal (katta migration oldida)
[ ] Monitoring dashboard ko'rinmoqda
[ ] Rollback rejasi bor
[ ] Maintenance window e'lon qilinganmi? (katta migration uchun)
```

### 6.2 Migration Jarayonida

```
[ ] Progress monitoring (katta data migration uchun)
[ ] Lock monitoring: pg_locks / pg_stat_activity
[ ] Replication lag kuzatish (replica ortda qolmasinmu)
[ ] Error log monitoring (real-time)
[ ] Migration vaqtini o'lchash
```

### 6.3 Post-Migration

```
[ ] manage.py showmigrations — barcha [X] belgilangan
[ ] Row count validation (muhim jadvallar uchun)
[ ] Constraint check: psql \d+ tablename
[ ] Index mavjudligi tekshirish: \di tablename
[ ] Application smoke test (10 ta muhim endpoint)
[ ] Health check: GET /api/health/detailed/
[ ] Error rate monitoring (5 daqiqa kuzatish)
[ ] Backup trigger (migration keyingi backup)
```

---

## 7. KATTA JADVAL MIGRATION (1M+ rows)

### 7.1 Chunked Data Migration

```python
def migrate_large_table(apps, schema_editor):
    Message = apps.get_model('chats', 'Message')

    BATCH_SIZE = 10_000
    last_id = 0

    while True:
        batch = list(
            Message.objects.filter(id__gt=last_id)
            .order_by('id')[:BATCH_SIZE]
        )
        if not batch:
            break

        # O'zgartirishlar
        for msg in batch:
            msg.new_field = compute_value(msg)

        Message.objects.bulk_update(batch, ['new_field'])
        last_id = batch[-1].id

        # Progress log
        print(f"Migrated up to id={last_id}")
```

### 7.2 Background Migration Pattern

```
Katta migration uchun (100M+ rows):

Faza 1 (Deploy 1): ADD COLUMN nullable, background job ishga tushadi
  Job: chunked update, rate-limited (DB load control)
  Monitoring: progress_percent = migrated / total * 100

Faza 2 (Deploy 2, 1-2 kun keyin): Migratsiya 100% tugagach
  ALTER COLUMN SET NOT NULL (endi xavfsiz)
  Background job o'chiriladi

Bu yondashuv bilan:
  ✅ Zero downtime
  ✅ DB load controlled
  ✅ Rollback oson (column still nullable)
```

---

## 8. EMERGENCY PROCEDURES

### 8.1 Migration Stuck (Lock Kutmoqda)

```
Simptom:
  manage.py migrate 10+ daqiqa ishlamayapti
  pg_stat_activity'da "waiting" holat

Diagnostika:
  SELECT pid, query, wait_event, wait_event_type
  FROM pg_stat_activity
  WHERE state = 'active';

  SELECT * FROM pg_locks WHERE NOT granted;

Yechim:
  1. Bloklayotgan connection'ni toping
  2. Agar idle transaction: SELECT pg_terminate_backend(pid)
  3. agar production — faqat DB admin qaror beradi

Oldini olish:
  lock_timeout = 5000ms (5 sek)  ← migration oldida set qiling
  statement_timeout = 300000ms   ← stuck query auto-kill
```

### 8.2 Disk To'lishi Migration Vaqtida

```
Simptom: migration "could not extend file" xatosi

Darhol:
  1. Migration to'xtatish: Ctrl+C
  2. Disk tozalash: old logs, temp files
  3. pg_cancel_backend(pid) — qisman migration
  4. VACUUM FULL (ehtiyotkorlik bilan — disk kerak)

Keyin:
  Disk kengaytirish (AWS EBS resize)
  Migration qayta ishga tushirish
```

### 8.3 Migration Log va Audit

```
Har migration uchun yoziladi:
  - Migration nomi va versiyasi
  - Bajarilgan vaqt (start va end)
  - Davomiyligi (ms)
  - Status (success/failure)
  - Error message (agar bor)
  - Kimning deploy'i (CI/CD user)

AuditLog'ga qo'shimcha:
  action = "database.migration"
  resource_type = "migration"
  after_data = {"migration": "0025_add_vector_index", "status": "success"}
```

---

## 9. MIGRATION SIYOSATI QOIDALARI

```
✅ MAJBURIY:
  1. Har migration faqat bitta mantiqiy o'zgarish
  2. Schema va data migration alohida fayllar
  3. Katta index → CONCURRENTLY
  4. Backward-compatible o'zgarishlar (eski kod ham ishlashi)
  5. Staging'da test qilingan
  6. Pre-migration backup

❌ TAQIQLANGAN:
  1. Production'da qo'lda SQL (migration orqali o'tkazilsin)
  2. Ma'lumotni yo'qotuvchi irreversible migration (backup talab qilinadi)
  3. Yuzlab ming rowni bir transactionda update qilish
  4. Staging test qilinmagan migration'ni production'ga deploy
  5. Ishlaydigan production'da VACUUM FULL
```

---

*Hujjat AIDA Development Bible — Book 1, Chapter 8 asosida tayyorlangan.*
