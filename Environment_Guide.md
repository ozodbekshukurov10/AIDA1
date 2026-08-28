# AIDA — Enterprise Environment Variable Guide

## 1. Convention

Barcha environment o'zgaruvchilari `UPPER_SNAKE_CASE` formatida. Guruhlar functional area bo'yicha prefix bilan ajratilgan:

| Prefix | Area | Status |
|--------|------|--------|
| `APP_` | Application metadata | Planned |
| `DATABASE_` | Database connection | Planned |
| `REDIS_` | Redis connection | Planned |
| `VECTOR_DB_` | Vector database | Planned |
| `OLLAMA_`, `OPENAI_`, `ANTHROPIC_`, `GEMINI_`, `DEEPSEEK_` | AI model providers | **Active** |
| `LMSTUDIO_` | LM Studio provider | **Active** |
| `AIDA_MODEL_` | AIDA local model | **Active** |
| `EMBEDDING_` | Embedding model | Planned |
| `RAG_` | RAG pipeline | Planned |
| `JWT_` | JWT tokens | Planned |
| `OAUTH_` | OAuth providers | Planned |
| `SMTP_` | Email/SMTP | Planned |
| `STORAGE_` | File storage | Planned |
| `CACHE_` | Cache | Planned |
| `LOG_` | Logging | Planned |
| `METRICS_` | Monitoring | Planned |
| `PLUGIN_` | Plugin system | Planned |
| `FFLAG_` | Feature flags | Planned |
| `RATE_LIMIT_` | Rate limiting | Planned |
| `SECRET_` | Secrets (never log) | Planned |
| `AIDA_` | AIDA-specific settings | **Active** |
| `DJANGO_` | Django-specific settings | **Active** |
| `GOOGLE_` | Google services | **Active** |
| `TENSORRT_` | TensorRT-LLM provider | **Active** |
| `VLLM_` | vLLM provider | **Active** |

## 2. Complete Variable Reference

### 2.1 Application

| Variable | Required | Default | Implemented | Description |
|----------|----------|---------|-------------|-------------|
| `APP_NAME` | No | `AIDA` | No | Application name |
| `APP_VERSION` | No | `1.0.0` | No | Application version |
| `APP_ENV` | No | `development` | No | Environment: development, testing, staging, production |
| `APP_DEBUG` | No | `false` | No | Debug mode (development only) |
| `APP_SECRET_KEY` | **YES (prod)** | `None` | No | Crypto signing key |
| `APP_PORT` | No | `8000` | No | HTTP server port |
| `APP_HOST` | No | `0.0.0.0` | No | HTTP bind address |
| `APP_TIMEZONE` | No | `UTC` | No | Default timezone |
| `APP_LANGUAGE` | No | `en` | No | Default language |
| `APP_BASE_DIR` | No | auto | No | Application base directory |
| `APP_DATA_DIR` | No | `data/` | No | Data directory |

### 2.2 Django (Active)

| Variable | Required | Default | Implemented | Description |
|----------|----------|---------|-------------|-------------|
| `DJANGO_DEBUG` | No | `false` | **YES** | Debug mode toggle |
| `DJANGO_SECRET_KEY` | No | auto-generated | **YES** | Django secret key |
| `DJANGO_ALLOWED_HOSTS` | No | `127.0.0.1,localhost` | **YES** | Comma-separated allowed hosts |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | No | `http://127.0.0.1:8080,...` | **YES** | CSRF trusted origins |
| `DJANGO_SECURE_PROXY_SSL_HEADER` | No | `false` | **YES** | Enable proxy SSL header |
| `DJANGO_PORT` | No | `8080` | No | Runserver port (manage.py) |

### 2.3 AI Model Providers (Active)

#### Ollama

| Variable | Required | Default | Implemented | Description |
|----------|----------|---------|-------------|-------------|
| `OLLAMA_ENABLED` | No | `true` | **YES** | Enable Ollama provider |
| `OLLAMA_URL` | No | `http://localhost:11434` | **YES** | Ollama server URL |
| `OLLAMA_MODEL` | No | `` | **YES** | Default model name |
| `OLLAMA_TIMEOUT` | No | `120` | **YES** | Request timeout (seconds) |
| `OLLAMA_QUANTIZATION` | No | `` | No | Model quantization level |
| `OLLAMA_NUM_BATCH` | No | `` | No | Batch size |
| `OLLAMA_NUM_GPU` | No | `` | No | GPU layers |
| `OLLAMA_NUM_THREAD` | No | `` | No | CPU threads |

