# AIDA Enterprise Database Architecture
## Entity Definitions

**Versiya:** 1.0.0
**Sana:** 2026-07-03
**Muallif:** AIDA Database Team

---

## 1. User

**Maqsad:** Tizimga kirgan barcha foydalanuvchilarni saqlaydi. Autentifikatsiya, avtorizatsiya va profil ma'lumotlarini boshqaradi.

**Jadval nomi:** `users`

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Asosiy kalit |
| email | VARCHAR(255) | UNIQUE, NOT NULL, encrypted | Foydalanuvchi email (AES-256) |
| username | VARCHAR(150) | UNIQUE, NOT NULL | Login nomi |
| hashed_password | VARCHAR(255) | NOT NULL | Argon2 hash |
| role | VARCHAR(50) | NOT NULL, DEFAULT 'user' | system_admin / org_admin / user |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Aktiv holat |
| is_verified | BOOLEAN | NOT NULL, DEFAULT FALSE | Email tasdiqlangan |
| first_name | VARCHAR(100) | NULL | Ism |
| last_name | VARCHAR(100) | NULL | Familiya |
| avatar_url | VARCHAR(500) | NULL | Profil rasmi URL |
| timezone | VARCHAR(50) | DEFAULT 'UTC' | Vaqt mintaqasi |
| language | VARCHAR(10) | DEFAULT 'en' | Interfeys tili |
| last_login_at | TIMESTAMPTZ | NULL | Oxirgi kirish vaqti |
| login_count | INTEGER | DEFAULT 0 | Kirish soni |
| failed_login_count | INTEGER | DEFAULT 0 | Muvaffaqiyatsiz urinishlar |
| locked_until | TIMESTAMPTZ | NULL | Blok tugash vaqti |
| deleted_at | TIMESTAMPTZ | NULL | Soft delete |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yangilangan vaqt |

**Relationships:**
- 1:N → sessions, api_keys, audit_logs, chats
- M:N → organizations (organization_members orqali)
- M:N → projects (project_members orqali)

**Indexes:**
- PK: `id`
- UNIQUE: `email`, `username`
- INDEX: `created_at`, `deleted_at`, `role`

**Constraints:**
- `CHECK (role IN ('system_admin','org_admin','user'))`
- `CHECK (failed_login_count >= 0)`

**Retention Policy:** Soft delete (deleted_at). 90 kun o'tgach hard delete. GDPR "right to erasure" so'rovida email va PII anonymize qilinadi.

---

## 2. Organization

**Maqsad:** Kompaniya yoki jamoa sifatida foydalanuvchilarni birlashtiradi. Multi-tenant izolyatsiyaning asosiy birligi.

**Jadval nomi:** `organizations`

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | UUID | PK | Asosiy kalit |
| name | VARCHAR(255) | NOT NULL | Tashkilot nomi |
| slug | VARCHAR(100) | UNIQUE, NOT NULL | URL-friendly nom |
| plan | VARCHAR(50) | NOT NULL, DEFAULT 'free' | free/pro/enterprise |
| owner_id | UUID | FK → users.id, NOT NULL | Egasi |
| logo_url | VARCHAR(500) | NULL | Logo URL |
| website | VARCHAR(500) | NULL | Veb-sayt |
| settings | JSONB | DEFAULT '{}' | Org sozlamalari |
| max_members | INTEGER | DEFAULT 5 | A'zolar limiti |
| max_projects | INTEGER | DEFAULT 10 | Loyihalar limiti |
| storage_quota_bytes | BIGINT | DEFAULT 10737418240 | 10 GB default |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Aktiv holat |
| deleted_at | TIMESTAMPTZ | NULL | Soft delete |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yangilangan vaqt |

**Relationships:**
- FK: owner_id → users.id (RESTRICT delete)
- 1:N → projects, api_keys
- M:N → users (organization_members orqali)

**Indexes:**
- PK: `id`
- UNIQUE: `slug`
- INDEX: `owner_id`, `plan`, `is_active`

**Constraints:**
- `CHECK (plan IN ('free','pro','enterprise'))`
- `CHECK (max_members > 0)`

**Retention Policy:** Soft delete. Owner hisobini o'chirganda org ham soft delete.

---

## 3. Project

**Maqsad:** Tashkilot ichidagi ish loyihalari. Repositorylar, chatlar, hujjatlar va bilim bazalarini birlashtiradi.

**Jadval nomi:** `projects`

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | UUID | PK | Asosiy kalit |
| org_id | UUID | FK → organizations.id, NOT NULL | Tashkilot |
| created_by | UUID | FK → users.id, NOT NULL | Yaratuvchi |
| name | VARCHAR(255) | NOT NULL | Loyiha nomi |
| slug | VARCHAR(100) | NOT NULL | URL-friendly nom |
| description | TEXT | NULL | Tavsif |
| settings | JSONB | DEFAULT '{}' | Loyiha sozlamalari |
| default_model_id | UUID | FK → models.id, NULL | Default AI modeli |
| is_archived | BOOLEAN | DEFAULT FALSE | Arxivlangan |
| is_public | BOOLEAN | DEFAULT FALSE | Ommaviy kirish |
| storage_used_bytes | BIGINT | DEFAULT 0 | Ishlatilgan joy |
| deleted_at | TIMESTAMPTZ | NULL | Soft delete |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yangilangan vaqt |

