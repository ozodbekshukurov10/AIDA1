# AIDA — Enterprise Deployment Configuration

## 1. Environment Profiles

### 1.1 Local Development

**Current `docker-compose.yml`** a single service with Ollama. Below is the evolved multi-service composition.

#### Infrastructure

```yaml
# docker-compose.dev.yml
services:
  aida:
    build: .
    ports:
      - "8000:8000"
      - "3000:3000"
    env_file: .env
    environment:
      - DJANGO_DEBUG=true
      - AIDA_LOG_LEVEL=DEBUG
    volumes:
      - .:/app
      - aida_data:/app/data
      - aida_models:/app/models
      - /var/run/docker.sock:/var/run/docker.sock  # Docker-in-Docker
    depends_on:
      - redis
      - qdrant
    command: python manage.py runserver 0.0.0.0:8000

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    volumes: [redis_data:/data]

  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
    volumes: [qdrant_data:/qdrant/storage]

  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes: [ollama_data:/root/.ollama]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

volumes:
  aida_data:
  aida_models:
  redis_data:
  qdrant_data:
  ollama_data:
```

#### Requirements

| Component | Required | Notes |
|-----------|----------|-------|
| Python 3.11+ | Yes | System or container |
| Docker | Yes | For full experience |
| SQLite | Yes | Zero-config, built-in |
| Redis | Optional | Falls back to in-memory cache |
| Qdrant | Optional | Falls back to in-memory vector store |
| Ollama | Optional | Falls back to cloud model APIs |
| GPU | Optional | NVIDIA + CUDA 12.2 |

### 1.2 Testing

```yaml
# docker-compose.test.yml
services:
  aida-test:
    build: .
    env_file: .env.test
    environment:
      - DJANGO_DEBUG=false
      - DATABASE_URL=sqlite:///:memory:
      - REDIS_URL=redis://redis:6379/1
      - AIDA_LOG_LEVEL=CRITICAL
      - CACHE_PROVIDER=memory
      - METRICS_ENABLED=false
    depends_on:
      - redis-test
    command: python -m pytest tests/ -v

  redis-test:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

### 1.3 Staging

```yaml
# docker-compose.staging.yml
services:
  aida:
    image: registry.example.com/aida:staging
    ports: ["8000:8000"]
    env_file: .env.staging
    environment:
      - APP_ENV=staging
      - APP_DEBUG=false
    secrets:
      - app_secret_key
      - jwt_secret
    depends_on:
      - redis
      - qdrant
      - postgres
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 2
      resources:
        limits: {cpus: "2", memory: "4G"}

  worker:
    image: registry.example.com/aida:staging
    env_file: .env.staging
    secrets:
      - app_secret_key
    depends_on: [redis, qdrant, postgres]
    command: celery -A aida.infrastructure.task_queue worker --loglevel=info --concurrency=4
    deploy:
      replicas: 2
      resources:
        limits: {cpus: "4", memory: "8G"}

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=aida
      - POSTGRES_USER=aida
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
    volumes: [postgres_data:/var/lib/postgresql/data]
    secrets:
      - db_password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aida"]
      interval: 10s

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes: [redis_data:/data]
    deploy:
      resources: {limits: {cpus: "1", memory: "2G"}}

  qdrant:
    image: qdrant/qdrant:latest
    volumes: [qdrant_data:/qdrant/storage]
    deploy:
      resources: {limits: {cpus: "2", memory: "4G"}}

  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - frontend_dist:/usr/share/nginx/html
    depends_on: [aida]

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  frontend_dist:

secrets:
  app_secret_key: {file: ./secrets/app_secret_key.txt}
  jwt_secret: {file: ./secrets/jwt_secret.txt}
  db_password: {file: ./secrets/db_password.txt}
```

### 1.4 Production

```yaml
# docker-compose.prod.yml
services:
  aida:
    image: registry.example.com/aida:${AIDA_VERSION}
    ports: ["8000:8000"]
    environment:
      - APP_ENV=production
      - APP_DEBUG=false
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    secrets:
      - app_secret_key
      - jwt_secret
      - openai_api_key
    depends_on: [redis, qdrant, postgres]
    deploy:
      replicas: 3
      resources:
        limits: {cpus: "2", memory: "4G"}
        reservations: {cpus: "1", memory: "2G"}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options: {max-size: "10m", max-file: "3"}

  worker:
    image: registry.example.com/aida:${AIDA_VERSION}
    environment:
      - APP_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    secrets:
      - app_secret_key
      - openai_api_key
    command: celery -A aida.infrastructure.task_queue worker --loglevel=warning --concurrency=4
    deploy:
      replicas: 3
      resources:
        limits: {cpus: "4", memory: "8G"}
        reservations: {cpus: "2", memory: "4G"}

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=aida
      - POSTGRES_USER=aida
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
    volumes: [postgres_data:/var/lib/postgresql/data]
    secrets:
      - db_password
    deploy:
      resources: {limits: {cpus: "2", memory: "4G"}}

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes: [redis_data:/data]
    deploy:
      resources: {limits: {cpus: "1", memory: "2G"}}

  qdrant:
    image: qdrant/qdrant:latest
    volumes: [qdrant_data:/qdrant/storage]
    deploy:
      resources: {limits: {cpus: "2", memory: "4G"}}

  prometheus:
    image: prom/prometheus:latest
    volumes: [./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml]
    ports: ["9090:9090"]
    deploy: {resources: {limits: {cpus: "0.5", memory: "1G"}}}

  grafana:
    image: grafana/grafana:latest
    ports: ["3001:3000"]
    volumes: [grafana_data:/var/lib/grafana]
    deploy: {resources: {limits: {cpus: "0.5", memory: "1G"}}}

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  grafana_data:

