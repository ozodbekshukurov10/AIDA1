"""
AIDA Enterprise API — Monitoring ViewSet

Tizim monitoringi, metrikalar va alertlarni boshqarish.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..responses import APIResponse

MOCK_METRICS = {
    "system": {
        "cpu_usage_percent": 42.5,
        "memory_usage_percent": 68.2,
        "disk_usage_percent": 55.1,
        "network_in_mb": 1240.5,
        "network_out_mb": 890.3,
        "uptime_seconds": 2592000,
        "load_average": [1.2, 0.8, 0.6],
        "processes_running": 142,
        "processes_total": 256,
    },
    "api": {
        "requests_total": 1256789,
        "requests_per_minute": 342,
        "avg_response_time_ms": 85,
        "p95_response_time_ms": 210,
        "p99_response_time_ms": 450,
        "error_rate_percent": 0.12,
        "active_connections": 45,
        "rate_limited_requests": 23,
    },
    "database": {
        "connections_active": 12,
        "connections_idle": 8,
        "connections_max": 50,
        "queries_per_second": 156,
        "avg_query_time_ms": 12,
        "slow_queries": 3,
        "cache_hit_ratio": 94.5,
        "replication_lag_ms": 0,
    },
}

MOCK_ALERTS = {
    "alert_1": {
        "id": "alert_1",
        "name": "CPU ishlatish yuqori",
        "severity": "warning",
        "status": "active",
        "source": "system",
        "metric": "cpu_usage_percent",
        "condition": "> 80%",
        "current_value": 42.5,
        "threshold": 80,
        "message": "CPU ishlatish 80% dan oshdi",
        "created_at": "2026-07-02T08:00:00Z",
        "acknowledged_at": None,
        "resolved_at": None,
    },
    "alert_2": {
        "id": "alert_2",
        "name": "Xotira yetishmovchiligi",
        "severity": "critical",
        "status": "resolved",
        "source": "system",
        "metric": "memory_usage_percent",
        "condition": "> 90%",
        "current_value": 68.2,
        "threshold": 90,
        "message": "Xotira ishlatish 90% dan oshdi",
        "created_at": "2026-06-28T14:00:00Z",
        "acknowledged_at": "2026-06-28T14:05:00Z",
        "resolved_at": "2026-06-28T16:00:00Z",
    },
    "alert_3": {
        "id": "alert_3",
        "name": "API javob vaqti sekinlashdi",
        "severity": "warning",
        "status": "active",
        "source": "api",
        "metric": "p95_response_time_ms",
        "condition": "> 300ms",
        "current_value": 210,
        "threshold": 300,
        "message": "API P95 javob vaqti 300ms dan oshdi",
        "created_at": "2026-07-01T20:00:00Z",
        "acknowledged_at": "2026-07-01T20:30:00Z",
        "resolved_at": None,
    },
}

MOCK_HEALTH_CHECKS = {
    "database": {
        "status": "healthy",
        "latency_ms": 3,
        "last_checked": "2026-07-02T15:00:00Z",
    },
    "redis": {
        "status": "healthy",
        "latency_ms": 1,
        "last_checked": "2026-07-02T15:00:00Z",
    },
    "celery": {
        "status": "healthy",
        "latency_ms": 0,
        "workers_active": 4,
        "workers_total": 4,
        "last_checked": "2026-07-02T15:00:00Z",
    },
    "storage": {
        "status": "healthy",
        "available_gb": 120.5,
        "total_gb": 500,
        "last_checked": "2026-07-02T15:00:00Z",
    },
}

MOCK_LOGS = [
    {"timestamp": "2026-07-02T15:30:00Z", "level": "info", "service": "api", "message": "Request handled successfully", "request_id": "req_abc123"},
    {"timestamp": "2026-07-02T15:29:55Z", "level": "warning", "service": "api", "message": "Rate limit exceeded for user_03", "request_id": "req_def456"},
    {"timestamp": "2026-07-02T15:29:50Z", "level": "error", "service": "worker", "message": "Task execution failed: timeout", "request_id": "req_ghi789"},
    {"timestamp": "2026-07-02T15:29:45Z", "level": "info", "service": "database", "message": "Query executed in 12ms", "request_id": ""},
    {"timestamp": "2026-07-02T15:29:40Z", "level": "info", "service": "auth", "message": "User login successful", "request_id": "req_jkl012"},
]


class MonitoringViewSet(viewsets.ViewSet):
    """
    Tizim monitoringi va nazorati.

    - GET  /monitoring/metrics/             — Tizim metrikalari
    - GET  /monitoring/metrics/{service}/   — Xizmat metrikalari
    - GET  /monitoring/alerts/              — Alertlar ro'yxati
    - POST /monitoring/alerts/              — Yangi alert yaratish
    - GET  /monitoring/alerts/{id}/         — Bitta alert
    - POST /monitoring/alerts/{id}/acknowledge/ — Alertni tasdiqlash
    - POST /monitoring/alerts/{id}/resolve/    — Alertni yechish
    - GET  /monitoring/health/              — Sog'liq tekshiruvi
    - GET  /monitoring/health/{service}/    — Xizmat sog'ligi
    - GET  /monitoring/logs/                — Tizim loglari
    - GET  /monitoring/dashboard/           — Dashboard ma'lumotlari
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def metrics(self, request):
        """Tizim metrikalari."""
        try:
            return Response(APIResponse.success(data=MOCK_METRICS))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["get"], url_path="metrics/(?P<service>[^/.]+)")
    def service_metrics(self, request, service=None, pk=None):
        """Xizmat metrikalari."""
        try:
            metrics = MOCK_METRICS.get(service)
            if not metrics:
                return Response(APIResponse.not_found(message=f"Xizmat topilmadi: {service}"))
            return Response(
                APIResponse.success(
                    data=metrics,
                    metadata={"service": service, "collected_at": datetime.utcnow().isoformat() + "Z"},
                )
            )
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=False, methods=["get"])
    def alerts(self, request):
        """Alertlar ro'yxati."""
        try:
            alerts = list(MOCK_ALERTS.values())

            severity = request.query_params.get("severity")
            if severity:
                alerts = [a for a in alerts if a["severity"] == severity]

            alert_status = request.query_params.get("status")
            if alert_status:
                alerts = [a for a in alerts if a["status"] == alert_status]

            source = request.query_params.get("source")
            if source:
                alerts = [a for a in alerts if a["source"] == source]

            return Response(APIResponse.success(data=alerts))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=False, methods=["post"], url_path="alerts")
    def create_alert(self, request):
        """Yangi alert yaratish."""
        try:
            name = request.data.get("name")
            if not name:
                return Response(APIResponse.bad_request(message="Alert nomi kiritilishi shart."))

            alert_id = f"alert_{uuid.uuid4().hex[:8]}"
            now = datetime.utcnow().isoformat() + "Z"

            alert = {
                "id": alert_id,
                "name": name,
                "severity": request.data.get("severity", "info"),
                "status": "active",
                "source": request.data.get("source", "manual"),
                "metric": request.data.get("metric", ""),
                "condition": request.data.get("condition", ""),
                "current_value": request.data.get("current_value", 0),
                "threshold": request.data.get("threshold", 0),
                "message": request.data.get("message", ""),
                "created_at": now,
                "acknowledged_at": None,
                "resolved_at": None,
            }
            MOCK_ALERTS[alert_id] = alert

            return Response(
                APIResponse.created(data=alert, message="Alert yaratildi."),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["get"], url_path="alerts/(?P<alert_pk>[^/.]+)")
    def get_alert(self, request, alert_pk=None, pk=None):
        """Bitta alert."""
        try:
            alert = MOCK_ALERTS.get(alert_pk)
            if not alert:
                return Response(APIResponse.not_found(message=f"Alert topilmadi: {alert_pk}"))
            return Response(APIResponse.success(data=alert))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["post"], url_path="alerts/(?P<alert_pk>[^/.]+)/acknowledge")
    def acknowledge_alert(self, request, alert_pk=None, pk=None):
        """Alertni tasdiqlash."""
        try:
            alert = MOCK_ALERTS.get(alert_pk)
            if not alert:
                return Response(APIResponse.not_found(message=f"Alert topilmadi: {alert_pk}"))

            if alert["status"] != "active":
                return Response(APIResponse.bad_request(message="Faqat faol alertlar tasdiqlanishi mumkin."))

            alert["status"] = "acknowledged"
            alert["acknowledged_at"] = datetime.utcnow().isoformat() + "Z"

            return Response(APIResponse.success(data=alert, message="Alert tasdiqlandi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["post"], url_path="alerts/(?P<alert_pk>[^/.]+)/resolve")
    def resolve_alert(self, request, alert_pk=None, pk=None):
        """Alertni yechish."""
        try:
            alert = MOCK_ALERTS.get(alert_pk)
            if not alert:
                return Response(APIResponse.not_found(message=f"Alert topilmadi: {alert_pk}"))

            alert["status"] = "resolved"
            alert["resolved_at"] = datetime.utcnow().isoformat() + "Z"

            return Response(APIResponse.success(data=alert, message="alert hal qilindi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=False, methods=["get"])
    def health(self, request):
        """Sog'liq tekshiruvi."""
        try:
            all_healthy = all(h["status"] == "healthy" for h in MOCK_HEALTH_CHECKS.values())

            return Response(
                APIResponse.success(
                    data=MOCK_HEALTH_CHECKS,
                    metadata={
                        "overall_status": "healthy" if all_healthy else "degraded",
                        "checked_at": datetime.utcnow().isoformat() + "Z",
                    },
                )
            )
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["get"], url_path="health/(?P<service>[^/.]+)")
    def service_health(self, request, service=None, pk=None):
        """Xizmat sog'ligi."""
        try:
            health = MOCK_HEALTH_CHECKS.get(service)
            if not health:
                return Response(APIResponse.not_found(message=f"Xizmat topilmadi: {service}"))
            return Response(
                APIResponse.success(
                    data=health,
                    metadata={"service": service},
                )
            )
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=False, methods=["get"])
    def logs(self, request):
        """Tizim loglari."""
        try:
            logs = MOCK_LOGS.copy()

            level = request.query_params.get("level")
            if level:
                logs = [l for l in logs if l["level"] == level]

            service = request.query_params.get("service")
            if service:
                logs = [l for l in logs if l["service"] == service]

            limit = int(request.query_params.get("limit", 50))
            logs = logs[:limit]

            return Response(
                APIResponse.success(
                    data=logs,
                    metadata={"total": len(logs)},
                )
            )
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        """Dashboard ma'lumotlari — barchasi bir joyda."""
        try:
            active_alerts = sum(
                1 for a in MOCK_ALERTS.values() if a["status"] == "active"
            )
            critical_alerts = sum(
                1 for a in MOCK_ALERTS.values()
                if a["status"] == "active" and a["severity"] == "critical"
            )
            all_healthy = all(h["status"] == "healthy" for h in MOCK_HEALTH_CHECKS.values())

            dashboard = {
                "overview": {
                    "system_status": "healthy" if all_healthy else "degraded",
                    "active_alerts": active_alerts,
                    "critical_alerts": critical_alerts,
                    "uptime_hours": MOCK_METRICS["system"]["uptime_seconds"] // 3600,
                },
                "metrics_summary": {
                    "cpu_percent": MOCK_METRICS["system"]["cpu_usage_percent"],
                    "memory_percent": MOCK_METRICS["system"]["memory_usage_percent"],
                    "api_rpm": MOCK_METRICS["api"]["requests_per_minute"],
                    "api_avg_response_ms": MOCK_METRICS["api"]["avg_response_time_ms"],
                    "api_error_rate": MOCK_METRICS["api"]["error_rate_percent"],
                },
                "recent_alerts": [
                    a for a in MOCK_ALERTS.values() if a["status"] == "active"
                ][:5],
                "health_summary": {
                    name: h["status"] for name, h in MOCK_HEALTH_CHECKS.items()
                },
            }

            return Response(APIResponse.success(data=dashboard))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))
