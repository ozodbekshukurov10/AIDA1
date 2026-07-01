"""AIDA Beta xotira tizimi — session persistence + checkpoint pattern + thread saqlash."""
from __future__ import annotations

import sqlite3
import time
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "aida_memory.db"


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


class AidaBetaMemory:
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
            c.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL DEFAULT 'default',
                    label TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )""")
            c.execute("""
                CREATE TABLE IF NOT EXISTS session_threads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL DEFAULT 'default',
                    thread_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_calls TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )""")
            c.execute("""
                CREATE TABLE IF NOT EXISTS session_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    system_prompt TEXT NOT NULL,
                    config TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL
                )""")
            c.execute("""
                CREATE TABLE IF NOT EXISTS prompt_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT NOT NULL UNIQUE,
                    static_part TEXT NOT NULL,
                    dynamic_part TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    hit_count INTEGER DEFAULT 0
                )""")
            c.execute("""
                CREATE TABLE IF NOT EXISTS project_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    section TEXT NOT NULL DEFAULT 'general',
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )""")
            for t in ["idx_ex_sid", "idx_lf_sid", "idx_cp_sid", "idx_st_sid", "idx_st_tid"]:
                try:
                    c.execute(f"CREATE INDEX IF NOT EXISTS {t} ON exchanges(session_id)")
                except Exception:
                    pass
            try:
                c.execute("CREATE INDEX IF NOT EXISTS idx_st_sid ON session_threads(session_id)")
                c.execute("CREATE INDEX IF NOT EXISTS idx_st_tid ON session_threads(thread_id)")
                c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_pm_sec_key ON project_memory(section, key)")
            except Exception:
                pass
            c.commit()

    def _sid(self, session_id: str) -> str:
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

    def save_checkpoint(self, label: str, state: Dict, session_id: str = "default") -> int:
        sid = self._sid(session_id)
        with self._conn as c:
            cur = c.execute(
                "INSERT INTO checkpoints (session_id, label, state, created_at) VALUES (?,?,?,?)",
                (sid, label, json.dumps(state, ensure_ascii=False), _now())
            )
            c.commit()
            return cur.lastrowid or 0

    def load_checkpoint(self, checkpoint_id: int) -> Optional[Dict]:
        row = self._conn.execute(
            "SELECT label, state, created_at FROM checkpoints WHERE id=?", (checkpoint_id,)
        ).fetchone()
        if not row:
            return None
        return {"label": row[0], "state": json.loads(row[1]), "created_at": row[2]}

    def list_checkpoints(self, session_id: str = "default", limit: int = 10) -> List[Dict]:
        sid = self._sid(session_id)
        rows = self._conn.execute(
            "SELECT id, label, created_at FROM checkpoints WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (sid, limit)
        ).fetchall()
        return [{"id": r[0], "label": r[1], "created_at": r[2]} for r in rows]

    def sessions(self) -> List[Dict[str, str]]:
        rows = self._conn.execute(
            """SELECT session_id, MAX(created_at) as last_act
               FROM exchanges WHERE session_id LIKE ?
               GROUP BY session_id ORDER BY last_act DESC""",
            (f"{self.SESSION_PREFIX}%",)
        ).fetchall()
        return [{"id": r[0].removeprefix(self.SESSION_PREFIX), "last_activity": r[1]} for r in rows]

    def save_thread_message(self, thread_id: str, role: str, content: str,
                            tool_calls: Optional[List[Dict]] = None,
                            session_id: str = "default") -> int:
        sid = self._sid(session_id)
        tc_json = json.dumps(tool_calls or [], ensure_ascii=False)
        with self._conn as c:
            cur = c.execute(
                "INSERT INTO session_threads (session_id, thread_id, role, content, tool_calls, created_at) "
                "VALUES (?,?,?,?,?,?)",
                (sid, thread_id, role, content[:8000], tc_json, _now())
            )
            c.commit()
            return cur.lastrowid or 0

    def load_thread(self, thread_id: str, limit: int = 50,
                    session_id: str = "default") -> List[Dict]:
        sid = self._sid(session_id)
        rows = self._conn.execute(
            "SELECT role, content, tool_calls, created_at FROM session_threads "
            "WHERE session_id=? AND thread_id=? AND is_active=1 ORDER BY id ASC LIMIT ?",
            (sid, thread_id, limit)
        ).fetchall()
        result = []
        for r, c, tc, t in rows:
            msg = {"role": r, "content": c, "created_at": t}
            if tc:
                try:
                    tcs = json.loads(tc)
                    if tcs:
                        msg["tool_calls"] = tcs
                except Exception:
                    pass
            result.append(msg)
        return result

    def list_threads(self, session_id: str = "default", limit: int = 20) -> List[Dict]:
        sid = self._sid(session_id)
        rows = self._conn.execute(
            "SELECT thread_id, COUNT(*) as msgs, MAX(created_at) as last_msg "
            "FROM session_threads WHERE session_id=? AND is_active=1 "
            "GROUP BY thread_id ORDER BY last_msg DESC LIMIT ?",
            (sid, limit)
        ).fetchall()
        return [{"thread_id": r[0], "message_count": r[1], "last_activity": r[2]} for r in rows]

    def close_thread(self, thread_id: str, session_id: str = "default") -> None:
        sid = self._sid(session_id)
        with self._conn as c:
            c.execute(
                "UPDATE session_threads SET is_active=0 WHERE session_id=? AND thread_id=?",
                (sid, thread_id)
            )
            c.commit()

    def save_template(self, name: str, system_prompt: str, config: Optional[Dict] = None) -> None:
        with self._conn as c:
            c.execute(
                "INSERT OR REPLACE INTO session_templates (name, system_prompt, config, created_at) "
                "VALUES (?,?,?,?)",
                (name, system_prompt, json.dumps(config or {}), _now())
            )
            c.commit()

    def get_template(self, name: str) -> Optional[Dict]:
        row = self._conn.execute(
            "SELECT name, system_prompt, config, created_at FROM session_templates WHERE name=?",
            (name,)
        ).fetchone()
        if not row:
            return None
        return {"name": row[0], "system_prompt": row[1],
                "config": json.loads(row[2]), "created_at": row[3]}

    def list_templates(self) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT name, created_at FROM session_templates ORDER BY created_at DESC"
        ).fetchall()
        return [{"name": r[0], "created_at": r[1]} for r in rows]

    def cache_prompt(self, static_part: str, dynamic_part: str = "") -> str:
        key = hashlib.md5((static_part + dynamic_part).encode()).hexdigest()
        existing = self._conn.execute(
            "SELECT static_part, dynamic_part, hit_count FROM prompt_cache WHERE cache_key=?",
            (key,)
        ).fetchone()
        if existing:
            with self._conn as c:
                c.execute("UPDATE prompt_cache SET hit_count=hit_count+1 WHERE cache_key=?", (key,))
                c.commit()
        else:
            with self._conn as c:
                c.execute(
                    "INSERT INTO prompt_cache (cache_key, static_part, dynamic_part, created_at) VALUES (?,?,?,?)",
                    (key, static_part[:2000], dynamic_part[:2000], _now())
                )
                c.commit()
        return key

    def get_cached_hit_count(self, cache_key: str) -> int:
        row = self._conn.execute(
            "SELECT hit_count FROM prompt_cache WHERE cache_key=?", (cache_key,)
        ).fetchone()
        return row[0] if row else 0

    def save_project_memory(self, section: str, key: str, value: str) -> None:
        now = _now()
        with self._conn as c:
            c.execute(
                "INSERT OR REPLACE INTO project_memory (section, key, value, created_at, updated_at) "
                "VALUES (?,?,?,COALESCE((SELECT created_at FROM project_memory WHERE section=? AND key=?), ?),?)",
                (section, key, value, section, key, now, now)
            )
            c.commit()

    def get_project_memory(self, section: str = "") -> Dict[str, str]:
        if section:
            rows = self._conn.execute(
                "SELECT key, value FROM project_memory WHERE section=? ORDER BY updated_at DESC",
                (section,)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT key, value FROM project_memory ORDER BY updated_at DESC"
            ).fetchall()
        result = {}
        for k, v in rows:
            result[k] = v
        return result

    def get_project_sections(self) -> List[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT section FROM project_memory ORDER BY section"
        ).fetchall()
        return [r[0] for r in rows]