**Relationships:**
- FK: org_id → organizations (CASCADE delete)
- FK: created_by → users (SET NULL)
- 1:N → repositories, chats, documents, knowledge
- M:N → users (project_members orqali)

**Indexes:**
- PK: `id`
- UNIQUE: `(org_id, slug)`
- INDEX: `org_id`, `created_by`, `is_archived`

**Constraints:**
- `CHECK (storage_used_bytes >= 0)`

**Retention Policy:** Soft delete. Org o'chirilganda cascade soft delete.

---

## 4. Repository

**Maqsad:** Loyihaga ulangan kod repositorylari (GitHub, GitLab, lokal). Kod tahlili va kontekst uchun.

**Jadval nomi:** `repositories`

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | UUID | PK | Asosiy kalit |
| project_id | UUID | FK → projects.id, NOT NULL | Loyiha |
| name | VARCHAR(255) | NOT NULL | Repo nomi |
| source | VARCHAR(50) | NOT NULL | github/gitlab/bitbucket/local |
| url | VARCHAR(1000) | NULL | Clone URL |
| branch | VARCHAR(255) | DEFAULT 'main' | Asosiy branch |
| sync_status | VARCHAR(50) | DEFAULT 'pending' | pending/syncing/synced/error |
| last_synced_at | TIMESTAMPTZ | NULL | Oxirgi sinxronizatsiya |
| metadata | JSONB | DEFAULT '{}' | Provider-specific ma'lumot |
| file_count | INTEGER | DEFAULT 0 | Fayllar soni |
| size_bytes | BIGINT | DEFAULT 0 | Repo hajmi |
| languages | JSONB | DEFAULT '[]' | Dasturlash tillari |
| is_active | BOOLEAN | DEFAULT TRUE | Aktiv holat |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yangilangan vaqt |

**Relationships:**
- FK: project_id → projects (CASCADE delete)

**Indexes:**
- PK: `id`
- INDEX: `project_id`, `source`, `sync_status`

**Constraints:**
- `CHECK (source IN ('github','gitlab','bitbucket','local'))`
- `CHECK (sync_status IN ('pending','syncing','synced','error'))`

**Retention Policy:** Loyiha o'chirilganda cascade delete.

---

## 5. Chat

**Maqsad:** Foydalanuvchi va AI o'rtasidagi suhbat sessiyasi. Har bir chat bir mavzu bo'yicha xabarlar to'plamini saqlaydi.

**Jadval nomi:** `chats`

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | UUID | PK | Asosiy kalit |
| user_id | UUID | FK → users.id, NOT NULL | Egasi |
| project_id | UUID | FK → projects.id, NULL | Bog'liq loyiha |
| model_id | UUID | FK → models.id, NULL | Ishlatilgan model |
| title | VARCHAR(500) | NOT NULL | Suhbat sarlavhasi |
| model_config | JSONB | DEFAULT '{}' | temperature, max_tokens, ... |
| system_prompt | TEXT | NULL | System prompt override |
| is_archived | BOOLEAN | DEFAULT FALSE | Arxivlangan |
| is_pinned | BOOLEAN | DEFAULT FALSE | Muhim sifatida belgilangan |
| message_count | INTEGER | DEFAULT 0 | Xabarlar soni (denormalized) |
| total_tokens | INTEGER | DEFAULT 0 | Jami tokenlar (denormalized) |
| last_message_at | TIMESTAMPTZ | NULL | Oxirgi xabar vaqti |
| deleted_at | TIMESTAMPTZ | NULL | Soft delete |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yangilangan vaqt |

**Relationships:**
- FK: user_id → users (CASCADE delete)
- FK: project_id → projects (SET NULL)
- 1:N → messages

**Indexes:**
- PK: `id`
- INDEX: `user_id`, `project_id`, `last_message_at DESC`, `is_archived`
- COMPOSITE: `(user_id, is_archived, last_message_at DESC)`

**Retention Policy:** Soft delete. User o'chirilganda 30 kun kutib hard delete.

---

## 6. Message

**Maqsad:** Chat ichidagi har bir xabar. Foydalanuvchi, assistant yoki system rolida bo'lishi mumkin. Eng ko'p insert bo'ladigan jadval.

**Jadval nomi:** `messages` (PARTITIONED BY RANGE created_at — oylik)

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | BIGINT | PK, GENERATED ALWAYS AS IDENTITY | Asosiy kalit |
| chat_id | UUID | FK → chats.id, NOT NULL | Suhbat |
| role | VARCHAR(20) | NOT NULL | user/assistant/system/tool |
| content | TEXT | NOT NULL | Xabar matni |
| tokens_input | INTEGER | DEFAULT 0 | Kirish tokenlar |
| tokens_output | INTEGER | DEFAULT 0 | Chiqish tokenlar |
| model_name | VARCHAR(200) | NULL | Ishlatilgan model nomi |
| finish_reason | VARCHAR(50) | NULL | stop/length/tool_calls/error |
| metadata | JSONB | DEFAULT '{}' | Tool calls, citations, ... |
| parent_id | BIGINT | FK → messages.id, NULL | Thread/reply uchun |
| is_deleted | BOOLEAN | DEFAULT FALSE | Soft delete |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |

**Relationships:**
- FK: chat_id → chats (CASCADE delete)
- M:N → knowledge (message_knowledge orqali)

