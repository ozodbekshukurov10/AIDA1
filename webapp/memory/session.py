from __future__ import annotations
import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from ..llm.base import Message, MessageRole

DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "aida_memory.db"

_lock = threading.Lock()


class SessionStore:
    _instance: SessionStore | None = None

    def __init__(self, db_path: str | Path = DB_PATH):
        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        with _lock, sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at REAL,
                    updated_at REAL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    tool_calls TEXT,
                    created_at REAL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    key TEXT,
                    value TEXT,
                    created_at REAL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                )
            """)

    def create_session(self, metadata: dict | None = None) -> str:
        session_id = uuid.uuid4().hex[:16]
        now = time.time()
        with _lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO sessions (id, created_at, updated_at, metadata) VALUES (?, ?, ?, ?)",
                (session_id, now, now, json.dumps(metadata or {})),
            )
        return session_id

    def add_message(self, session_id: str, message: Message):
        now = time.time()
        with _lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, tool_calls, created_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, message.role.value, message.content,
                 json.dumps(message.tool_calls) if message.tool_calls else None, now),
            )
            conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))

    def get_history(self, session_id: str, limit: int = 100) -> list[Message]:
        with _lock, sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT role, content, tool_calls FROM messages WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        msgs = []
        for role, content, tool_calls in reversed(rows):
            msgs.append(Message(
                role=MessageRole(role),
                content=content or "",
                tool_calls=json.loads(tool_calls) if tool_calls else None,
            ))
        return msgs

    def list_sessions(self) -> list[dict]:
        with _lock, sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, created_at, updated_at, metadata FROM sessions ORDER BY updated_at DESC"
            ).fetchall()
        return [
            {"id": r[0], "created_at": r[1], "updated_at": r[2], "metadata": json.loads(r[3])}
            for r in rows
        ]

    def delete_session(self, session_id: str):
        with _lock, sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM facts WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    def add_fact(self, session_id: str, key: str, value: str):
        now = time.time()
        with _lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO facts (session_id, key, value, created_at) VALUES (?, ?, ?, ?)",
                (session_id, key, value, now),
            )

    def get_facts(self, session_id: str) -> list[dict]:
        with _lock, sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT key, value, created_at FROM facts WHERE session_id = ? ORDER BY created_at DESC",
                (session_id,),
            ).fetchall()
        return [{"key": r[0], "value": r[1], "created_at": r[2]} for r in rows]


_store_instance: SessionStore | None = None


def get_session_store() -> SessionStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = SessionStore()
    return _store_instance
