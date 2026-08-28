"""System service — provides system status, diagnostics, and information."""

from __future__ import annotations
import platform
import time
from typing import Any
from aidaos.infrastructure.logging import get_logger

logger = get_logger("services.system")


class SystemService:
    """System-level operations: status, diagnostics, version info."""

    def __init__(self, settings: Any = None, provider_service: Any = None):
        self._settings = settings
        self._provider_service = provider_service
        self._start_time = time.time()

    def status(self) -> dict[str, Any]:
        """Return system status with provider info and resource usage."""
        import psutil
        primary = self._provider_service.get_primary() if self._provider_service else None
        all_providers = self._provider_service.get_all() if self._provider_service else {}

        uptime_seconds = int(time.time() - self._start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        process = psutil.Process()
        memory_mb = process.memory_info().rss / (1024 * 1024)

        info = {
            "status": "running",
            "uptime": f"{hours}h {minutes}m {seconds}s",
            "uptime_seconds": uptime_seconds,
            "provider": {
                "active": getattr(primary, "name", "none") if primary else "none",
                "model": getattr(primary, "model", "") if primary else "",
                "available": len(all_providers),
                "providers": list(all_providers.keys()) if all_providers else [],
            },
            "system": {
                "platform": platform.system(),
                "python": platform.python_version(),
                "hostname": platform.node(),
            },
            "resources": {
                "memory_mb": round(memory_mb, 1),
                "cpu_percent": process.cpu_percent(interval=0),
            },
        }
        logger.info(f"Status requested: uptime={uptime_seconds}s providers={len(all_providers)}")
        return info

    def health(self) -> dict[str, Any]:
        """Quick health check for monitoring/load balancers."""
        try:
            primary = self._provider_service.get_primary() if self._provider_service else None
            return {
                "status": "healthy",
                "provider_online": primary is not None,
                "uptime_seconds": int(time.time() - self._start_time),
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def version(self) -> dict[str, str]:
        """Return software version information."""
        return {
            "version": "2.1.0",
            "name": "AIDA",
            "description": "AI-powered code assistant",
        }
