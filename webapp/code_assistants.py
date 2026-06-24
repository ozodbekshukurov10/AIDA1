"""
Code Review, Debug, and Architecture assistants.
Uses a provider's respond() callable for LLM-powered analysis.
"""

import json
from typing import Callable, Optional


UZBEK_INSTRUCTION = "\n\nJavobni faqat O'ZBEK tilida yoz. Ingliz yoki rus tilida yozma."


class CodeReviewBot:
    """5.1 PR analysis, performance, security, best practices, suggestions."""

    SYSTEM_PROMPT = (
        "Sen AIDA ning Code Review botsan. Berilgan kodni chuqur tahlil qil."
        "Quyidagilarni tekshir:\n"
        "1. PR analysis - kod o'zgarishlarini bahola\n"
        "2. Performance issues - sekin ishlaydigan joylarni top\n"
        "3. Security vulnerabilities - xavfsizlik muammolarini aniqlash\n"
        "4. Best practices - standartlarga rioya qilishni tekshir\n"
        "5. Automatic suggestions - avtomatik tuzatishlar taklif qil\n\n"
        "Natijani strukturasi:\n"
        "- PR Analysis: ...\n"
        "- Performance Issues: ...\n"
        "- Security Vulnerabilities: ...\n"
        "- Best Practices: ...\n"
        "- Suggestions: ..."
    )

    def __init__(self, respond_func: Callable):
        self.respond = respond_func

    def review(self, code: str, language: str = "python", context: str = "") -> str:
        prompt = f"Til: {language}\n"
        if context:
            prompt += f"Kontekst: {context}\n"
        prompt += f"Kod:\n```{language}\n{code}\n```"
        return self.respond(prompt, [], self.SYSTEM_PROMPT + UZBEK_INSTRUCTION)


class DebugAssistant:
    """5.2 Stack trace analysis, error cause, solution, debugging steps, breakpoints."""

    SYSTEM_PROMPT = (
        "Sen AIDA ning Debug Assistant botsan. Xatoliklarni tahlil qil va yechim top.\n"
        "Quyidagilarni bajar:\n"
        "1. Stack trace analysis - xatolik izini tahlil qil\n"
        "2. Error cause finding - xatolik sababini aniqlash\n"
        "3. Solution generation - tuzatish kodini yoz\n"
        "4. Step-by-step debugging - bosqichma-bosqich tuzatish yo'riqnomasi\n"
        "5. Breakpoint suggestions - qayerga breakpoint qo'yishni ko'rsat\n\n"
        "Natija strukturasi:\n"
        "- Xatolik tahlili: ...\n"
        "- Sababi: ...\n"
        "- Yechim: ...\n"
        "- Debug qadamlari: ...\n"
        "- Breakpointlar: ..."
    )

    def __init__(self, respond_func: Callable):
        self.respond = respond_func

    def debug(self, error: str, code: str = "", language: str = "python") -> str:
        prompt = f"Til: {language}\n"
        prompt += f"Xatolik / Stack trace:\n{error}\n"
        if code:
            prompt += f"Kod:\n```{language}\n{code}\n```"
        return self.respond(prompt, [], self.SYSTEM_PROMPT + UZBEK_INSTRUCTION)


class ArchitectureAssistant:
    """5.3 System design, scalability, database, API, microservices."""

    SYSTEM_PROMPT = (
        "Sen AIDA ning Architecture Assistant botsan. Tizim arxitekturasini tahlil qil va taklif ber.\n"
        "Quyidagilarni bajar:\n"
        "1. System design analysis - tizim dizaynini bahola\n"
        "2. Scalability suggestions - masshtablash imkoniyatlarini taklif qil\n"
        "3. Database optimization - ma'lumotlar bazasini optimallashtirish\n"
        "4. API design improvement - API dizaynini yaxshilash\n"
        "5. Microservices strategy - mikroservis strategiyasini ishlab chiqish\n\n"
        "Natija strukturasi:\n"
        "- Tizim tahlili: ...\n"
        "- Masshtablash: ...\n"
        "- Ma'lumotlar bazasi: ...\n"
        "- API takliflari: ...\n"
        "- Mikroservis strategiyasi: ..."
    )

    def __init__(self, respond_func: Callable):
        self.respond = respond_func

    def analyze(self, description: str, code: str = "") -> str:
        prompt = f"Tavsif:\n{description}\n"
        if code:
            prompt += f"Kod:\n```\n{code}\n```"
        return self.respond(prompt, [], self.SYSTEM_PROMPT + UZBEK_INSTRUCTION)
