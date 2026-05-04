import json
import mimetypes
import uuid
from pathlib import Path

from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .aida_controller import controller
from .models import AccessKey
from .security import authenticate_access_key, generate_access_key_with_profile


DIST_DIR = Path(__file__).resolve().parent.parent / "dist"
ASSETS_DIR = DIST_DIR / "assets"


def spa_index(request):
    dist_index = DIST_DIR / "index.html"
    template_name = "index.html" if dist_index.exists() else "webapp/build_pending.html"
    return render(request, template_name)


@require_GET
def dist_asset(request, asset_path: str):
    file_path = (ASSETS_DIR / asset_path).resolve()
    if not str(file_path).startswith(str(ASSETS_DIR.resolve())) or not file_path.exists():
        raise Http404("Asset topilmadi.")

    content_type, encoding = mimetypes.guess_type(file_path.name)
    response = FileResponse(open(file_path, "rb"), content_type=content_type or "application/octet-stream")
    if encoding:
        response["Content-Encoding"] = encoding
    return response


@require_GET
def api_status(request):
    return JsonResponse(controller.status())


@require_GET
def api_keys_list(request):
    keys = AccessKey.objects.all().values(
        "id",
        "name",
        "prefix",
        "platform_name",
        "business_type",
        "audience",
        "tone",
        "assistant_goal",
        "custom_instructions",
        "created_at",
        "last_used_at",
        "is_active",
    )
    return JsonResponse({"items": list(keys)})


@csrf_exempt
@require_POST
def api_keys_create(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON formati noto'g'ri."}, status=400)

    name = str(payload.get("name", "")).strip() or "Platform key"
    profile = {
        "platform_name": payload.get("platform_name", ""),
        "business_type": payload.get("business_type", ""),
        "audience": payload.get("audience", ""),
        "tone": payload.get("tone", ""),
        "assistant_goal": payload.get("assistant_goal", ""),
        "custom_instructions": payload.get("custom_instructions", ""),
    }
    access_key, raw_secret = generate_access_key_with_profile(name, profile)
    return JsonResponse(
        {
            "id": access_key.id,
            "name": access_key.name,
            "prefix": access_key.prefix,
            "platform_name": access_key.platform_name,
            "business_type": access_key.business_type,
            "audience": access_key.audience,
            "tone": access_key.tone,
            "assistant_goal": access_key.assistant_goal,
            "custom_instructions": access_key.custom_instructions,
            "secret": raw_secret,
            "created_at": access_key.created_at.isoformat(),
        },
        status=201,
    )


@csrf_exempt
@require_POST
def api_chat(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON formati noto'g'ri."}, status=400)

    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        return JsonResponse({"error": "Prompt yuborilmadi."}, status=400)

    research_enabled = bool(payload.get("research"))
    session_id = str(payload.get("session_id", "default")).strip() or "default"

    runtime_context = {
        "page": str(payload.get("page", "")).strip(),
        "customer_intent": str(payload.get("customer_intent", "")).strip(),
        "locale": str(payload.get("locale", "")).strip(),
    }

    try:
        response = controller.chat(
            prompt,
            runtime_context=runtime_context,
            research_enabled=research_enabled,
            session_id=session_id,
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse(response)


@require_GET
def api_sessions_list(request):
    sessions = controller.sessions()
    return JsonResponse({"sessions": sessions})


@require_GET
def api_session_history(request, session_id: str):
    history = controller.session_history(session_id)
    return JsonResponse({"session_id": session_id, "messages": history})


@csrf_exempt
@require_POST
def api_session_create(request):
    new_id = str(uuid.uuid4())
    return JsonResponse({"session_id": new_id})


@csrf_exempt
@require_POST
def api_platform_chat(request):
    auth_header = request.headers.get("Authorization", "")
    bearer_key = auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else ""
    api_key = request.headers.get("X-AIDA-Key", "").strip() or bearer_key
    if not api_key:
        return JsonResponse({"error": "API key yuborilmadi."}, status=401)

    access_key = authenticate_access_key(api_key)
    if access_key is None:
        return JsonResponse({"error": "API key noto'g'ri yoki o'chirilgan."}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON formati noto'g'ri."}, status=400)

    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        return JsonResponse({"error": "Prompt yuborilmadi."}, status=400)
    research_enabled = bool(payload.get("research"))
    session_id = str(payload.get("session_id", "default")).strip() or "default"

    runtime_context = {
        "page": str(payload.get("page", "")).strip(),
        "customer_intent": str(payload.get("customer_intent", "")).strip(),
        "locale": str(payload.get("locale", "")).strip(),
    }

    try:
        response = controller.chat(
            prompt,
            platform_profile={
                "key_name": access_key.name,
                "platform_name": access_key.platform_name,
                "business_type": access_key.business_type,
                "audience": access_key.audience,
                "tone": access_key.tone,
                "assistant_goal": access_key.assistant_goal,
                "custom_instructions": access_key.custom_instructions,
            },
            runtime_context=runtime_context,
            research_enabled=research_enabled,
            session_id=session_id,
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse(
        {
            "message": response["message"],
            "status": response["status"],
            "key_name": access_key.name,
        }
    )
