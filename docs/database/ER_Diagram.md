# AIDA Enterprise Database Architecture
## ER Diagram

**Versiya:** 1.0.0
**Sana:** 2026-07-03
**Muallif:** AIDA Database Team

---

## 1. CLUSTER BO'YICHA DIAGRAMLAR

### 1.1 USER CLUSTER

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER CLUSTER                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────┐       ┌───────────────────────────┐   │
│  │        users          │       │      organizations        │   │
│  ├───────────────────────┤       ├───────────────────────────┤   │
│  │ PK id (UUID)          │       │ PK id (UUID)              │   │
│  │    email (encrypted)  │       │    name (VARCHAR 255)     │   │
│  │    username           │       │    slug (UNIQUE)          │   │
│  │    hashed_password    │◄──┐   │    plan (VARCHAR)         │   │
│  │    role               │   │   │ FK owner_id → users.id    │   │
│  │    is_active          │   │   │    settings (JSONB)       │   │
│  │    is_verified        │   │   │    created_at             │   │
│  │    created_at         │   │   └───────────────────────────┘   │
│  │    last_login_at      │   │              │ 1:N               │
│  └───────────────────────┘   │              ▼                   │
│             │ 1:N             │   ┌───────────────────────────┐   │
│             │                │   │   organization_members    │   │
│             ▼                │   │   (M:N junction)          │   │
│  ┌───────────────────────┐   │   ├───────────────────────────┤   │
│  │       sessions        │   │   │ PK id (UUID)              │   │
│  ├───────────────────────┤   │   │ FK user_id → users.id     │   │
│  │ PK id (UUID)          │   └───│ FK org_id → orgs.id       │   │
│  │ FK user_id → users    │       │    role (VARCHAR)         │   │
│  │    token_hash         │       │    joined_at              │   │
│  │    ip_masked          │       └───────────────────────────┘   │
│  │    device_info(JSONB) │                                       │
│  │    expires_at         │       ┌───────────────────────────┐   │
│  │    created_at         │       │        api_keys           │   │
│  └───────────────────────┘       ├───────────────────────────┤   │
│                                  │ PK id (UUID)              │   │
│                                  │ FK user_id → users        │   │
│                                  │ FK org_id → orgs          │   │
│                                  │    key_hash (UNIQUE)      │   │
│                                  │    name                   │   │
│                                  │    scopes (JSONB)         │   │
│                                  │    last_used_at           │   │
│                                  │    expires_at             │   │
│                                  │    is_active              │   │
│                                  └───────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### 1.2 PROJECT CLUSTER

```
┌──────────────────────────────────────────────────────────────────┐
│                      PROJECT CLUSTER                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────┐       ┌───────────────────────────┐   │
│  │       projects        │       │      repositories         │   │
│  ├───────────────────────┤       ├───────────────────────────┤   │
│  │ PK id (UUID)          │──1:N─▶│ PK id (UUID)              │   │
│  │ FK org_id             │       │ FK project_id             │   │
│  │ FK created_by         │       │    source (ENUM)          │   │
│  │    name               │       │    url                    │   │
│  │    slug (UNIQUE)      │       │    branch                 │   │
│  │    description        │       │    last_synced_at         │   │
│  │    settings (JSONB)   │       │    sync_status            │   │
│  │    is_archived        │       │    metadata (JSONB)       │   │
│  │    created_at         │       └───────────────────────────┘   │
│  └───────────────────────┘                                       │
│            │                                                     │
│     ┌──────┼──────────────┐                                      │
│     │ 1:N  │ 1:N          │ 1:N                                  │
│     ▼      ▼              ▼                                      │
│  ┌────────┐  ┌──────────┐  ┌──────────────────────────────────┐  │
│  │ chats  │  │knowledge │  │         documents                │  │
│  ├────────┤  ├──────────┤  ├──────────────────────────────────┤  │
│  │ id     │  │ id       │  │ PK id (UUID)                     │  │
│  │ proj_  │  │ title    │  │ FK project_id                    │  │
│  │  id FK │  │ source   │  │    filename                      │  │
│  │ user_id│  │ content_ │  │    file_type                     │  │
│  │ title  │  │  type    │  │    size_bytes                    │  │
│  │ model_ │  │ proj_id  │  │    storage_path                  │  │
│  │  config│  │ created_ │  │    checksum                      │  │
│  └────────┘  │  at      │  │    is_processed                  │  │
│              └──────────┘  │    created_at                    │  │
│                  │ 1:N     └──────────────────────────────────┘  │
│                  ▼                      │ 1:1                    │
│           ┌──────────┐                  ▼                        │
│           │embeddings│         ┌────────────────┐               │
│           ├──────────┤         │     files      │               │
│           │ id       │         ├────────────────┤               │
│           │knowledge_│         │ id             │               │
│           │  id FK   │         │ document_id FK │               │
│           │chunk_text│         │ storage_backend│               │
│           │ vector   │         │ url            │               │
│           │model_name│         │ checksum       │               │
│           │dimensions│         │ size_bytes     │               │
│           └──────────┘         └────────────────┘               │
└──────────────────────────────────────────────────────────────────┘
```