#### OpenAI / Compatible

| Variable | Required | Default | Implemented | Description |
|----------|----------|---------|-------------|-------------|
| `OPENAI_API_KEY` | Conditional | `None` | **YES** | OpenAI API key |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | **YES** | API base URL |
| `OPENAI_MODEL` | No | `gpt-4o` | **YES** | Default model |
| `OPENAI_TIMEOUT` | No | `120` | **YES** | Request timeout |
| `OPENAI_ORG_ID` | No | `None` | No | Organization ID |
| `OPENAI_MAX_RETRIES` | No | `3` | No | Retry count |

#### Anthropic

| Variable | Required | Default | Implemented | Description |
|----------|----------|---------|-------------|-------------|
| `ANTHROPIC_API_KEY` | Conditional | `None` | **YES** | Anthropic API key |
| `ANTHROPIC_MODEL` | No | `claude-3-opus-20240229` | **YES** | Default model |
| `ANTHROPIC_BASE_URL` | No | `None` | **YES** | API base URL |
| `ANTHROPIC_TIMEOUT` | No | `` | **YES** | Request timeout |

#### Google Gemini

| Variable | Required | Default | Implemented | Description |
|----------|----------|---------|-------------|-------------|
| `GEMINI_API_KEY` | Conditional | `None` | **YES** | Google AI API key |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | **YES** | Default model |
| `GEMINI_TIMEOUT` | No | `60` | **YES** | Request timeout |

#### DeepSeek

| Variable | Required | Default | Implemented | Description |
|----------|----------|---------|-------------|-------------|
| `DEEPSEEK_API_KEY` | Conditional | `None` | **YES** | DeepSeek API key |
| `DEEPSEEK_MODEL` | No | `deepseek-chat` | **YES** | Default model |
| `DEEPSEEK_BASE_URL` | No | `None` | **YES** | API base URL |
| `DEEPSEEK_TIMEOUT` | No | `` | **YES** | Request timeout |

#### LM Studio

| Variable | Required | Default | Implemented | Description |
|----------|----------|---------|-------------|-------------|
| `LMSTUDIO_ENABLED` | No | `true` | **YES** | Enable LM Studio |
| `LMSTUDIO_URL` | No | `http://localhost:1234` | **YES** | LM Studio URL |
| `LMSTUDIO_MODEL` | No | `` | **YES** | Default model |
| `LMSTUDIO_TIMEOUT` | No | `120` | **YES** | Request timeout |
| `LMSTUDIO_API_URL` | No | `` | **YES** | Alternative API URL |

#### AIDA Local Model

| Variable | Required | Default | Implemented | Description |
|----------|----------|---------|-------------|-------------|
| `AIDA_MODEL_ENABLED` | No | `false` | **YES** | Enable AIDA model |
| `AIDA_MODEL_URL` | No | `` | **YES** | Model server URL |
| `AIDA_MODEL_API_KEY` | No | `` | **YES** | API key |
| `AIDA_MODEL_TIMEOUT` | No | `` | **YES** | Request timeout |
| `AIDA_MODEL_LOCAL` | No | `` | **YES** | Local model flag |

#### TensorRT-LLM

| Variable | Required | Default | Implemented | Description |
|----------|----------|---------|-------------|-------------|
| `TENSORRT_URL` | Conditional | `None` | **YES** | TensorRT server URL |
| `TENSORRT_BASE_URL` | No | `None` | **YES** | Base URL |
| `TENSORRT_MODEL` | No | `` | **YES** | Default model |
| `TENSORRT_API_KEY` | No | `` | **YES** | API key |
| `TENSORRT_TIMEOUT` | No | `` | **YES** | Request timeout |

#### vLLM

| Variable | Required | Default | Implemented | Description |
|----------|----------|---------|-------------|-------------|
| `VLLM_URL` | Conditional | `None` | **YES** | vLLM server URL |
| `VLLM_BASE_URL` | No | `None` | **YES** | Base URL |
| `VLLM_MODEL` | No | `` | **YES** | Default model |
| `VLLM_API_KEY` | No | `` | **YES** | API key |
| `VLLM_TIMEOUT` | No | `` | **YES** | Request timeout |

#### Provider Selection

