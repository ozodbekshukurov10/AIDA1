"""
6.1 Language Support, 6.2 Framework Integration, 6.3 Version Control.
Uses a provider's respond() callable for LLM-powered assistance.
"""

from typing import Callable


UZBEK_INSTRUCTION = "\n\nJavobni faqat O'ZBEK tilida yoz. Ingliz yoki rus tilida yozma."


class LanguageAssistant:
    """6.1 — Python/Django/FastAPI/Flask, JS/TS/React/Next/Node, Go, Rust, SQL, Shell."""

    SYSTEM_PROMPT = (
        "Sen AIDA ning Language Support assistantisan. Berilgan til va framework bo'yicha kod yoz, tushuntir va maslahat ber.\n"
        "Quyidagi tillar va frameworklarni bilasan:\n"
        "- Python (Django, FastAPI, Flask) — model, view, serializer, URL, middleware\n"
        "- JavaScript/TypeScript (React, Next.js, Node.js) — component, hook, API route, middleware\n"
        "- Go (gin, echo) — handler, router, middleware, struct\n"
        "- Rust (Axum, Actix) — route, handler, state, middleware\n"
        "- SQL (PostgreSQL, MySQL, MongoDB) — schema, query, index, aggregation\n"
        "- Shell/Bash — script, loop, condition, pipe, cron\n\n"
        "Natija strukturasi:\n"
        "- Kod: ...\n"
        "- Izoh: ...\n"
        "- Framework xususiyatlari: ...\n"
        "- Eng yaxshi amaliyotlar: ..."
    )

    def __init__(self, respond_func: Callable):
        self.respond = respond_func

    def generate(self, prompt: str, language: str, framework: str = "") -> str:
        full_prompt = f"Topshiriq: {prompt}\nTil: {language}"
        if framework:
            full_prompt += f"\nFramework: {framework}"
        return self.respond(full_prompt, [], self.SYSTEM_PROMPT + UZBEK_INSTRUCTION)


class FrameworkAssistant:
    """6.2 — Django patterns, React components, REST API, DB migrations, DevOps."""

    SYSTEM_PROMPT = (
        "Sen AIDA ning Framework Integration assistantisan. Framework'larga oid kod va patternlarni yozib ber.\n"
        "Quyidagilarni bajar:\n"
        "1. Django patterns — model, view, serializer, signal, management command, middleware\n"
        "2. React components — functional component, hook, context, HOC, custom hook\n"
        "3. REST API design — endpoint, status code, auth, pagination, versioning, error handling\n"
        "4. Database migrations — schema change, data migration, rollback, index\n"
        "5. DevOps scripts — Dockerfile, CI/CD, deployment, monitoring, backup\n\n"
        "Natija strukturasi:\n"
        "- Kod: ...\n"
        "- Pattern tavsifi: ...\n"
        "- Qo'llanilishi: ...\n"
        "- Alternativlar: ..."
    )

    def __init__(self, respond_func: Callable):
        self.respond = respond_func

    def generate(self, prompt: str, category: str, framework: str = "") -> str:
        full_prompt = f"Topshiriq: {prompt}\nKategoriya: {category}"
        if framework:
            full_prompt += f"\nFramework: {framework}"
        return self.respond(full_prompt, [], self.SYSTEM_PROMPT + UZBEK_INSTRUCTION)


class VersionControlAssistant:
    """6.3 — Git commands, branch strategies, commits, PR templates, releases."""

    SYSTEM_PROMPT = (
        "Sen AIDA ning Version Control assistantisan. Git va versiya nazorati bo'yicha maslahat ber.\n"
        "Quyidagilarni bajar:\n"
        "1. Git commands — git init, add, commit, push, pull, merge, rebase, stash, cherry-pick, bisect\n"
        "2. Branch strategies — GitFlow, GitHub Flow, trunk-based, feature branch, release branch\n"
        "3. Commit messaging — conventional commits, semantic versioning, commit body\n"
        "4. Pull request templates — PR description, checklist, testing, review guide\n"
        "5. Release management — semantic version, changelog, tag, hotfix, release branch\n\n"
        "Natija strukturasi:\n"
        "- Buyruq/maslahat: ...\n"
        "- Izoh: ...\n"
        "- Misol: ...\n"
        "- Xavfsizlik: ..."
    )

    def __init__(self, respond_func: Callable):
        self.respond = respond_func

    def generate(self, prompt: str, category: str) -> str:
        full_prompt = f"Topshiriq: {prompt}\nKategoriya: {category}"
        return self.respond(full_prompt, [], self.SYSTEM_PROMPT + UZBEK_INSTRUCTION)
