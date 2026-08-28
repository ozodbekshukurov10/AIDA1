# AIDA Enterprise Database Architecture
## Indexing Strategy

**Versiya:** 1.0.0
**Sana:** 2026-07-03
**Muallif:** AIDA Database Team

---

## 1. INDEX TURLARI

| Index turi | PostgreSQL | Ishlatilishi |
|------------|-----------|--------------|
| **B-tree** | DEFAULT | Barcha standart qidiruv, sort, range |
| **Hash** | USING HASH | Faqat `=` tenglik tekshiruvi |
| **GiST** | USING GiST | Geometric, full-text (tsvector) |
| **GIN** | USING GIN | JSONB, array, full-text search |
| **BRIN** | USING BRIN | Juda katta, naturally ordered (logs, messages) |
| **IVFFlat** | pgvector | Vector similarity (100K–1M vectors) |
| **HNSW** | pgvector | Vector similarity (>1M vectors, tez) |

### Index Tanlash Qoidasi

```
Qiymat tur:   = operator faqat    → Hash
Qiymat tur:   <, >, BETWEEN, LIKE → B-tree
JSONB qidruv: @>, ?, ?|, ?&       → GIN
Full-text:    to_tsvector/tsquery  → GIN yoki GiST
Katta jadval: append-only (logs)   → BRIN
Vector:       <->, <=>, <#>        → HNSW (production) / IVFFlat (dev)
```

---

## 2. NAMING CONVENTION

```
Format:  idx_{jadval}_{ustun(lar)}[_{qualifier}]

Misollar:
  idx_users_email                    → users.email ustuni
  idx_messages_chat_id_created_at    → composite index
  idx_chats_user_id_archived         → partial index
  idx_embeddings_vector_hnsw         → vector index
  uniq_users_email                   → unique index
  uniq_projects_org_id_slug          → unique composite
```

---

## 3. JADVALLAR BO'YICHA INDEX STRATEGIYASI

### 3.1 users

```
PRIMARY KEY:
  idx_users_pkey           ON users(id)                    -- UUID

UNIQUE INDEXES:
  uniq_users_email         ON users(email)                 -- login
  uniq_users_username      ON users(username)              -- login

SECONDARY INDEXES:
  idx_users_role           ON users(role)                  -- admin filterlash
  idx_users_is_active      ON users(is_active)             -- aktiv foydalanuvchilar
  idx_users_created_at     ON users(created_at DESC)       -- yangi ro'yxatdan o'tganlar

PARTIAL INDEXES:
  idx_users_active_only    ON users(email, username)
                           WHERE deleted_at IS NULL         -- soft delete skip
  idx_users_locked         ON users(locked_until)
                           WHERE locked_until IS NOT NULL   -- bloklangan userlar

COMPOSITE INDEXES:
  idx_users_role_active    ON users(role, is_active)       -- role + status filter

Asosiy query patterns:
  SELECT * FROM users WHERE email = ?              → uniq_users_email
  SELECT * FROM users WHERE username = ?           → uniq_users_username
  SELECT * FROM users WHERE role = ? AND is_active = TRUE → idx_users_role_active
```

### 3.2 organizations

```
PRIMARY KEY:
  idx_orgs_pkey            ON organizations(id)

UNIQUE INDEXES:
  uniq_orgs_slug           ON organizations(slug)

SECONDARY INDEXES:
  idx_orgs_owner_id        ON organizations(owner_id)      -- user'ning orglari
  idx_orgs_plan            ON organizations(plan)          -- plan filterlash
  idx_orgs_is_active       ON organizations(is_active)

PARTIAL INDEXES:
  idx_orgs_active          ON organizations(slug, plan)
                           WHERE deleted_at IS NULL
```

### 3.3 projects

```
PRIMARY KEY:
  idx_projects_pkey        ON projects(id)

UNIQUE INDEXES:
  uniq_projects_org_slug   ON projects(org_id, slug)       -- org ichida noyob

SECONDARY INDEXES:
  idx_projects_org_id      ON projects(org_id)
  idx_projects_created_by  ON projects(created_by)
  idx_projects_archived    ON projects(is_archived)

COMPOSITE INDEXES:
  idx_projects_org_active  ON projects(org_id, is_archived, created_at DESC)
  -- Query: org loyihalarini tizimlangan ko'rsatish

PARTIAL INDEXES:
  idx_projects_not_deleted ON projects(org_id, name)
                           WHERE deleted_at IS NULL
```

