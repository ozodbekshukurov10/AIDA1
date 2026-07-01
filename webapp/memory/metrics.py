from __future__ import annotations
import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "aida_metrics.db"

_lock = threading.Lock()


class MetricsCollector:
    _instance: MetricsCollector | None = None

    def __init__(self, db_path: str | Path = DB_PATH):
        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        with _lock, sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint TEXT,
                    method TEXT,
                    status_code INTEGER,
                    latency_ms INTEGER,
                    provider TEXT,
                    model TEXT,
                    timestamp REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT,
                    task_type TEXT,
                    success INTEGER,
                    latency_ms INTEGER,
                    tokens_used INTEGER,
                    timestamp REAL
                )
            """)

    def record_request(self, endpoint: str, method: str, status_code: int,
                       latency_ms: int, provider: str = "", model: str = ""):
        with _lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO requests (endpoint, method, status_code, latency_ms, provider, model, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (endpoint, method, status_code, latency_ms, provider, model, time.time()),
            )

    def record_agent_call(self, agent_name: str, task_type: str, success: bool,
                          latency_ms: int, tokens_used: int = 0):
        with _lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO agent_calls (agent_name, task_type, success, latency_ms, tokens_used, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (agent_name, task_type, 1 if success else 0, latency_ms, tokens_used, time.time()),
            )

    def get_stats(self, hours: int = 24) -> dict:
        cutoff = time.time() - hours * 3600
        with _lock, sqlite3.connect(self.db_path) as conn:
            total_reqs = conn.execute(
                "SELECT COUNT(*) FROM requests WHERE timestamp > ?", (cutoff,)
            ).fetchone()[0]
            total_agents = conn.execute(
                "SELECT COUNT(*) FROM agent_calls WHERE timestamp > ?", (cutoff,)
            ).fetchone()[0]
            avg_latency = conn.execute(
                "SELECT AVG(latency_ms) FROM requests WHERE timestamp > ?", (cutoff,)
            ).fetchone()[0] or 0
            errors = conn.execute(
                "SELECT COUNT(*) FROM requests WHERE timestamp > ? AND status_code >= 400", (cutoff,)
            ).fetchone()[0]
            by_endpoint = conn.execute(
                "SELECT endpoint, COUNT(*) as c, AVG(latency_ms) as avg_l FROM requests WHERE timestamp > ? GROUP BY endpoint ORDER BY c DESC LIMIT 10",
                (cutoff,),
            ).fetchall()
        return {
            "total_requests": total_reqs,
            "total_agent_calls": total_agents,
            "avg_latency_ms": round(avg_latency, 1),
            "errors": errors,
            "error_rate": round(errors / max(total_reqs, 1) * 100, 1),
            "top_endpoints": [
                {"endpoint": r[0], "count": r[1], "avg_latency_ms": round(r[2], 1)} for r in by_endpoint
            ],
        }


_collector_instance: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = MetricsCollector()
    return _collector_instance
