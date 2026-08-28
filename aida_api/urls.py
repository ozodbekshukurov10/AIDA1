"""
AIDA Enterprise API — URL Router

Barcha API endpointlari uchun yagona URL router.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# ── ViewSet Imports ────────────────────────────────────────────────────────────
from .viewsets.auth import AuthViewSet
from .viewsets.api_keys import APIKeyViewSet
from .viewsets.users import UserViewSet
from .viewsets.chats import ChatViewSet
from .viewsets.messages import MessageViewSet
from .viewsets.models import ModelsViewSet
from .viewsets.agents import AgentsViewSet
from .viewsets.memory import MemoryViewSet
from .viewsets.knowledge import KnowledgeViewSet
from .viewsets.tasks import TasksViewSet
from .viewsets.repositories import RepositoriesViewSet
from .viewsets.sandbox import SandboxViewSet
from .viewsets.monitoring import MonitoringViewSet
from .viewsets.plugins import PluginsViewSet
from .viewsets.streaming import StreamingViewSet

# ── Router ─────────────────────────────────────────────────────────────────────
router = DefaultRouter()
router.trailing_slash = False

# Auth & Account
router.register(r"auth", AuthViewSet, basename="auth")
router.register(r"api-keys", APIKeyViewSet, basename="api-keys")

# Users
router.register(r"users", UserViewSet, basename="users")

# Chat & Messages
router.register(r"chats", ChatViewSet, basename="chats")
router.register(r"messages", MessageViewSet, basename="messages")

# AI Models & Agents
router.register(r"models", ModelsViewSet, basename="models")
router.register(r"agents", AgentsViewSet, basename="agents")

# Memory & Knowledge
router.register(r"memory", MemoryViewSet, basename="memory")
router.register(r"knowledge", KnowledgeViewSet, basename="knowledge")

# Tasks & Workflows
router.register(r"tasks", TasksViewSet, basename="tasks")

# DevOps
router.register(r"repositories", RepositoriesViewSet, basename="repositories")
router.register(r"sandbox", SandboxViewSet, basename="sandbox")

# Monitoring
router.register(r"monitoring", MonitoringViewSet, basename="monitoring")

# Plugins
router.register(r"plugins", PluginsViewSet, basename="plugins")

# Streaming
router.register(r"stream", StreamingViewSet, basename="stream")

# ── URL Patterns ───────────────────────────────────────────────────────────────
urlpatterns = [
    # API v1 — Asosiy
    path("v1/", include([
        # Router URLs
        path("", include(router.urls)),

        # Health check
        path("health/", include("aida_api.health.urls")),
    ])),

    # API v2 — Legacy compatibility already in webapp.urls

    # Public API — Autentifikatsiya talab qilinmaydi
    path("public/", include("aida_api.public.urls")),

    # Internal API — Faqat service-to-service
    path("internal/", include("aida_api.internal.urls")),

    # Admin API — Faqat admin foydalanuvchilar
    path("admin/", include("aida_api.admin.urls")),

    # OpenAPI Schema
    path("schema/", SpectacularAPIView.as_view(), name="schema"),

    # Swagger UI
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    # ReDoc
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
