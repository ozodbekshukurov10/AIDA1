# AIDA Enterprise Database Architecture
## Relationship Guide

**Versiya:** 1.0.0
**Sana:** 2026-07-03
**Muallif:** AIDA Database Team

---

## 1. MUNOSABATLAR UMUMIY KO'RINISHI

```
Jami munosabatlar:
  One-to-One  (1:1):  2 ta
  One-to-Many (1:N): 22 ta
  Many-to-Many(M:N):  6 ta
  Junction tables:    6 ta
```

---

## 2. ONE-TO-ONE (1:1) MUNOSABATLAR

### 2.1 Document ↔ File (Primary)

```
documents.id ←──────────── files.document_id (UNIQUE)

Texnik ta'rif:
  Har bir Document uchun aynan bitta primary File mavjud.
  File.document_id UNIQUE constraint bilan ta'minlanadi.

Cascade:
  Document DELETE → File CASCADE DELETE
  File DELETE → Document da NULL (storage_path yo'qoladi, hujjat mavjud bo'ladi lekin yuklab bo'lmaydi)

Django:
  class File(Model):
      document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='file')

Sabab: Hujjat metama'lumoti (filename, type, size) va storage ma'lumoti (path, checksum, encryption)
alohida entity bo'lishi arxitektura tozaligini ta'minlaydi. Storage backend o'zgarganda Document o'zgarmaydi.
```

### 2.2 User ↔ UserProfile (kengaytirilgan)

```
users.id ←──────────── user_profiles.user_id (UNIQUE)

Texnik ta'rif:
  Asosiy User jadvalida faqat autentifikatsiya ma'lumotlari.
  Kengaytirilgan profil ma'lumotlari (bio, social links, preferences) alohida jadvalda.

Cascade:
  User DELETE → UserProfile CASCADE DELETE

Django:
  class UserProfile(Model):
      user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

Sabab: User jadvali eng ko'p join qilinadigan jadval. Uning kichik bo'lishi performance uchun muhim.
Profil ma'lumotlari faqat profil sahifasida kerak — lazy loading imkoni.
```

---

## 3. ONE-TO-MANY (1:N) MUNOSABATLAR

### 3.1 Organization → Users (owner)

| Xususiyat | Qiymat |
|-----------|--------|
| Parent | organizations |
| Child | users (owner_id field orqali emas — organization_members) |
| FK field | organizations.owner_id → users.id |
| ON DELETE | RESTRICT — egasi bo'lmagan org yaratib bo'lmaydi |
| ON UPDATE | CASCADE |
| NULL | NOT NULL |

### 3.2 Organization → Projects

| Xususiyat | Qiymat |
|-----------|--------|
| FK field | projects.org_id → organizations.id |
| ON DELETE | CASCADE — org o'chirilsa loyihalar ham o'chadi |
| ON UPDATE | CASCADE |
| NULL | NOT NULL |
| Sabab | Loyiha tashkilotsiz mavjud bo'la olmaydi |

### 3.3 Organization → APIKeys

| Xususiyat | Qiymat |
|-----------|--------|
| FK field | api_keys.org_id → organizations.id |
| ON DELETE | SET NULL — org o'chirilsa kalit user'ga bog'liq qoladi |
| ON UPDATE | CASCADE |
| NULL | NULLABLE |

### 3.4 Project → Repositories

| Xususiyat | Qiymat |
|-----------|--------|
| FK field | repositories.project_id → projects.id |
| ON DELETE | CASCADE |
| ON UPDATE | CASCADE |
| NULL | NOT NULL |

### 3.5 Project → Chats

| Xususiyat | Qiymat |
|-----------|--------|
| FK field | chats.project_id → projects.id |
| ON DELETE | SET NULL — loyiha o'chirilsa chat saqlanib qoladi |
| ON UPDATE | CASCADE |
| NULL | NULLABLE |
| Sabab | Chat foydalanuvchiga tegishli, loyiha konteksti yo'qolishi mumkin |

### 3.6 Project → Documents

| Xususiyat | Qiymat |
|-----------|--------|
| FK field | documents.project_id → projects.id |
| ON DELETE | CASCADE |
| ON UPDATE | CASCADE |
| NULL | NOT NULL |

### 3.7 Project → Knowledge

| Xususiyat | Qiymat |
|-----------|--------|
| FK field | knowledge.project_id → projects.id |
| ON DELETE | CASCADE |
| ON UPDATE | CASCADE |
| NULL | NOT NULL |

