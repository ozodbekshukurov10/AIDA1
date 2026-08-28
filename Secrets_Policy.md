# AIDA — Enterprise Secrets Management Policy

## 1. Core Principles

### 1.1 Zero Secrets in Source Code

```python
# ❌ FORBIDDEN
OPENAI_API_KEY = "sk-proj-abc123..."
DATABASE_URL = "postgresql://admin:password123@localhost:5432/aida"

# ✅ CORRECT — environment variables
import os
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# ✅ CORRECT — config system
from aidaos.infrastructure.config import get_settings
config = get_settings()
api_key = config.openai.api_key
```

### 1.2 Zero Secrets in Git

`.gitignore` himoyasi:

```gitignore
# Core environment files
.env
.env.*
!.env.example

# Local config overrides
aida/config/local.yaml
aida/config/secrets.yaml
**/secrets.yaml

# Credential files
*.key
*.pem
credentials.json
service-account.json
*.cred
*.credential

# IDE/editor secrets
.idea/
.vscode/
```

### 1.3 Zero Secrets in Logs

```python
# ❌ FORBIDDEN
logger.info(f"Connecting to {db_url}")       # db_url ichida password
logger.debug(config.to_dict())                # config ichida API keys

# ✅ CORRECT
from aidaos.infrastructure.config.utils import redact_secrets
safe_config = redact_secrets(config.to_dict())
logger.debug(f"Config loaded: {safe_config}")
```

## 2. Secret Classification

| Level | Examples | Storage | Access | Rotation |
|-------|----------|---------|--------|----------|
| **CRITICAL** | `APP_SECRET_KEY`, `JWT_SECRET`, `DJANGO_SECRET_KEY` | Vault only (prod), auto-generated fallback (dev) | Platform owner | Every 6 months |
| **HIGH** | `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DATABASE_URL`, `GEMINI_API_KEY` | Vault (prod), `.env` (dev) | Team lead + DevOps | Every 12 months |
| **MEDIUM** | `OAUTH_CLIENT_SECRET`, `SMTP_PASSWORD`, `STORAGE_S3_SECRET_KEY`, `VECTOR_DB_API_KEY` | Vault (prod), `.env` (dev) | Developers | Every 12 months |
| **LOW** | `OLLAMA_URL` (local), `REDIS_URL` (dev), `AIDA_API_KEY` | `.env` | All developers | On incident |

## 3. Secret Resolution Order

```
1. Runtime API overrides          ← Highest precedence (session/temporary)
2. Secrets Vault                  ← HashiCorp Vault / AWS SM / Azure KV
3. Environment variables          ← OS env + .env files
4. local.yaml / secrets.yaml      ← Gitignored local files
5. Base config defaults           ← Dataclass defaults (lowest)
```

## 4. Current Implementation Analysis

### 4.1 What Works Today

| Mechanism | Status | Location |
|-----------|--------|----------|
| `.gitignore` .env protection | ✅ Active | `.gitignore` lines 15-16 |
| Django secret key auto-generation | ✅ Active | `AIDA/settings.py:18` |
| API key generation (`secrets.token_urlsafe`) | ✅ Active | `webapp/security.py` |
| Hardcoded secret detection in quality checks | ✅ Active | `webapp/repo_analyzer/quality.py:184` |
| Security audit agent | ✅ Active | `webapp/agents/security_agent.py` |

### 4.2 What Needs Implementation

| Mechanism | Priority | Target |
|-----------|----------|--------|
| HashiCorp Vault integration | High | Phase 2 |
| AWS Secrets Manager integration | Medium | Phase 3 |
| Secret redaction in logging | High | Phase 1 |
| Pre-commit hooks (gitleaks) | Medium | Phase 2 |
| CI/CD secret scanning gates | Medium | Phase 2 |
| Secret rotation CLI commands | Low | Phase 3 |

## 5. Implementation Patterns

### 5.1 HashiCorp Vault Integration

