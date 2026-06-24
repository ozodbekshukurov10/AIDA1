"""
7.1 Docker, 7.2 Kubernetes, 7.3 Performance Tuning.
Uses a provider's respond() callable for LLM-powered assistance.
"""

from typing import Callable


UZBEK_INSTRUCTION = "\n\nJavobni faqat O'ZBEK tilida yoz. Ingliz yoki rus tilida yozma."


class DockerAssistant:
    """7.1 — Multi-stage builds, model caching, resource limits, health checks, graceful shutdown."""

    SYSTEM_PROMPT = (
        "Sen AIDA ning Docker Containerization assistantisan. Docker konteynerizatsiya bo'yicha maslahat ber.\n"
        "Quyidagilarni bajar:\n"
        "1. Multi-stage builds — qadamli qurish, oraliq artefaktlarni tozalash, yakuniy image hajmini kichraytirish\n"
        "2. Model caching — ML model, sozlamalar va kutubxonalarni cache qilish\n"
        "3. Resource limits — CPU, RAM, disk cheklovlari, ulimit, cgroups\n"
        "4. Health checks — HEALTHCHECK, readiness, liveness, startup probe\n"
        "5. Graceful shutdown — SIGTERM, SIGINT, preStop, drain connections\n\n"
        "Natija strukturasi:\n"
        "- Kod/senario: ...\n"
        "- Izoh: ...\n"
        "- Xavfsizlik: ..."
    )

    def __init__(self, respond_func: Callable):
        self.respond = respond_func

    def generate(self, prompt: str, category: str = "") -> str:
        full = f"Topshiriq: {prompt}\n"
        if category:
            full += f"Kategoriya: {category}\n"
        return self.respond(full, [], self.SYSTEM_PROMPT + UZBEK_INSTRUCTION)


class KubernetesAssistant:
    """7.2 — Horizontal scaling, load balancing, auto-restart, resource optimization, monitoring."""

    SYSTEM_PROMPT = (
        "Sen AIDA ning Kubernetes Orchestration assistantisan. K8s klasterini sozlash va optimallashtirish.\n"
        "Quyidagilarni bajar:\n"
        "1. Horizontal scaling — HPA, cluster autoscaler, metrics-server, target CPU/memory\n"
        "2. Load balancing — Service (ClusterIP, NodePort, LoadBalancer), Ingress, nginx-ingress, session stickiness\n"
        "3. Auto-restart — livenessProbe, restartPolicy, pod lifecycle, node failure\n"
        "4. Resource optimization — requests/limits, resource quotas, limit ranges, spot instances, bin packing\n"
        "5. Monitoring & logging — Prometheus, Grafana, Loki, ELK stack, metrics-server, custom metrics\n\n"
        "Natija strukturasi:\n"
        "- YAML/senario: ...\n"
        "- Izoh: ...\n"
        "- Xavfsizlik: ..."
    )

    def __init__(self, respond_func: Callable):
        self.respond = respond_func

    def generate(self, prompt: str, category: str = "") -> str:
        full = f"Topshiriq: {prompt}\n"
        if category:
            full += f"Kategoriya: {category}\n"
        return self.respond(full, [], self.SYSTEM_PROMPT + UZBEK_INSTRUCTION)


class PerformanceTuningAssistant:
    """7.3 — Response caching, batch processing, connection pooling, CDN, metrics."""

    SYSTEM_PROMPT = (
        "Sen AIDA ning Performance Tuning assistantisan. Tizim ishlashini optimallashtirish.\n"
        "Quyidagilarni bajar:\n"
        "1. Response caching — Redis/Memcached, HTTP cache headers (ETag, Cache-Control), CDN cache, browser cache\n"
        "2. Batch processing — bulk operations, chunked processing, queue-based batch (Celery, RabbitMQ, Kafka)\n"
        "3. Connection pooling — database pool (psycopg2, SQLAlchemy), HTTP pool (aiohttp, requests), gRPC pool\n"
        "4. CDN integration — static assets, edge caching, CDN providers (Cloudflare, Akamai, AWS CloudFront)\n"
        "5. Metrics collection — Prometheus endpoints, structured logging, OpenTelemetry, APM, custom metrics\n\n"
        "Natija strukturasi:\n"
        "- Kod/konfiguratsiya: ...\n"
        "- Izoh: ...\n"
        "- Kutulgan natija: ..."
    )

    def __init__(self, respond_func: Callable):
        self.respond = respond_func

    def generate(self, prompt: str, category: str = "") -> str:
        full = f"Topshiriq: {prompt}\n"
        if category:
            full += f"Kategoriya: {category}\n"
        return self.respond(full, [], self.SYSTEM_PROMPT + UZBEK_INSTRUCTION)
