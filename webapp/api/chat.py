import asyncio
import json
from django.http import JsonResponse, StreamingHttpResponse

from ..llm.base import Message, MessageRole
from ..agents import get_orchestrator
from ..memory.session import get_session_store
from .decorators import api_endpoint, parse_json_body


def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import threading
            result = []
            exception = []
            def run():
                try:
                    result.append(asyncio.run(coro))
                except Exception as e:
                    exception.append(e)
            t = threading.Thread(target=run)
            t.start()
            t.join()
            if exception:
                raise exception[0]
            return result[0] if result else None
        else:
            return asyncio.run(coro)
    except RuntimeError:
        return asyncio.run(coro)


@api_endpoint(require_key=True)
def api_chat(request):
    data = parse_json_body(request)
    message = data.get("message", "") or data.get("prompt", "")
    session_id = data.get("session_id", "")
    store = get_session_store()
    if not session_id:
        session_id = store.create_session({"source": "api"})
    user_msg = Message(role=MessageRole.USER, content=message)
    store.add_message(session_id, user_msg)
    history = store.get_history(session_id, limit=20)
    msgs = history + [user_msg]
    orch = get_orchestrator()
    completion = _run_async(orch.gateway.chat(msgs))
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
