from django.http import JsonResponse

from ..llm.gateway import get_gateway
from .decorators import api_endpoint, parse_json_body


@api_endpoint(require_key=True)
def api_gateway_status(request):
    gateway = get_gateway()
    return JsonResponse(gateway.get_status())


@api_endpoint(require_key=True)
def api_gateway_switch(request):
    data = parse_json_body(request)
    provider = data.get("provider", "")
    gateway = get_gateway()
    if gateway.switch_provider(provider):
        return JsonResponse({"status": "ok", "active_provider": provider})
    return JsonResponse({"error": f"Provider '{provider}' not found"}, status=404)


@api_endpoint(require_key=True)
def api_gateway_plugins(request):
    gateway = get_gateway()
    plugins = gateway.discover_plugins()
    return JsonResponse({"plugins": plugins, "count": len(plugins)})


@api_endpoint(require_key=True)
def api_gateway_register(request):
    data = parse_json_body(request)
    plugin_name = data.get("plugin", "")
    config = data.get("config", {})
    gateway = get_gateway()
    if gateway.register_plugin(plugin_name, **config):
        return JsonResponse({"status": "ok", "plugin": plugin_name})
    return JsonResponse({"error": f"Plugin '{plugin_name}' not found"}, status=404)


@api_endpoint(require_key=True)
def api_gateway_health(request):
    import asyncio
    gateway = get_gateway()
    health = asyncio.run(gateway.check_all_health())
    return JsonResponse({
        "health": health,
        "online": [k for k, v in health.items() if v],
        "offline": [k for k, v in health.items() if not v],
    })
