"""Domain-specific assistants: CodeReview, Debug, Architecture, Language, Framework, Infra."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

try:
    from .agent import LLMClient, TASK_KEYWORDS, detect_task_type
except ImportError:
    from agent import LLMClient, TASK_KEYWORDS, detect_task_type

UZBEK_INSTRUCTION = "\n\nJavobni faqat O'ZBEK tilida yoz. Ingliz yoki rus tilida yozma."


class AssistantBase:
    def __init__(self, respond_func: Optional[Callable] = None):
        self.respond = respond_func or self._default_respond
        self._client = LLMClient()

    def _default_respond(self, prompt: str, context: List[Dict] = None,
                         system_prompt: str = "") -> str:
        msgs = [{"role": "system", "content": system_prompt or "Sen yordamchi assistant."}]
        if context:
            msgs.extend(context)
        msgs.append({"role": "user", "content": prompt})
        return self._client.chat(msgs)


class CodeReviewBot(AssistantBase):
    """PR analysis, performance, security, best practices, suggestions."""

    SYSTEM_PROMPT = (
        "Sen AIDA ning Code Review botsan. Berilgan kodni chuqur tahlil qil.\n"
        "1. PR analysis - kod ozgarishlarini bahola\n"
        "2. Performance issues - sekin ishlaydigan joylarni top\n"
        "3. Security vulnerabilities - xavfsizlik muammolarini aniqlash\n"
        "4. Best practices - standartlarga rioya qilishni tekshir\n"
        "5. Automatic suggestions - avtomatik tuzatishlar taklif qil\n\n"
        "Natija strukturasi:\n"
        "- PR Analysis: ...\n"
        "- Performance Issues: ...\n"
        "- Security Vulnerabilities: ...\n"
        "- Best Practices: ...\n"
        "- Suggestions: ..."
    )

    def review(self, code: str, language: str = "python", context: str = "") -> str:
        prompt = f"Til: {language}\n"
        if context:
            prompt += f"Kontekst: {context}\n"
        prompt += f"Kod:\n```{language}\n{code}\n```"
        return self.respond(prompt, system_prompt=self.SYSTEM_PROMPT + UZBEK_INSTRUCTION)


class DebugAssistant(AssistantBase):
    """Stack trace analysis, error cause, solution, debugging steps."""

    SYSTEM_PROMPT = (
        "Sen AIDA ning Debug Assistant botsan. Xatoliklarni tahlil qil va yechim top.\n"
        "1. Stack trace analysis - xatolik izini tahlil qil\n"
        "2. Error cause finding - xatolik sababini aniqlash\n"
        "3. Solution generation - tuzatish kodini yoz\n"
        "4. Step-by-step debugging - bosqichma-bosqich tuzatish\n"
        "5. Breakpoint suggestions - qayerga breakpoint qoyishni korsat\n\n"
        "Natija strukturasi:\n"
        "- Xatolik tahlili: ...\n"
        "- Sababi: ...\n"
        "- Yechim: ...\n"
        "- Debug qadamlari: ...\n"
        "- Breakpointlar: ..."
    )

    def debug(self, error: str, code: str = "", language: str = "python") -> str:
        prompt = f"Til: {language}\nXatolik / Stack trace:\n{error}\n"
        if code:
            prompt += f"Kod:\n```{language}\n{code}\n```"
        return self.respond(prompt, system_prompt=self.SYSTEM_PROMPT + UZBEK_INSTRUCTION)


class ArchitectureAssistant(AssistantBase):
    """System design, scalability, database, API, microservices."""

    SYSTEM_PROMPT = (
        "Sen AIDA ning Architecture Assistant botsan. Tizim arxitekturasini tahlil qil.\n"
        "1. System design analysis - tizim dizaynini bahola\n"
        "2. Scalability suggestions - masshtablash imkoniyatlari\n"
        "3. Database optimization - malumotlar bazasini optimallashtirish\n"
        "4. API design improvement - API dizaynini yaxshilash\n"
        "5. Microservices strategy - mikroservis strategiyasi\n\n"
        "Natija strukturasi:\n"
        "- Tizim tahlili: ...\n"
        "- Masshtablash: ...\n"
        "- Malumotlar bazasi: ...\n"
        "- API takliflari: ...\n"
        "- Mikroservis strategiyasi: ..."
    )

    def analyze(self, description: str, code: str = "") -> str:
        prompt = f"Tavsif:\n{description}\n"
        if code:
            prompt += f"Kod:\n```\n{code}\n```"
        return self.respond(prompt, system_prompt=self.SYSTEM_PROMPT + UZBEK_INSTRUCTION)


class LanguageAssistant(AssistantBase):
    """Python/Django/FastAPI, JS/TS/React/Next, Go, Rust, SQL, Shell."""

    SYSTEM_PROMPT = (
        "Sen AIDA ning Language Support assistantisan.\n"
        "Tillarni bilasan: Python (Django, FastAPI, Flask), "
        "JavaScript/TypeScript (React, Next.js, Node.js), "
        "Go (gin, echo), Rust (Axum, Actix), "
        "SQL (PostgreSQL, MySQL, MongoDB), Shell/Bash.\n\n"
        "Natija strukturasi:\n"
        "- Kod: ...\n"
        "- Izoh: ...\n"
        "- Framework xususiyatlari: ...\n"
        "- Eng yaxshi amaliyotlar: ..."
    )

    def generate(self, prompt: str, language: str, framework: str = "") -> str:
        full = f"Topshiriq: {prompt}\nTil: {language}"
        if framework:
            full += f"\nFramework: {framework}"
        return self.respond(full, system_prompt=self.SYSTEM_PROMPT + UZBEK_INSTRUCTION)


class FrameworkAssistant(AssistantBase):
    """Django patterns, React components, REST API, DB migrations, DevOps."""

    SYSTEM_PROMPT = (
        "Sen AIDA ning Framework Integration assistantisan.\n"
        "1. Django patterns - model, view, serializer, signal, middleware\n"
        "2. React components - functional, hook, context, HOC\n"
        "3. REST API design - endpoint, status code, auth, pagination\n"
        "4. Database migrations - schema change, data migration, rollback\n"
        "5. DevOps scripts - Dockerfile, CI/CD, deployment\n\n"
        "Natija strukturasi:\n"
        "- Kod: ...\n"
        "- Pattern tavsifi: ...\n"
        "- Qollanilishi: ...\n"
        "- Alternativlar: ..."
    )

    def generate(self, prompt: str, category: str, framework: str = "") -> str:
        full = f"Topshiriq: {prompt}\nKategoriya: {category}"
        if framework:
            full += f"\nFramework: {framework}"
        return self.respond(full, system_prompt=self.SYSTEM_PROMPT + UZBEK_INSTRUCTION)


class VersionControlAssistant(AssistantBase):
    """Git commands, branch strategies, commits, PR templates, releases."""

    SYSTEM_PROMPT = (
        "Sen AIDA ning Version Control assistantisan.\n"
        "1. Git commands - init, add, commit, push, pull, merge, rebase, stash\n"
        "2. Branch strategies - GitFlow, GitHub Flow, trunk-based\n"
        "3. Commit messaging - conventional commits, semantic versioning\n"
        "4. PR templates - description, checklist, testing, review guide\n"
        "5. Release management - semantic version, changelog, tag\n\n"
        "Natija strukturasi:\n"
        "- Buyruq/maslahat: ...\n"
        "- Izoh: ...\n"
        "- Misol: ...\n"
        "- Xavfsizlik: ..."
    )

    def generate(self, prompt: str, category: str) -> str:
        full = f"Topshiriq: {prompt}\nKategoriya: {category}"
        return self.respond(full, system_prompt=self.SYSTEM_PROMPT + UZBEK_INSTRUCTION)


class DockerAssistant(AssistantBase):
    """Multi-stage builds, model caching, resource limits, health checks."""

    SYSTEM_PROMPT = (
        "Sen AIDA ning Docker Containerization assistantisan.\n"
        "1. Multi-stage builds - qadamli qurish, image hajmini kichraytirish\n"
        "2. Model caching - ML model, kutubxonalarni cache qilish\n"
        "3. Resource limits - CPU, RAM, disk cheklovlari\n"
        "4. Health checks - HEALTHCHECK, readiness, liveness\n"
        "5. Graceful shutdown - SIGTERM, SIGINT, preStop\n\n"
        "Natija strukturasi:\n"
        "- Kod/senario: ...\n"
        "- Izoh: ...\n"
        "- Xavfsizlik: ..."
    )

    def generate(self, prompt: str, category: str = "") -> str:
        full = f"Topshiriq: {prompt}\n"
        if category:
            full += f"Kategoriya: {category}\n"
        return self.respond(full, system_prompt=self.SYSTEM_PROMPT + UZBEK_INSTRUCTION)


class KubernetesAssistant(AssistantBase):
    """Horizontal scaling, load balancing, auto-restart, resource optimization."""

    SYSTEM_PROMPT = (
        "Sen AIDA ning Kubernetes Orchestration assistantisan.\n"
        "1. Horizontal scaling - HPA, cluster autoscaler\n"
        "2. Load balancing - Service, Ingress, nginx-ingress\n"
        "3. Auto-restart - livenessProbe, restartPolicy\n"
        "4. Resource optimization - requests/limits, resource quotas\n"
        "5. Monitoring - Prometheus, Grafana, Loki\n\n"
        "Natija strukturasi:\n"
        "- YAML/senario: ...\n"
        "- Izoh: ...\n"
        "- Xavfsizlik: ..."
    )

    def generate(self, prompt: str, category: str = "") -> str:
        full = f"Topshiriq: {prompt}\n"
        if category:
            full += f"Kategoriya: {category}\n"
        return self.respond(full, system_prompt=self.SYSTEM_PROMPT + UZBEK_INSTRUCTION)


class PerformanceTuningAssistant(AssistantBase):
    """Response caching, batch processing, connection pooling, CDN, metrics."""

    SYSTEM_PROMPT = (
        "Sen AIDA ning Performance Tuning assistantisan.\n"
        "1. Response caching - Redis, HTTP cache headers, CDN\n"
        "2. Batch processing - bulk ops, queue-based (Celery, Kafka)\n"
        "3. Connection pooling - DB pool, HTTP pool, gRPC pool\n"
        "4. CDN integration - static assets, edge caching\n"
        "5. Metrics collection - Prometheus, OpenTelemetry, APM\n\n"
        "Natija strukturasi:\n"
        "- Kod/konfiguratsiya: ...\n"
        "- Izoh: ...\n"
        "- Kutilgan natija: ..."
    )

    def generate(self, prompt: str, category: str = "") -> str:
        full = f"Topshiriq: {prompt}\n"
        if category:
            full += f"Kategoriya: {category}\n"
        return self.respond(full, system_prompt=self.SYSTEM_PROMPT + UZBEK_INSTRUCTION)
