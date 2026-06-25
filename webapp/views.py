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
from .code_fixer import fix_code_automatically, optimize_performance, generate_comprehensive_tests, analyze_and_improve
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
    try:
        return JsonResponse(controller.status())
    except Exception as exc:
        logger.exception("Status error: %s", exc)
        return JsonResponse({"error": "Statusni olishda xatolik yuz berdi."}, status=500)


@require_GET
def api_keys_list(request):
    try:
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
    except Exception as exc:
        logger.exception("Keys list error: %s", exc)
        return JsonResponse({"items": [], "warning": "Access key jadvali hali tayyor emas. Migration ishga tushiring."})


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
    except Exception as exc:
        logger.exception("Chat fatal error: %s", exc)
        return JsonResponse({"error": "AIDA ichki xatosi. Backend loglarini tekshiring."}, status=500)

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


def _make_code_responder():
    """CodeGenerator uchun real LLM provayder chaqiruvchi respond_func yaratadi."""
    def respond(p: str, mem: list, sys: str) -> str:
        try:
            return controller.provider.respond(prompt=p, memory=mem, system_prompt=sys)
        except Exception:
            return ""
    return respond


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

    cg = CodeGenerator(respond_func=_make_code_responder())
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


@safe_api_endpoint
@require_POST
def api_code_fix(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    code = str(payload.get("code", "")).strip()
    language = str(payload.get("language", "python")).strip().lower()
    if not code:
        return JsonResponse({"error": "Kod yuborilmadi."}, status=400)
    result = fix_code_automatically(code, language)
    return JsonResponse(result)


@safe_api_endpoint
@require_POST
def api_code_optimize(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    code = str(payload.get("code", "")).strip()
    language = str(payload.get("language", "python")).strip().lower()
    if not code:
        return JsonResponse({"error": "Kod yuborilmadi."}, status=400)
    result = optimize_performance(code, language)
    return JsonResponse(result)


@safe_api_endpoint
@require_POST
def api_code_tests(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    code = str(payload.get("code", "")).strip()
    language = str(payload.get("language", "python")).strip().lower()
    if not code:
        return JsonResponse({"error": "Kod yuborilmadi."}, status=400)
    result = generate_comprehensive_tests(code, language)
    return JsonResponse(result)


@safe_api_endpoint
@require_POST
def api_code_improve(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    code = str(payload.get("code", "")).strip()
    language = str(payload.get("language", "python")).strip().lower()
    if not code:
        return JsonResponse({"error": "Kod yuborilmadi."}, status=400)
    result = analyze_and_improve(code, language)
    return JsonResponse(result)


@safe_api_endpoint
@require_POST
def api_code_review(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    code = str(payload.get("code", "")).strip()
    language = str(payload.get("language", "python")).strip().lower()
    context = str(payload.get("context", "")).strip()
    mode = str(payload.get("mode", "")).strip().lower()
    if not code:
        return JsonResponse({"error": "Kod yuborilmadi."}, status=400)
    try:
        message = controller.review_code(code, language, context, mode)
        return JsonResponse({"message": message, "status": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_debug_assist(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    error = str(payload.get("error", "")).strip()
    code = str(payload.get("code", "")).strip()
    language = str(payload.get("language", "python")).strip().lower()
    mode = str(payload.get("mode", "")).strip().lower()
    if not error:
        return JsonResponse({"error": "Xatolik tavsifi yuborilmadi."}, status=400)
    try:
        message = controller.debug_error(error, code, language, mode)
        return JsonResponse({"message": message, "status": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_architecture_analyze(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    description = str(payload.get("description", "")).strip()
    code = str(payload.get("code", "")).strip()
    mode = str(payload.get("mode", "")).strip().lower()
    if not description:
        return JsonResponse({"error": "Tavsif yuborilmadi."}, status=400)
    try:
        message = controller.analyze_architecture(description, code, mode)
        return JsonResponse({"message": message, "status": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_language_generate(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    prompt = str(payload.get("prompt", "")).strip()
    language = str(payload.get("language", "python")).strip().lower()
    framework = str(payload.get("framework", "")).strip()
    mode = str(payload.get("mode", "")).strip().lower()
    if not prompt:
        return JsonResponse({"error": "Prompt yuborilmadi."}, status=400)
    try:
        message = controller.language_generate(prompt, language, framework, mode)
        return JsonResponse({"message": message, "status": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_framework_generate(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    prompt = str(payload.get("prompt", "")).strip()
    category = str(payload.get("category", "django")).strip().lower()
    framework = str(payload.get("framework", "")).strip()
    mode = str(payload.get("mode", "")).strip().lower()
    if not prompt:
        return JsonResponse({"error": "Prompt yuborilmadi."}, status=400)
    try:
        message = controller.framework_generate(prompt, category, framework, mode)
        return JsonResponse({"message": message, "status": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_version_control(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    prompt = str(payload.get("prompt", "")).strip()
    category = str(payload.get("category", "git-commands")).strip().lower()
    mode = str(payload.get("mode", "")).strip().lower()
    if not prompt:
        return JsonResponse({"error": "Prompt yuborilmadi."}, status=400)
    try:
        message = controller.version_control_generate(prompt, category, mode)
        return JsonResponse({"message": message, "status": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_docker_generate(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    prompt = str(payload.get("prompt", "")).strip()
    category = str(payload.get("category", "")).strip()
    mode = str(payload.get("mode", "")).strip().lower()
    if not prompt:
        return JsonResponse({"error": "Prompt yuborilmadi."}, status=400)
    try:
        message = controller.docker_generate(prompt, category, mode)
        return JsonResponse({"message": message, "status": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_kubernetes_generate(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    prompt = str(payload.get("prompt", "")).strip()
    category = str(payload.get("category", "")).strip()
    mode = str(payload.get("mode", "")).strip().lower()
    if not prompt:
        return JsonResponse({"error": "Prompt yuborilmadi."}, status=400)
    try:
        message = controller.kubernetes_generate(prompt, category, mode)
        return JsonResponse({"message": message, "status": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_performance_tuning(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    prompt = str(payload.get("prompt", "")).strip()
    category = str(payload.get("category", "")).strip()
    mode = str(payload.get("mode", "")).strip().lower()
    if not prompt:
        return JsonResponse({"error": "Prompt yuborilmadi."}, status=400)
    try:
        message = controller.performance_tuning_generate(prompt, category, mode)
        return JsonResponse({"message": message, "status": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_feedback_submit(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    rating = int(payload.get("rating", 0))
    if rating < 1 or rating > 5:
        return JsonResponse({"error": "Rating 1-5 oralig'ida bo'lishi kerak."}, status=400)
    result = controller.feedback_submit(
        rating=rating,
        comment=str(payload.get("comment", "")).strip(),
        session_id=str(payload.get("session_id", "")).strip(),
        prompt=str(payload.get("prompt", "")).strip(),
        response=str(payload.get("response", "")).strip(),
        provider=str(payload.get("provider", "")).strip(),
        mode=str(payload.get("mode", "")).strip().lower(),
        latency_ms=int(payload.get("latency_ms", 0)),
    )
    return JsonResponse(result)


@require_GET
def api_feedback_analytics(request):
    return JsonResponse(controller.feedback_analytics())


@safe_api_endpoint
@require_POST
def api_feedback_analyze(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    question = str(payload.get("question", "")).strip()
    mode = str(payload.get("mode", "")).strip().lower()
    try:
        message = controller.feedback_analyze(question, mode)
        return JsonResponse({"message": message, "status": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_training_save(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    prompt = str(payload.get("prompt", "")).strip()
    response = str(payload.get("response", "")).strip()
    if not prompt or not response:
        return JsonResponse({"error": "prompt va response kerak."}, status=400)
    result = controller.training_save(
        prompt=prompt,
        response=response,
        domain=str(payload.get("domain", "")).strip(),
        language=str(payload.get("language", "uz")).strip(),
        rating=int(payload.get("rating", 0)),
    )
    return JsonResponse(result, status=201)


@safe_api_endpoint
@require_POST
def api_training_domain(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    domain = str(payload.get("domain", "")).strip()
    system_prompt = str(payload.get("system_prompt", "")).strip()
    if not domain:
        return JsonResponse({"error": "domain kerak."}, status=400)
    result = controller.training_set_domain(
        domain=domain,
        system_prompt=system_prompt,
        temperature=float(payload.get("temperature", 0.7)),
        max_tokens=int(payload.get("max_tokens", 1024)),
    )
    return JsonResponse(result)


@require_GET
def api_training_stats(request):
    return JsonResponse(controller.training_stats())


@safe_api_endpoint
@require_POST
def api_training_analyze(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    question = str(payload.get("question", "")).strip()
    mode = str(payload.get("mode", "")).strip().lower()
    try:
        message = controller.training_analyze(question, mode)
        return JsonResponse({"message": message, "status": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_knowledge_suggest(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    topic = str(payload.get("topic", "")).strip()
    context = str(payload.get("context", "")).strip()
    mode = str(payload.get("mode", "")).strip().lower()
    try:
        message = controller.knowledge_suggest(topic, context, mode)
        return JsonResponse({"message": message, "status": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def api_models_discover(request):
    from .model_discovery import discover_all
    try:
        result = discover_all()
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ──────────────────────────────────────────────
# Task 3 — Model Manager endpoints
# ──────────────────────────────────────────────

@require_GET
def api_manager_list(request):
    from .model_manager import ModelManager
    try:
        return JsonResponse(ModelManager.list_all())
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def api_manager_get(request, model_id: str):
    from .model_manager import ModelManager
    try:
        return JsonResponse(ModelManager.get_model(model_id))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_manager_pull(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    model = str(payload.get("model", "")).strip()
    if not model:
        return JsonResponse({"error": "model nomi kerak"}, status=400)
    from .model_manager import ModelManager
    try:
        result = ModelManager.pull_model(model)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_manager_remove(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    model = str(payload.get("model", "")).strip()
    if not model:
        return JsonResponse({"error": "model nomi kerak"}, status=400)
    from .model_manager import ModelManager
    try:
        result = ModelManager.remove_model(model)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_manager_load(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    model = str(payload.get("model", "")).strip()
    if not model:
        return JsonResponse({"error": "model nomi kerak"}, status=400)
    from .model_manager import ModelManager
    try:
        result = ModelManager.load_model(model)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_manager_unload(request):
    from .model_manager import ModelManager
    try:
        result = ModelManager.unload_model()
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_manager_select(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    model = str(payload.get("model", "")).strip()
    if not model:
        return JsonResponse({"error": "model nomi kerak"}, status=400)
    from .model_manager import ModelManager
    try:
        result = ModelManager.select_active(model)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


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


# ── Agent Layer API endpoints ─────────────────────────────────────────────

_AGENT_MODULE = None

def _get_agent_module():
    global _AGENT_MODULE
    if _AGENT_MODULE is None:
        try:
            from .aida_controller import AGENTS_AVAILABLE
            if AGENTS_AVAILABLE:
                from . import agents as _agents
                _AGENT_MODULE = _agents
        except ImportError:
            pass
    return _AGENT_MODULE


def _get_orch():
    mod = _get_agent_module()
    if mod:
        return mod.get_orchestrator()
    return None


@safe_api_endpoint
@require_GET
def api_agent_stats(request):
    mod = _get_agent_module()
    orch = _get_orch()
    if not orch or not mod:
        return JsonResponse({"error": "Agent Layer mavjud emas"}, status=404)
    return JsonResponse({
        "agents": orch.get_agent_stats(),
        "queue": orch.get_queue_stats(),
        "task_model_map": {k.value: v for k, v in mod.TASK_MODEL_MAP.items()},
    })


@safe_api_endpoint
@require_POST
def api_agent_submit(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)

    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        return JsonResponse({"error": "Prompt yuborilmadi."}, status=400)

    orch = _get_orch()
    if not orch:
        return JsonResponse({"error": "Agent Layer mavjud emas"}, status=404)

    task = orch.submit(prompt)
    return JsonResponse({
        "task_id": task.id,
        "task_type": task.task_type.value,
        "priority": task.priority,
        "status": task.status,
        "queue_size": orch.queue.size,
    })


@safe_api_endpoint
@require_GET
def api_agent_queue(request):
    orch = _get_orch()
    if not orch:
        return JsonResponse({"error": "Agent Layer mavjud emas"}, status=404)
    return JsonResponse({
        "queue_size": orch.queue.size,
    })


# ── Tool Hub API endpoints ────────────────────────────────────────────────

@safe_api_endpoint
@require_GET
def api_tools_list(request):
    try:
        from .tool_hub import get_tool_hub
        hub = get_tool_hub()
        return JsonResponse({"tools": hub.list_tools()})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_tools_execute(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    tool_name = str(payload.get("tool", "")).strip()
    params = payload.get("params", {})
    if not tool_name:
        return JsonResponse({"error": "Tool nomi kerak"}, status=400)
    try:
        from .tool_hub import get_tool_hub
        hub = get_tool_hub()
        result = hub.execute(tool_name, **params)
        return JsonResponse({
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "data": result.data,
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ── Sandbox API endpoints ─────────────────────────────────────────────────

@safe_api_endpoint
@require_POST
def api_sandbox_create(request):
    try:
        from .sandbox import get_sandbox
        sandbox = get_sandbox()
        session = sandbox.create_session()
        return JsonResponse({
            "session_id": session.id,
            "dir": str(session.dir),
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_sandbox_run(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    session_id = str(payload.get("session_id", "")).strip()
    code = str(payload.get("code", "")).strip()
    language = str(payload.get("language", "python")).strip().lower()
    timeout = int(payload.get("timeout", 10))
    if not session_id or not code:
        return JsonResponse({"error": "session_id va code kerak"}, status=400)
    try:
        from .sandbox import get_sandbox
        sandbox = get_sandbox()
        session = sandbox.get_session(session_id)
        if not session:
            return JsonResponse({"error": "Session topilmadi"}, status=404)
        if language == "python":
            result = session.run_python(code, timeout=timeout)
        else:
            result = session.run_shell(code, timeout=timeout)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_sandbox_file_write(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    session_id = str(payload.get("session_id", "")).strip()
    path = str(payload.get("path", "")).strip()
    content = str(payload.get("content", ""))
    if not session_id or not path:
        return JsonResponse({"error": "session_id va path kerak"}, status=400)
    try:
        from .sandbox import get_sandbox
        sandbox = get_sandbox()
        session = sandbox.get_session(session_id)
        if not session:
            return JsonResponse({"error": "Session topilmadi"}, status=404)
        result = session.write_file(path, content)
        return JsonResponse({"message": result})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_GET
def api_sandbox_list(request):
    try:
        from .sandbox import get_sandbox
        sandbox = get_sandbox()
        sessions = sandbox.list_sessions()
        return JsonResponse({"sessions": sessions})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_sandbox_destroy(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    session_id = str(payload.get("session_id", "")).strip()
    if not session_id:
        return JsonResponse({"error": "session_id kerak"}, status=400)
    try:
        from .sandbox import get_sandbox
        sandbox = get_sandbox()
        sandbox.destroy_session(session_id)
        return JsonResponse({"message": f"Session {session_id} o'chirildi"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ── Knowledge Store API endpoints ─────────────────────────────────────────

@safe_api_endpoint
@require_POST
def api_knowledge_add(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    content = str(payload.get("content", "")).strip()
    if not content:
        return JsonResponse({"error": "Content kerak"}, status=400)
    try:
        from .knowledge_store import get_knowledge_store
        store = get_knowledge_store()
        doc_id = store.add(content, metadata=payload.get("metadata", {}))
        return JsonResponse({"doc_id": doc_id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_knowledge_search(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    query = str(payload.get("query", "")).strip()
    if not query:
        return JsonResponse({"error": "Query kerak"}, status=400)
    top_k = int(payload.get("top_k", 5))
    try:
        from .knowledge_store import get_knowledge_store
        store = get_knowledge_store()
        results = store.search(query, top_k=top_k)
        return JsonResponse({"results": results})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_GET
def api_knowledge_list(request):
    try:
        from .knowledge_store import get_knowledge_store
        store = get_knowledge_store()
        docs = store.list_all()
        return JsonResponse({"docs": docs, "total": len(docs)})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@safe_api_endpoint
@require_POST
def api_knowledge_remove(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON noto'g'ri."}, status=400)
    doc_id = str(payload.get("doc_id", "")).strip()
    if not doc_id:
        return JsonResponse({"error": "doc_id kerak"}, status=400)
    try:
        from .knowledge_store import get_knowledge_store
        store = get_knowledge_store()
        ok = store.remove(doc_id)
        return JsonResponse({"removed": ok})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