```python
# aida/config/sources/vault_source.py
import hvac

class VaultSource:
    def __init__(self, optional=False):
        self._client = hvac.Client(
            url=os.environ.get("VAULT_ADDR", "http://vault:8200"),
            token=os.environ.get("VAULT_TOKEN"),
        )
        self._optional = optional

    def load(self) -> dict:
        try:
            secret = self._client.secrets.kv.v2.read_secret_version(
                mount_point="aida",
                path="config",
            )
            return secret["data"]["data"]
        except Exception:
            if not self._optional:
                raise
            return {}
```

### 5.2 AWS Secrets Manager Integration

```python
# aida/config/sources/aws_secrets_source.py
import boto3
import json

class AWSSecretsSource:
    def __init__(self, secret_name="aida/production", region="us-east-1"):
        self._secret_name = secret_name
        self._region = region

    def load(self) -> dict:
        client = boto3.client("secretsmanager", region_name=self._region)
        try:
            response = client.get_secret_value(SecretId=self._secret_name)
            return json.loads(response["SecretString"])
        except Exception:
            return {}
```

### 5.3 Secret Redaction Utility

```python
# aidaos/infrastructure/config/utils.py
import re

SECRET_PATTERNS = [
    r"(api_key|apikey|token|secret|password|passwd)\s*[:=]\s*['\"][^'\"]+['\"]',
    r"(sk-[a-zA-Z0-9]{20,})",                # OpenAI keys
    r"(sk-ant-[a-zA-Z0-9]{20,})",            # Anthropic keys
    r"(AIza[0-9A-Za-z\-_]{35})",             # Google API keys
    r"(ghp_[0-9a-zA-Z]{36})",                # GitHub tokens
]

def redact_secrets(data: dict, redact_str: str = "***REDACTED***") -> dict:
    """Recursively redact known secret patterns from a dict."""
    if isinstance(data, dict):
        return {k: redact_secrets(v, redact_str) for k, v in data.items()}
    if isinstance(data, str):
        for pattern in SECRET_PATTERNS:
            data = re.sub(pattern, redact_str, data, flags=re.IGNORECASE)
        return data
    return data
```

### 5.4 Current AIDASettings Redaction

`aidaos/infrastructure/config/settings.py:176` — `to_dict()` already redacts:

```python
def to_dict(self) -> dict[str, Any]:
    return {
        "openai_configured": bool(self.openai.api_key),  # Boolean, not the actual key
        "anthropic_configured": bool(self.anthropic.api_key),
        # ...
    }
```

## 6. Secret Injection Methods

### 6.1 Docker Compose

```yaml
services:
  aida:
    image: aida:latest
    env_file:
      - .env
    secrets:
      - db_password
      - jwt_secret
      - openai_api_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt
  openai_api_key:
    file: ./secrets/openai_api_key.txt
```

### 6.2 Kubernetes

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: SealedSecret      # SealedSecrets for GitOps
metadata:
  name: aida-secrets
spec:
  encryptedData:
    OPENAI_API_KEY: AgBy3z4y...  # encrypted
    DATABASE_URL: AgBx7w2q...    # encrypted

# k8s/deployment.yaml
spec:
  containers:
    - name: aida
      envFrom:
        - secretRef:
            name: aida-secrets
```

### 6.3 HashiCorp Vault Agent Sidecar (K8s)

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "aida"
  vault.hashicorp.com/agent-inject-secret-config: "aida/data/config"
```

## 7. Secret Rotation

### 7.1 Rotation Schedule

| Secret | Frequency | Method | Downtime |
|--------|-----------|--------|----------|
| `DJANGO_SECRET_KEY` | Every 6 months | Generate new, update env/vault | Rolling restart |
| `JWT_SECRET` | Every 3 months | Dual-key period (see below) | Zero |
| `OPENAI_API_KEY` | On incident / 12 months | Regenerate in dashboard | None |
| `ANTHROPIC_API_KEY` | On incident / 12 months | Regenerate in dashboard | None |
| `DATABASE_URL` | On incident / 12 months | Rotate DB creds, update vault | Connection drain |
| `OAUTH_CLIENT_SECRET` | On incident / 12 months | Regenerate in provider | None |
| `AIDA_API_KEY` | Every 6 months | `secrets.token_urlsafe(30)` | None |

