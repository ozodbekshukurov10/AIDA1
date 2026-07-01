from django.http import JsonResponse

from ..tools import get_tool_registry, get_tool_manager, PermissionLevel
from .decorators import api_endpoint, parse_json_body


def _get_user_level(request) -> PermissionLevel:
    if getattr(request, "user", None) and request.user.is_staff:
        return PermissionLevel.ADMIN
    key = request.headers.get("X-API-Key", "")
    if key:
        try:
            from ..models.access_key import AccessKey
            ak = AccessKey.objects.get(key=key)
            if ak.is_admin:
                return PermissionLevel.ADMIN
            return PermissionLevel.USER
        except Exception:
            pass
    if request.headers.get("X-System-Key"):
        return PermissionLevel.SYSTEM
    return PermissionLevel.PUBLIC


@api_endpoint(require_key=True)
def api_tools_list(request):
    registry = get_tool_registry()
    tools = registry.list_tools()
    return JsonResponse({
        "tools": tools,
        "count": len(tools),
        "manager": get_tool_manager().get_stats(),
    })


@api_endpoint(require_key=True)
def api_tools_execute(request):
    data = parse_json_body(request)
    tool_name = data.get("tool", "")
    params = data.get("params", {})
    if not tool_name:
        return JsonResponse({"error": "tool name is required"}, status=400)

    user_level = _get_user_level(request)
    manager = get_tool_manager()
    import asyncio
    result = asyncio.run(manager.execute(tool_name, user_level=user_level, **params))
    return JsonResponse(result.to_dict())


@api_endpoint(require_key=True)
def api_tools_permissions(request):
    manager = get_tool_manager()
    tools = manager.list_tools(_get_user_level(request))
    return JsonResponse({
        "tools": tools,
        "count": len(tools),
    })
