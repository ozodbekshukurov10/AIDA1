import json
import logging
import mimetypes
import time
import uuid
from functools import wraps
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .aida_controller import CodeGenerator, controller, ReasoningEngine, runtime
from .models import AccessKey
from .security import authenticate_access_key, generate_access_key_with_profile

logger = logging.getLogger("webapp")


def safe_api_endpoint(view_func):
    @wraps(view_func)
    @csrf_exempt
    def wrapper(request, *args, **kwargs):
        origin = request.headers.get("Origin", "")
        allowed = settings.CSRF_TRUSTED_ORIGINS
        if origin:
            from urllib.parse import urlparse
            o = urlparse(origin).netloc
            # Ruxsat etilgan host yoki joriy so'rov yuborilgan xost bo'lsa (same-origin), ruxsat berish
            if o == request.get_host():
                return view_func(request, *args, **kwargs)
            if allowed:
                if not any(o == urlparse(a).netloc for a in allowed if a):
                    return JsonResponse({"error": "Not allowed origin"}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"
ASSETS_DIR = DIST_DIR / "assets"
LOGIN_HTML = BASE_DIR / "login.html"


def login_page(request):
    if LOGIN_HTML.exists():
        with open(LOGIN_HTML, "r", encoding="utf-8") as f:
            html = f.read()
        return HttpResponse(html, content_type="text/html; charset=utf-8")
    return spa_index(request)


def spa_index(request):
    dist_index = DIST_DIR / "index.html"
    template_name = "index.html" if dist_index.exists() else "webapp/build_pending.html"
    response = render(request, template_name)
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


@require_GET
def dist_asset(request, asset_path: str):
    resolved = (ASSETS_DIR / asset_path).resolve()
    try:
        resolved.relative_to(ASSETS_DIR.resolve())
    except ValueError:
        raise Http404("Asset topilmadi.")
    if not resolved.exists():
        raise Http404("Asset topilmadi.")
    file_path = resolved

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


@safe_api_endpoint
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


@safe_api_endpoint
@require_POST
def api_chat(request):
    content_type = request.headers.get("Content-Type", "")
    if "multipart/form-data" in content_type or "application/octet-stream" in content_type:
        return JsonResponse(
            {"error": "Men faqat matnli xabarlarni qabul qila olaman. Rasm yoki fayl yubordingiz, ammo men ularni qayta ishlay olmayman. Iltimos, matnli so'rov yuboring."},
            status=400,
        )
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON formati noto'g'ri."}, status=400)

    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        return JsonResponse({"error": "Prompt yuborilmadi."}, status=400)

    research_enabled = bool(payload.get("research"))
    session_id = str(payload.get("session_id", "default")).strip() or "default"
    mode = str(payload.get("mode", "")).strip().lower()

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
            mode=mode,
        )
    except ValueError as exc:
        logger.warning("Chat error: %s", exc)
        return JsonResponse({"error": str(exc)}, status=400)

    logger.info("Chat success: session=%s len=%d", session_id, len(prompt))
    return JsonResponse(response)


@safe_api_endpoint
@require_POST
def api_chat_stream(request):
    content_type = request.headers.get("Content-Type", "")
    if "multipart/form-data" in content_type or "application/octet-stream" in content_type:
        return JsonResponse({"error": "Faqat matnli xabarlar qabul qilinadi."}, status=400)
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

    message = response["message"]
    sources = response.get("sources", [])

    def event_stream():
        yield "data: {\"type\":\"meta\",\"session_id\":\"%s\"}\n\n" % session_id
        chunk_size = 20
        for i in range(0, len(message), chunk_size):
            chunk = message[i:i+chunk_size]
            yield "data: {\"type\":\"text\",\"content\":\"%s\"}\n\n" % chunk.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n")
            time.sleep(0.015)
        if sources:
            src_json = json.dumps(sources)
            yield "data: {\"type\":\"sources\",\"content\":%s}\n\n" % src_json
        yield "data: {\"type\":\"done\"}\n\n"

    response_http = HttpResponse(event_stream(), content_type="text/event-stream")
    response_http["Cache-Control"] = "no-cache"
    response_http["X-Accel-Buffering"] = "no"
    return response_http


@require_GET
def api_sessions_list(request):
    sessions = controller.sessions()
    return JsonResponse({"sessions": sessions})


@require_GET
def api_session_history(request, session_id: str):
    history = controller.session_history(session_id)
    return JsonResponse({"session_id": session_id, "messages": history})


@safe_api_endpoint
@require_POST
def api_session_create(request):
    new_id = str(uuid.uuid4())
    return JsonResponse({"session_id": new_id})


@safe_api_endpoint
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

    content_type = request.headers.get("Content-Type", "")
    if "multipart/form-data" in content_type or "application/octet-stream" in content_type:
        return JsonResponse(
            {"error": "Men faqat matnli xabarlarni qabul qila olaman. Rasm yoki fayl yubordingiz, ammo men ularni qayta ishlay olmayman. Iltimos, matnli so'rov yuboring."},
            status=400,
        )
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON formati noto'g'ri."}, status=400)

    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        return JsonResponse({"error": "Prompt yuborilmadi."}, status=400)
    research_enabled = bool(payload.get("research"))
    session_id = str(payload.get("session_id", "default")).strip() or "default"
    mode = str(payload.get("mode", "")).strip().lower()

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
            mode=mode,
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


CODE_HTML = BASE_DIR / "code.html"


