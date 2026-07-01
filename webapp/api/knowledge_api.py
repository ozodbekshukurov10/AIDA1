from django.http import JsonResponse

from ..memory.knowledge import get_knowledge_store
from .decorators import api_endpoint, parse_json_body


@api_endpoint(require_key=True)
def api_knowledge_add(request):
    data = parse_json_body(request)
    content = data.get("content", "")
    tags = data.get("tags", [])
    if not content:
        return JsonResponse({"error": "content is required"}, status=400)
    store = get_knowledge_store()
    doc_id = store.add(content, tags=tags)
    return JsonResponse({"id": doc_id, "total_docs": store.count()})


@api_endpoint(require_key=True)
def api_knowledge_search(request):
    data = parse_json_body(request)
    query = data.get("query", "") or request.GET.get("q", "")
    limit = int(data.get("limit", 5) or request.GET.get("limit", 5))
    if not query:
        return JsonResponse({"error": "query is required"}, status=400)
    store = get_knowledge_store()
    results = store.search(query, top_k=limit)
    return JsonResponse({"results": results, "count": len(results)})


@api_endpoint(require_key=True)
def api_knowledge_list(request):
    store = get_knowledge_store()
    docs = store.list_all()
    return JsonResponse({"documents": docs, "count": len(docs)})


@api_endpoint(require_key=True)
def api_knowledge_remove(request):
    data = parse_json_body(request)
    doc_id = data.get("id", "")
    if not doc_id:
        return JsonResponse({"error": "id is required"}, status=400)
    store = get_knowledge_store()
    if store.delete(doc_id):
        return JsonResponse({"status": "deleted"})
    return JsonResponse({"error": "document not found"}, status=404)
