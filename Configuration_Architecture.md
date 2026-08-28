# AIDA — Enterprise Configuration Architecture

## 1. Architectural Overview

AIDA configuration tizimi quyidagi 7 qatlamli override chain asosida ishlaydi. Har bir yuqori qatlam pastdagi qatlamni qisman yoki to'liq override qiladi:

```
Layer 1: Built-in Defaults          ← Dataclass field defaults (lowest priority)
Layer 2: Base Config File           ← aida/config/base.yaml (git-tracked)
Layer 3: Environment Config File    ← aida/config/{env}.yaml (git-tracked)
Layer 4: Local Override File        ← aida/config/local.yaml (gitignored)
Layer 5: Environment Variables      ← .env / OS env vars (gitignored)
Layer 6: Secrets Vault              ← HashiCorp Vault / AWS SM / Azure KV
Layer 7: Runtime Overrides          ← API calls / feature flags / admin panel
```

**Current State**: AIDA hozirda ikkita parallel config tizimiga ega:
1. `AIDA/settings.py` — Django-centric (webapp, views, ASGI/WSGI)
2. `aidaos/infrastructure/config/settings.py` — `AIDASettings` dataclass (aidaos services)

**Target State**: Ikkala tizim `AIDASettings` dataclass ostida birlashtiriladi. Django settings `from_django()` factory method orqali yuklanadi.

## 2. Configuration Sources

### 2.1 Built-in Defaults (Layer 1)

Location: `aidaos/infrastructure/config/settings.py` — `AIDASettings` dataclass

Har bir config key dataclass field default qiymatiga ega. Bu eng past priority.

```
┌─────────────────────────────────────────────────────────┐
│  AIDASettings dataclass                                 │
│  ├── project_root, data_dir, logs_dir                   │
│  ├── default_provider, default_model                    │
│  ├── ollama, openai, anthropic, gemini, deepseek, ...   │
│  ├── database (dsn, pool_size)                          │
│  ├── api_key, rate_limit, max_request_size              │
│  ├── debug, log_level, log_json                         │
│  └── django_secret_key, allowed_hosts, cors_origins     │
└─────────────────────────────────────────────────────────┘
```

### 2.2 YAML Config Files (Layer 2-4)

Planned directory layout:

```
aida/config/
├── base.yaml             # Barcha muhitlar uchun umumiy
├── development.yaml      # Development override
├── testing.yaml          # Testing override
├── staging.yaml          # Staging override
├── production.yaml       # Production override
├── local.yaml            # Shaxsiy override (gitignored)
└── secrets.yaml          # Lokal sirlar (gitignored)
```

YAML fayllar `deep_merge` semantikasida birlashtiriladi:
- Scalar: yuqori qiymat pastkini almashtiradi
- Dict: recursive merge
- List: yuqori qatlam pastkini to'liq almashtiradi
- None: "o'rnatilmagan" deb hisoblanadi, override qilmaydi

### 2.3 Environment Variables (Layer 5)

Ikki xil yuklash mexanizmi mavjud:

**A) Custom parser (`AIDA/env.py`)**:
- `load_dotenv()` funksiyasi `.env` faylni satrma-satr o'qiydi
- `os.environ.setdefault()` orqali faqat bo'sh bo'lmagan o'zgaruvchilarni o'rnatadi
- Mavjud environment o'zgaruvchilarni override qilmaydi

**B) python-dotenv (`aidaos/infrastructure/config/settings.py`)**:
- Agar `python-dotenv` kutubxonasi mavjud bo'lsa, `load_dotenv(override=False)` chaqiradi
- Aks holda faqat log yozadi, davom etadi

**Yuklash tartibi**:
```
1. .env                        (proyekt ildizi, development)
2. .env.{environment}          (masalan .env.production)
3. System environment          (OS env vars — eng yuqori priority)
```

### 2.4 Secrets Vault (Layer 6)

Enterprise muhitda sir ma'lumotlar vault orqali boshqariladi:

- **HashiCorp Vault** — self-hosted, KV v2 engine
- **AWS Secrets Manager** — AWS deployment
- **Azure Key Vault** — Azure deployment
- **GCP Secret Manager** — GCP deployment

Vault dan qiymatlar startup vaqtida olinadi va config obyektiga merge qilinadi.

### 2.5 Runtime Overrides (Layer 7)

Runtime override yo'llari:
- **Admin API**: `POST /api/v1/admin/config` (superuser talab qilinadi)
- **Feature Flags**: per-user yoki per-tenant runtime toggle
- **Plugin Registration**: pluginlar o'z config schema va defaultlarini ro'yxatdan o'tkazadi

## 3. Configuration Loader Pipeline

### 3.1 Startup Pipeline

```
STARTUP
  │
  ├── 1. AIDA/env.py: load_dotenv()             ← .env faylni yuklash
  ├── 2. AIDASettings.__init__()                 ← Dataclass yaratish
  ├── 3. _load_from_env()                        ← env var larni o'qish
  ├── 4. If Django: from_django()                ← Django settings ni merge
  ├── 5. (Future) Load base.yaml                 ← Layer 2
  ├── 6. (Future) Load {env}.yaml                ← Layer 3
  ├── 7. (Future) Load local.yaml                ← Layer 4
  ├── 8. (Future) Load vault secrets             ← Layer 6
  ├── 9. Validate                                ← ValidationRules
  ├── 10. Freeze                                 ← Immutable runtime config
  └── 11. Register watchers                      ← Hot-reload (dev only)
```

