"""
8.1 Feedback Loop, 8.2 Model Fine-tuning, 8.3 Knowledge Updates.
Uses provider respond() for LLM assistance + local storage for persistent data.
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional


UZBEK_INSTRUCTION = "\n\nJavobni faqat O'ZBEK tilida yoz."

FEEDBACK_DB = Path(__file__).resolve().parent.parent / "aida_feedback.db"
TRAINING_DB = Path(__file__).resolve().parent.parent / "aida_training.db"


def _init_feedback_db():
    conn = sqlite3.connect(str(FEEDBACK_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rating INTEGER NOT NULL,
            comment TEXT DEFAULT '',
            session_id TEXT DEFAULT '',
            prompt TEXT DEFAULT '',
            response TEXT DEFAULT '',
            provider TEXT DEFAULT '',
            mode TEXT DEFAULT '',
            latency_ms INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS error_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_type TEXT NOT NULL,
            error_message TEXT DEFAULT '',
            endpoint TEXT DEFAULT '',
            session_id TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usage_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT NOT NULL,
            session_id TEXT DEFAULT '',
            mode TEXT DEFAULT '',
            latency_ms INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def _init_training_db():
    conn = sqlite3.connect(str(TRAINING_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS training_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            response TEXT NOT NULL,
            domain TEXT DEFAULT '',
            language TEXT DEFAULT 'uz',
            rating INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS domain_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL UNIQUE,
            system_prompt TEXT DEFAULT '',
            temperature REAL DEFAULT 0.7,
            max_tokens INTEGER DEFAULT 1024,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


_init_feedback_db()
_init_training_db()


# ---------------------------------------------------------------------------
# 8.1 — Feedback Loop
# ---------------------------------------------------------------------------
class FeedbackLoop:
    """User ratings, performance metrics, error tracking, A/B testing, usage analytics."""

    def __init__(self, respond_func: Optional[Callable] = None):
        self.respond = respond_func
        self._conn = sqlite3.connect(str(FEEDBACK_DB))

    def submit_rating(self, rating: int, comment: str = "", session_id: str = "",
                      prompt: str = "", response: str = "", provider: str = "",
                      mode: str = "", latency_ms: int = 0) -> dict:
        now = datetime.utcnow().isoformat()
        self._conn.execute(
            "INSERT INTO feedback (rating,comment,session_id,prompt,response,provider,mode,latency_ms,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (rating, comment, session_id, prompt, response, provider, mode, latency_ms, now),
        )
        self._conn.commit()
        return {"status": "ok", "id": self._conn.execute("SELECT last_insert_rowid()").fetchone()[0]}

    def log_error(self, error_type: str, error_message: str = "", endpoint: str = "",
                  session_id: str = "") -> dict:
        now = datetime.utcnow().isoformat()
        self._conn.execute(
            "INSERT INTO error_log (error_type,error_message,endpoint,session_id,created_at) VALUES (?,?,?,?,?)",
            (error_type, error_message, endpoint, session_id, now),
        )
        self._conn.commit()
        return {"status": "ok"}

    def log_usage(self, endpoint: str, session_id: str = "", mode: str = "",
                  latency_ms: int = 0) -> dict:
        now = datetime.utcnow().isoformat()
        self._conn.execute(
            "INSERT INTO usage_log (endpoint,session_id,mode,latency_ms,created_at) VALUES (?,?,?,?,?)",
            (endpoint, session_id, mode, latency_ms, now),
        )
        self._conn.commit()
        return {"status": "ok"}

    def analytics(self) -> dict:
        total_ratings = self._conn.execute("SELECT COUNT(*), AVG(rating) FROM feedback").fetchone()
        total_errors = self._conn.execute("SELECT COUNT(*) FROM error_log").fetchone()[0]
        total_usage = self._conn.execute("SELECT COUNT(*) FROM usage_log").fetchone()[0]
        last_7d = (datetime.utcnow() - timedelta(days=7)).isoformat()
        usage_7d = self._conn.execute(
            "SELECT COUNT(*) FROM usage_log WHERE created_at >= ?", (last_7d,)
        ).fetchone()[0]
        top_endpoints = self._conn.execute(
            "SELECT endpoint, COUNT(*) as cnt FROM usage_log GROUP BY endpoint ORDER BY cnt DESC LIMIT 5"
        ).fetchall()
        mode_breakdown = self._conn.execute(
            "SELECT mode, COUNT(*) as cnt FROM usage_log WHERE mode != '' GROUP BY mode"
        ).fetchall()
        recent_ratings = self._conn.execute(
            "SELECT rating, comment, created_at FROM feedback ORDER BY id DESC LIMIT 10"
        ).fetchall()
        return {
            "total_ratings": total_ratings[0] or 0,
            "avg_rating": round(total_ratings[1] or 0, 2),
            "total_errors": total_errors,
            "total_usage": total_usage,
            "usage_last_7d": usage_7d,
            "top_endpoints": dict(top_endpoints),
            "mode_breakdown": dict(mode_breakdown),
            "recent_feedback": [
                {"rating": r[0], "comment": r[1], "time": r[2]}
                for r in recent_ratings
            ],
        }

    def analyze(self, question: str = "") -> str:
        if not self.respond:
            return "Feedback provider mavjud emas."
        data = self.analytics()
        prompt = f"Savol: {question or 'Foydalanuvchi statistikasini tahlil qil'}\n\nStatistika:\n{json.dumps(data, indent=2, ensure_ascii=False)}"
        return self.respond(prompt, [], (
            "Sen AIDA Feedback Loop assistantisan. Foydalanuvchi statistikasini tahlil qil va taklif ber."
            + UZBEK_INSTRUCTION
        ))


# ---------------------------------------------------------------------------
# 8.2 — Model Fine-tuning
# ---------------------------------------------------------------------------
class ModelFineTuning:
    """Custom training data, domain tuning, performance optimization, new languages, edge cases."""

    def __init__(self, respond_func: Optional[Callable] = None):
        self.respond = respond_func
        self._conn = sqlite3.connect(str(TRAINING_DB))

    def save_training_pair(self, prompt: str, response: str, domain: str = "",
                           language: str = "uz", rating: int = 0) -> dict:
        now = datetime.utcnow().isoformat()
        self._conn.execute(
            "INSERT INTO training_data (prompt,response,domain,language,rating,created_at) VALUES (?,?,?,?,?,?)",
            (prompt, response, domain, language, rating, now),
        )
        self._conn.commit()
        return {"status": "ok", "id": self._conn.execute("SELECT last_insert_rowid()").fetchone()[0]}

    def set_domain_prompt(self, domain: str, system_prompt: str,
                          temperature: float = 0.7, max_tokens: int = 1024) -> dict:
        now = datetime.utcnow().isoformat()
        self._conn.execute(
            "INSERT INTO domain_prompts (domain,system_prompt,temperature,max_tokens,updated_at) "
            "VALUES (?,?,?,?,?) ON CONFLICT(domain) DO UPDATE SET "
            "system_prompt=excluded.system_prompt, temperature=excluded.temperature, "
            "max_tokens=excluded.max_tokens, updated_at=excluded.updated_at",
            (domain, system_prompt, temperature, max_tokens, now),
        )
        self._conn.commit()
        return {"status": "ok"}

    def get_domain_prompt(self, domain: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT system_prompt, temperature, max_tokens FROM domain_prompts WHERE domain = ?",
            (domain,),
        ).fetchone()
        if row:
            return {"system_prompt": row[0], "temperature": row[1], "max_tokens": row[2]}
        return None

    def list_domains(self) -> list:
        rows = self._conn.execute("SELECT domain, updated_at FROM domain_prompts ORDER BY updated_at DESC").fetchall()
        return [{"domain": r[0], "updated_at": r[1]} for r in rows]

    def training_stats(self) -> dict:
        total = self._conn.execute("SELECT COUNT(*) FROM training_data").fetchone()[0]
        by_domain = self._conn.execute(
            "SELECT domain, COUNT(*) as cnt FROM training_data WHERE domain != '' GROUP BY domain"
        ).fetchall()
        by_lang = self._conn.execute(
            "SELECT language, COUNT(*) as cnt FROM training_data GROUP BY language"
        ).fetchall()
        return {
            "total_pairs": total,
            "by_domain": dict(by_domain),
            "by_language": dict(by_lang),
        }

    def analyze(self, question: str = "") -> str:
        if not self.respond:
            return "Fine-tuning provider mavjud emas."
        stats = self.training_stats()
        domains = self.list_domains()
        prompt = f"Savol: {question or 'Modelni yaxshilash bo\'yicha tavsiya ber'}\n\nStatistika:\n{json.dumps(stats, indent=2, ensure_ascii=False)}\n\nSozlangan domainlar:\n{json.dumps(domains, indent=2, ensure_ascii=False)}"
        return self.respond(prompt, [], (
            "Sen AIDA Model Fine-tuning assistantisan. Training data va domain sozlamalarini tahlil qil."
            + UZBEK_INSTRUCTION
        ))


# ---------------------------------------------------------------------------
# 8.3 — Knowledge Updates
# ---------------------------------------------------------------------------
class KnowledgeUpdater:
    """New frameworks, library updates, security patches, best practices, industry trends."""

    def __init__(self, respond_func: Optional[Callable] = None):
        self.respond = respond_func
        self._kb_conn = sqlite3.connect(str(FEEDBACK_DB))

    def suggest_updates(self, topic: str = "", context: str = "") -> str:
        if not self.respond:
            return "Knowledge updater provider mavjud emas."
        prompt = f"Mavzu: {topic or 'Bilimlarni yangilash'}\n"
        if context:
            prompt += f"Kontekst: {context}\n"
        return self.respond(prompt, [], (
            "Sen AIDA Knowledge Update assistantisan. Eng so'nggi framework, kutubxona, xavfsizlik "
            "va trendlar haqida ma'lumot ber. Hozirgi yil: 2026.\n\n"
            "Quyidagilarni qamrab ol:\n"
            "1. Yangi framework va kutubxona versiyalari\n"
            "2. Xavfsizlik patch'lari va CVE\n"
            "3. Eng yaxshi amaliyotlar (best practices)\n"
            "4. Sanoat trendlari va yangiliklar\n\n"
            "Natija strukturasi:\n"
            "- Yangilik: ...\n"
            "- Ta'siri: ...\n"
            "- Qo'llanma: ..."
            + UZBEK_INSTRUCTION
        ))

    def render(self, query: str) -> str:
        return self.suggest_updates(topic=query)
