import asyncio
from django.http import JsonResponse

from ..agents import (
    get_orchestrator, AgentContext, WORKFLOW_TEMPLATES,
)
from .decorators import api_endpoint, parse_json_body


@api_endpoint(require_key=True)
def api_agents_status(request):
    orch = get_orchestrator()
    return JsonResponse(orch.get_status())


@api_endpoint(require_key=True)
def api_agents_list(request):
    orch = get_orchestrator()
    return JsonResponse({"agents": orch.list_agents()})


@api_endpoint(require_key=True)
def api_agent_execute(request):
    data = parse_json_body(request)
    agent_name = data.get("agent", "")
    prompt = data.get("prompt", "")
    if not agent_name:
        return JsonResponse({"error": "agent name is required"}, status=400)
    if not prompt:
        return JsonResponse({"error": "prompt is required"}, status=400)
    orch = get_orchestrator()
    result = asyncio.run(orch.execute_single(agent_name, prompt))
    return JsonResponse({
        "task_id": result.task_id,
        "agent": agent_name,
        "content": result.content,
        "status": result.status.value,
        "latency_ms": result.latency_ms,
        "error": result.error,
    })


@api_endpoint(require_key=True)
def api_workflow_execute(request):
    data = parse_json_body(request)
    prompt = data.get("prompt", "")
    workflow = data.get("workflow", "")
    if not prompt:
        return JsonResponse({"error": "prompt is required"}, status=400)
    orch = get_orchestrator()
    results = asyncio.run(orch.execute_workflow(prompt, workflow_name=workflow))
    return JsonResponse({
        "workflow": workflow or "auto",
        "steps": len(results),
        "results": [
            {
                "task_id": r.task_id,
                "status": r.status.value,
                "content_preview": r.content[:300] if r.content else "",
                "latency_ms": r.latency_ms,
                "error": r.error,
            }
            for r in results
        ],
    })


@api_endpoint(require_key=True)
def api_workflows_list(request):
    return JsonResponse({"workflows": list(WORKFLOW_TEMPLATES.keys())})


@api_endpoint(require_key=True)
def api_agent_messages(request):
    orch = get_orchestrator()
    limit = int(request.GET.get("limit", 50))
    messages = orch.get_message_history(limit=limit)
    return JsonResponse({"messages": messages, "count": len(messages)})


@api_endpoint(require_key=True)
def api_workflow_history(request):
    orch = get_orchestrator()
    return JsonResponse({"workflows": orch.get_workflow_history()})