**Indexes:**
- PK: `(id, created_at)` — partition key bilan
- INDEX: `chat_id`, `created_at DESC`, `role`
- COMPOSITE: `(chat_id, created_at DESC)`
- PARTIAL: `(chat_id) WHERE is_deleted = FALSE`

**Constraints:**
- `CHECK (role IN ('user','assistant','system','tool'))`

**Retention Policy:** Chat o'chirilganda cascade. Partition pruning orqali eski ma'lumotlar arxivlanadi (12 oydan eski → cold storage).

---

## 7. Session

**Maqsad:** Foydalanuvchi autentifikatsiya sessiyalarini boshqaradi. Token hash'lari saqlanadi, hech qachon ochiq token emas.

**Jadval nomi:** `sessions`

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | UUID | PK | Asosiy kalit |
| user_id | UUID | FK → users.id, NOT NULL | Foydalanuvchi |
| token_hash | VARCHAR(64) | UNIQUE, NOT NULL | SHA-256 hash |
| refresh_token_hash | VARCHAR(64) | UNIQUE, NULL | Refresh token hash |
| ip_masked | VARCHAR(50) | NULL | Subnet (192.168.x.x) |
| user_agent | VARCHAR(500) | NULL | Browser/client info |
| device_info | JSONB | DEFAULT '{}' | Device fingerprint |
| expires_at | TIMESTAMPTZ | NOT NULL | Token amal qilish muddati |
| refresh_expires_at | TIMESTAMPTZ | NULL | Refresh token muddati |
| is_active | BOOLEAN | DEFAULT TRUE | Aktiv sessiya |
| revoked_at | TIMESTAMPTZ | NULL | Bekor qilingan vaqt |
| last_activity_at | TIMESTAMPTZ | NULL | Oxirgi faollik |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |

**Relationships:**
- FK: user_id → users (CASCADE delete)

**Indexes:**
- PK: `id`
- UNIQUE: `token_hash`, `refresh_token_hash`
- INDEX: `user_id`, `expires_at`, `is_active`
- PARTIAL: `(token_hash) WHERE is_active = TRUE`

**Retention Policy:** Muddati o'tgan sessionlar 7 kundan keyin avtomatik o'chiriladi. Revoked sessionlar 30 kun audit uchun saqlanadi.

---

## 8. Agent

**Maqsad:** AIDA tizimidagi AI agentlarni ifodalaydi. Har bir agent ma'lum vazifalarni bajara oladi va turli tool va pluginlarga ega.

**Jadval nomi:** `agents`

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | UUID | PK | Asosiy kalit |
| org_id | UUID | FK → organizations.id, NULL | Tashkilotga tegishli |
| created_by | UUID | FK → users.id, NULL | Yaratuvchi |
| name | VARCHAR(255) | NOT NULL | Agent nomi |
| slug | VARCHAR(100) | UNIQUE, NOT NULL | Noyob identifikator |
| type | VARCHAR(50) | NOT NULL | general/code/research/data/custom |
| description | TEXT | NULL | Agent tavsifi |
| system_prompt | TEXT | NULL | Agent system prompt |
| config | JSONB | DEFAULT '{}' | Agent konfiguratsiyasi |
| capabilities | JSONB | DEFAULT '[]' | Imkoniyatlar ro'yxati |
| model_id | UUID | FK → models.id, NULL | Default model |
| status | VARCHAR(50) | DEFAULT 'active' | active/inactive/maintenance |
| max_iterations | INTEGER | DEFAULT 10 | Maksimal iteratsiya |
| timeout_seconds | INTEGER | DEFAULT 300 | Timeout |
| is_public | BOOLEAN | DEFAULT FALSE | Barchaga ochiq |
| version | VARCHAR(20) | DEFAULT '1.0.0' | Versiya |
| deleted_at | TIMESTAMPTZ | NULL | Soft delete |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yangilangan vaqt |

**Relationships:**
- FK: org_id → organizations (SET NULL)
- M:N → tools (agent_tools orqali)
- M:N → plugins (agent_plugins orqali)
- 1:N → tasks

**Indexes:**
- PK: `id`
- UNIQUE: `slug`
- INDEX: `org_id`, `type`, `status`, `is_public`

**Retention Policy:** Soft delete. Tasks va logs saqlanib qoladi.

---

## 9. Task

**Maqsad:** Agent tomonidan bajariladigan yoki bajarilgan vazifalar. Input, output va holat ma'lumotlarini saqlaydi.

**Jadval nomi:** `tasks`

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | UUID | PK | Asosiy kalit |
| agent_id | UUID | FK → agents.id, NULL | Bajaruvchi agent |
| workflow_id | UUID | FK → workflows.id, NULL | Tegishli workflow |
| parent_task_id | UUID | FK → tasks.id, NULL | Ota-vazifa |
| type | VARCHAR(100) | NOT NULL | Vazifa turi |
| status | VARCHAR(50) | NOT NULL, DEFAULT 'pending' | pending/running/completed/failed/cancelled |
| priority | INTEGER | DEFAULT 5 | 1 (yuqori) — 10 (past) |
| input | JSONB | DEFAULT '{}' | Kirish ma'lumotlari |
| output | JSONB | NULL | Chiqish natijasi |
| error_message | TEXT | NULL | Xato xabari |
| retry_count | INTEGER | DEFAULT 0 | Qayta urinish soni |
| max_retries | INTEGER | DEFAULT 3 | Maksimal qayta urinish |
| timeout_seconds | INTEGER | DEFAULT 300 | Timeout |
| started_at | TIMESTAMPTZ | NULL | Boshlangan vaqt |
| completed_at | TIMESTAMPTZ | NULL | Tugagan vaqt |
| duration_ms | INTEGER | NULL | Bajarish vaqti (ms) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yangilangan vaqt |

