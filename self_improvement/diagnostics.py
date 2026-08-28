# -*- coding: utf-8 -*-
"""
AIDA System Diagnostics Engine
================================
Butun tizimni skanerlaydi:
- Python fayllardagi sintaksis xatolar
- Import xatolari
- API endpoint holatlari
- DB connection
- Model availability
- Log faylidagi critical xatolar
"""
import os, ast, sys, subprocess, importlib, logging, traceback
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("aida.diagnostics")

BASE_DIR = Path(__file__).resolve().parent.parent

SCAN_DIRS = [
    "aida_api",
    "self_improvement",
    "webapp",
    "AIDA",
]

SKIP_DIRS  = {"__pycache__", ".venv", "migrations", "node_modules", ".git"}
SKIP_FILES = {"seed.py", "test_api.py", "test_full.py", "test_key.py", "test_key2.py", "check_result.py", "test_si.json"}


# --- 1. SYNTAX CHECKER -------------------------------------------------------

def check_syntax(filepath: str) -> dict | None:
    """Python faylidagi sintaksis xatolarni aniqlaydi."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
        ast.parse(source, filename=filepath)
        return None
    except SyntaxError as e:
        return {
            "type": "SyntaxError",
            "file": filepath,
            "line": e.lineno,
            "message": str(e.msg),
            "text": e.text or "",
            "severity": "critical",
        }
    except Exception as e:
        return {
            "type": "ReadError",
            "file": filepath,
            "line": None,
            "message": str(e),
            "text": "",
            "severity": "warning",
        }


def scan_python_files() -> list[dict]:
    """Barcha Python fayllarini skanerlaydi."""
    errors = []
    for scan_dir in SCAN_DIRS:
        dir_path = BASE_DIR / scan_dir
        if not dir_path.exists():
            continue
        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in files:
                if fname.endswith(".py") and fname not in SKIP_FILES:
                    fpath = os.path.join(root, fname)
                    err = check_syntax(fpath)
                    if err:
                        errors.append(err)
                        logger.warning(f"Sintaksis xato: {fpath} - {err['message']}")
    return errors


# --- 2. IMPORT CHECKER -------------------------------------------------------

def check_imports() -> list[dict]:
    """Asosiy modullarning import imkoniyatini tekshiradi."""
    required_modules = [
        "django", "rest_framework", "httpx",
        "jwt", "cryptography", "dotenv",
    ]
    errors = []
    for mod in required_modules:
        try:
            importlib.import_module(mod)
        except ImportError as e:
            errors.append({
                "type": "ImportError",
                "module": mod,
                "message": str(e),
                "severity": "critical",
            })
    return errors


# --- 3. API ENDPOINT CHECKER -------------------------------------------------

def check_api_endpoints() -> list[dict]:
    """Asosiy API endpointlarning holati."""
    import urllib.request
    endpoints = [
        ("http://127.0.0.1:8001/api/si/stats/",   "Self-Improvement Stats"),
        ("http://127.0.0.1:8001/api/status/",     "AIDA Status"),
        ("http://127.0.0.1:8001/",                 "Root"),
    ]
    results = []
    for url, name in endpoints:
        try:
            req = urllib.request.Request(url, method="GET")
            resp = urllib.request.urlopen(req, timeout=5)
            results.append({
                "name": name,
                "url": url,
                "status": resp.status,
                "ok": True,
            })
        except Exception as e:
            results.append({
                "name": name,
                "url": url,
                "status": 0,
                "ok": False,
                "error": str(e)[:100],
            })
    return results


# --- 4. LOG ANALYZER ---------------------------------------------------------

def check_logs() -> list[dict]:
    """Log fayllarida critical xatolarni qidiradi."""
    log_files = [
        BASE_DIR / "logs" / "aida.log",
        BASE_DIR / "server.log",
        BASE_DIR / "server_err.log",
    ]
    issues = []
    keywords = ["ERROR", "CRITICAL", "EXCEPTION", "Traceback", "SyntaxError", "ImportError"]
    for lf in log_files:
        if not lf.exists():
            continue
        try:
            with open(lf, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            recent = lines[-100:]  # oxirgi 100 satr
            for i, line in enumerate(recent):
                if any(kw in line for kw in keywords):
                    issues.append({
                        "file": str(lf),
                        "line": line.strip()[:200],
                        "severity": "critical" if "CRITICAL" in line or "SyntaxError" in line else "warning",
                    })
        except Exception:
            pass
    return issues


# --- 5. DATABASE HEALTH -------------------------------------------------------

def check_database() -> dict:
    """Database ulanishini tekshiradi."""
    try:
        import django
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AIDA.settings")
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {"ok": True, "message": "DB ulanishi normal."}
    except Exception as e:
        return {"ok": False, "message": str(e)[:200]}


# --- 6. FULL SYSTEM SCAN -----------------------------------------------------

def run_full_diagnostics() -> dict:
    """
    Butun tizimni skanerlaydi va hisobot qaytaradi.
    """
    logger.info("[AIDA Diagnostics] To'liq skanerlash boshlandi...")
    start = datetime.now()

    syntax_errors  = scan_python_files()
    import_errors  = check_imports()
    api_status     = check_api_endpoints()
    log_issues     = check_logs()
    db_health      = check_database()

    total_issues = len(syntax_errors) + len(import_errors) + len(log_issues)
    api_ok = sum(1 for a in api_status if a["ok"])

    report = {
        "timestamp": start.isoformat(),
        "duration_ms": int((datetime.now() - start).total_seconds() * 1000),
        "summary": {
            "total_issues": total_issues,
            "syntax_errors": len(syntax_errors),
            "import_errors": len(import_errors),
            "api_ok": api_ok,
            "api_total": len(api_status),
            "log_issues": len(log_issues),
            "db_ok": db_health["ok"],
        },
        "syntax_errors":  syntax_errors,
        "import_errors":  import_errors,
        "api_status":     api_status,
        "log_issues":     log_issues[:20],
        "db_health":      db_health,
        "healthy": total_issues == 0 and db_health["ok"],
    }

    logger.info(
        f"[AIDA Diagnostics] Tugadi. Jami xatolar: {total_issues} | "
        f"API: {api_ok}/{len(api_status)} | DB: {db_health['ok']}"
    )
    return report