| Variable | Required | Default | Implemented | Description |
|----------|----------|---------|-------------|-------------|
| `AIDA_PROVIDER` | No | `auto` | **YES** | Provider: auto, ollama, openai, anthropic, gemini, deepseek, lmstudio, aida_model |
| `AIDA_DEFAULT_MODEL` | No | `` | **YES** | Global default model |
| `AIDA_API_KEY` | No | `` | **YES** | AIDA API access key |
| `MULTI_MODEL_ENABLED` | No | `false` | **YES** | Enable multi-model routing |

### 2.4 Google Services

| Variable | Required | Default | Implemented | Description |
|----------|----------|---------|-------------|-------------|
| `GOOGLE_CSE_API_KEY` | No | `None` | **YES** | Google Custom Search API key |
| `GOOGLE_CSE_ID` | No | `None` | **YES** | Google Custom Search engine ID |

### 2.5 AIDA Runtime

| Variable | Required | Default | Implemented | Description |
|----------|----------|---------|-------------|-------------|
| `AIDA_LOG_LEVEL` | No | `INFO` | **YES** | Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `AIDA_LOG_FORMAT` | No | `text` | **YES** | Log format |
| `AIDA_API_URL` | No | `None` | **YES** | AIDA API base URL |
| `AIDA_MODE` | No | `None` | **YES** | AIDA operation mode |
| `DISABLE_HMR` | No | `false` | **YES** | Disable frontend HMR |

### 2.6 Database (Planned)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | **YES (prod)** | `sqlite:///data/aida.db` | Database connection URL |
| `DATABASE_POOL_SIZE` | No | `5` | Connection pool size |
| `DATABASE_POOL_OVERFLOW` | No | `10` | Max overflow connections |
| `DATABASE_ECHO` | No | `false` | Log all SQL |
| `DATABASE_SSL_MODE` | No | `prefer` | SSL mode for PostgreSQL |

### 2.7 Redis (Planned)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | **YES (prod)** | `redis://localhost:6379/0` | Redis connection URL |
| `REDIS_SOCKET_TIMEOUT` | No | `5` | Socket timeout |
| `REDIS_RETRY_ON_TIMEOUT` | No | `true` | Retry on timeout |
| `REDIS_PASSWORD` | No | `None` | Redis password |
| `REDIS_DB` | No | `0` | Database number |
| `REDIS_PREFIX` | No | `aida:` | Key prefix |

### 2.8 Vector Database (Planned)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VECTOR_DB_PROVIDER` | No | `qdrant` | Provider: qdrant, chroma, pinecone, weaviate, milvus |
| `VECTOR_DB_URL` | **YES (prod)** | `http://localhost:6333` | Vector DB URL |
| `VECTOR_DB_API_KEY` | No | `None` | Cloud vector DB API key |
| `VECTOR_DB_COLLECTION` | No | `aida_vectors` | Collection name |
| `VECTOR_DB_EMBEDDING_DIM` | No | `768` | Embedding dimension |

### 2.9 Embedding Model (Planned)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EMBEDDING_PROVIDER` | No | `ollama` | Provider: ollama, openai, huggingface |
| `EMBEDDING_MODEL` | No | `nomic-embed-text` | Model name |
| `EMBEDDING_DIMENSION` | No | `768` | Vector dimension |

### 2.10 RAG Pipeline (Planned)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RAG_ENABLED` | No | `true` | Enable RAG |
| `RAG_CHUNK_SIZE` | No | `512` | Chunk size (characters) |
| `RAG_CHUNK_OVERLAP` | No | `64` | Chunk overlap |
| `RAG_TOP_K` | No | `5` | Chunks to retrieve |
| `RAG_SIMILARITY_THRESHOLD` | No | `0.75` | Minimum similarity |

### 2.11 Security / JWT (Planned)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET` | **YES (prod)** | `None` | JWT signing secret |
| `JWT_ALGORITHM` | No | `HS256` | Signing algorithm |
| `JWT_ACCESS_TTL` | No | `3600` | Access token TTL |
| `JWT_REFRESH_TTL` | No | `2592000` | Refresh token TTL (30 days) |
| `JWT_ISSUER` | No | `aida` | Token issuer |

### 2.12 OAuth (Planned)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OAUTH_GOOGLE_CLIENT_ID` | No | `None` | Google OAuth client ID |
| `OAUTH_GOOGLE_CLIENT_SECRET` | No | `None` | Google OAuth client secret |
| `OAUTH_GITHUB_CLIENT_ID` | No | `None` | GitHub OAuth client ID |
| `OAUTH_GITHUB_CLIENT_SECRET` | No | `None` | GitHub OAuth client secret |
| `OAUTH_MICROSOFT_CLIENT_ID` | No | `None` | Microsoft OAuth client ID |
| `OAUTH_MICROSOFT_CLIENT_SECRET` | No | `None` | Microsoft OAuth client secret |