**Relationships:**
- FK: agent_id → agents (SET NULL)
- FK: workflow_id → workflows (SET NULL)

**Indexes:**
- PK: `id`
- INDEX: `agent_id`, `workflow_id`, `status`, `priority`, `created_at DESC`
- COMPOSITE: `(status, priority, created_at)` — queue query uchun

**Constraints:**
- `CHECK (status IN ('pending','running','completed','failed','cancelled'))`
- `CHECK (priority BETWEEN 1 AND 10)`
- `CHECK (retry_count >= 0)`

**Retention Policy:** Completed/failed tasks 90 kun saqlanadi, so'ng arxivlanadi.

---

## 10. Workflow

**Maqsad:** Bir nechta agent va vazifalarni o'z ichiga olgan murakkab ish jarayonlarini boshqaradi.

**Jadval nomi:** `workflows`

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | UUID | PK | Asosiy kalit |
| org_id | UUID | FK → organizations.id, NULL | Tashkilot |
| created_by | UUID | FK → users.id, NULL | Yaratuvchi |
| name | VARCHAR(255) | NOT NULL | Workflow nomi |
| slug | VARCHAR(100) | NOT NULL | Noyob nom |
| description | TEXT | NULL | Tavsif |
| steps | JSONB | NOT NULL, DEFAULT '[]' | Qadamlar ta'rifi |
| status | VARCHAR(50) | DEFAULT 'active' | active/inactive/archived |
| trigger | JSONB | DEFAULT '{}' | Ishga tushirish sharti |
| config | JSONB | DEFAULT '{}' | Qo'shimcha sozlamalar |
| is_active | BOOLEAN | DEFAULT TRUE | Aktiv |
| run_count | INTEGER | DEFAULT 0 | Ishga tushirilgan marta |
| last_run_at | TIMESTAMPTZ | NULL | Oxirgi ishlash vaqti |
| version | VARCHAR(20) | DEFAULT '1.0.0' | Versiya |
| deleted_at | TIMESTAMPTZ | NULL | Soft delete |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yangilangan vaqt |

**Relationships:**
- FK: org_id → organizations (SET NULL)
- 1:N → tasks
- M:N → agents (workflow_agents orqali)

**Indexes:**
- PK: `id`
- UNIQUE: `(org_id, slug)`
- INDEX: `org_id`, `status`, `is_active`

**Retention Policy:** Soft delete. Run tarixi tasks jadvalida.

---

## 11. Model

**Maqsad:** AIDA tizimida ishlatilishi mumkin bo'lgan barcha AI modellarini ro'yxatga oladi va ularning qobiliyatlari, narxlari haqida ma'lumot saqlaydi.

**Jadval nomi:** `models`

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | UUID | PK | Asosiy kalit |
| provider_id | UUID | FK → providers.id, NOT NULL | Provider |
| name | VARCHAR(255) | NOT NULL | Model nomi |
| slug | VARCHAR(100) | UNIQUE, NOT NULL | gpt-4o, claude-3-5-sonnet, ... |
| display_name | VARCHAR(255) | NOT NULL | Ko'rsatiladigan nom |
| type | VARCHAR(50) | DEFAULT 'chat' | chat/completion/embedding/image |
| capabilities | JSONB | DEFAULT '{}' | vision, tools, json_mode, ... |
| context_window | INTEGER | NOT NULL | Maksimal context (tokens) |
| max_output_tokens | INTEGER | NULL | Maksimal chiqish |
| pricing | JSONB | DEFAULT '{}' | input/output narx ($/1M token) |
| is_active | BOOLEAN | DEFAULT TRUE | Ishlatish mumkin |
| is_default | BOOLEAN | DEFAULT FALSE | Standart model |
| supports_streaming | BOOLEAN | DEFAULT TRUE | Streaming qo'llab-quvvatlash |
| supports_tools | BOOLEAN | DEFAULT FALSE | Function calling |
| deprecation_date | DATE | NULL | Eskirish sanasi |
| metadata | JSONB | DEFAULT '{}' | Qo'shimcha ma'lumot |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yangilangan vaqt |

**Relationships:**
- FK: provider_id → providers (RESTRICT delete)
- 1:N → chats

**Indexes:**
- PK: `id`
- UNIQUE: `slug`
- INDEX: `provider_id`, `type`, `is_active`, `is_default`

**Constraints:**
- `CHECK (type IN ('chat','completion','embedding','image','audio'))`
- `CHECK (context_window > 0)`

**Retention Policy:** Eskirgan modellar o'chirilmaydi, faqat `is_active=FALSE` va `deprecation_date` belgilanadi.


---

## 12. Provider

**Maqsad:** AI xizmat ko'rsatuvchilarni (OpenAI, Anthropic, Google va boshqalar) ro'yxatga oladi. Har bir provider bir nechta modelga ega bo'lishi mumkin.