### 3.2 Config Loader API (Target Design)

```python
# aida/config/loader.py
from aida.config.sources import (
    DefaultsSource,
    FileSource,
    EnvSource,
    VaultSource,
    RuntimeOverrideSource,
)
from aida.config.validator import ConfigValidator

class ConfigLoader:
    def __init__(self):
        self._sources = [
            DefaultsSource(),
            FileSource("base.yaml"),
            FileSource("{env}.yaml"),
            FileSource("local.yaml", optional=True),
            EnvSource(".env", optional=True),
            VaultSource(optional=not is_production),
            RuntimeOverrideSource(),
        ]

    def load(self) -> ImmutableConfig:
        config = {}
        for source in self._sources:
            config = deep_merge(config, source.load())
        ConfigValidator().validate(config)
        return ImmutableConfig(config)
```

### 3.3 Current vs Target Architecture

| Component | Current | Target |
|-----------|---------|--------|
| Loader | `AIDASettings.__init__()` | `ConfigLoader` pipeline |
| Sources | env vars only | defaults → YAML → env → vault → runtime |
| Django bridge | `from_django()` classmethod | Native integration |
| Validation | None | `ConfigValidator` with JSON Schema |
| Immutability | Mutable dataclass | `ImmutableConfig` wrapper |
| Hot-reload | None | File watcher + event system |

## 4. Configuration Object Schema

### 4.1 Current Schema (AIDASettings)

```python
@dataclass
class AIDASettings:
    # Paths
    project_root: str
    data_dir: str
    logs_dir: str
    projects_dir: str
    # ... more paths

    # LLM Providers
    default_provider: str
    default_model: str
    ollama: ProviderEndpoint
    openai: ProviderEndpoint
    anthropic: ProviderEndpoint
    gemini: ProviderEndpoint
    deepseek: ProviderEndpoint
    lmstudio: ProviderEndpoint
    aida_model: ProviderEndpoint

    # Database
    database: DatabaseSettings

    # Security
    api_key: str
    rate_limit: int
    max_request_size: int
    django_secret_key: str
    allowed_hosts: str
    cors_origins: str

    # System
    debug: bool
    log_level: str
    log_json: bool
    max_files: int
    max_file_size: int
```

### 4.2 Target Namespace Schema

```yaml
# aida/config/base.yaml
app:
  name: AIDA
  version: 1.0.0
  debug: false
  secret_key: null           # PRODUCTION: required
  port: 8000
  host: 0.0.0.0
  timezone: UTC
  language: en
  data_dir: data/

database:
  url: sqlite:///data/aida.db
  pool_size: 5
  max_overflow: 10
  echo: false
  ssl_mode: prefer

redis:
  url: redis://localhost:6379/0
  socket_timeout: 5
  retry_on_timeout: true
  prefix: aida:

vector_db:
  provider: qdrant          # qdrant, chroma, pinecone, weaviate, milvus
  url: http://localhost:6333
  api_key: null
  collection: aida_vectors
  embedding_dim: 768

models:
  default_provider: ollama
  providers:
    ollama:
      url: http://localhost:11434
      timeout: 120
      default_model: llama3
    openai:
      api_key: null
      org_id: null
      base_url: https://api.openai.com/v1
      default_model: gpt-4
    anthropic:
      api_key: null
      default_model: claude-3-opus
    gemini:
      api_key: null
      default_model: gemini-pro

embedding:
  provider: ollama
  model: nomic-embed-text
  dimension: 768

rag:
  enabled: true
  chunk_size: 512
  chunk_overlap: 64
  top_k: 5
  similarity_threshold: 0.75

logging:
  level: INFO
  format: json              # json, text
  handlers: [console]
  file: null

monitoring:
  metrics_enabled: true
  tracing_enabled: false
  profiler_enabled: false
  exporter: prometheus

security:
  jwt_algorithm: HS256
  access_token_ttl: 3600
  refresh_token_ttl: 2592000   # 30 days
  cors_origins: []
  allowed_hosts: []
  ssl_redirect: false
  hsts_seconds: 0

auth:
  providers: [local]            # local, oauth, saml, ldap
  oauth:
    google: {client_id: null, client_secret: null}
    github: {client_id: null, client_secret: null}
    microsoft: {client_id: null, client_secret: null}

smtp:
  host: localhost
  port: 587
  username: null
  password: null
  use_tls: true
  from_email: noreply@aida.local

file_storage:
  provider: local               # local, s3, gcs, azure
  local_path: data/storage
  s3: {bucket: null, region: null, access_key: null, secret_key: null}

cache:
  provider: redis               # redis, memory
  default_ttl: 300
  max_size: 1000

plugins:
  enabled: true
  directory: plugins
  allow_external: false
  sandbox: docker               # docker, subprocess, none

feature_flags:
  voice: false
  vision: false
  rag: true
  memory: true
  agents: true
  docker: false
  github: false
  internet_search: false
  browser: false
  auto_mode: true
  plugins: true
  streaming: true
  batch_processing: false
  audit_logging: true
  multi_tenant: false
  experimental_models: false

rate_limits:
  api:
    requests_per_minute: 60
    burst: 100
  chat:
    requests_per_minute: 30
    burst: 50
  enabled: true
```