### 2.13 SMTP / Email (Planned)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SMTP_HOST` | No | `localhost` | SMTP host |
| `SMTP_PORT` | No | `587` | SMTP port |
| `SMTP_USERNAME` | No | `None` | SMTP username |
| `SMTP_PASSWORD` | No | `None` | SMTP password |
| `SMTP_USE_TLS` | No | `true` | Enable TLS |
| `SMTP_FROM_EMAIL` | No | `noreply@aida.local` | From address |

### 2.14 File Storage (Planned)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `STORAGE_PROVIDER` | No | `local` | Provider: local, s3, gcs, azure |
| `STORAGE_LOCAL_PATH` | No | `data/storage` | Local path |
| `STORAGE_S3_BUCKET` | No | `None` | S3 bucket |
| `STORAGE_S3_REGION` | No | `None` | S3 region |
| `STORAGE_S3_ACCESS_KEY` | No | `None` | S3 access key |
| `STORAGE_S3_SECRET_KEY` | No | `None` | S3 secret key |
| `STORAGE_GCS_BUCKET` | No | `None` | GCS bucket |
| `STORAGE_AZURE_CONTAINER` | No | `None` | Azure container |

### 2.15 Cache (Planned)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CACHE_PROVIDER` | No | `redis` | Provider: redis, memory |
| `CACHE_DEFAULT_TTL` | No | `300` | Default TTL (seconds) |
| `CACHE_MAX_SIZE` | No | `1000` | Max entries (memory) |

### 2.16 Logging (Planned)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LOG_LEVEL` | No | `INFO` | Level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `LOG_FORMAT` | No | `json` | Format: json, text |
| `LOG_FILE` | No | `None` | Log file path |
| `LOG_HANDLERS` | No | `console` | Handlers: console, file, syslog |
| `LOG_QUERIES` | No | `false` | Log database queries |

### 2.17 Monitoring (Planned)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `METRICS_ENABLED` | No | `true` | Enable metrics |
| `METRICS_PORT` | No | `9090` | Metrics endpoint port |
| `METRICS_TRACING` | No | `false` | Enable tracing |
| `METRICS_PROFILER` | No | `false` | Enable profiler |
| `METRICS_EXPORTER` | No | `prometheus` | Exporter: prometheus, datadog, newrelic |

### 2.18 Plugins (Planned)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PLUGIN_ENABLED` | No | `true` | Enable plugin system |
| `PLUGIN_DIRECTORY` | No | `plugins` | Plugin directory |
| `PLUGIN_ALLOW_EXTERNAL` | No | `false` | Allow external plugins |
| `PLUGIN_SANDBOX` | No | `docker` | Sandbox: docker, subprocess, none |

### 2.19 Rate Limits (Planned)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RATE_LIMIT_API_REQUESTS_PER_MIN` | No | `60` | API requests/minute |
| `RATE_LIMIT_API_BURST` | No | `100` | API burst |
| `RATE_LIMIT_CHAT_PER_MIN` | No | `30` | Chat requests/minute |
| `RATE_LIMIT_CHAT_BURST` | No | `50` | Chat burst |
| `RATE_LIMIT_ENABLED` | No | `true` | Enable rate limiting |

### 2.20 CORS & Security (Planned)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CORS_ORIGINS` | No | `*` | Comma-separated allowed origins |
| `ALLOWED_HOSTS` | No | `*` | Comma-separated allowed hosts |
| `SECURE_SSL_REDIRECT` | No | `false` | Force HTTPS redirect |
| `SECURE_HSTS_SECONDS` | No | `0` | HSTS header |
| `SECURE_CONTENT_TYPE_NOSNIFF` | No | `true` | X-Content-Type-Options |

### 2.21 Feature Flags (Planned)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FFLAG_VOICE` | No | `false` | Voice I/O |
| `FFLAG_VISION` | No | `false` | Image processing |
| `FFLAG_RAG` | No | `true` | RAG pipeline |
| `FFLAG_MEMORY` | No | `true` | Conversation memory |
| `FFLAG_AGENTS` | No | `true` | Multi-agent orchestration |
| `FFLAG_DOCKER` | No | `false` | Docker management |
| `FFLAG_GITHUB` | No | `false` | GitHub integration |
| `FFLAG_INTERNET_SEARCH` | No | `false` | Internet search |
| `FFLAG_BROWSER` | No | `false` | Browser automation |
| `FFLAG_AUTO_MODE` | No | `true` | Autonomous mode |