### 3.4 chats

```
PRIMARY KEY:
  idx_chats_pkey           ON chats(id)

SECONDARY INDEXES:
  idx_chats_user_id        ON chats(user_id)
  idx_chats_project_id     ON chats(project_id)
  idx_chats_model_id       ON chats(model_id)

COMPOSITE INDEXES:
  idx_chats_user_recent    ON chats(user_id, is_archived, last_message_at DESC)
  -- Query: foydalanuvchi so'nggi chatlari (sidebar uchun eng muhim query)

  idx_chats_project_list   ON chats(project_id, is_archived, created_at DESC)

PARTIAL INDEXES:
  idx_chats_active         ON chats(user_id, last_message_at DESC)
                           WHERE is_archived = FALSE AND deleted_at IS NULL
  idx_chats_pinned         ON chats(user_id)
                           WHERE is_pinned = TRUE
```

### 3.5 messages ⚠️ ENG MUHIM JADVAL

```
PARTITIONED BY RANGE (created_at) — oylik partitionlar
Her partition o'z indexlariga ega

PRIMARY KEY (per partition):
  idx_messages_pkey        ON messages(id, created_at)

SECONDARY INDEXES:
  idx_messages_chat_id     ON messages(chat_id)
  idx_messages_created_at  ON messages(created_at DESC)

COMPOSITE INDEXES (ENG KO'P ISHLATILADIGAN):
  idx_messages_chat_time   ON messages(chat_id, created_at DESC)
  -- Query: chat xabarlari sahifalash uchun

  idx_messages_chat_role   ON messages(chat_id, role, created_at DESC)
  -- Query: faqat user yoki assistant xabarlarini olish

PARTIAL INDEXES:
  idx_messages_not_deleted ON messages(chat_id, created_at DESC)
                           WHERE is_deleted = FALSE

BRIN INDEX (katta partitionlar uchun):
  idx_messages_created_brin USING BRIN ON messages(created_at)
  -- created_at natural order bo'lgani uchun BRIN juda samarali

Muhim: OFFSET ishlatilmaydi!
  Pagination: WHERE (created_at, id) < (cursor_time, cursor_id)
              ORDER BY created_at DESC, id DESC LIMIT 50
```

### 3.6 sessions

```
PRIMARY KEY:
  idx_sessions_pkey         ON sessions(id)

UNIQUE INDEXES:
  uniq_sessions_token_hash  ON sessions(token_hash)        -- auth lookup
  uniq_sessions_refresh     ON sessions(refresh_token_hash)
                            WHERE refresh_token_hash IS NOT NULL

SECONDARY INDEXES:
  idx_sessions_user_id      ON sessions(user_id)
  idx_sessions_expires_at   ON sessions(expires_at)        -- cleanup job

PARTIAL INDEXES:
  idx_sessions_active       ON sessions(token_hash)
                            WHERE is_active = TRUE          -- aktiv session lookup
  idx_sessions_cleanup      ON sessions(expires_at)
                            WHERE is_active = TRUE          -- muddati o'tganlarni topish
```

### 3.7 agents

```
PRIMARY KEY:
  idx_agents_pkey           ON agents(id)

UNIQUE INDEXES:
  uniq_agents_slug          ON agents(slug)

SECONDARY INDEXES:
  idx_agents_org_id         ON agents(org_id)
  idx_agents_type           ON agents(type)
  idx_agents_status         ON agents(status)

COMPOSITE INDEXES:
  idx_agents_org_status     ON agents(org_id, status, type)
  idx_agents_public         ON agents(is_public, type, status)
  -- Query: ommaviy agentlar katalogi

PARTIAL INDEXES:
  idx_agents_active         ON agents(org_id, type)
                            WHERE status = 'active' AND deleted_at IS NULL
```

### 3.8 tasks ⚠️ QUEUE QUERY MUHIM