## 5. ENV-to-Config Mapping Convention

```
Config Path                    → Environment Variable
─────────────────────────────────────────────────────
app.name                       → APP_NAME
app.debug                      → APP_DEBUG / DJANGO_DEBUG
app.secret_key                 → APP_SECRET_KEY / DJANGO_SECRET_KEY
database.url                   → DATABASE_URL
redis.url                      → REDIS_URL
vector_db.provider             → VECTOR_DB_PROVIDER
vector_db.url                  → VECTOR_DB_URL
models.default_provider        → AIDA_PROVIDER
models.providers.ollama.url    → OLLAMA_URL
models.providers.openai.api_key → OPENAI_API_KEY
embedding.provider             → EMBEDDING_PROVIDER
embedding.model                → EMBEDDING_MODEL
rag.enabled                    → RAG_ENABLED
security.jwt_secret            → JWT_SECRET
logging.level                  → LOG_LEVEL
cache.provider                 → CACHE_PROVIDER
```

Nested keys uchun `__` separator ishlatiladi:
```
models__providers__ollama__url → MODELS_PROVIDERS_OLLAMA_URL
feature_flags__voice           → FFLAG_VOICE
```

## 6. Configuration Access Patterns

### 6.1 Python (current)

```python
from aidaos.infrastructure.config import get_settings

config = get_settings()
provider = config.default_provider
ollama_url = config.ollama.url
debug = config.debug
```

### 6.2 Python (target)

```python
from aida.config import Config

class MyService:
    def __init__(self, config: Config):
        self._config = config

    def execute(self):
        db_url = self._config.get("database.url")
        debug = self._config.get("app.debug", default=False)
        model = self._config.get("models.default_provider")
```

### 6.3 Module Registration

Modules o'z default configlarini `config.py` da ro'yxatdan o'tkazadi:

```python
# aida/kernel/agents/config.py
DEFAULT_CONFIG = {
    "agents": {
        "max_concurrent": 10,
        "task_timeout": 300,
        "retry_attempts": 3,
    }
}
```

## 7. Configuration Hot-Reload

**Development**:
- File watcher `aida/config/*.yaml` va `.env` fayllarni kuzatadi
- O'zgarishda config obyekti qayta merge va validate qilinadi
- Listenerlar `ConfigChanged` event orqali xabardor qilinadi

**Production**:
- Hot-reload YO'Q — restart yoki API call talab qilinadi
- `POST /api/v1/admin/config/reload` — xavfsiz reload

## 8. Enterprise Additions

### 8.1 Multi-Tenant Configuration

Har bir tenant o'z config override lariga ega:

```python
config.with_tenant(tenant_id="acme_corp").get("models.openai.api_key")
```

Tenant overrides databaseda saqlanadi va har bir request boshida merge qilinadi.

### 8.2 Configuration Auditing

Har bir config o'zgarishi loglanadi:

```json
{
  "event": "config_changed",
  "key": "models.openai.api_key",
  "changed_by": "admin@example.com",
  "source": "api",
  "timestamp": "2026-07-03T12:00:00Z"
}
```

### 8.3 Configuration Diffing

```bash
aida config diff --from staging --to production
aida config validate --environment production
aida config show --format json
```

### 8.4 Migration Path: Dual System → Unified

```
Phase 1 (Current): Dual system
  - Django settings.py → webapp
  - AIDASettings dataclass → aidaos

Phase 2: AIDASettings becomes primary
  - Django reads from AIDASettings via from_django()
  - settings.py imports get_settings()

Phase 3: YAML config files added
  - base.yaml, {env}.yaml as additional sources
  - ConfigLoader pipeline implemented

Phase 4: Vault integration
  - VaultSource for production secrets
  - Runtime override API
  - Feature flag engine
```

## 9. Complete File Layout (Target)

```
aida/config/
├── __init__.py                  # Config, get_config()
├── defaults.py                  # Built-in defaults dictionary
├── loader.py                    # ConfigLoader pipeline
├── validator.py                 # ConfigValidator
├── schema.yaml                  # JSON Schema
├── sources/
│   ├── __init__.py
│   ├── base.py                  # BaseSource abstract class
│   ├── defaults_source.py       # Layer 1
│   ├── file_source.py           # Layers 2-4
│   ├── env_source.py            # Layer 5
│   ├── vault_source.py          # Layer 6
│   └── runtime_source.py        # Layer 7
├── base.yaml                    # Base configuration
├── development.yaml
├── testing.yaml
├── staging.yaml
├── production.yaml
├── local.yaml                   # Gitignored
└── secrets.yaml                 # Gitignored
```
