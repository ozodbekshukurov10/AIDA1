"""
AIDA Enterprise API — AI Models ViewSet

AI modellarini boshqarish endpointlari:
- GET    /models/                      — Modellar ro'yxati
- GET    /models/{id}/                 — Model ma'lumotlari
- POST   /models/switch/               — Faol modelni almashtirish
- GET    /models/providers/            — Providerlar ro'yxati
- POST   /models/providers/{name}/health/ — Provider sog'lig'ini tekshirish
- GET    /models/status/               — Tizim modeli holati
"""
from __future__ import annotations
from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..responses import APIResponse


# ── Mock Data ──────────────────────────────────────────────────────────────────

MOCK_MODELS = [
    {
        "id": "gpt-4o",
        "name": "GPT-4o",
        "provider": "openai",
        "type": "chat",
        "max_tokens": 128000,
        "cost_per_1k_input": 0.005,
        "cost_per_1k_output": 0.015,
        "capabilities": ["text", "vision", "function_calling"],
        "status": "available",
    },
    {
        "id": "gpt-4o-mini",
        "name": "GPT-4o Mini",
        "provider": "openai",
        "type": "chat",
        "max_tokens": 128000,
        "cost_per_1k_input": 0.00015,
        "cost_per_1k_output": 0.0006,
        "capabilities": ["text", "vision", "function_calling"],
        "status": "available",
    },
    {
        "id": "gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "provider": "gemini",
        "type": "chat",
        "max_tokens": 1048576,
        "cost_per_1k_input": 0.00125,
        "cost_per_1k_output": 0.01,
        "capabilities": ["text", "vision", "code", "function_calling"],
        "status": "available",
    },
    {
        "id": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "provider": "gemini",
        "type": "chat",
        "max_tokens": 1048576,
        "cost_per_1k_input": 0.000075,
        "cost_per_1k_output": 0.0003,
        "capabilities": ["text", "vision", "code"],
        "status": "available",
    },
    {
        "id": "llama3.1-70b",
        "name": "LLaMA 3.1 70B",
        "provider": "ollama",
        "type": "chat",
        "max_tokens": 131072,
        "cost_per_1k_input": 0.0,
        "cost_per_1k_output": 0.0,
        "capabilities": ["text", "code"],
        "status": "available",
    },
    {
        "id": "llama3.1-8b",
        "name": "LLaMA 3.1 8B",
        "provider": "ollama",
        "type": "chat",
        "max_tokens": 131072,
        "cost_per_1k_input": 0.0,
        "cost_per_1k_output": 0.0,
        "capabilities": ["text"],
        "status": "available",
    },
]

MOCK_PROVIDERS = [
    {
        "name": "openai",
        "display_name": "OpenAI",
        "status": "healthy",
        "models_count": 2,
        "api_key_configured": True,
        "base_url": "https://api.openai.com/v1",
        "rate_limit": 10000,
        "last_health_check": "2026-07-04T10:30:00Z",
    },
    {
        "name": "gemini",
        "display_name": "Google Gemini",
        "status": "healthy",
        "models_count": 2,
        "api_key_configured": True,
        "base_url": "https://generativelanguage.googleapis.com",
        "rate_limit": 15000,
        "last_health_check": "2026-07-04T10:30:00Z",
    },
    {
        "name": "ollama",
        "display_name": "Ollama (Local)",
        "status": "healthy",
        "models_count": 2,
        "api_key_configured": False,
        "base_url": "http://localhost:11434",
        "rate_limit": -1,
        "last_health_check": "2026-07-04T10:30:00Z",
    },
]

MOCK_ACTIVE_MODEL = {
    "id": "gpt-4o",
    "name": "GPT-4o",
    "provider": "openai",
    "switched_at": "2026-07-04T08:00:00Z",
    "switched_by": "admin@aida.io",
}