### 1.3 CHAT CLUSTER

```
┌──────────────────────────────────────────────────────────────────┐
│                       CHAT CLUSTER                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────┐                               │
│  │             chats             │                               │
│  ├───────────────────────────────┤                               │
│  │ PK id (UUID)                  │                               │
│  │ FK user_id → users            │                               │
│  │ FK project_id → projects      │                               │
│  │ FK model_id → models          │                               │
│  │    title (VARCHAR 500)        │                               │
│  │    model_config (JSONB)       │                               │
│  │    is_archived                │                               │
│  │    message_count              │                               │
│  │    total_tokens               │                               │
│  │    created_at                 │                               │
│  │    updated_at                 │                               │
│  └───────────────┬───────────────┘                               │
│                  │ 1:N                                           │
│                  ▼                                               │
│  ┌───────────────────────────────┐                               │
│  │            messages           │  ← PARTITIONED by month      │
│  ├───────────────────────────────┤                               │
│  │ PK id (BIGINT)                │                               │
│  │ FK chat_id → chats            │                               │
│  │    role (ENUM: user/         │                               │
│  │          assistant/system)   │                               │
│  │    content (TEXT)             │                               │
│  │    tokens_input (INT)         │                               │
│  │    tokens_output (INT)        │                               │
│  │    model_name                 │                               │
│  │    metadata (JSONB)           │                               │
│  │    created_at (TIMESTAMPTZ)   │                               │
│  └───────────────────────────────┘                               │
│                  │ M:N                                           │
│                  ▼                                               │
│  ┌───────────────────────────────┐                               │
│  │      message_knowledge        │  ← Junction table            │
│  ├───────────────────────────────┤                               │
│  │ FK message_id                 │                               │
│  │ FK knowledge_id               │                               │
│  │    relevance_score (FLOAT)    │                               │
│  └───────────────────────────────┘                               │
└──────────────────────────────────────────────────────────────────┘
```

### 1.4 AI CLUSTER

```
┌──────────────────────────────────────────────────────────────────┐
│                        AI CLUSTER                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐       ┌──────────────────────────────────┐  │
│  │    providers     │──1:N─▶│           models                 │  │
│  ├──────────────────┤       ├──────────────────────────────────┤  │
│  │ PK id (UUID)     │       │ PK id (UUID)                     │  │
│  │    name          │       │ FK provider_id → providers       │  │
│  │    type (ENUM)   │       │    name                          │  │
│  │    base_url      │       │    slug (UNIQUE)                  │  │
│  │    auth_type     │       │    capabilities (JSONB)          │  │
│  │    rate_limits   │       │    context_window (INT)          │  │
│  │     (JSONB)      │       │    pricing (JSONB)               │  │
│  │    is_active     │       │    is_active                     │  │
│  └──────────────────┘       └──────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────┐       ┌──────────────────────────────────┐  │
│  │     agents       │──1:N─▶│            tasks                 │  │
│  ├──────────────────┤       ├──────────────────────────────────┤  │
│  │ PK id (UUID)     │       │ PK id (UUID)                     │  │
│  │    name          │       │ FK agent_id → agents             │  │
│  │    type (ENUM)   │       │ FK workflow_id → workflows       │  │
│  │    config (JSONB)│       │    type                          │  │
│  │    status        │       │    status (ENUM)                 │  │
│  │    capabilities  │       │    input (JSONB)                 │  │
│  │     (JSONB)      │       │    output (JSONB)                │  │
│  │    created_at    │       │    retry_count (INT)             │  │
│  └──────────────────┘       │    started_at                    │  │
│           │ M:N             │    completed_at                  │  │
│           ▼                 │    error_message                 │  │
│  ┌──────────────────┐       └──────────────────────────────────┘  │
│  │  agent_tools     │                                             │
│  │  (junction)      │       ┌──────────────────────────────────┐  │
│  ├──────────────────┤       │          workflows               │  │
│  │ FK agent_id      │       ├──────────────────────────────────┤  │
│  │ FK tool_id       │       │ PK id (UUID)                     │  │
│  └──────────────────┘       │ FK created_by → users            │  │
│                             │    name                          │  │
│  ┌──────────────────┐       │    steps (JSONB)                 │  │
│  │  agent_plugins   │       │    status (ENUM)                 │  │
│  │  (junction)      │       │    trigger (JSONB)               │  │
│  ├──────────────────┤       │    is_active                     │  │
│  │ FK agent_id      │       │    created_at                    │  │
│  │ FK plugin_id     │       └──────────────────────────────────┘  │
│  └──────────────────┘                                             │
└──────────────────────────────────────────────────────────────────┘
```

### 1.5 SYSTEM CLUSTER

