# -*- coding: utf-8 -*-
"""
AIDA Dynamic Skill Factory
============================
AIDA o'z-o'ziga yangi "skill" (ixtisoslashgan strategiya va tizim qoidalari)
yaratishi va o'rganishi uchun javobgar modul.
"""
import os, json, logging
import httpx
from django.utils import timezone
from .models import Task, Strategy, Evaluation

logger = logging.getLogger("aida.skills_factory")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


def analyze_failed_domains_and_tasks() -> tuple[str, str, int] | None:
    """
    Bahosi past bo'lgan sohalar va qiyin topshiriqlarni tahlil qiladi.
    Qaytaradi: (domain, user_request, difficulty) yoki None
    """
    # Baholash reytingi < 0.6 bo'lgan eng oxirgi topshiriqni topish
    failed_eval = (
        Evaluation.objects
        .filter(score__lt=0.6)
        .order_by("-created_at")
        .first()
    )
    if failed_eval and failed_eval.execution and failed_eval.execution.task:
        task = failed_eval.execution.task
        return task.domain, task.user_request, task.difficulty

    # Agar xatoliklar bo'lmasa, eng qiyin hal etilmagan topshiriqni tanlash
    hard_task = (
        Task.objects
        .filter(status="retrying")
        .order_by("-difficulty")
        .first()
    )
    if hard_task:
        return hard_task.domain, hard_task.user_request, hard_task.difficulty

    return None


def generate_new_skill(domain: str, sample_request: str, difficulty: int) -> dict | None:
    """
    Gemini yordamida yangi ixtisoslashgan skill (strategiya) sintez qiladi.
    """
    prompt = f"""Siz AIDA loyihasining "Metadasturlash" (Meta-programming) qismisiz. AIDA o'zi uchun yangi ixtisoslashgan "Skill" (Strategiya) yaratishi kerak.

Vazifa quyidagi soha va topshiriq uchun maxsus qoidalarga ega professional shablon tayyorlash:
Soha (Domain): {domain}
Qiyinlik darajasi: {difficulty}/10
Topshiriq namunasi: {sample_request}

Yangi skill (strategiya) uchun quyidagi ma'lumotlarni JSON formatida qaytaring:
1. "name": Skill nomi (Masalan: "AIDA Advanced Math Solver" yoki "AIDA Python Security Auditor")
2. "description": Skill nima qila olishi haqida to'liq tushuntirish
3. "prompt_template": Gemini uchun tizimli yo'riqnomani o'z ichiga olgan mukammal prompt shabloni. Shablon ichida albatta `{{{{user_request}}}}` va `{{{{knowledge}}}}` o'zgaruvchilari bo'lishi shart!

FAQAT JSON formatida qaytaring, hech qanday markdown (` ```json ` kabi) yoki tushuntirish yozmang:"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2048,
        }
    }
    import time
    for attempt in range(4):
        try:
            resp = httpx.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json=payload,
                timeout=30,
            )
            if resp.status_code in (503, 429) and attempt < 3:
                logger.warning(f"Gemini API 503/429 error. Retrying in {2.5 * (attempt + 1)}s...")
                time.sleep(2.5 * (attempt + 1))
                continue
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            # Strip markdown if Gemini adds it
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0]
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0]
                
            skill_data = json.loads(raw_text)
            return skill_data
        except Exception as e:
            logger.error(f"Skill sintezlashda xato (urinish #{attempt + 1}): {e}")
            if attempt < 3:
                time.sleep(2.0)
            else:
                break

    # Gemini API fail bo'lganda Fallback qilish
    fallback_skills = {
        "reasoning": {
            "name": f"AIDA Advanced Reasoning Specialist {timezone.now().strftime('%M%S')}",
            "description": "Mantiqiy va murakkab masalalarni yechish uchun maxsus tahlil skill.",
            "prompt_template": "Siz AIDA - mantiqiy tahlilchi va murakkab masalalar yechish bo'yicha mutaxassissiz.\n\nTOPSHIRIQ: {{user_request}}\nBILIMLAR:\n{{knowledge}}\n\nBosqichma-bosqich yechim:"
        },
        "code": {
            "name": f"AIDA Advanced Code Optimizer {timezone.now().strftime('%M%S')}",
            "description": "Dasturlash kodini xavfsizlik va tezlik bo'yicha optimallashtirish skill.",
            "prompt_template": "Siz AIDA - yuqori darajadagi dasturchisiz. Berilgan kodni optimallashtiring va xavfsizlik xatolarini tuzating.\n\nKOD: {{user_request}}\nBILIMLAR:\n{{knowledge}}\n\nOptimallashtirilgan kod va izohlar:"
        },
        "general": {
            "name": f"AIDA General Problem Solver {timezone.now().strftime('%M%S')}",
            "description": "Har qanday topshiriqni tahlil qilish va yechish skill.",
            "prompt_template": "Siz AIDA - umumiy yordamchisiz.\n\nTOPSHIRIQ: {{user_request}}\n\nJAVOB:"
        }
    }
    logger.warning(f"Gemini API band yoki xato berdi. '{domain}' uchun Fallback skill ishlatildi.")
    return fallback_skills.get(domain, fallback_skills["general"])


def learn_new_skill() -> dict:
    """
    AIDA o'zi uchun avtomatik ravishda yangi skill yaratadi va ro'yxatdan o'tkazadi.
    """
    analysis = analyze_failed_domains_and_tasks()
    if not analysis:
        # Default: Yangi ixtiyoriy foydali skill yaratish
        domain, request, diff = "general", "Umumiy tahlil qilish", 5
    else:
        domain, request, diff = analysis

    logger.info(f"[SkillFactory] Yangi skill yaratish jarayoni boshlandi. Domain: {domain}")
    
    skill_data = generate_new_skill(domain, request, diff)
    if not skill_data:
        return {"success": False, "message": "Yangi skill sintez qilib bo'lmadi."}

    # Baza tekshirish va yaratish
    strategy, created = Strategy.objects.get_or_create(
        name=skill_data["name"],
        defaults={
            "description": skill_data.get("description", ""),
            "prompt_template": skill_data["prompt_template"],
            "domain": domain,
            "success_rate": 0.70,
            "is_active": True,
        }
    )

    if created:
        msg = f"AIDA yangi skill o'rgandi: '{strategy.name}' ?"
        logger.info(msg)
        return {
            "success": True,
            "created": True,
            "name": strategy.name,
            "description": strategy.description,
            "domain": domain,
            "message": msg
        }
    else:
        msg = f"Skill allaqachon mavjud: '{strategy.name}'"
        return {
            "success": True,
            "created": False,
            "name": strategy.name,
            "message": msg
        }
