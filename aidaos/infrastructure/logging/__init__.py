"""Professional structured logging system with rotation, JSON output, and context propagation."""

from __future__ import annotations
import json
import logging
import logging.handlers
import os
import sys
import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_LOG_CONTEXT = threading.local()


def set_context(**kwargs: Any) -> None:
    """Set context key-value pairs for the current thread (session_id, request_id, etc.)."""
    if not hasattr(_LOG_CONTEXT, "data"):
        _LOG_CONTEXT.data = {}
    _LOG_CONTEXT.data.update(kwargs)


def get_context() -> dict[str, Any]:
    return getattr(_LOG_CONTEXT, "data", {})


def clear_context() -> None:
    _LOG_CONTEXT.data = {}


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON lines for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        msg = record.getMessage()
        data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": msg,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        context = get_context()
        if context:
            data["context"] = context
        if record.exc_info and record.exc_info[0]:
            data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": "".join(traceback.format_exception(*record.exc_info)),
            }
        if hasattr(record, "extra_data"):
            data["extra"] = record.extra_data
        return json.dumps(data, ensure_ascii=False, default=str)


class ColoredConsoleFormatter(logging.Formatter):
    """Human-friendly colored output for development."""

    _LEVEL_COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[41m",
    }
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self._LEVEL_COLORS.get(record.levelname, "")
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        ctx = get_context()
        ctx_str = f" [{', '.join(f'{k}={v}' for k, v in ctx.items())}]" if ctx else ""
        return f"{color}{ts} {record.levelname:8s}{self._RESET} {record.name:<25s}{ctx_str}  {record.getMessage()}"


def setup_logging(
    name: str = "aida",
    level: str = "INFO",
    log_dir: str | Path = "logs",
    json_output: bool = False,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    """Configure the root logger with file rotation and optional JSON output.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files
        json_output: Use JSON format (for production) or colored (for dev)
        max_bytes: Max size per log file before rotation
        backup_count: Number of rotated log files to keep
    """
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    root = logging.getLogger(name)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()

    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_path / f"{name}.log"),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(JSONFormatter() if json_output else ColoredConsoleFormatter())
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter() if json_output else ColoredConsoleFormatter())
    root.addHandler(console_handler)

    logging.getLogger("django").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    root.info(f"Logging initialized: level={level}, file={log_path / f'{name}.log'}, json={json_output}")
    return root


def get_logger(name: str) -> logging.Logger:
    """Get a child logger with proper namespace."""
    return logging.getLogger(f"aida.{name}")