```
PRIMARY KEY:
  idx_tasks_pkey            ON tasks(id)

SECONDARY INDEXES:
  idx_tasks_agent_id        ON tasks(agent_id)
  idx_tasks_workflow_id     ON tasks(workflow_id)
  idx_tasks_status          ON tasks(status)
  idx_tasks_created_at      ON tasks(created_at DESC)

COMPOSITE INDEXES:
  idx_tasks_queue           ON tasks(status, priority, created_at ASC)
  -- Query: keyingi pending taskni olish (Celery queue pattern)

  idx_tasks_agent_history   ON tasks(agent_id, status, created_at DESC)
  -- Query: agent task tarixi

PARTIAL INDEXES:
  idx_tasks_pending         ON tasks(priority ASC, created_at ASC)
                            WHERE status = 'pending'        -- queue lookup
  idx_tasks_running         ON tasks(agent_id, started_at)
                            WHERE status = 'running'        -- stuck task detection
```

### 3.9 knowledge

```
PRIMARY KEY:
  idx_knowledge_pkey        ON knowledge(id)

SECONDARY INDEXES:
  idx_knowledge_project_id  ON knowledge(project_id)
  idx_knowledge_source_type ON knowledge(source_type)
  idx_knowledge_index_status ON knowledge(index_status)

GIN FULL-TEXT INDEX:
  idx_knowledge_fts         USING GIN ON knowledge
                            (to_tsvector('english',
                              coalesce(title,'') || ' ' ||
                              coalesce(processed_content,'')))
  -- Query: SELECT ... WHERE to_tsvector(...) @@ to_tsquery(?)

COMPOSITE INDEXES:
  idx_knowledge_proj_status ON knowledge(project_id, is_indexed, source_type)

PARTIAL INDEXES:
  idx_knowledge_active      ON knowledge(project_id, created_at DESC)
                            WHERE deleted_at IS NULL
```

### 3.10 embeddings ⚠️ VECTOR INDEX

```
PARTITIONED BY HASH (knowledge_id) — 8 partition

PRIMARY KEY (per partition):
  idx_embeddings_pkey       ON embeddings(id, knowledge_id)

SECONDARY INDEXES:
  idx_embeddings_knowledge  ON embeddings(knowledge_id, chunk_index)
  -- Query: knowledge'ga tegishli barcha chunklar

VECTOR INDEXES (production uchun HNSW tanlangan):
  idx_embeddings_hnsw       USING HNSW ON embeddings(vector vector_cosine_ops)
                            WITH (m=16, ef_construction=64)
  -- Similarity search: SELECT ... ORDER BY vector <=> query_vector LIMIT 10

  -- Development / small dataset (< 100K vectors):
  -- idx_embeddings_ivfflat  USING IVFFlat ON embeddings(vector vector_l2_ops)
  --                         WITH (lists=100)

HNSW parametrlari tanlash:
  m = 16            (connections per node, RAM vs recall tradeoff)
  ef_construction = 64  (build quality, sekin build, yaxshi recall)
  ef_search = 40    (query vaqtida, tezlik vs recall)
```

### 3.11 api_keys

```
PRIMARY KEY:
  idx_api_keys_pkey         ON api_keys(id)

UNIQUE INDEXES:
  uniq_api_keys_hash        ON api_keys(key_hash)           -- auth lookup

SECONDARY INDEXES:
  idx_api_keys_user_id      ON api_keys(user_id)
  idx_api_keys_org_id       ON api_keys(org_id)

PARTIAL INDEXES:
  idx_api_keys_active       ON api_keys(key_hash)
                            WHERE is_active = TRUE
                              AND deleted_at IS NULL
                              AND (expires_at IS NULL OR expires_at > NOW())
  -- Query: API auth — en muhim partial index
```

### 3.12 audit_logs

```
PARTITIONED BY RANGE (created_at) — choraklik

PRIMARY KEY:
  idx_audit_pkey            ON audit_logs(id, created_at)

SECONDARY INDEXES:
  idx_audit_user_id         ON audit_logs(user_id)
  idx_audit_action          ON audit_logs(action)
  idx_audit_resource        ON audit_logs(resource_type, resource_id)
  idx_audit_created_at      ON audit_logs(created_at DESC)

COMPOSITE INDEXES:
  idx_audit_org_time        ON audit_logs(org_id, created_at DESC)
  idx_audit_user_time       ON audit_logs(user_id, created_at DESC)
  idx_audit_resource_time   ON audit_logs(resource_type, resource_id, created_at DESC)

BRIN INDEX:
  idx_audit_created_brin    USING BRIN ON audit_logs(created_at)
  -- Partition ichida ordering, range queries
```