### 3.8 Chat → Messages

| Xususiyat | Qiymat |
|-----------|--------|
| FK field | messages.chat_id → chats.id |
| ON DELETE | CASCADE |
| ON UPDATE | CASCADE |
| NULL | NOT NULL |
| Sabab | Xabar chatsiz mavjud bo'la olmaydi. Chat o'chirilsa xabarlar ma'nosiz. |

### 3.9 Provider → Models

| Xususiyat | Qiymat |
|-----------|--------|
| FK field | models.provider_id → providers.id |
| ON DELETE | RESTRICT — provider o'chirilmaydi, faqat inactive |
| ON UPDATE | CASCADE |
| NULL | NOT NULL |
| Sabab | Tarixiy chat ma'lumotlari uchun model va provider ma'lumotlari saqlanishi kerak |

### 3.10 Plugin → Tools

| Xususiyat | Qiymat |
|-----------|--------|
| FK field | tools.plugin_id → plugins.id |
| ON DELETE | CASCADE — plagin o'chirilsa toollar ham o'chadi |
| ON UPDATE | CASCADE |
| NULL | NOT NULL |

### 3.11 Agent → Tasks

| Xususiyat | Qiymat |
|-----------|--------|
| FK field | tasks.agent_id → agents.id |
| ON DELETE | SET NULL — agent o'chirilsa task tarixi saqlanadi |
| ON UPDATE | CASCADE |
| NULL | NULLABLE |

### 3.12 Workflow → Tasks

| Xususiyat | Qiymat |
|-----------|--------|
| FK field | tasks.workflow_id → workflows.id |
| ON DELETE | SET NULL |
| ON UPDATE | CASCADE |
| NULL | NULLABLE |

### 3.13 Knowledge → Embeddings

| Xususiyat | Qiymat |
|-----------|--------|
| FK field | embeddings.knowledge_id → knowledge.id |
| ON DELETE | CASCADE — knowledge o'chirilsa vektorlar ham o'chadi |
| ON UPDATE | CASCADE |
| NULL | NOT NULL |

### 3.14 User → Sessions

| Xususiyat | Qiymat |
|-----------|--------|
| FK field | sessions.user_id → users.id |
| ON DELETE | CASCADE |
| ON UPDATE | CASCADE |
| NULL | NOT NULL |

### 3.15 User → AuditLogs

| Xususiyat | Qiymat |
|-----------|--------|
| FK field | audit_logs.user_id → users.id |
| ON DELETE | SET NULL — user o'chirilsa log qoladi (audit immutability) |
| ON UPDATE | CASCADE |
| NULL | NULLABLE |

### 3.16 User → APIKeys

| Xususiyat | Qiymat |
|-----------|--------|
| FK field | api_keys.user_id → users.id |
| ON DELETE | CASCADE |
| ON UPDATE | CASCADE |
| NULL | NOT NULL |

### 3.17 Document → Files

| Xususiyat | Qiymat |
|-----------|--------|
| FK field | files.document_id → documents.id |
| ON DELETE | CASCADE |
| ON UPDATE | CASCADE |
| NULL | NOT NULL |

---

## 4. MANY-TO-MANY (M:N) MUNOSABATLAR

### 4.1 User ↔ Organization

**Junction table:** `organization_members`

```
┌──────────────────────────────────────────────────┐
│              organization_members                │
├──────────────────────────────────────────────────┤
│ PK id          UUID                              │
│ FK user_id     → users.id (CASCADE)              │
│ FK org_id      → organizations.id (CASCADE)      │
│    role        VARCHAR(50) NOT NULL              │
│                (owner/admin/member/viewer)        │
│    joined_at   TIMESTAMPTZ NOT NULL              │
│    invited_by  UUID → users.id (SET NULL)        │
│ UNIQUE (user_id, org_id)                         │
└──────────────────────────────────────────────────┘

Indexes:
  UNIQUE: (user_id, org_id)
  INDEX: org_id, user_id, role
```

### 4.2 User ↔ Project

**Junction table:** `project_members`

```
┌──────────────────────────────────────────────────┐
│               project_members                    │
├──────────────────────────────────────────────────┤
│ PK id           UUID                             │
│ FK user_id      → users.id (CASCADE)             │
│ FK project_id   → projects.id (CASCADE)          │
│    permissions  JSONB DEFAULT '[]'               │
│                 (read/write/admin/deploy)         │
│    role         VARCHAR(50)                      │
│    joined_at    TIMESTAMPTZ NOT NULL             │
│ UNIQUE (user_id, project_id)                     │
└──────────────────────────────────────────────────┘
```