## 3. Implementation Status

| Status | Count | Description |
|--------|-------|-------------|
| **Active** | 32 | Currently implemented in Python code |
| **Planned** | 67 | Documented, ready for implementation |
| **Total** | 99 | Full environment variable surface |

## 4. Environment-Specific Requirements

### 4.1 Development

```bash
# Minimal .env for development
DJANGO_DEBUG=true
DJANGO_SECRET_KEY=dev-secret-key-not-for-production
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8080
AIDA_LOG_LEVEL=DEBUG
AIDA_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
```

### 4.2 Testing

```bash
# .env for test suite
DJANGO_DEBUG=false
DATABASE_URL=sqlite:///:memory:
REDIS_URL=redis://localhost:6379/1
AIDA_LOG_LEVEL=CRITICAL
CACHE_PROVIDER=memory
METRICS_ENABLED=false
```

### 4.3 Staging

```bash
# .env.staging
APP_ENV=staging
APP_DEBUG=false
DATABASE_URL=postgresql://user:pass@staging-db:5432/aida
REDIS_URL=redis://staging-redis:6379/0
VECTOR_DB_URL=http://staging-vector:6333
AIDA_LOG_LEVEL=INFO
SECURE_SSL_REDIRECT=true
JWT_SECRET=<staging-jwt-secret>
```

### 4.4 Production

```bash
# .env.production (gitignored — serverda saqlanadi)
APP_ENV=production
APP_DEBUG=false
APP_SECRET_KEY=<generated-256-bit-key>
DATABASE_URL=postgresql://user:pass@prod-db.internal:5432/aida
REDIS_URL=redis://:pass@prod-redis.internal:6379/0
VECTOR_DB_URL=https://vector.internal:6333
AIDA_LOG_LEVEL=WARNING
SECURE_SSL_REDIRECT=true
CORS_ORIGINS=https://app.example.com
ALLOWED_HOSTS=api.example.com
JWT_SECRET=<generated-256-bit-key>
OPENAI_API_KEY=sk-proj-...
```

## 5. `.env.example` Templates

### 5.1 Root `.env.example`

```bash
# ── AIDA Environment Configuration ─────────────────────────
# Copy to .env and customize

# ── Provider ──────────────────────────────────────
AIDA_PROVIDER=auto

# ── Ollama ────────────────────────────────────────
OLLAMA_ENABLED=true
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_TIMEOUT=120

# ── LM Studio ─────────────────────────────────────
LMSTUDIO_ENABLED=true
LMSTUDIO_URL=http://127.0.0.1:1234
LMSTUDIO_TIMEOUT=120

# ── Google Gemini ─────────────────────────────────
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TIMEOUT=60

# ── OpenAI / Compatible ──────────────────────────
OPENAI_BASE_URL=
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o
OPENAI_TIMEOUT=120

# ── Django ─────────────────────────────────────────
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8080
DJANGO_SECURE_PROXY_SSL_HEADER=false
```

### 5.2 Production `.env.production`

```bash
# ── AIDA Production Configuration ─────────────────
# NEVER COMMIT THIS FILE

# ── Environment ──────────────────────────────────
APP_ENV=production
APP_DEBUG=false
APP_SECRET_KEY=<256-bit-random>

# ── Database ──────────────────────────────────────
DATABASE_URL=postgresql://aida:password@prod-db.internal:5432/aida

# ── Redis ──────────────────────────────────────────
REDIS_URL=redis://:password@prod-redis.internal:6379/0

# ── AI Models ──────────────────────────────────────
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...

# ── Security ──────────────────────────────────────
JWT_SECRET=<256-bit-random>
```

## 6. Implementation Notes

### 6.1 Adding a New Variable

1. Add to `aidaos/infrastructure/config/settings.py` `_load_from_env()` method
2. Add to `.env.example` (git-tracked template)
3. Add to `Environment_Guide.md` reference table
4. Add validation rule in `Validation_Rules.md`
5. Never commit sensitive values to `.env.example` — leave blank

### 6.2 Migration: Active → Standardized

Current active variables use mixed naming (`DJANGO_DEBUG`, `AIDA_LOG_LEVEL`). Target state standardizes to `APP_` prefix convention. During migration, both old and new names are supported (old name takes precedence).
