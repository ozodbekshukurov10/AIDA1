"""AIDA Beta xotira tizimi — asosiy MemoryStore bilan birlashgan."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import List, Dict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "aida_memory.db"   # Asosiy loyiha DB si bilan bir xil fayl


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


class AidaBetaMemory:
    """
    Asosiy MemoryStore ustiga qurilgan wrapper.
    aida-beta sessiyalari uchun alohida session_id prefix ishlatadi.
    """
    SESSION_PREFIX = "aida_beta:"

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init()

    def _init(self) -> None:
        with self._conn as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS exchanges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL DEFAULT 'default',
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )""")
            c.execute("""
                CREATE TABLE IF NOT EXISTS learned_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL DEFAULT 'default',
                    fact TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_ex_sid ON exchanges(session_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_lf_sid ON learned_facts(session_id)")
            c.commit()

    def _sid(self, session_id: str) -> str:
        """aida-beta prefix qo'shilgan session id."""
        if session_id.startswith(self.SESSION_PREFIX):
            return session_id
        return f"{self.SESSION_PREFIX}{session_id}"

    def save(self, role: str, content: str, session_id: str = "default") -> None:
        sid = self._sid(session_id)
        with self._conn as c:
            c.execute(
                "INSERT INTO exchanges (session_id, role, content, created_at) VALUES (?,?,?,?)",
                (sid, role, content, _now())
            )
            c.commit()

    def recent(self, limit: int = 20, session_id: str = "default") -> List[Dict[str, str]]:
        sid = self._sid(session_id)
        rows = self._conn.execute(
            "SELECT role, content, created_at FROM exchanges WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (sid, limit)
        ).fetchall()
        return [{"role": r, "content": c, "created_at": t} for r, c, t in reversed(rows)]

    def remember_fact(self, fact: str, session_id: str = "default") -> None:
        fact = fact.strip()
        if not fact:
            return
        sid = self._sid(session_id)
        with self._conn as c:
            c.execute(
                "INSERT INTO learned_facts (session_id, fact, created_at) VALUES (?,?,?)",
                (sid, fact[:800], _now())
            )
            c.commit()

    def learned_facts(self, limit: int = 8, session_id: str = "default") -> List[str]:
        sid = self._sid(session_id)
        rows = self._conn.execute(
            "SELECT fact FROM learned_facts WHERE session_id IN (?,?) ORDER BY id DESC LIMIT ?",
            (sid, "aida_beta:default", limit)
        ).fetchall()
        return [r[0] for r in rows]

    def sessions(self) -> List[Dict[str, str]]:
        rows = self._conn.execute(
            """SELECT session_id, MAX(created_at) as last_act
               FROM exchanges WHERE session_id LIKE ?
               GROUP BY session_id ORDER BY last_act DESC""",
            (f"{self.SESSION_PREFIX}%",)
        ).fetchall()
        return [{"id": r[0].removeprefix(self.SESSION_PREFIX), "last_activity": r[1]} for r in rows]