### 4.3 Agent ↔ Tool

**Junction table:** `agent_tools`

```
┌──────────────────────────────────────────────────┐
│                  agent_tools                     │
├──────────────────────────────────────────────────┤
│ FK agent_id  → agents.id (CASCADE)               │
│ FK tool_id   → tools.id (CASCADE)                │
│    enabled   BOOLEAN DEFAULT TRUE                │
│    config    JSONB DEFAULT '{}'                  │
│ PK (agent_id, tool_id)                           │
└──────────────────────────────────────────────────┘
```

### 4.4 Agent ↔ Plugin

**Junction table:** `agent_plugins`

```
┌──────────────────────────────────────────────────┐
│                 agent_plugins                    │
├──────────────────────────────────────────────────┤
│ FK agent_id   → agents.id (CASCADE)              │
│ FK plugin_id  → plugins.id (CASCADE)             │
│    enabled    BOOLEAN DEFAULT TRUE               │
│ PK (agent_id, plugin_id)                         │
└──────────────────────────────────────────────────┘
```

### 4.5 Workflow ↔ Agent

**Junction table:** `workflow_agents`

```
┌──────────────────────────────────────────────────┐
│               workflow_agents                    │
├──────────────────────────────────────────────────┤
│ FK workflow_id → workflows.id (CASCADE)          │
│ FK agent_id    → agents.id (CASCADE)             │
│    step_index  INTEGER                           │
│    role        VARCHAR(50)                       │
│ PK (workflow_id, agent_id)                       │
└──────────────────────────────────────────────────┘
```

### 4.6 Message ↔ Knowledge (cited sources)

**Junction table:** `message_knowledge`

```
┌──────────────────────────────────────────────────┐
│              message_knowledge                   │
├──────────────────────────────────────────────────┤
│ FK message_id    → messages.id (CASCADE)         │
│ FK knowledge_id  → knowledge.id (CASCADE)        │
│    relevance_score FLOAT NOT NULL                │
│    chunk_ids       JSONB DEFAULT '[]'            │
│ PK (message_id, knowledge_id)                    │
└──────────────────────────────────────────────────┘

Maqsad: AI javob qaysi knowledge chunk'laridan foydalanganini kuzatish.
RAG (Retrieval Augmented Generation) attribution uchun zarur.
```

---

## 5. CASCADE RULES MATRIX

```
JADVAL              | FK field         | ON DELETE   | ON UPDATE | NULL?
--------------------|------------------|-------------|-----------|------
users               | (no FK)          | —           | —         | —
organizations       | owner_id→users   | RESTRICT    | CASCADE   | NO
organization_members| user_id→users    | CASCADE     | CASCADE   | NO
organization_members| org_id→orgs      | CASCADE     | CASCADE   | NO
project_members     | user_id→users    | CASCADE     | CASCADE   | NO
project_members     | project_id→proj  | CASCADE     | CASCADE   | NO
projects            | org_id→orgs      | CASCADE     | CASCADE   | NO
projects            | created_by→users | SET NULL    | CASCADE   | YES
repositories        | project_id→proj  | CASCADE     | CASCADE   | NO
chats               | user_id→users    | CASCADE     | CASCADE   | NO
chats               | project_id→proj  | SET NULL    | CASCADE   | YES
chats               | model_id→models  | SET NULL    | CASCADE   | YES
messages            | chat_id→chats    | CASCADE     | CASCADE   | NO
message_knowledge   | message_id→msgs  | CASCADE     | CASCADE   | NO
message_knowledge   | knowledge_id→kn  | CASCADE     | CASCADE   | NO
sessions            | user_id→users    | CASCADE     | CASCADE   | NO
agents              | org_id→orgs      | SET NULL    | CASCADE   | YES
agents              | created_by→users | SET NULL    | CASCADE   | YES
agents              | model_id→models  | SET NULL    | CASCADE   | YES
tasks               | agent_id→agents  | SET NULL    | CASCADE   | YES
tasks               | workflow_id→wf   | SET NULL    | CASCADE   | YES
tasks               | parent_task_id   | SET NULL    | CASCADE   | YES
workflows           | org_id→orgs      | SET NULL    | CASCADE   | YES
workflows           | created_by→users | SET NULL    | CASCADE   | YES
workflow_agents     | workflow_id→wf   | CASCADE     | CASCADE   | NO
workflow_agents     | agent_id→agents  | CASCADE     | CASCADE   | NO
models              | provider_id→prov | RESTRICT    | CASCADE   | NO
plugins             | installed_by→usr | SET NULL    | CASCADE   | YES
tools               | plugin_id→plugs  | CASCADE     | CASCADE   | NO
agent_tools         | agent_id→agents  | CASCADE     | CASCADE   | NO
agent_tools         | tool_id→tools    | CASCADE     | CASCADE   | NO
agent_plugins       | agent_id→agents  | CASCADE     | CASCADE   | NO
agent_plugins       | plugin_id→plugs  | CASCADE     | CASCADE   | NO
knowledge           | project_id→proj  | CASCADE     | CASCADE   | NO
knowledge           | created_by→users | SET NULL    | CASCADE   | YES
embeddings          | knowledge_id→kn  | CASCADE     | CASCADE   | NO
documents           | project_id→proj  | CASCADE     | CASCADE   | NO
documents           | uploaded_by→usr  | SET NULL    | CASCADE   | YES
documents           | knowledge_id→kn  | SET NULL    | CASCADE   | YES
files               | document_id→docs | CASCADE     | CASCADE   | NO
audit_logs          | user_id→users    | SET NULL    | CASCADE   | YES
api_keys            | user_id→users    | CASCADE     | CASCADE   | NO
api_keys            | org_id→orgs      | SET NULL    | CASCADE   | YES
configurations      | created_by→users | SET NULL    | CASCADE   | YES
configurations      | updated_by→users | SET NULL    | CASCADE   | YES
```

