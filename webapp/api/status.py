from django.http import JsonResponse

from ..agents import get_orchestrator
from .decorators import api_endpoint


@api_endpoint(require_key=False)
def api_status(request):
    orch = get_orchestrator()
    gateway = orch.gateway
    return JsonResponse({
        "status": "ok",
        "version": "2.1.0",
        "platform": "AIDA Agentic Platform",
        "active_provider": gateway.get_status()["active_provider"],
        "providers": gateway.get_status()["providers"],
        "agents": {n: {"name": a.name, "status": a.status.value, "metrics": a.metrics}
                   for n, a in orch.agents.items()},
    })
