import json
import logging
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("webapp.monitoring.metrics")

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "metrics.db")
DATA_RETENTION_DAYS = 7


class MetricsCollector:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()
        self._cleanup_old_data()

    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        agent TEXT NOT NULL,
                        model TEXT NOT NULL,
                        success INTEGER NOT NULL,
                        response_time REAL NOT NULL,
                        request_type TEXT DEFAULT ''
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics(timestamp)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_agent ON metrics(agent)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_model ON metrics(model)
                """)
                conn.commit()
            finally:
                conn.close()

    def _cleanup_old_data(self):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=DATA_RETENTION_DAYS)).isoformat()
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            try:
                conn.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff,))
                conn.commit()
            finally:
                conn.close()

    def record_request(
        self,
        agent: str,
        model: str,
        success: bool,
        response_time: float,
        request_type: str = "",
    ):
        ts = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            try:
                conn.execute(
                    "INSERT INTO metrics (timestamp, agent, model, success, response_time, request_type) VALUES (?, ?, ?, ?, ?, ?)",
                    (ts, agent, model, 1 if success else 0, response_time, request_type),
                )
                conn.commit()
            finally:
                conn.close()

    @property
    def request_count(self) -> int:
        return self._aggregate("COUNT(*)") or 0

    @property
    def success_count(self) -> int:
        return self._aggregate("COUNT(*)", "success = 1") or 0

    @property
    def error_count(self) -> int:
        return self._aggregate("COUNT(*)", "success = 0") or 0

    @property
    def avg_response_time(self) -> float:
        val = self._aggregate("AVG(response_time)")
        return round(val, 4) if val else 0.0

    def _aggregate(self, expr: str, condition: str = "") -> Any:
        query = f"SELECT {expr} FROM metrics"
        if condition:
            query += f" WHERE {condition}"
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            try:
                cur = conn.execute(query)
                return cur.fetchone()[0]
            finally:
                conn.close()

    def get_health_score(self) -> float:
        total = self.request_count
        if total == 0:
            return 1.0
        success_rate = self.success_count / total
        response_score = 1.0 - (self.avg_response_time / 60.0)
        health = success_rate * 0.7 + max(response_score, 0.0) * 0.3
        return round(max(0.0, min(health, 1.0)), 4)

    def get_report(self) -> Dict[str, Any]:
        total = self.request_count
        success = self.success_count
        errors = self.error_count
        avg_time = self.avg_response_time
        return {
            "total_requests": total,
            "success_rate": round(success / total, 4) if total else 0.0,
            "error_rate": round(errors / total, 4) if total else 0.0,
            "avg_response_time": avg_time,
            "health_score": self.get_health_score(),
            "agent_stats": self._all_agent_stats(),
            "model_usage": self._all_model_usage(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _all_agent_stats(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            try:
                cur = conn.execute(
                    "SELECT agent, COUNT(*), SUM(success), SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END), AVG(response_time) FROM metrics GROUP BY agent"
                )
                rows = cur.fetchall()
                result = {}
                for agent, total, succ, fail, avg in rows:
                    result[agent] = {
                        "total_calls": total,
                        "success_count": succ or 0,
                        "failure_count": fail or 0,
                        "avg_time": round(avg, 4) if avg else 0.0,
                    }
                return result
            finally:
                conn.close()

    def _all_model_usage(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            try:
                cur = conn.execute(
                    "SELECT model, COUNT(*), AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END), AVG(response_time) FROM metrics GROUP BY model"
                )
                rows = cur.fetchall()
                result = {}
                for model, count, success_rate, avg_time in rows:
                    result[model] = {
                        "usage_count": count,
                        "success_rate": round(success_rate, 4) if success_rate else 0.0,
                        "avg_time": round(avg_time, 4) if avg_time else 0.0,
                    }
                return result
            finally:
                conn.close()

    def get_agent_stats(self, agent_name: str) -> Dict[str, Any]:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            try:
                cur = conn.execute(
                    "SELECT COUNT(*), SUM(success), SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END), AVG(response_time) FROM metrics WHERE agent = ?",
                    (agent_name,),
                )
                row = cur.fetchone()
                if not row or row[0] == 0:
                    return {
                        "total_calls": 0,
                        "success_count": 0,
                        "failure_count": 0,
                        "avg_time": 0.0,
                    }
                return {
                    "total_calls": row[0],
                    "success_count": row[1] or 0,
                    "failure_count": row[2] or 0,
                    "avg_time": round(row[3], 4) if row[3] else 0.0,
                }
            finally:
                conn.close()

    def get_model_stats(self, model_name: str) -> Dict[str, Any]:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            try:
                cur = conn.execute(
                    "SELECT COUNT(*), AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END), AVG(response_time) FROM metrics WHERE model = ?",
                    (model_name,),
                )
                row = cur.fetchone()
                if not row or row[0] == 0:
                    return {"usage_count": 0, "success_rate": 0.0, "avg_time": 0.0}
                return {
                    "usage_count": row[0],
                    "success_rate": round(row[1], 4) if row[1] else 0.0,
                    "avg_time": round(row[2], 4) if row[2] else 0.0,
                }
            finally:
                conn.close()

    def get_history(
        self,
        limit: int = 50,
        offset: int = 0,
        agent: Optional[str] = None,
        model: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        conditions = []
        params = []
        if agent:
            conditions.append("agent = ?")
            params.append(agent)
        if model:
            conditions.append("model = ?")
            params.append(model)
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time)
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time)

        where = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT timestamp, agent, model, success, response_time, request_type FROM metrics WHERE {where} ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._lock:
            conn = sqlite3.connect(self._db_path)
            try:
                cur = conn.execute(query, params)
                rows = cur.fetchall()
                result = []
                for ts, agent, model, success, resp_time, req_type in rows:
                    result.append({
                        "timestamp": ts,
                        "agent": agent,
                        "model": model,
                        "success": bool(success),
                        "response_time": resp_time,
                        "request_type": req_type or "",
                    })
                return result
            finally:
                conn.close()

    def get_last_n(self, n: int = 10) -> List[Dict[str, Any]]:
        return self.get_history(limit=n)

    def get_by_agent(self, agent_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self.get_history(limit=limit, agent=agent_name)

    def get_by_model(self, model_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self.get_history(limit=limit, model=model_name)

    def get_success_failure_ratio(self) -> Dict[str, float]:
        total = self.request_count
        if total == 0:
            return {"success_ratio": 0.0, "failure_ratio": 0.0}
        return {
            "success_ratio": round(self.success_count / total, 4),
            "failure_ratio": round(self.error_count / total, 4),
        }

    def export_json(self, filepath: Optional[str] = None) -> str:
        rows = self.get_history(limit=100000)
        data = json.dumps(rows, ensure_ascii=False, indent=2)
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(data)
        return data
