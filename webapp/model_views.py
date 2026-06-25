"""
Task 4 — Model Management API Views.
Barcha model API endpointlarini birlashtirilgan holda taqdim etadi.
"""

import json
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

try:
    from .model_discovery import discover_all
    HAS_DISCOVERY = True
except ImportError:
    HAS_DISCOVERY = False

try:
    from .model_manager import ModelManager
    HAS_MANAGER = True
except ImportError:
    HAS_MANAGER = False

try:
    from .model_auto_start import ModelAutoStart, ModelProvider, ProviderStatus
    HAS_AUTOSTART = True
except ImportError:
    HAS_AUTOSTART = False


def _get_auto_start():
    if not HAS_AUTOSTART:
        return None
    from pathlib import Path
    project_path = Path(__file__).resolve().parent.parent
    return ModelAutoStart(str(project_path))


# ──────────────────────────────────────────────
# DISCOVERY
# ──────────────────────────────────────────────

@require_GET
def model_discover(request):
    """Barcha provider'lardan modellarni topish."""
    if not HAS_DISCOVERY:
        return JsonResponse({"error": "Discovery module not available"}, status=503)
    try:
        result = discover_all()
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ──────────────────────────────────────────────
# MANAGER (unified CRUD)
# ──────────────────────────────────────────────

@require_GET
def manager_list(request):
    """Barcha modellarni unified ro'yxatda qaytarish."""
    if not HAS_MANAGER:
        return JsonResponse({"error": "Manager module not available"}, status=503)
    try:
        return JsonResponse(ModelManager.list_all())
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def manager_get(request, model_id: str):
    """Model haqida batafsil ma'lumot."""
    if not HAS_MANAGER:
        return JsonResponse({"error": "Manager module not available"}, status=503)
    try:
        return JsonResponse(ModelManager.get_model(model_id))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_POST
def manager_pull(request):
    """Modelni Ollama'ga yuklab olish (pull)."""
    if not HAS_MANAGER:
        return JsonResponse({"error": "Manager module not available"}, status=503)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "JSON noto'g'ri"}, status=400)
    model = str(body.get("model", "")).strip()
    if not model:
        return JsonResponse({"error": "model nomi kerak"}, status=400)
    try:
        return JsonResponse(ModelManager.pull_model(model))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_POST
def manager_remove(request):
    """Modelni Ollama'dan o'chirish."""
    if not HAS_MANAGER:
        return JsonResponse({"error": "Manager module not available"}, status=503)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "JSON noto'g'ri"}, status=400)
    model = str(body.get("model", "")).strip()
    if not model:
        return JsonResponse({"error": "model nomi kerak"}, status=400)
    try:
        return JsonResponse(ModelManager.remove_model(model))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_POST
def manager_load(request):
    """Modelni LM Studio'ga yuklash."""
    if not HAS_MANAGER:
        return JsonResponse({"error": "Manager module not available"}, status=503)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "JSON noto'g'ri"}, status=400)
    model = str(body.get("model", "")).strip()
    if not model:
        return JsonResponse({"error": "model nomi kerak"}, status=400)
    try:
        return JsonResponse(ModelManager.load_model(model))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_POST
def manager_unload(request):
    """LM Studio'dagi modelni tushirish."""
    if not HAS_MANAGER:
        return JsonResponse({"error": "Manager module not available"}, status=503)
    try:
        return JsonResponse(ModelManager.unload_model())
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_POST
def manager_select(request):
    """Modelni avtomatik tanlash (Ollama → LM Studio)."""
    if not HAS_MANAGER:
        return JsonResponse({"error": "Manager module not available"}, status=503)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "JSON noto'g'ri"}, status=400)
    model = str(body.get("model", "")).strip()
    if not model:
        return JsonResponse({"error": "model nomi kerak"}, status=400)
    try:
        return JsonResponse(ModelManager.select_active(model))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ──────────────────────────────────────────────
# AUTO-START (provider management)
# ──────────────────────────────────────────────

@require_GET
def models_status(request):
    """Barcha provider'larning holatini qaytarish."""
    auto_start = _get_auto_start()
    if not auto_start:
        return JsonResponse({"error": "Auto-start system not available"}, status=503)
    try:
        report = auto_start.get_status_report()
        return JsonResponse(report)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_POST
def models_start(request, provider_name: str):
    """Provider'ni ishga tushirish."""
    auto_start = _get_auto_start()
    if not auto_start:
        return JsonResponse({"error": "Auto-start system not available"}, status=503)
    try:
        provider_map = {
            "ollama": ModelProvider.OLLAMA,
            "lmstudio": ModelProvider.LM_STUDIO,
        }
        provider = provider_map.get(provider_name.lower())
        if not provider:
            return JsonResponse({"error": f"Noma'lum provider: {provider_name}"}, status=400)
        success = auto_start.start_provider(provider)
        health = auto_start.check_provider_health(provider) if success else None
        return JsonResponse({
            "success": success,
            "provider": provider_name,
            "status": health.status.value if health else "error",
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_POST
def models_stop(request, provider_name: str):
    """Provider'ni to'xtatish."""
    auto_start = _get_auto_start()
    if not auto_start:
        return JsonResponse({"error": "Auto-start system not available"}, status=503)
    try:
        provider_map = {
            "ollama": ModelProvider.OLLAMA,
            "lmstudio": ModelProvider.LM_STUDIO,
        }
        provider = provider_map.get(provider_name.lower())
        if not provider:
            return JsonResponse({"error": f"Noma'lum provider: {provider_name}"}, status=400)
        success = auto_start.stop_provider(provider)
        return JsonResponse({"success": success, "provider": provider_name})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_POST
def models_switch(request, provider_name: str):
    """Active provider'ni almashtirish."""
    if not HAS_AUTOSTART:
        return JsonResponse({"error": "Auto-start system not available"}, status=503)
    if provider_name not in ("ollama", "lmstudio", "collab", "local"):
        return JsonResponse({"error": f"Noma'lum provider: {provider_name}"}, status=400)
    try:
        import os
        # .env faylda AIDA_PROVIDER ni yangilaymiz
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if env_path.exists():
            content = env_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            new_lines = []
            for line in lines:
                if line.startswith("AIDA_PROVIDER="):
                    new_lines.append(f"AIDA_PROVIDER={provider_name}")
                else:
                    new_lines.append(line)
            env_path.write_text("\n".join(new_lines), encoding="utf-8")
        os.environ["AIDA_PROVIDER"] = provider_name
        return JsonResponse({"success": True, "provider": provider_name,
                             "message": f"Provider {provider_name} ga o'zgartirildi. Qayta ishga tushiring."})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_POST
def models_install(request, provider_name: str):
    """Modelni provider'ga o'rnatish."""
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "JSON noto'g'ri"}, status=400)
    model = str(body.get("model", "")).strip()
    if not model:
        return JsonResponse({"error": "model nomi kerak"}, status=400)
    if provider_name == "ollama":
        if not HAS_MANAGER:
            return JsonResponse({"error": "Manager module not available"}, status=503)
        return JsonResponse(ModelManager.pull_model(model))
    return JsonResponse({"error": f"Install not supported for {provider_name}"}, status=400)


@csrf_exempt
@require_POST
def models_pull(request):
    """Model pull qilish (Ollama uchun shortcut)."""
    if not HAS_MANAGER:
        return JsonResponse({"error": "Manager module not available"}, status=503)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "JSON noto'g'ri"}, status=400)
    model = str(body.get("model", "")).strip()
    if not model:
        return JsonResponse({"error": "model nomi kerak"}, status=400)
    try:
        return JsonResponse(ModelManager.pull_model(model))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
