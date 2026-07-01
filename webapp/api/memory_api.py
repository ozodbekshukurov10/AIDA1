from django.http import JsonResponse

from ..memory.manager import get_memory_manager
from .decorators import api_endpoint, parse_json_body


@api_endpoint(require_key=True)
def api_memory_store(request):
    data = parse_json_body(request)
    content = data.get("content", "")
    memory_type = data.get("memory_type", "conversation")
    importance = data.get("importance", "medium")
    tags = data.get("tags", [])
    metadata = data.get("metadata", {})

    if not content:
        return JsonResponse({"error": "content is required"}, status=400)

    import asyncio
    mgr = get_memory_manager()
    mem_id = asyncio.run(mgr.store(content, memory_type, importance, tags, metadata))
    return JsonResponse({"id": mem_id, "status": "stored"})


@api_endpoint(require_key=True)
def api_memory_search(request):
    data = parse_json_body(request)
    query = data.get("query", "")
    memory_type = data.get("memory_type")
    tags = data.get("tags")
    limit = data.get("limit", 10)

    import asyncio
    mgr = get_memory_manager()
    result = asyncio.run(mgr.search(query, memory_type, tags, limit))
    return JsonResponse(result.to_dict())


@api_endpoint(require_key=True)
def api_memory_semantic_search(request):
    data = parse_json_body(request)
    query = data.get("query", "")
    limit = data.get("limit", 10)

    import asyncio
    mgr = get_memory_manager()
    result = asyncio.run(mgr.semantic_search_all(query, limit))
    return JsonResponse(result.to_dict())


@api_endpoint(require_key=True)
def api_memory_get(request, item_id):
    import asyncio
    mgr = get_memory_manager()
    item = asyncio.run(mgr.get(item_id))
    if not item:
        return JsonResponse({"error": "not found"}, status=404)
    return JsonResponse(item.to_dict())


@api_endpoint(require_key=True)
def api_memory_delete(request):
    data = parse_json_body(request)
    item_id = data.get("item_id", "")
    if not item_id:
        return JsonResponse({"error": "item_id is required"}, status=400)

    import asyncio
    mgr = get_memory_manager()
    deleted = asyncio.run(mgr.delete(item_id))
    return JsonResponse({"deleted": deleted})


@api_endpoint(require_key=True)
def api_memory_stats(request):
    import asyncio
    mgr = get_memory_manager()
    stats = asyncio.run(mgr.get_stats())
    return JsonResponse(stats)


@api_endpoint(require_key=True)
def api_memory_maintenance(request):
    import asyncio
    mgr = get_memory_manager()
    result = asyncio.run(mgr.run_maintenance())
    return JsonResponse(result)