secrets:
  app_secret_key: {external: true}
  jwt_secret: {external: true}
  openai_api_key: {external: true}
  db_password: {external: true}
```

## 2. Kubernetes Configuration

### 2.1 Namespace

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: aida
```

### 2.2 ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aida-config
  namespace: aida
data:
  APP_ENV: "production"
  APP_NAME: "AIDA"
  APP_VERSION: "1.0.0"
  APP_DEBUG: "false"
  APP_PORT: "8000"
  AIDA_LOG_LEVEL: "WARNING"
  AIDA_LOG_FORMAT: "json"
  CACHE_PROVIDER: "redis"
  RAG_ENABLED: "true"
  VECTOR_DB_PROVIDER: "qdrant"
  VECTOR_DB_URL: "http://qdrant:6333"
  REDIS_URL: "redis://redis:6379/0"
  CORS_ORIGINS: "https://app.example.com"
  ALLOWED_HOSTS: "api.example.com"
```

### 2.3 SealedSecret (GitOps safe)

```yaml
# k8s/sealedsecret.yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: aida-secrets
  namespace: aida
spec:
  encryptedData:
    APP_SECRET_KEY: AgBy3z4y...      # encrypted with cluster public key
    JWT_SECRET: AgBx7w2q...          # encrypted
    OPENAI_API_KEY: AgCv5u8r...      # encrypted
    DATABASE_URL: AgDn1m4p...        # encrypted
```

### 2.4 Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aida-api
  namespace: aida
spec:
  replicas: 3
  strategy:
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
    type: RollingUpdate
  selector:
    matchLabels:
      app: aida-api
  template:
    metadata:
      labels:
        app: aida-api
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
    spec:
      containers:
        - name: api
          image: registry.example.com/aida:1.0.0
          ports:
            - containerPort: 8000
              name: http
            - containerPort: 9090
              name: metrics
          envFrom:
            - configMapRef:
                name: aida-config
            - secretRef:
                name: aida-secrets
          resources:
            requests: {cpu: "500m", memory: "1Gi"}
            limits: {cpu: "2", memory: "4Gi"}
          livenessProbe:
            httpGet: {path: /health, port: 8000}
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet: {path: /ready, port: 8000}
            initialDelaySeconds: 5
            periodSeconds: 5
          volumeMounts:
            - name: data
              mountPath: /app/data
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: aida-data-pvc
      imagePullSecrets:
        - name: registry-credentials
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aida-worker
  namespace: aida
spec:
  replicas: 2
  selector:
    matchLabels:
      app: aida-worker
  template:
    metadata:
      labels:
        app: aida-worker
    spec:
      containers:
        - name: worker
          image: registry.example.com/aida:1.0.0
          command: ["celery", "-A", "aida.infrastructure.task_queue", "worker"]
          args: ["--loglevel=warning", "--concurrency=4"]
          envFrom:
            - configMapRef:
                name: aida-config
            - secretRef:
                name: aida-secrets
          resources:
            requests: {cpu: "1", memory: "2Gi"}
            limits: {cpu: "4", memory: "8Gi"}
```

### 2.5 Service

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: aida-api
  namespace: aida
spec:
  selector:
    app: aida-api
  ports:
    - name: http
      port: 80
      targetPort: 8000
    - name: metrics
      port: 9090
      targetPort: 9090
  type: ClusterIP
```

### 2.6 Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: aida-ingress
  namespace: aida
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts: [api.example.com]
      secretName: aida-tls
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: aida-api
                port:
                  name: http
```

### 2.7 PersistentVolumeClaim

```yaml
# k8s/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: aida-data-pvc
  namespace: aida
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
```

## 3. Cloud Deployment

### 3.1 AWS (ECS / EKS)

| Service | AIDA Component | Notes |
|---------|---------------|-------|
| **ECS Fargate / EKS** | API + Worker | Container orchestration |
| **RDS PostgreSQL** | Database | HA with Multi-AZ |
| **ElastiCache Redis** | Cache + Queue | Cluster mode enabled |
| **S3** | File storage | Static assets + uploads |
| **Secrets Manager** | Secret storage | All CRITICAL/HIGH secrets |
| **CloudWatch** | Logging + Metrics | Log groups + dashboards |
| **ALB** | Load balancing | TLS termination |
| **ECR** | Container registry | Private image repository |
| **Route53** | DNS | api.example.com → ALB |
| **WAF** | Security | Rate limiting + IP filtering |

