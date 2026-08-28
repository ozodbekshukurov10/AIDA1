# -*- coding: utf-8 -*-
"""
AIDA Autonomous Code Fixer
============================
Sintaksis xatolarni Gemini yordamida avtomatik to'g'irlaydi:
1. Buzilgan faylni o'qiydi
2. Gemini ga yuboradi: "Bu faylda xato bor, to'g'irla"
3. Gemini yangi to'g'ri kodni qaytaradi
4. Backup qilib, yangi kodni yozadi
5. Sintaksisni qayta tekshiradi
"""
import os, ast, shutil, logging
from pathlib import Path
from datetime import datetime
import httpx

logger = logging.getLogger("aida.fixer")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
BACKUP_DIR = Path(__file__).resolve().parent.parent / ".self_improvement_backups"
BACKUP_DIR.mkdir(exist_ok=True)


# --- 1. FILE READER ----------------------------------------------------------

def read_file(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


# --- 2. BACKUP ---------------------------------------------------------------

def backup_file(filepath: str) -> str:
    """Faylni .self_improvement_backups/ ga nusxalaydi."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = Path(filepath).name
    backup_path = BACKUP_DIR / f"{fname}.{ts}.bak"
    shutil.copy2(filepath, backup_path)
    logger.info(f"Backup: {backup_path}")
    return str(backup_path)


# --- 3. GEMINI CODE FIXER ----------------------------------------------------

def ask_gemini_to_fix(filepath: str, code: str, error_info: dict) -> str | None:
    """Gemini ga buzilgan kodni to'g'irlashni so'raydi."""
    error_desc = f"Fayl: {filepath}\nXato turi: {error_info.get('type','?')}\nXato: {error_info.get('message','?')}\nQator: {error_info.get('line','?')}"

    prompt = f"""Sen Python kod muharririsisan. Quyidagi Python kodda xato bor.

XATO MA'LUMOTI:
{error_desc}

BUZILGAN KOD:
```python
{code}
```

VAZIFA:
1. Xatoni topib to'g'irla
2. FAQAT to'g'irlangan Python kodni qaytara - hech qanday tushuntirish yoki markdown yo'q
3. Barcha import va funksiyalar saqlansin
4. Kod to'liq bo'lsin

TO'G'IRLANGAN KOD (FAQAT PYTHON, BOSHQA HECH NARSA YO'Q):"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 8192,
        }
    }
    try:
        resp = httpx.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        fixed_code = data["candidates"][0]["content"]["parts"][0]["text"]

        # Markdown code block ni olib tashlash
        if "```python" in fixed_code:
            fixed_code = fixed_code.split("```python")[1].split("```")[0]
        elif "```" in fixed_code:
            fixed_code = fixed_code.split("```")[1].split("```")[0]

        return fixed_code.strip()
    except Exception as e:
        logger.error(f"Gemini fixer xatosi: {e}")
        return None


# --- 4. FIX APPLIER ----------------------------------------------------------

def apply_fix(filepath: str, fixed_code: str) -> bool:
    """To'g'irlangan kodni faylga yozadi va sintaksisni tekshiradi."""
    # Sintaksisni tekshirish
    try:
        ast.parse(fixed_code)
    except SyntaxError as e:
        logger.error(f"Gemini javobida ham sintaksis xato: {e}")
        return False

    # Faylga yozish
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(fixed_code)
    logger.info(f"To'g'irlangan kod yozildi: {filepath}")
    return True


# --- 5. MAIN FIX PIPELINE ----------------------------------------------------

def fix_file(filepath: str, error_info: dict) -> dict:
    """
    Buzilgan faylni avtomatik to'g'irlash pipeline:
    Read -> Backup -> Gemini Fix -> Validate -> Apply
    """
    result = {
        "filepath": filepath,
        "error": error_info,
        "backup": None,
        "fixed": False,
        "attempts": 0,
        "message": "",
    }

    logger.info(f"[FIXER] Tuzatish boshlandi: {filepath}")

    # 1. Faylni o'qish
    try:
        code = read_file(filepath)
    except Exception as e:
        result["message"] = f"Faylni o'qib bo'lmadi: {e}"
        return result

    # 2. Backup
    result["backup"] = backup_file(filepath)

    # 3. Gemini dan to'g'irlash (3 urinish)
    for attempt in range(1, 4):
        result["attempts"] = attempt
        logger.info(f"  Urinish #{attempt}: Gemini dan to'g'irlash so'ralmoqda...")

        fixed_code = ask_gemini_to_fix(filepath, code, error_info)
        if not fixed_code:
            logger.warning(f"  Urinish #{attempt}: Gemini javob bermadi.")
            continue

        # 4. To'g'irlangan kodni qo'llash
        if apply_fix(filepath, fixed_code):
            result["fixed"] = True
            result["message"] = f"Muvaffaqiyatli to'g'irildi (urinish #{attempt})"
            logger.info(f"[FIXER] MUVAFFAQIYAT: {filepath} - {result['message']}")
            return result
        else:
            logger.warning(f"  Urinish #{attempt}: To'g'irlangan kod ham xato.")

    # 4. Agar to'g'irib bo'lmasa - backup ni qaytarish
    if result["backup"]:
        shutil.copy2(result["backup"], filepath)
        result["message"] = "To'g'irlab bo'lmadi - backup qaytarildi"
    else:
        result["message"] = "To'g'irlab bo'lmadi"

    logger.error(f"[FIXER] MUVAFFAQIYATSIZ: {filepath}")
    return result


# --- 6. BATCH FIXER ----------------------------------------------------------

def fix_all_errors(syntax_errors: list) -> list[dict]:
    """Barcha topilgan xatolarni to'g'irlaydi."""
    results = []
    for err in syntax_errors:
        if err.get("type") in ("SyntaxError", "ReadError") and err.get("file"):
            fix_result = fix_file(err["file"], err)
            results.append(fix_result)
    return results
