from django.http import JsonResponse

from ..llm.gateway import get_gateway
from .decorators import api_endpoint, parse_json_body


@api_endpoint(require_key=True)
def api_models_list(request):
    gateway = get_gateway()
    return JsonResponse(gateway.get_status())


@api_endpoint(require_key=True)
def api_models_switch(request):
    data = parse_json_body(request)
    provider = data.get("provider", "")
    gateway = get_gateway()
    if gateway.switch_provider(provider):
        return JsonResponse({"status": "ok", "active_provider": provider})
    return JsonResponse({"error": f"Provider '{provider}' not found"}, status=404)