**Jadval nomi:** `providers`

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | UUID | PK | Asosiy kalit |
| name | VARCHAR(255) | NOT NULL | Provider nomi |
| slug | VARCHAR(100) | UNIQUE, NOT NULL | openai, anthropic, google, ... |
| type | VARCHAR(50) | NOT NULL | cloud/local/custom |
| base_url | VARCHAR(500) | NOT NULL | API bazaviy URL |
| auth_type | VARCHAR(50) | DEFAULT 'api_key' | api_key/oauth/none |
| rate_limits | JSONB | DEFAULT '{}' | rpm, tpm, rpd cheklovlari |
| health_check_url | VARCHAR(500) | NULL | Status tekshiruv URL |
| status | VARCHAR(50) | DEFAULT 'active' | active/inactive/maintenance |
| is_default | BOOLEAN | DEFAULT FALSE | Standart provider |
| supports_streaming | BOOLEAN | DEFAULT TRUE | Streaming |
| timeout_seconds | INTEGER | DEFAULT 30 | So'rov timeout |
| metadata | JSONB | DEFAULT '{}' | Qo'shimcha ma'lumot |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yangilangan vaqt |

**Relationships:**
- 1:N → models

**Indexes:**
- PK: `id`
- UNIQUE: `slug`
- INDEX: `type`, `status`, `is_default`

**Constraints:**
- `CHECK (type IN ('cloud','local','custom'))`
- `CHECK (auth_type IN ('api_key','oauth','none'))`

**Retention Policy:** Provider o'chirilmaydi, faqat `status='inactive'` qilinadi. Unga bog'liq modellar mavjud.

---

## 13. Plugin

**Maqsad:** AIDA tizimiga o'rnatilgan plaginlarni boshqaradi. Har bir plagin bir yoki bir nechta tool ta'minlaydi.