---

## 6. SOFT DELETE STRATEGIYASI

### Soft Delete qo'llaniladigan entitylar

```
✅ Soft Delete (deleted_at field):
  users, organizations, projects, chats, knowledge,
  documents, agents, workflows, api_keys

❌ Hard Delete (to'g'ridan-to'g'ri o'chiriladi):
  messages (chat cascade), sessions (expired),
  embeddings (knowledge cascade), files (document cascade),
  system_logs (partition drop)

⚠️ Immutable (o'chirilmaydi, faqat status o'zgaradi):
  audit_logs, providers, models
```

### Cascading Soft Delete zanjiri

```
Organization soft deleted
  └── Projects soft deleted
        └── Chats soft deleted  (messages HARD deleted after 30 days)
        └── Knowledge soft deleted  (embeddings HARD deleted)
        └── Documents soft deleted  (files HARD deleted after 30 days)
  └── APIKeys soft deleted
```

### Django Soft Delete Implementation (dizayn)

```python
# SoftDeleteManager — barcha querylar deleted_at IS NULL filter qiladi
# Faqat .with_deleted() orqali o'chirilganlar ko'rinadi
# undelete() metodi soft delete'ni bekor qiladi
```

---

## 7. CIRCULAR DEPENDENCY OLDINI OLISH

```
Muammo: Organization → User (owner_id) va User → Organization (M:N)

Yechim:
  1. Organization.owner_id → users.id (DEFERRABLE INITIALLY DEFERRED)
  2. Avval User yaratiladi
  3. So'ng Organization yaratiladi (owner_id bilan)
  4. organization_members ga qo'shiladi

Django da:
  Organization.owner = ForeignKey(User, related_name='owned_orgs')
  # Circular import oldini olish uchun string reference ishlatiladi
  # 'users.User' emas, settings.AUTH_USER_MODEL
```

---

## 8. ROW-LEVEL SECURITY (Multi-tenant izolyatsiya)

```sql
-- Dizayn konsepsiyasi (SQL migration'da emas, arxitektura hujjatida)

-- projects jadvalida RLS:
-- Foydalanuvchi faqat o'zi a'zo bo'lgan org loyihalarini ko'radi

Policy: user_project_isolation
  USING: org_id IN (
    SELECT org_id FROM organization_members WHERE user_id = current_user_id()
  )

-- messages jadvalida RLS:
-- Foydalanuvchi faqat o'z chatlari xabarlarini ko'radi

Policy: user_message_isolation
  USING: chat_id IN (
    SELECT id FROM chats WHERE user_id = current_user_id()
  )
```

---

*Hujjat AIDA Development Bible — Book 1, Chapter 8 asosida tayyorlangan.*
