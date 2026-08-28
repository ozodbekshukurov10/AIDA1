import asyncio
import json
import urllib.parse
from django.http import JsonResponse, StreamingHttpResponse

from ..llm.base import Message, MessageRole
from ..agents.orchestrator import get_orchestrator
from ..memory.session import get_session_store
from ..tools.registry import get_tool_registry
from .decorators import api_endpoint, parse_json_body


import concurrent.futures

_THREAD_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="async_bridge")

def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_running():
        return _THREAD_POOL.submit(asyncio.run, coro).result()
    return loop.run_until_complete(coro)


@api_endpoint(require_key=False)
def api_chat(request):
    data = parse_json_body(request)
    message = data.get("message", "") or data.get("prompt", "")
    session_id = data.get("session_id", "")
    provider = data.get("provider")
    model = data.get("model")
    research_mode = data.get("research", False)
    
    store = get_session_store()
    if not session_id:
        session_id = store.create_session({"source": "api"})
    user_msg = Message(role=MessageRole.USER, content=message)
    store.add_message(session_id, user_msg)
    history = store.get_history(session_id, limit=20)
    
    search_context = ""
    sources = []
    if research_mode and message.strip():
        try:
            registry = get_tool_registry()
            search_res = _run_async(registry.execute("web_search", query=message))
            if search_res.success and search_res.output:
                search_context = f"\n\n[Internet Qidiruv Natijalari]:\n{search_res.output}"
                sources = [{"title": "DuckDuckGo Search", "url": f"https://duckduckgo.com/?q={urllib.parse.quote(message)}"}]
        except Exception:
            pass

    llm_user_msg = Message(role=MessageRole.USER, content=f"{message}{search_context}" if search_context else message)
    msgs = history + [llm_user_msg]
    orch = get_orchestrator()
    kwargs = {}
    if provider:
        kwargs["provider"] = provider
    if model:
        kwargs["model"] = model
    completion = _run_async(orch.gateway.chat(msgs, **kwargs))
    if completion and completion.content:
        assistant_msg = Message(role=MessageRole.ASSISTANT, content=completion.content)
        store.add_message(session_id, assistant_msg)
        return JsonResponse({
            "response": completion.content,
            "message": completion.content,
            "session_id": session_id,
            "model": completion.model,
            "provider": completion.provider,
            "latency_ms": completion.latency_ms,
            "sources": sources,
        })
    return JsonResponse({"error": "Chat failed"}, status=500)


@api_endpoint(require_key=True)
def api_chat_stream(request):
    data = parse_json_body(request)
    message = data.get("message", "")
    session_id = data.get("session_id", "")
    store = get_session_store()
    if not session_id:
        session_id = store.create_session({"source": "api"})
    user_msg = Message(role=MessageRole.USER, content=message)
    store.add_message(session_id, user_msg)
    history = store.get_history(session_id, limit=20)
    msgs = history + [user_msg]

    async def generate():
        full_response = ""
        orch = get_orchestrator()
        async for chunk in orch.gateway.chat_stream(msgs):
            if chunk.content:
                full_response += chunk.content
                yield f"data: {json.dumps({'content': chunk.content, 'done': False})}\n\n"
            if chunk.done:
                assistant_msg = Message(role=MessageRole.ASSISTANT, content=full_response)
                store.add_message(session_id, assistant_msg)
                yield f"data: {json.dumps({'content': '', 'done': True, 'session_id': session_id})}\n\n"

    async def async_iter_to_sync():
        async for item in generate():
            yield item

    return StreamingHttpResponse(
        async_iter_to_sync(),
        content_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
