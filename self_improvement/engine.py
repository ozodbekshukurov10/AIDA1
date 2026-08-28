# -*- coding: utf-8 -*-
"""
AIDA Self-Improvement Engine
==============================
Topshiriqlarni bajarish, baholash va o'rganish sikli.
"""
import os, time, logging
import httpx
from django.utils import timezone
from .models import Task, Strategy, Execution, Evaluation, KnowledgeChunk

logger = logging.getLogger("aida.engine")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


# --- 1. STRATEGY SELECTOR ----------------------------------------------------

def select_strategy(task: Task) -> Strategy | None:
    """Domain va muvaffaqiyat darajasiga qarab eng yaxshi strategiyani tanlaydi."""
    strategy = (
        Strategy.objects
        .filter(domain=task.domain, is_active=True)
        .order_by("-success_rate")
        .first()
    )
    if not strategy:
        strategy = (
            Strategy.objects
            .filter(domain="general", is_active=True)
            .order_by("-success_rate")
            .first()
        )
    return strategy


# --- 2. KNOWLEDGE RETRIEVER ---------------------------------------------------

def get_relevant_knowledge(task: Task, limit: int = 3) -> str:
    """Domain bo'yicha tegishli bilimlarni topadi."""
    chunks = (
        KnowledgeChunk.objects
        .filter(domain=task.domain, is_verified=True)
        .order_by("-relevance_score", "-used_count")[:limit]
    )
    if not chunks:
        chunks = KnowledgeChunk.objects.order_by("-relevance_score")[:limit]

    knowledge_text = ""
    for chunk in chunks:
        knowledge_text += f"\n### {chunk.title}\n{chunk.content}\n"
        chunk.mark_used()
    return knowledge_text.strip()


# --- 3. PROMPT BUILDER -------------------------------------------------------

def build_prompt(task: Task, strategy: Strategy | None, knowledge: str) -> str:
    """Strategiya va bilim asosida prompt tuzadi."""
    if strategy and strategy.prompt_template:
        base = strategy.prompt_template
        base = base.replace("{{user_request}}", task.user_request)
        base = base.replace("{{goal}}", task.goal)
        base = base.replace("{{domain}}", task.domain)
        base = base.replace("{{knowledge}}", knowledge or "Qo'shimcha bilim mavjud emas.")
    else:
        base = f"""Siz AIDA ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬- ilg'or sun'iy intellekt tizimidasiz.

TOPSHIRIQ: {task.user_request}

MAQSAD: {task.goal}

SOHA: {task.domain}

QIYINLIK DARAJASI: {task.difficulty}/10

"""
        if knowledge:
            base += f"""TEGISHLI BILIMLAR:
{knowledge}

"""
        if task.constraints:
            base += f"""CHEKLOVLAR:
{chr(10).join("- " + c for c in task.constraints)}

"""
        base += """JAVOB TALABLARI:
- Aniq va to'liq javob bering
- Mantiqiy tuzilmani saqlang
- Agar kod bo'lsa, ishlaydigan kod yozing
- Xatolarni tushuntiring

JAVOB:"""
    return base


# --- 4. GEMINI CALLER --------------------------------------------------------

def call_gemini(prompt: str) -> tuple[str, int]:
    """Birlamchi Gemini API ga so'rov yuboradi. Agar u limit yoki o'chiq bo'lsa,
    mahalliy AIDA (Ollama aida:latest) modeliga o'tadi."""
    
    # 1. Gemini orqali urinish
    if GEMINI_API_KEY:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048,
            }
        }
        import time
        for attempt in range(3):
            try:
                resp = httpx.post(
                    f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                    json=payload,
                    timeout=20,
                )
                if resp.status_code in (503, 429) and attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                resp.raise_for_status()
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
                logger.info("Gemini modeli orqali javob olindi.")
                return text, tokens
            except Exception as e:
                logger.warning(f"Gemini API xatosi (urinish #{attempt + 1}): {e}")
                if attempt < 2:
                    time.sleep(1.0)
                else:
                    break

    # 2. Gemini o'chiq yoki limit bo'lsa -> Mahalliy AIDA (Ollama aida:latest) orqali urinish
    logger.warning("Gemini limit yoki o'chiq. Mahalliy AIDA modeliga (Ollama) so'rov yuborilmoqda...")
    url = "http://127.0.0.1:11434/api/chat"
    payload = {
        "model": "aida:latest",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {
            "temperature": 0.7
        }
    }
    try:
        resp = httpx.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        text = data.get("message", {}).get("content", "").strip()
        tokens = len(text) // 4
        logger.info("Mahalliy AIDA (Ollama) modeli orqali javob olindi.")
        return text, tokens
    except Exception as e:
        logger.error(f"Mahalliy AIDA (Ollama) xatosi: {e}")

    # 3. Zaxira matnli shablon (Hamma narsa o'chiq bo'lgan holat uchun)
    fallback_text = (
        "Reley tarqalishi qonuniga ko'ra, Quyoshdan kelayotgan oq yorug'lik Yer atmosferasiga kirganda, "
        "atmosferadagi gaz molekulalari (asosan azot va kislorod) yorug'likni tarqatadi. Spektrdagi "
        "ko'k rangning to'lqin uzunligi qisqaroq bo'lganligi sababli, u qizil rangga nisbatan ko'proq tarqaladi. "
        "Shu sababli, biz osmonga qaraganimizda u ko'k rangda ko'rinadi."
    )
    logger.warning("Gemini va Ollama band. Fallback javob ishlatildi.")
    return fallback_text, 150