### 3.13 system_logs

```
PARTITIONED BY RANGE (created_at) — haftalik

PRIMARY KEY:
  idx_syslog_pkey           ON system_logs(id, created_at)

SECONDARY INDEXES:
  idx_syslog_level          ON system_logs(level)
  idx_syslog_service        ON system_logs(service)
  idx_syslog_trace_id       ON system_logs(trace_id)
                            WHERE trace_id IS NOT NULL
  idx_syslog_created_at     ON system_logs(created_at DESC)

PARTIAL INDEXES:
  idx_syslog_errors         ON system_logs(service, created_at DESC)
                            WHERE level IN ('ERROR','CRITICAL')

BRIN INDEX:
  idx_syslog_created_brin   USING BRIN ON system_logs(created_at)
```

### 3.14 configurations

```
PRIMARY KEY:
  idx_config_pkey           ON configurations(id)

UNIQUE INDEXES:
  uniq_config_scope_key     ON configurations(scope, scope_id, key)
  -- scope_id NULL uchun: UNIQUE(scope, key) WHERE scope_id IS NULL

SECONDARY INDEXES:
  idx_config_scope          ON configurations(scope, scope_id)
  -- Query: org/project/user sozlamalarini olish
```

---

## 4. JSONB INDEXES

```
Qaysi JSONB fieldlar qidiriladi:

agents.capabilities  → GIN INDEX
  idx_agents_capabilities   USING GIN ON agents(capabilities)
  -- Query: capabilities @> '["code_review"]'

models.capabilities  → GIN INDEX
  idx_models_capabilities   USING GIN ON models(capabilities)
  -- Query: capabilities @> '{"vision": true}'

configurations.value → GIN INDEX (faqat non-secret)
  idx_config_value_gin      USING GIN ON configurations(value)
                            WHERE is_secret = FALSE
```

---

## 5. INDEX OVERHEAD VA TRADEOFF

```
Har bir index:
  ✅ SELECT tezlashtiradi
  ❌ INSERT sekinlashtiradi (~2-5%)
  ❌ UPDATE sekinlashtiradi (indexed column o'zgarganda)
  ❌ DELETE sekinlashtiradi
  ❌ Disk joy egallaydi (~10-30% table size)
  ❌ VACUUM/AUTOVACUUM ishi oshadi

Qoida:
  messages jadvalida 3 ta index → yuqori write performance uchun minimal index
  api_keys jadvalida 4 ta index → read-heavy (auth har requestda)
  audit_logs → write-heavy, minimal index, BRIN afzal
```

---

## 6. INDEX MONITORING

```sql
-- Ishlatilmayotgan indexlarni topish (dizayn darajasida)
-- pg_stat_user_indexes.idx_scan = 0 bo'lganlari

-- Katta indexlarni tekshirish
-- pg_indexes.indexdef va pg_relation_size()

-- Bloating tekshirish
-- pgstattuple extension

Siyosat:
  30 kun ichida 0 scan → INDEX o'chirish nomzodi
  Fasldan keyin reindeks:
    REINDEX INDEX CONCURRENTLY idx_name;
    -- CONCURRENTLY: production'da lock olmaydi
```

---

## 7. EXPLAIN ANALYZE O'QISH

```
Yaxshi plan belgilari:
  Index Scan     → B-tree index ishlatilmoqda ✅
  Index Only Scan → covering index ✅✅ (table'ga kirmasdan)
  Bitmap Scan    → partial index yoki low selectivity ✅
  Seq Scan       → index yo'q yoki juda kichik jadval ⚠️

Yomon belgilar:
  Seq Scan + katta rows → index kerak ❌
  Nested Loop + katta rows → index kerak yoki query qayta yozish ❌
  Hash Join + katta memory → work_mem oshirish kerak ⚠️

cost = 0.00..145.23:
  Birinchi raqam: birinchi row cost
  Ikkinchi raqam: jami cost
  rows=1000: taxminiy natija soni
  width=42: har row o'rtacha bayt
```

---

*Hujjat AIDA Development Bible — Book 1, Chapter 8 asosida tayyorlangan.*