@require_GET
def code_workspace(request):
    if CODE_HTML.exists():
        with open(CODE_HTML, "r", encoding="utf-8") as f:
            html = f.read()
        return HttpResponse(html, content_type="text/html; charset=utf-8")
    return HttpResponse("AIDA Code yuklanmadi", status=404)


@safe_api_endpoint
@require_POST
def api_code_generate(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)

    prompt = str(payload.get("prompt", "")).strip()
    language = str(payload.get("language", "python")).strip().lower()
    if not prompt:
        return JsonResponse({"error": "Prompt yuborilmadi."}, status=400)

    cg = CodeGenerator()
    reng = ReasoningEngine()

    trace = reng.reason(prompt, "code", reng._extract_keywords(prompt), [])
    code = cg.generate(prompt, language=language)
    analysis = cg.analyze(code, language=language)

    return JsonResponse({
        "code": code,
        "language": language,
        "trace": trace,
        "analysis": analysis,
        "preview_html": code if language in ("html", "css", "javascript", "js") else "",
    })


@safe_api_endpoint
@require_POST
def api_code_analyze(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)

    code = str(payload.get("code", "")).strip()
    language = str(payload.get("language", "python")).strip().lower()
    if not code:
        return JsonResponse({"error": "Kod yuborilmadi."}, status=400)

    cg = CodeGenerator()
    analysis = cg.analyze(code, language=language)
    fixed = cg.fix_errors(code, language=language)

    return JsonResponse({
        "analysis": analysis,
        "fixed": fixed,
        "language": language,
    })


@safe_api_endpoint
@require_POST
def api_code_preview(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)

    code = str(payload.get("code", "")).strip()
    language = str(payload.get("language", "html")).strip().lower()

    if language in ("html",):
        return JsonResponse({"html": code, "type": "html"})
    if language in ("css",):
        wrapped = "<!DOCTYPE html><html><head><style>" + code + "</style></head><body><p>CSS preview</p></body></html>"
        return JsonResponse({"html": wrapped, "type": "html"})
    if language in ("javascript", "js"):
        wrapped = "<!DOCTYPE html><html><head></head><body><script>" + code + "</script></body></html>"
        return JsonResponse({"html": wrapped, "type": "html"})

    return JsonResponse({"html": "<pre>" + code + "</pre>", "type": "text"})


@require_GET
def code_workspace_asset(request, file_path: str):
    try:
        data = runtime.read(file_path)
        if "error" in data:
            raise Http404(data["error"])
        content_type, _ = mimetypes.guess_type(file_path)
        return HttpResponse(data["content"], content_type=content_type or "text/plain; charset=utf-8")
    except ValueError:
        raise Http404("Xavfsizlik cheklovi")


@safe_api_endpoint
@require_POST
def api_runtime_save(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    path = str(payload.get("path", "")).strip()
    content = str(payload.get("content", ""))
    if not path or not content:
        return JsonResponse({"error": "path va content kerak"}, status=400)
    try:
        result = runtime.save(path, content)
        return JsonResponse(result)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)


@safe_api_endpoint
@require_POST
def api_runtime_read(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    path = str(payload.get("path", "")).strip()
    if not path:
        return JsonResponse({"error": "path kerak"}, status=400)
    try:
        result = runtime.read(path)
        return JsonResponse(result)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)


@safe_api_endpoint
@require_POST
def api_runtime_delete(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    path = str(payload.get("path", "")).strip()
    if not path:
        return JsonResponse({"error": "path kerak"}, status=400)
    try:
        result = runtime.delete(path)
        return JsonResponse(result)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_GET
def api_runtime_files(request):
    try:
        files = runtime.tree()
        return JsonResponse({"files": files})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_runtime_run(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    path = str(payload.get("path", "")).strip()
    if not path:
        return JsonResponse({"error": "path kerak"}, status=400)
    try:
        result = runtime.run(path)
        return JsonResponse(result)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)


@safe_api_endpoint
@require_POST
def api_runtime_server_start(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    path = str(payload.get("path", "")).strip()
    port = int(payload.get("port", 0))
    if not path:
        return JsonResponse({"error": "path kerak"}, status=400)
    try:
        result = runtime.start_server(path, port=port)
        return JsonResponse(result)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)


@safe_api_endpoint
@require_POST
def api_runtime_server_stop(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    path = str(payload.get("path", "")).strip()
    if not path:
        return JsonResponse({"error": "path kerak"}, status=400)
    try:
        result = runtime.stop_server(path)
        return JsonResponse(result)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)


@safe_api_endpoint
@require_POST
def api_runtime_server_output(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    path = str(payload.get("path", "")).strip()
    if not path:
        return JsonResponse({"error": "path kerak"}, status=400)
    try:
        result = runtime.server_status(path)
        return JsonResponse(result)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)


@safe_api_endpoint
@require_POST
def api_project_open(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    path = str(payload.get("path", "")).strip()
    if not path:
        return JsonResponse({"error": "path kerak"}, status=400)
    try:
        result = runtime.open_project(path)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def api_project_current(request):
    try:
        return JsonResponse(runtime.current_project())
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_project_close(request):
    try:
        return JsonResponse(runtime.close_project())
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def api_project_list(request):
    try:
        return JsonResponse({"projects": runtime.list_projects()})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_project_git_clone(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    url = str(payload.get("url", "")).strip()
    name = str(payload.get("name", "")).strip()
    if not url:
        return JsonResponse({"error": "Git URL kerak"}, status=400)
    try:
        result = runtime.git_clone(url, name=name)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