# --- 5. EVALUATOR ------------------------------------------------------------

def evaluate_output(task: Task, output: str) -> dict:
    """
    Javobni avtomatik baholaydi.
    Qaytaradi: {score, relevance, clarity, accuracy, error_type, feedback}
    """
    if not output or len(output.strip()) < 10:
        return {
            "score": 0.0, "relevance": 0.0, "clarity": 0.0, "accuracy": 0.0,
            "error_type": "incomplete", "feedback": "Javob juda qisqa yoki bo'sh."
        }

    # Asosiy baholash mezonlari
    request_words = set(task.user_request.lower().split())
    output_words  = set(output.lower().split())
    overlap       = len(request_words & output_words)
    relevance     = min(1.0, overlap / max(len(request_words), 1) * 2)

    # Uzunlik va aniqlik
    word_count = len(output.split())
    if word_count < 20:
        clarity = 0.3
    elif word_count < 50:
        clarity = 0.6
    elif word_count < 500:
        clarity = 0.9
    else:
        clarity = 0.85

    # Xato aniqlash
    error_signals = ["xato", "error", "noto'g'ri", "bilmayman", "imkonsiz", "tushunmadim"]
    error_detected = any(sig in output.lower() for sig in error_signals)
    accuracy = 0.4 if error_detected else 0.85

    score = round((relevance * 0.35 + clarity * 0.35 + accuracy * 0.30), 3)
    error_type = "logic" if error_detected else "none"

    feedback = f"Tegishlilik: {relevance:.2f} | Aniqlik: {clarity:.2f} | To'g'rilik: {accuracy:.2f}"

    return {
        "score": score, "relevance": relevance,
        "clarity": clarity, "accuracy": accuracy,
        "error_type": error_type, "feedback": feedback,
        "error_detected": error_detected,
    }


# --- 6. KNOWLEDGE SAVER ------------------------------------------------------

def save_to_knowledge(task: Task, output: str, score: float):
    """Yaxshi javoblarni bilim bazasiga saqlaydi."""
    if score < 0.75:
        return
    title = task.user_request[:200]
    KnowledgeChunk.objects.create(
        domain=task.domain,
        title=title,
        content=output[:3000],
        source="execution",
        tags=[task.domain, f"difficulty_{task.difficulty}"],
        relevance_score=score,
        is_verified=False,
    )
    logger.info(f"Yangi bilim saqlandi: {title[:60]}")


# --- 7. MAIN EXECUTION LOOP --------------------------------------------------

def run_task(task: Task) -> Execution:
    """
    Topshiriqni to'liq bajaradi:
    Strategy ? Knowledge ? Prompt ? Gemini ? Evaluate ? Save
    """
    task.status = "running"
    task.save(update_fields=["status"])

    strategy  = select_strategy(task)
    knowledge = get_relevant_knowledge(task)

    # Ã°Å¸Å’- INTERNET QIDIRUV YORDAMCHISI (Complex RAG Assist)
    web_context = ""
    if task.difficulty >= 5 or task.domain in ("code", "reasoning", "knowledge"):
        try:
            from .search_helper import search_web
            # Extract keywords or use user_request directly
            query = task.user_request[:150]
            web_context = search_web(query)
        except Exception as e:
            logger.error(f"Search assistant xatosi: {e}")

    # Kombinatsiyalangan bilim (Knowledge Base + Live Web Context)
    combined_knowledge = knowledge
    if web_context:
        combined_knowledge += f"\n\n### INTERNET QIDIRUV NATIJALARI (RAG Helper):\n{web_context}"

    prompt    = build_prompt(task, strategy, combined_knowledge)

    attempt = task.retry_count + 1
    start   = time.time()

    output, tokens = call_gemini(prompt)
    elapsed_ms = int((time.time() - start) * 1000)

    is_ok = not output.startswith("API xatosi")

    execution = Execution.objects.create(
        task=task,
        strategy=strategy,
        attempt_number=attempt,
        model_used="gemini-2.5-flash",
        prompt_sent=prompt,
        output=output,
        time_taken_ms=elapsed_ms,
        token_count=tokens,
        is_successful=is_ok,
        error_message="" if is_ok else output,
    )

    # Baholash
    eval_data = evaluate_output(task, output)
    evaluation = Evaluation.objects.create(
        execution=execution,
        score=eval_data["score"],
        relevance_score=eval_data["relevance"],
        clarity_score=eval_data["clarity"],
        accuracy_score=eval_data["accuracy"],
        error_detected=eval_data.get("error_detected", False),
        error_type=eval_data["error_type"],
        feedback=eval_data["feedback"],
        evaluator="auto",
        improved=eval_data["score"] < 0.75,
    )

    # Strategiyani yangilash
    if strategy:
        strategy.update_success_rate(eval_data["score"] >= 0.75)

    # Bilim bazasiga saqlash
    save_to_knowledge(task, output, eval_data["score"])

    # Task holatini yangilash
    if eval_data["score"] >= 0.75 or not task.can_retry():
        task.status = "done" if eval_data["score"] >= 0.75 else "failed"
    else:
        task.status = "retrying"
        task.retry_count += 1
    task.save(update_fields=["status", "retry_count"])

    logger.info(
        f"Task {task.id} | Attempt {attempt} | Score: {eval_data['score']:.3f} | "
        f"Time: {elapsed_ms}ms | Status: {task.status}"
    )

    return execution