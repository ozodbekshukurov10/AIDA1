from django.http import JsonResponse

from ..memory.session import get_session_store
from .decorators import api_endpoint, parse_json_body


@api_endpoint(require_key=True)
def api_sessions_list(request):
    store = get_session_store()
    sessions = store.list_sessions()
    return JsonResponse({"sessions": sessions, "count": len(sessions)})


@api_endpoint(require_key=True)
def api_session_create(request):
    data = parse_json_body(request)
    metadata = data.get("metadata", {})
    store = get_session_store()
    session_id = store.create_session(metadata)
    return JsonResponse({"session_id": session_id})


@api_endpoint(require_key=True)
def api_session_history(request, session_id):
    store = get_session_store()
    messages = store.get_history(session_id)
    facts = store.get_facts(session_id)
    return JsonResponse({
        "session_id": session_id,
        "messages": [m.to_dict() for m in messages],
        "facts": facts,
        "count": len(messages),
    })