```
┌──────────────────────────────────────────────────────────────────┐
│                      SYSTEM CLUSTER                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────┐       ┌──────────────────────────────┐    │
│  │      plugins      │──1:N─▶│           tools              │    │
│  ├───────────────────┤       ├──────────────────────────────┤    │
│  │ PK id (UUID)      │       │ PK id (UUID)                 │    │
│  │    name           │       │ FK plugin_id → plugins       │    │
│  │    version        │       │    name                      │    │
│  │    manifest(JSONB)│       │    function_schema (JSONB)   │    │
│  │    status (ENUM)  │       │    permissions (JSONB)       │    │
│  │    install_config │       │    is_active                 │    │
│  │     (JSONB)       │       └──────────────────────────────┘    │
│  │    installed_by   │                                           │
│  └───────────────────┘                                           │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                     audit_logs                            │   │
│  ├───────────────────────────────────────────────────────────┤   │
│  │ PK id (BIGINT, PARTITIONED by quarter)                    │   │
│  │ FK user_id → users (NULLABLE — system actions)           │   │
│  │    action (VARCHAR)                                       │   │
│  │    resource_type (VARCHAR)                                │   │
│  │    resource_id (UUID)                                     │   │
│  │    before_data (JSONB)                                    │   │
│  │    after_data (JSONB)                                     │   │
│  │    ip_masked (VARCHAR)                                    │   │
│  │    user_agent                                             │   │
│  │    created_at (TIMESTAMPTZ)                               │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                    system_logs                            │   │
│  ├───────────────────────────────────────────────────────────┤   │
│  │ PK id (BIGINT, PARTITIONED by week)                       │   │
│  │    level (ENUM: DEBUG/INFO/WARNING/ERROR/CRITICAL)        │   │
│  │    service (VARCHAR)                                      │   │
│  │    message (TEXT)                                         │   │
│  │    context (JSONB)                                        │   │
│  │    trace_id (VARCHAR)                                     │   │
│  │    created_at (TIMESTAMPTZ)                               │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                   configurations                          │   │
│  ├───────────────────────────────────────────────────────────┤   │
│  │ PK id (UUID)                                              │   │
│  │    scope (ENUM: system/org/project/user)                  │   │
│  │    scope_id (UUID, NULLABLE)                              │   │
│  │    key (VARCHAR)                                          │   │
│  │    value (JSONB)                                          │   │
│  │    is_secret (BOOLEAN)                                    │   │
│  │    UNIQUE(scope, scope_id, key)                           │   │
│  └───────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. CROSS-CLUSTER MUNOSABATLAR

```
┌──────────────────────────────────────────────────────────────────┐
│                   CROSS-CLUSTER RELATIONS                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  USER CLUSTER ──────────────────────────────────────────────┐   │
│     users                                                    │   │
│       │                                                      │   │
│       ├──── 1:N ───► chats (CHAT CLUSTER)                   │   │
│       ├──── 1:N ───► projects.created_by (PROJECT CLUSTER)  │   │
│       ├──── 1:N ───► workflows.created_by (AI CLUSTER)      │   │
│       ├──── 1:N ───► audit_logs.user_id (SYSTEM CLUSTER)    │   │
│       └──── 1:N ───► api_keys (USER CLUSTER)                │   │
│                                                              │   │
│  PROJECT CLUSTER                                             │   │
│     projects                                                 │   │
│       │                                                      │   │
│       ├──── 1:N ───► chats (CHAT CLUSTER)                   │   │
│       ├──── 1:N ───► knowledge (PROJECT CLUSTER)            │   │
│       └──── 1:N ───► documents (PROJECT CLUSTER)            │   │
│                                                              │   │
│  AI CLUSTER                                                  │   │
│     models                                                   │   │
│       └──── 1:N ───► chats.model_id (CHAT CLUSTER)          │   │
│     agents                                                   │   │
│       └──── M:N ───► tools, plugins (SYSTEM CLUSTER)        │   │
│                                                              │   │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. JUNCTION (M:N) JADVALLAR

```
┌─────────────────────┬─────────────────────┬─────────────────────┐
│ Junction Table      │ Left Entity         │ Right Entity        │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ organization_members│ users               │ organizations       │
│   + role, joined_at │                     │                     │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ project_members     │ users               │ projects            │
│   + permissions     │                     │                     │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ agent_tools         │ agents              │ tools               │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ agent_plugins       │ agents              │ plugins             │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ workflow_agents     │ workflows           │ agents              │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ message_knowledge   │ messages            │ knowledge           │
│   + relevance_score │                     │                     │
└─────────────────────┴─────────────────────┴─────────────────────┘
```

---

## 4. PRIMARY KEY STRATEGIYASI

```
UUID v4:  users, organizations, projects, chats, agents, workflows,
          models, providers, plugins, tools, knowledge, documents,
          files, api_keys, configurations
          → Nima uchun: distributed generation, no sequence bottleneck

BIGINT (IDENTITY): messages, audit_logs, system_logs, embeddings
          → Nima uchun: very high insert rate, partition-friendly,
            storage efficient (8 bytes vs 16 bytes UUID)

UUID v7 (future): sortable UUID, time-based — PostgreSQL 17+ ready
```

---

*Hujjat AIDA Development Bible — Book 1, Chapter 8 asosida tayyorlangan.*