```hcl
# terraform/aws/main.tf (abridged)
resource "aws_ecs_service" "aida_api" {
  name            = "aida-api"
  cluster         = aws_ecs_cluster.aida.id
  task_definition = aws_ecs_task_definition.aida_api.arn
  desired_count   = 3

  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.aida_api.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.aida.arn
    container_name   = "aida-api"
    container_port   = 8000
  }
}
```

### 3.2 Google Cloud (Cloud Run + GKE)

| Service | AIDA Component | Notes |
|---------|---------------|-------|
| **Cloud Run** | API | Serverless, auto-scale |
| **GKE** | Worker | If Cloud Run doesn't fit |
| **Cloud SQL** | PostgreSQL | Managed, HA |
| **Memorystore** | Redis | Managed |
| **GCS** | File storage | Bucket for uploads |
| **Secret Manager** | Secret storage | All secrets |
| **Cloud Logging** | Logging | Structured logs |

### 3.3 Azure (AKS)

| Service | AIDA Component | Notes |
|---------|---------------|-------|
| **AKS** | API + Worker | Kubernetes |
| **Azure Database** | PostgreSQL | Flexible Server |
| **Azure Cache** | Redis | Premium tier |
| **Blob Storage** | File storage | Hot tier |
| **Key Vault** | Secret storage | RBAC + soft-delete |
| **Monitor** | Logging + Metrics | Container insights |

## 4. Environment Comparison Matrix

| Component | Development | Testing | Staging | Production |
|-----------|-------------|---------|---------|------------|
| **Python** | 3.11+ | 3.11+ | 3.11+ (container) | 3.11+ (container) |
| **Database** | SQLite | SQLite (:memory:) | PostgreSQL 15+ | PostgreSQL 15+ HA |
| **Redis** | Optional | Required (DB 1) | Required | Required (HA) |
| **Vector DB** | Optional / Qdrant | Mocked | Qdrant | Qdrant/Pinecone HA |
| **Ollama** | Local / Container | Mocked | Local/Cloud | Cloud only |
| **Model API** | Mock/Ollama | Mocked | Ollama + Cloud | Cloud (OpenAI, etc.) |
| **Cache** | In-memory | In-memory | Redis | Redis cluster |
| **Logging** | stdout text | JSON muted | JSON → file | JSON → CloudWatch |
| **Metrics** | Disabled | Disabled | Prometheus | Prometheus + Grafana |
| **Tracing** | Disabled | Disabled | Jaeger | Jaeger (sampled) |
| **Secrets** | `.env` | `.env.test` | Vault | Vault (prod) |
| **Replicas** | 1 | 1 | 2 | 3+ |
| **SSL** | No | No | Yes (LetsEncrypt) | Yes (TLS 1.3) |
| **Auth** | None | None | SSO | SSO + MFA |
| **Container** | Docker Compose | Docker Compose | Docker Compose / K8s | Kubernetes |
| **Monitoring** | None | None | Basic | Full (P+G) |

## 5. Docker Best Practices

### 5.1 Image Building

```dockerfile
# Multi-stage build (current Dockerfile is single-stage — target state)
FROM python:3.11-slim AS builder
COPY requirements.txt .
RUN pip install --user --no-cache-deps -r requirements.txt

FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04 AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3-pip curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY . /app
WORKDIR /app
EXPOSE 8000 3000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### 5.2 .dockerignore

```gitignore
.git
__pycache__
.env
.env.*
!.env.example
db.sqlite3
node_modules
dist
.venv
data/
logs/
*.md
tests/
```

## 6. Startup Validation

Each environment runs configuration validation on startup:

```bash
# Manual validation
aida config validate --environment production

# On server start (automatic)
[BOOT] Running configuration validation...
[BOOT]   ✓ app.secret_key is set
[BOOT]   ✓ database.url is set
[BOOT]   ✓ redis.url is set
[BOOT]   ✓ jwt_secret is set
[BOOT]   ✓ openai_api_key is set
[BOOT]   ✓ Database connection successful (6ms)
[BOOT]   ✓ Redis connection successful (3ms)
[BOOT]   ✓ Vector DB connection successful (12ms)
[BOOT] Configuration validation PASSED
```

## 7. Migration Path: Current → Target

| Step | Change | Impact |
|------|--------|--------|
| 0 | Single Dockerfile + docker-compose.yml | Current state |
| 1 | Add multi-stage Dockerfile | Smaller images, faster builds |
| 2 | Add docker-compose.dev.yml with Redis + Qdrant | Full local stack |
| 3 | Add docker-compose.prod.yml with workers | Production-ready |
| 4 | Create k8s/ directory with manifests | Kubernetes support |
| 5 | Add Terraform for cloud deployments | Infrastructure as Code |
| 6 | Add Helm chart | Configurable K8s deployments |