### 7.2 Zero-Downtime JWT Rotation

```python
# Support dual-key period during rotation
OLD_SECRET = get_secret("jwt_secret_old")   # exists during rotation window
NEW_SECRET = get_secret("jwt_secret")        # current active secret

def verify_token(token):
    try:
        return jwt.decode(token, NEW_SECRET)
    except jwt.InvalidTokenError:
        return jwt.decode(token, OLD_SECRET)  # fallback to old
```

Procedure:
1. Set `JWT_SECRET` to new value, `JWT_SECRET_OLD` to current value
2. Deploy — all new tokens use new secret, old tokens still valid
3. After 2x token TTL (e.g., 2 hours for 1h TTL), remove `JWT_SECRET_OLD`
4. All tokens now use new secret

## 8. Secret Detection Pipeline

### 8.1 Pre-Commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

### 8.2 CI/CD Gate

```yaml
jobs:
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: GitLeaks
        uses: gitleaks/gitleaks-action@v2
      - name: TruffleHog
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.before }}
          head: ${{ github.sha }}
```

### 8.3 Runtime Detection (Existing)

`webapp/repo_analyzer/quality.py:184` already detects hardcoded secrets in code being analyzed:

```python
HARDCODED_SECRET_PATTERN = re.compile(
    r'(secret|api_key|apikey|token)\s*=\s*["\'][^"\']+["\']',
    re.IGNORECASE
)
```

## 9. Secrets in Transit and at Rest

| State | Requirement | Implementation |
|-------|-------------|----------------|
| At rest (vault) | Encrypted AES-256 | Vault auto-encrypts |
| At rest (`.env`) | File permissions 600 | `chmod 600 .env` |
| In transit | TLS 1.3 | HTTPS for all external APIs |
| In memory | Minimize lifetime | Clear variables after use |
| In logs | Redacted | `redact_secrets()` utility |
| In error messages | Redacted | `SecretRedactingFormatter` |
| In dumps/backups | Excluded | `.gitignore` + backup filters |

## 10. Emergency Secret Rotation

```bash
# CLI command (planned)
aida secrets rotate --service openai --reason "suspected_compromise"
aida secrets rotate --service database --reason "scheduled"
aida secrets rotate --service jwt --reason "rotation_policy"
```

## 11. Audit Trail

Every secret access and rotation is logged:

```json
{
  "event": "secret_accessed",
  "key": "models.openai.api_key",
  "service": "ModelGateway",
  "request_id": "req-abc123",
  "timestamp": "2026-07-03T12:00:00Z"
}
```

```json
{
  "event": "secret_rotated",
  "key": "jwt_secret",
  "reason": "rotation_policy",
  "initiated_by": "devops@example.com",
  "timestamp": "2026-07-03T12:00:00Z"
}
```

## 12. Compliance Matrix

| Standard | Requirement | AIDA Implementation |
|----------|-------------|---------------------|
| SOC 2 | Access control | Vault policies + IAM roles |
| GDPR | Data minimization | Secrets segregated from config |
| HIPAA | Encryption at rest | Vault AES-256 + TLS 1.3 |
| PCI DSS | Key rotation | Automated rotation schedules |
| ISO 27001 | Audit logging | Full secret audit trail |
| OWASP | No hardcoded secrets | Pre-commit hooks + CI/CD scanning |

## 13. Secret Health Checklist

```
[ ] .env files in .gitignore (verified)
[ ] Auto-generated fallback for DJANGO_SECRET_KEY (verified)
[ ] No hardcoded API keys in source code (scan required)
[ ] to_dict() redacts secrets (verified: boolean only)
[ ] Secret scanning in quality checks (verified)
[ ] Security agent audits for secrets (verified)
[ ] Pre-commit hooks configured (pending)
[ ] CI/CD secret scanning gates (pending)
[ ] Vault integration configured (pending)
[ ] Log redaction utility (pending)
[ ] Rotation schedule documented (this document)
[ ] Emergency rotation procedure documented (this document)
```