class ModelsViewSet(viewsets.ViewSet):
    """
    AI modellarini boshqarish.

    - GET    /models/                      — Modellar ro'yxati
    - GET    /models/{id}/                 — Model ma'lumotlari
    - POST   /models/switch/               — Faol modelni almashtirish
    - GET    /models/providers/            — Providerlar ro'yxati
    - POST   /models/providers/{name}/health/ — Provider sog'lig'ini tekshirish
    - GET    /models/status/               — Tizim modeli holati
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Modellar ro'yxati."""
        provider = request.query_params.get("provider")
        model_type = request.query_params.get("type")

        models = MOCK_MODELS[:]
        if provider:
            models = [m for m in models if m["provider"] == provider]
        if model_type:
            models = [m for m in models if m["type"] == model_type]

        return Response(
            APIResponse.success(
                data=models,
                metadata={"total": len(models)},
            )
        )

    def retrieve(self, request, pk=None):
        """Model ma'lumotlari."""
        model = next((m for m in MOCK_MODELS if m["id"] == pk), None)
        if not model:
            return Response(
                APIResponse.not_found(message=f"Model topilmadi: {pk}"),
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(APIResponse.success(data=model))

    @action(detail=False, methods=["post"], url_path="switch")
    def switch_model(self, request):
        """Faol modelni almashtirish."""
        model_id = request.data.get("model_id")
        if not model_id:
            return Response(
                APIResponse.bad_request(message="model_id kiritilishi shart."),
                status=status.HTTP_400_BAD_REQUEST,
            )

        model = next((m for m in MOCK_MODELS if m["id"] == model_id), None)
        if not model:
            return Response(
                APIResponse.not_found(message=f"Model topilmadi: {model_id}"),
                status=status.HTTP_404_NOT_FOUND,
            )

        global MOCK_ACTIVE_MODEL
        MOCK_ACTIVE_MODEL = {
            "id": model["id"],
            "name": model["name"],
            "provider": model["provider"],
            "switched_at": datetime.utcnow().isoformat() + "Z",
            "switched_by": request.user.email if hasattr(request.user, "email") else "unknown",
        }

        return Response(
            APIResponse.success(
                data=MOCK_ACTIVE_MODEL,
                message=f"Faol model '{model['name']}' ga almashtirildi.",
            )
        )

    @action(detail=False, methods=["get"], url_path="providers")
    def list_providers(self, request):
        """Providerlar ro'yxati."""
        return Response(
            APIResponse.success(
                data=MOCK_PROVIDERS,
                metadata={"total": len(MOCK_PROVIDERS)},
            )
        )

    @action(detail=False, methods=["post"], url_path=r"providers/(?P<name>[^/.]+)/health")
    def provider_health(self, request, name=None):
        """Provider sog'lig'ini tekshirish."""
        provider = next((p for p in MOCK_PROVIDERS if p["name"] == name), None)
        if not provider:
            return Response(
                APIResponse.not_found(message=f"Provider topilmadi: {name}"),
                status=status.HTTP_404_NOT_FOUND,
            )

        health_data = {
            "provider": name,
            "status": "healthy",
            "latency_ms": 42,
            "checked_at": datetime.utcnow().isoformat() + "Z",
            "details": {
                "api_reachable": True,
                "models_loaded": provider["models_count"],
                "queue_depth": 0,
            },
        }

        return Response(
            APIResponse.success(
                data=health_data,
                message=f"{provider['display_name']} sog'lom.",
            )
        )

    @action(detail=False, methods=["get"], url_path="status")
    def system_status(self, request):
        """Tizim modeli holati."""
        status_data = {
            "active_model": MOCK_ACTIVE_MODEL,
            "providers_summary": [
                {
                    "name": p["name"],
                    "status": p["status"],
                    "models_count": p["models_count"],
                }
                for p in MOCK_PROVIDERS
            ],
            "total_models": len(MOCK_MODELS),
            "uptime_hours": 168,
            "total_requests_today": 1247,
            "avg_latency_ms": 380,
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }

        return Response(APIResponse.success(data=status_data))
