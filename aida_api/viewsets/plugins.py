"""
AIDA Enterprise API — Plugins ViewSet

Pluginlarni boshqarish uchun CRUD va maxsus endpointlar.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..responses import APIResponse

MOCK_PLUGINS = {
    "plugin_1": {
        "id": "plugin_1",
        "name": "aida-slack",
        "display_name": "Slack Integration",
        "description": "AIDA ni Slack bilan bog'laydi — xabarlarni kanallarga yuboradi",
        "version": "2.1.0",
        "author": "aida-team",
        "category": "messaging",
        "status": "active",
        "enabled": True,
        "installed": True,
        "config": {
            "webhook_url": "https://hooks.slack.com/services/xxx/yyy/zzz",
            "channel": "#aida-alerts",
            "mention_on_critical": "@channel",
        },
        "permissions": ["read_messages", "post_messages", "manage_channels"],
        "rating": 4.8,
        "downloads": 12560,
        "created_at": "2025-09-01T10:00:00Z",
        "updated_at": "2026-06-15T12:00:00Z",
    },
    "plugin_2": {
        "id": "plugin_2",
        "name": "aida-jira",
        "display_name": "Jira Integration",
        "description": "Jira bilan integratsiya — vazifalarni sinxronlashtiradi",
        "version": "1.5.3",
        "author": "aida-team",
        "category": "project-management",
        "status": "active",
        "enabled": True,
        "installed": True,
        "config": {
            "instance_url": "https://aida-team.atlassian.net",
            "project_key": "AIDA",
            "sync_interval_minutes": 15,
        },
        "permissions": ["read_issues", "create_issues", "update_issues"],
        "rating": 4.5,
        "downloads": 8930,
        "created_at": "2025-10-15T08:00:00Z",
        "updated_at": "2026-07-01T09:00:00Z",
    },
    "plugin_3": {
        "id": "plugin_3",
        "name": "aida-github",
        "display_name": "GitHub Integration",
        "description": "GitHub bilan integratsiya — repozitoriyalarni boshqaradi",
        "version": "3.0.1",
        "author": "community",
        "category": "version-control",
        "status": "active",
        "enabled": False,
        "installed": True,
        "config": {
            "token": "ghp_xxx",
            "organization": "aida-team",
        },
        "permissions": ["read_repos", "manage_webhooks"],
        "rating": 4.7,
        "downloads": 15670,
        "created_at": "2025-08-20T14:00:00Z",
        "updated_at": "2026-06-28T11:00:00Z",
    },
    "plugin_4": {
        "id": "plugin_4",
        "name": "aida-analytics",
        "display_name": "Analytics Dashboard",
        "description": "Batafsil analitika va hisobot dashboardi",
        "version": "1.0.0",
        "author": "community",
        "category": "analytics",
        "status": "beta",
        "enabled": False,
        "installed": False,
        "config": {},
        "permissions": ["read_metrics", "export_reports"],
        "rating": 4.2,
        "downloads": 3210,
        "created_at": "2026-03-10T16:00:00Z",
        "updated_at": "2026-06-20T14:00:00Z",
    },
}

PLUGIN_CATEGORIES = [
    {"id": "messaging", "name": "Xabardorlik", "count": 2},
    {"id": "project-management", "name": "Loyiha boshqarish", "count": 3},
    {"id": "version-control", "name": "Kod boshqarish", "count": 4},
    {"id": "analytics", "name": "Analitika", "count": 2},
    {"id": "security", "name": "Xavfsizlik", "count": 3},
    {"id": "ci-cd", "name": "CI/CD", "count": 2},
]

PLUGIN_EVENTS = [
    {"event": "plugin.installed", "description": "Plugin o'rnatildi"},
    {"event": "plugin.enabled", "description": "Plugin yoqildi"},
    {"event": "plugin.disabled", "description": "Plugin o'chirildi"},
    {"event": "plugin.uninstalled", "description": "Plugin o'chirildi"},
    {"event": "plugin.config_updated", "description": "Plugin konfiguratsiyasi yangilandi"},
]


class PluginsViewSet(viewsets.ViewSet):
    """
    Pluginlarni boshqarish.

    - GET    /plugins/                   — Pluginlar ro'yxati
    - POST   /plugins/                   — Yangi plugin yaratish
    - GET    /plugins/{id}/              — Bitta plugin
    - PUT    /plugins/{id}/              — Pluginni to'liq yangilash
    - PATCH  /plugins/{id}/              — Pluginni qisman yangilash
    - DELETE /plugins/{id}/              — Pluginni o'chirish
    - POST   /plugins/{id}/install/      — Pluginni o'rnatish
    - POST   /plugins/{id}/uninstall/    — Pluginni o'chirish
    - POST   /plugins/{id}/enable/       — Pluginni yoqish
    - POST   /plugins/{id}/disable/      — Pluginni o'chirish
    - PUT    /plugins/{id}/config/       — Plugin konfiguratsiyasini yangilash
    - GET    /plugins/categories/        — Plugin kategoriyalari
    - GET    /plugins/events/            — Plugin hodisalari
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Pluginlar ro'yxati."""
        try:
            plugins = list(MOCK_PLUGINS.values())

            category = request.query_params.get("category")
            if category:
                plugins = [p for p in plugins if p["category"] == category]

            installed = request.query_params.get("installed")
            if installed is not None:
                is_installed = installed.lower() in ("true", "1", "yes")
                plugins = [p for p in plugins if p["installed"] == is_installed]

            enabled = request.query_params.get("enabled")
            if enabled is not None:
                is_enabled = enabled.lower() in ("true", "1", "yes")
                plugins = [p for p in plugins if p["enabled"] == is_enabled]

            search = request.query_params.get("search")
            if search:
                plugins = [
                    p for p in plugins
                    if search.lower() in p["name"].lower() or search.lower() in p["display_name"].lower()
                ]

            return Response(APIResponse.success(data=plugins))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    def create(self, request):
        """Yangi plugin yaratish."""
        try:
            name = request.data.get("name")
            if not name:
                return Response(APIResponse.bad_request(message="Plugin nomi kiritilishi shart."))

            display_name = request.data.get("display_name", name)
            plugin_id = f"plugin_{uuid.uuid4().hex[:8]}"
            now = datetime.utcnow().isoformat() + "Z"

            plugin = {
                "id": plugin_id,
                "name": name,
                "display_name": display_name,
                "description": request.data.get("description", ""),
                "version": request.data.get("version", "0.1.0"),
                "author": request.data.get("author", "community"),
                "category": request.data.get("category", "other"),
                "status": "draft",
                "enabled": False,
                "installed": False,
                "config": request.data.get("config", {}),
                "permissions": request.data.get("permissions", []),
                "rating": 0,
                "downloads": 0,
                "created_at": now,
                "updated_at": now,
            }
            MOCK_PLUGINS[plugin_id] = plugin

            return Response(
                APIResponse.created(data=plugin, message="Plugin yaratildi."),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    def retrieve(self, request, pk=None):
        """Bitta plugin."""
        try:
            plugin = MOCK_PLUGINS.get(pk)
            if not plugin:
                return Response(APIResponse.not_found(message=f"Plugin topilmadi: {pk}"))
            return Response(APIResponse.success(data=plugin))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    def update(self, request, pk=None):
        """Pluginni to'liq yangilash."""
        try:
            plugin = MOCK_PLUGINS.get(pk)
            if not plugin:
                return Response(APIResponse.not_found(message=f"Plugin topilmadi: {pk}"))

            plugin.update({
                "name": request.data.get("name", plugin["name"]),
                "display_name": request.data.get("display_name", plugin["display_name"]),
                "description": request.data.get("description", plugin["description"]),
                "version": request.data.get("version", plugin["version"]),
                "author": request.data.get("author", plugin["author"]),
                "category": request.data.get("category", plugin["category"]),
                "permissions": request.data.get("permissions", plugin["permissions"]),
                "updated_at": datetime.utcnow().isoformat() + "Z",
            })

            return Response(APIResponse.success(data=plugin, message="Plugin yangilandi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    def partial_update(self, request, pk=None):
        """Pluginni qisman yangilash."""
        try:
            plugin = MOCK_PLUGINS.get(pk)
            if not plugin:
                return Response(APIResponse.not_found(message=f"Plugin topilmadi: {pk}"))

            for key in ["name", "display_name", "description", "version", "category", "permissions"]:
                if key in request.data:
                    plugin[key] = request.data[key]
            plugin["updated_at"] = datetime.utcnow().isoformat() + "Z"

            return Response(APIResponse.success(data=plugin, message="Plugin yangilandi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    def destroy(self, request, pk=None):
        """Pluginni o'chirish."""
        try:
            plugin = MOCK_PLUGINS.pop(pk, None)
            if not plugin:
                return Response(APIResponse.not_found(message=f"Plugin topilmadi: {pk}"))
            return Response(APIResponse.success(message="Plugin o'chirildi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["post"])
    def install(self, request, pk=None):
        """Pluginni o'rnatish."""
        try:
            plugin = MOCK_PLUGINS.get(pk)
            if not plugin:
                return Response(APIResponse.not_found(message=f"Plugin topilmadi: {pk}"))

            if plugin["installed"]:
                return Response(APIResponse.bad_request(message="Plugin allaqachon o'rnatilgan."))

            plugin["installed"] = True
            plugin["status"] = "active"
            plugin["updated_at"] = datetime.utcnow().isoformat() + "Z"

            return Response(APIResponse.success(data=plugin, message="Plugin muvaffaqiyatli o'rnatildi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["post"])
    def uninstall(self, request, pk=None):
        """Pluginni o'chirish."""
        try:
            plugin = MOCK_PLUGINS.get(pk)
            if not plugin:
                return Response(APIResponse.not_found(message=f"Plugin topilmadi: {pk}"))

            if not plugin["installed"]:
                return Response(APIResponse.bad_request(message="Plugin o'rnatilmagan."))

            plugin["installed"] = False
            plugin["enabled"] = False
            plugin["status"] = "inactive"
            plugin["config"] = {}
            plugin["updated_at"] = datetime.utcnow().isoformat() + "Z"

            return Response(APIResponse.success(data=plugin, message="Plugin o'chirildi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["post"])
    def enable(self, request, pk=None):
        """Pluginni yoqish."""
        try:
            plugin = MOCK_PLUGINS.get(pk)
            if not plugin:
                return Response(APIResponse.not_found(message=f"Plugin topilmadi: {pk}"))

            if not plugin["installed"]:
                return Response(APIResponse.bad_request(message="Plugin avval o'rnatilishi kerak."))

            plugin["enabled"] = True
            plugin["updated_at"] = datetime.utcnow().isoformat() + "Z"

            return Response(APIResponse.success(data=plugin, message="Plugin yoqildi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["post"])
    def disable(self, request, pk=None):
        """Pluginni o'chirish."""
        try:
            plugin = MOCK_PLUGINS.get(pk)
            if not plugin:
                return Response(APIResponse.not_found(message=f"Plugin topilmadi: {pk}"))

            plugin["enabled"] = False
            plugin["updated_at"] = datetime.utcnow().isoformat() + "Z"

            return Response(APIResponse.success(data=plugin, message="Plugin o'chirildi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["put"], url_path="config")
    def update_config(self, request, pk=None):
        """Plugin konfiguratsiyasini yangilash."""
        try:
            plugin = MOCK_PLUGINS.get(pk)
            if not plugin:
                return Response(APIResponse.not_found(message=f"Plugin topilmadi: {pk}"))

            if not plugin["installed"]:
                return Response(APIResponse.bad_request(message="Plugin avval o'rnatilishi kerak."))

            new_config = request.data.get("config")
            if not new_config:
                return Response(APIResponse.bad_request(message="Config ma'lumotlari kiritilishi shart."))

            plugin["config"].update(new_config)
            plugin["updated_at"] = datetime.utcnow().isoformat() + "Z"

            return Response(APIResponse.success(data=plugin, message="Plugin konfiguratsiyasi yangilandi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=False, methods=["get"])
    def categories(self, request):
        """Plugin kategoriyalari."""
        try:
            return Response(APIResponse.success(data=PLUGIN_CATEGORIES))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=False, methods=["get"])
    def events(self, request):
        """Plugin hodisalari."""
        try:
            return Response(APIResponse.success(data=PLUGIN_EVENTS))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))