**Jadval nomi:** `plugins`

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | UUID | PK | Asosiy kalit |
| name | VARCHAR(255) | NOT NULL | Plagin nomi |
| slug | VARCHAR(100) | UNIQUE, NOT NULL | URL-friendly nom |
| version | VARCHAR(20) | NOT NULL | Semver versiya |
| description | TEXT | NULL | Tavsif |
| author | VARCHAR(255) | NULL | Muallif |
| manifest | JSONB | NOT NULL | OpenAPI-style manifest |
| status | VARCHAR(50) | DEFAULT 'inactive' | inactive/active/error/disabled |
| install_config | JSONB | DEFAULT '{}' | O'rnatish sozlamalari |
| installed_by | UUID | FK → users.id, NULL | O'rnatgan foydalanuvchi |
| installed_at | TIMESTAMPTZ | NULL | O'rnatish vaqti |
| error_message | TEXT | NULL | Xato xabari |
| is_system | BOOLEAN | DEFAULT FALSE | Tizim plagini (o'chirilmaydi) |
| permissions | JSONB | DEFAULT '[]' | Talab qilinadigan ruxsatlar |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yangilangan vaqt |

**Relationships:**
- FK: installed_by → users (SET NULL)
- 1:N → tools
- M:N → agents (agent_plugins orqali)

**Indexes:**
- PK: `id`
- UNIQUE: `slug`
- INDEX: `status`, `is_system`, `installed_by`

**Constraints:**
- `CHECK (status IN ('inactive','active','error','disabled'))`

**Retention Policy:** Tizim plaginlari o'chirilmaydi. Foydalanuvchi plaginlari deinstall qilinganda `status='disabled'`, 30 kundan keyin hard delete.

---

## 14. Tool

**Maqsad:** Plagin tomonidan ta'minlanadigan individual funksiyalar. Agent function calling orqali ishlatadi.

**Jadval nomi:** `tools`

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | UUID | PK | Asosiy kalit |
| plugin_id | UUID | FK → plugins.id, NOT NULL | Tegishli plagin |
| name | VARCHAR(255) | NOT NULL | Tool nomi |
| slug | VARCHAR(100) | NOT NULL | Noyob nom (plugin ichida) |
| description | TEXT | NULL | Tavsif |
| function_schema | JSONB | NOT NULL | OpenAI function schema |
| permissions | JSONB | DEFAULT '[]' | Ruxsatlar ro'yxati |
| is_active | BOOLEAN | DEFAULT TRUE | Aktiv holat |
| is_dangerous | BOOLEAN | DEFAULT FALSE | Xavfli amal (confirm kerak) |
| timeout_seconds | INTEGER | DEFAULT 30 | Timeout |
| rate_limit | JSONB | DEFAULT '{}' | Chastota cheklovi |
| usage_count | BIGINT | DEFAULT 0 | Ishlatilgan marta |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yangilangan vaqt |

**Relationships:**
- FK: plugin_id → plugins (CASCADE delete)
- M:N → agents (agent_tools orqali)

**Indexes:**
- PK: `id`
- UNIQUE: `(plugin_id, slug)`
- INDEX: `plugin_id`, `is_active`, `is_dangerous`

**Retention Policy:** Plugin o'chirilganda cascade delete.

---

## 15. Knowledge

**Maqsad:** Loyihaga tegishli bilim bazasi. Hujjatlar, veb-sahifalar, qo'llanmalar va boshqa manbalardagi ma'lumotlar.

**Jadval nomi:** `knowledge`

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | UUID | PK | Asosiy kalit |
| project_id | UUID | FK → projects.id, NOT NULL | Loyiha |
| title | VARCHAR(500) | NOT NULL | Sarlavha |
| source | VARCHAR(1000) | NULL | Manba URL yoki yo'l |
| source_type | VARCHAR(50) | NOT NULL | document/url/text/repo/api |
| content_type | VARCHAR(50) | NOT NULL | text/markdown/html/pdf/code |
| raw_content | TEXT | NULL | Asl matn |
| processed_content | TEXT | NULL | Tozalangan matn |
| chunk_count | INTEGER | DEFAULT 0 | Qismlarga bo'lingan soni |
| embedding_model | VARCHAR(200) | NULL | Vektor modeli |
| is_indexed | BOOLEAN | DEFAULT FALSE | Vektorlashtirilgan |
| index_status | VARCHAR(50) | DEFAULT 'pending' | pending/processing/indexed/error |
| metadata | JSONB | DEFAULT '{}' | Qo'shimcha ma'lumot |
| created_by | UUID | FK → users.id, NULL | Qo'shgan foydalanuvchi |
| deleted_at | TIMESTAMPTZ | NULL | Soft delete |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yangilangan vaqt |

**Relationships:**
- FK: project_id → projects (CASCADE delete)
- 1:N → embeddings
- M:N → messages (message_knowledge orqali)

**Indexes:**
- PK: `id`
- INDEX: `project_id`, `source_type`, `is_indexed`, `index_status`
- GIN INDEX: `to_tsvector('english', title || ' ' || coalesce(processed_content,''))` — full-text search

**Retention Policy:** Soft delete. Project o'chirilganda cascade.

---

## 16. Embedding

**Maqsad:** Knowledge chunkalarining vektor ko'rinishlari. Semantik qidiruv uchun asosiy jadval.

**Jadval nomi:** `embeddings` (PARTITIONED BY HASH knowledge_id — 8 partition)

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | BIGINT | PK, GENERATED ALWAYS AS IDENTITY | Asosiy kalit |
| knowledge_id | UUID | FK → knowledge.id, NOT NULL | Manba |
| chunk_index | INTEGER | NOT NULL | Chunk tartib raqami |
| chunk_text | TEXT | NOT NULL | Chunk matni |
| vector | vector(1536) | NOT NULL | Embedding vektori (pgvector) |
| model_name | VARCHAR(200) | NOT NULL | text-embedding-3-small, ... |
| dimensions | INTEGER | NOT NULL | 768/1536/3072 |
| token_count | INTEGER | NULL | Chunk token soni |
| metadata | JSONB | DEFAULT '{}' | Page number, section, ... |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |

**Relationships:**
- FK: knowledge_id → knowledge (CASCADE delete)

**Indexes:**
- PK: `(id, knowledge_id)` — partition key bilan
- INDEX: `knowledge_id`, `chunk_index`
- HNSW INDEX: `vector vector_cosine_ops` — similarity search uchun
- IVFFlat INDEX (muqobil): `vector vector_l2_ops` WITH (lists=100)

**Constraints:**
- `CHECK (dimensions IN (768, 1536, 3072))`
- `CHECK (chunk_index >= 0)`

**Retention Policy:** Knowledge o'chirilganda cascade delete. Partition pruning orqali samarali boshqaruv.

---

## 17. Document

**Maqsad:** Loyihaga yuklangan hujjatlar metama'lumotlari. Faylning o'zi `files` jadvalida.

**Jadval nomi:** `documents`

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | UUID | PK | Asosiy kalit |
| project_id | UUID | FK → projects.id, NOT NULL | Loyiha |
| uploaded_by | UUID | FK → users.id, NULL | Yuklovchi |
| filename | VARCHAR(500) | NOT NULL | Fayl nomi |
| original_filename | VARCHAR(500) | NOT NULL | Asl fayl nomi |
| file_type | VARCHAR(50) | NOT NULL | pdf/docx/txt/md/py/... |
| mime_type | VARCHAR(100) | NULL | MIME turi |
| size_bytes | BIGINT | NOT NULL | Fayl hajmi |
| page_count | INTEGER | NULL | Sahifalar soni |
| processing_status | VARCHAR(50) | DEFAULT 'pending' | pending/processing/done/error |
| is_indexed | BOOLEAN | DEFAULT FALSE | Knowledge'ga qo'shilgan |
| knowledge_id | UUID | FK → knowledge.id, NULL | Bog'liq knowledge |
| metadata | JSONB | DEFAULT '{}' | Qo'shimcha ma'lumot |
| deleted_at | TIMESTAMPTZ | NULL | Soft delete |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yangilangan vaqt |

**Relationships:**
- FK: project_id → projects (CASCADE delete)
- 1:1 → files (primary file)

**Indexes:**
- PK: `id`
- INDEX: `project_id`, `file_type`, `processing_status`, `uploaded_by`

**Retention Policy:** Soft delete. 30 kun o'tgach fayl storage'dan o'chiriladi.

---

## 18. File

**Maqsad:** Hujjatning fizik fayl ma'lumotlari — storage path, checksum, backend. Haqiqiy binary fayl object storage'da saqlanadi.

**Jadval nomi:** `files`

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | UUID | PK | Asosiy kalit |
| document_id | UUID | FK → documents.id, NOT NULL | Hujjat |
| storage_backend | VARCHAR(50) | NOT NULL | s3/minio/local/gcs |
| bucket | VARCHAR(255) | NULL | S3/MinIO bucket |
| storage_path | VARCHAR(1000) | NOT NULL | Fayl yo'li |
| url | VARCHAR(1000) | NULL | Ochiq URL (agar public) |
| checksum_md5 | VARCHAR(32) | NULL | MD5 nazorat yig'indisi |
| checksum_sha256 | VARCHAR(64) | NOT NULL | SHA-256 nazorat yig'indisi |
| size_bytes | BIGINT | NOT NULL | Hajm |
| is_encrypted | BOOLEAN | DEFAULT TRUE | Shifrlangan |
| encryption_key_id | VARCHAR(100) | NULL | KMS key ID |
| version | VARCHAR(50) | DEFAULT '1' | Fayl versiyasi |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |

**Relationships:**
- FK: document_id → documents (CASCADE delete)

**Indexes:**
- PK: `id`
- UNIQUE: `document_id` (1:1 munosabat)
- INDEX: `storage_backend`, `checksum_sha256`

**Constraints:**
- `CHECK (storage_backend IN ('s3','minio','local','gcs','azure_blob'))`

**Retention Policy:** Document o'chirilganda cascade. Storage'dan fayl o'chirish async task orqali amalga oshiriladi.

---

## 19. AuditLog

**Maqsad:** Barcha muhim harakatlarni yozib boruvchi immutable jurnal. Compliance, forensics va xavfsizlik uchun zarur.

**Jadval nomi:** `audit_logs` (PARTITIONED BY RANGE created_at — choraklik)

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | BIGINT | PK, GENERATED ALWAYS AS IDENTITY | Asosiy kalit |
| user_id | UUID | FK → users.id, NULL | Harakat egasi (NULL=system) |
| org_id | UUID | NULL | Tashkilot konteksti |
| action | VARCHAR(100) | NOT NULL | user.login, chat.create, ... |
| resource_type | VARCHAR(100) | NOT NULL | user/chat/project/... |
| resource_id | UUID | NULL | Resurs identifikatori |
| before_data | JSONB | NULL | O'zgarishdan oldingi holat |
| after_data | JSONB | NULL | O'zgarishdan keyingi holat |
| ip_masked | VARCHAR(50) | NULL | Subnet (PII himoyasi) |
| user_agent | VARCHAR(500) | NULL | Client info |
| request_id | VARCHAR(100) | NULL | HTTP request ID |
| trace_id | VARCHAR(100) | NULL | Distributed trace ID |
| status | VARCHAR(20) | DEFAULT 'success' | success/failure |
| error_message | TEXT | NULL | Xato (status=failure) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Hodisa vaqti |

**Relationships:**
- FK: user_id → users (SET NULL — user o'chirilsa ham log qoladi)

**Indexes:**
- PK: `(id, created_at)` — partition key bilan
- INDEX: `user_id`, `action`, `resource_type`, `resource_id`, `created_at DESC`
- COMPOSITE: `(org_id, created_at DESC)` — org audit uchun

**Constraints:**
- IMMUTABLE: UPDATE va DELETE taqiqlanadi (RLS + trigger orqali)
- `CHECK (status IN ('success','failure'))`

**Retention Policy:** 365 kun hot/warm storage, so'ng cold archive. GDPR bo'yicha user PII anonymize, log qoladi.

---

## 20. SystemLog

**Maqsad:** Tizim darajasidagi texnik loglar. Application errors, warnings, debug ma'lumotlari.

**Jadval nomi:** `system_logs` (PARTITIONED BY RANGE created_at — haftalik)

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | BIGINT | PK, GENERATED ALWAYS AS IDENTITY | Asosiy kalit |
| level | VARCHAR(10) | NOT NULL | DEBUG/INFO/WARNING/ERROR/CRITICAL |
| service | VARCHAR(100) | NOT NULL | backend/celery/agent/workflow |
| component | VARCHAR(100) | NULL | api/database/cache/ai/auth |
| message | TEXT | NOT NULL | Log xabari |
| context | JSONB | DEFAULT '{}' | Qo'shimcha ma'lumot |
| exception | TEXT | NULL | Stack trace |
| trace_id | VARCHAR(100) | NULL | Distributed trace ID |
| span_id | VARCHAR(50) | NULL | Span ID |
| duration_ms | INTEGER | NULL | Amal vaqti |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Log vaqti |

**Indexes:**
- PK: `(id, created_at)` — partition key bilan
- INDEX: `level`, `service`, `created_at DESC`, `trace_id`
- PARTIAL: `(service, created_at DESC) WHERE level IN ('ERROR','CRITICAL')`

**Constraints:**
- `CHECK (level IN ('DEBUG','INFO','WARNING','ERROR','CRITICAL'))`

**Retention Policy:** DEBUG: 1 kun, INFO: 7 kun, WARNING: 30 kun, ERROR/CRITICAL: 90 kun. Partition drop orqali avtomatik tozalash.

---

## 21. APIKey

**Maqsad:** Tashqi platformalar va integratsiyalar uchun API kalitlarini boshqaradi. Faqat hash saqlanadi.

**Jadval nomi:** `api_keys`

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | UUID | PK | Asosiy kalit |
| user_id | UUID | FK → users.id, NOT NULL | Egasi |
| org_id | UUID | FK → organizations.id, NULL | Tashkilot |
| name | VARCHAR(255) | NOT NULL | Kalit nomi |
| key_hash | VARCHAR(64) | UNIQUE, NOT NULL | SHA-256 hash |
| key_prefix | VARCHAR(10) | NOT NULL | aida_sk_... (ko'rsatish uchun) |
| scopes | JSONB | DEFAULT '["chat"]' | Ruxsat doiralari |
| platform_name | VARCHAR(255) | NULL | Platforma nomi |
| business_type | VARCHAR(255) | NULL | Biznes turi |
| audience | TEXT | NULL | Maqsadli auditoriya |
| tone | VARCHAR(100) | NULL | Muloqot uslubi |
| assistant_goal | TEXT | NULL | Yordamchi maqsadi |
| custom_instructions | TEXT | NULL | Maxsus ko'rsatmalar |
| rate_limit_rpm | INTEGER | DEFAULT 60 | Daqiqada so'rovlar |
| is_active | BOOLEAN | DEFAULT TRUE | Aktiv holat |
| expires_at | TIMESTAMPTZ | NULL | Amal qilish muddati |
| last_used_at | TIMESTAMPTZ | NULL | Oxirgi foydalanish |
| usage_count | BIGINT | DEFAULT 0 | Foydalanish soni |
| deleted_at | TIMESTAMPTZ | NULL | Soft delete (revoke) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yangilangan vaqt |

**Relationships:**
- FK: user_id → users (CASCADE delete)
- FK: org_id → organizations (SET NULL)

**Indexes:**
- PK: `id`
- UNIQUE: `key_hash`
- INDEX: `user_id`, `org_id`, `is_active`, `expires_at`
- PARTIAL: `(key_hash) WHERE is_active = TRUE AND deleted_at IS NULL`

**Retention Policy:** Revoke qilinganda soft delete. 90 kundan keyin hard delete. Audit log qoladi.

---

## 22. Configuration

**Maqsad:** Tizim, tashkilot, loyiha va foydalanuvchi darajasidagi sozlamalarni ierarxik tarzda boshqaradi.

**Jadval nomi:** `configurations`

**Fieldlar:**

| Field | Tur | Cheklov | Tavsif |
|-------|-----|---------|--------|
| id | UUID | PK | Asosiy kalit |
| scope | VARCHAR(20) | NOT NULL | system/org/project/user |
| scope_id | UUID | NULL | Scope ob'ekti ID (system=NULL) |
| key | VARCHAR(255) | NOT NULL | Sozlama kaliti |
| value | JSONB | NOT NULL | Sozlama qiymati |
| value_type | VARCHAR(50) | DEFAULT 'json' | string/number/boolean/json/encrypted |
| is_secret | BOOLEAN | DEFAULT FALSE | Maxfiy (encrypted saqlash) |
| description | TEXT | NULL | Sozlama tavsifi |
| is_readonly | BOOLEAN | DEFAULT FALSE | Faqat o'qish |
| version | INTEGER | DEFAULT 1 | Optimistic locking |
| created_by | UUID | FK → users.id, NULL | Yaratuvchi |
| updated_by | UUID | FK → users.id, NULL | Oxirgi yangilovchi |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yaratilgan vaqt |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Yangilangan vaqt |

**Relationships:**
- FK: created_by → users (SET NULL)

**Indexes:**
- PK: `id`
- UNIQUE: `(scope, scope_id, key)` — bir scope'da kalit noyob
- INDEX: `scope`, `scope_id`, `is_secret`

**Constraints:**
- `CHECK (scope IN ('system','org','project','user'))`
- `CHECK (value_type IN ('string','number','boolean','json','encrypted'))`

**Retention Policy:** Sozlamalar o'chirilmaydi, yangilanadi. Version field orqali tarix kuzatiladi. AuditLog orqali barcha o'zgarishlar qayd qilinadi.

---

## XULOSA

| # | Entity | Jadval | PK turi | Partitioning |
|---|--------|--------|---------|--------------|
| 1 | User | users | UUID | — |
| 2 | Organization | organizations | UUID | — |
| 3 | Project | projects | UUID | — |
| 4 | Repository | repositories | UUID | — |
| 5 | Chat | chats | UUID | — |
| 6 | Message | messages | BIGINT | RANGE (monthly) |
| 7 | Session | sessions | UUID | — |
| 8 | Agent | agents | UUID | — |
| 9 | Task | tasks | UUID | — |
| 10 | Workflow | workflows | UUID | — |
| 11 | Model | models | UUID | — |
| 12 | Provider | providers | UUID | — |
| 13 | Plugin | plugins | UUID | — |
| 14 | Tool | tools | UUID | — |
| 15 | Knowledge | knowledge | UUID | — |
| 16 | Embedding | embeddings | BIGINT | HASH (x8) |
| 17 | Document | documents | UUID | — |
| 18 | File | files | UUID | — |
| 19 | AuditLog | audit_logs | BIGINT | RANGE (quarterly) |
| 20 | SystemLog | system_logs | BIGINT | RANGE (weekly) |
| 21 | APIKey | api_keys | UUID | — |
| 22 | Configuration | configurations | UUID | — |

---

*Hujjat AIDA Development Bible — Book 1, Chapter 8 asosida tayyorlangan.*
