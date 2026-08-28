"""
AIDA Enterprise API — Agents ViewSet

Agent va workflow boshqarish endpointlari:
- GET    /agents/                       — Agentlar ro'yxati
- GET    /agents/{id}/                  — Agent ma'lumotlari
- POST   /agents/{id}/execute/          — Agent topshirig'ini bajarish
- GET    /agents/{id}/messages/         — Agent xabarlari
- GET    /workflows/                    — Workflow lar ro'yxati
- POST   /workflows/{name}/execute/     — Workflow ni bajarish
- GET    /workflows/history/            — Workflow tarixi
"""
from __future__ import annotations
from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..responses import APIResponse


# ── Mock Data ──────────────────────────────────────────────────────────────────

MOCK_AGENTS = [
    {
        "id": "code-reviewer",
        "name": "Code Reviewer",
        "description": "Kod sifatini tekshiradi, xatoliklarni topadi va takliflar beradi.",
        "type": "reviewer",
        "status": "active",
        "capabilities": ["code_review", "security_audit", "performance_analysis"],
        "model": "gpt-4o",
        "created_at": "2026-06-01T10:00:00Z",
        "execution_count": 342,
        "avg_execution_time_ms": 5200,
        "config": {
            "max_file_size_kb": 500,
            "supported_languages": ["python", "javascript", "typescript", "go", "rust"],
            "auto_fix": False,
        },
    },
    {
        "id": "code-generator",
        "name": "Code Generator",
        "description": "Tavsif asosida kod generatsiya qiladi.",
        "type": "generator",
        "status": "active",
        "capabilities": ["code_generation", "test_generation", "documentation"],
        "model": "gpt-4o",
        "created_at": "2026-06-01T10:00:00Z",
        "execution_count": 891,
        "avg_execution_time_ms": 8400,
        "config": {
            "output_format": "standard",
            "include_tests": True,
            "include_docstrings": True,
        },
    },
    {
        "id": "bug-fixer",
        "name": "Bug Fixer",
        "description": "Xatoliklarni tahlil qiladi va tuzatish takliflari beradi.",
        "type": "fixer",
        "status": "active",
        "capabilities": ["bug_detection", "root_cause_analysis", "fix_suggestion"],
        "model": "gemini-2.5-pro",
        "created_at": "2026-06-15T14:30:00Z",
        "execution_count": 156,
        "avg_execution_time_ms": 7100,
        "config": {
            "context_window": "full_file",
            "max_suggestions": 3,
        },
    },
    {
        "id": "doc-writer",
        "name": "Documentation Writer",
        "description": "Kod uchun hujjatlar yozadi.",
        "type": "writer",
        "status": "active",
        "capabilities": ["doc_generation", "readme_creation", "api_docs"],
        "model": "gemini-2.5-flash",
        "created_at": "2026-06-20T09:00:00Z",
        "execution_count": 234,
        "avg_execution_time_ms": 3800,
        "config": {
            "format": "markdown",
            "language": "en",
            "include_examples": True,
        },
    },
    {
        "id": "test-runner",
        "name": "Test Runner",
        "description": "Testlarni yaratadi va bajaradi.",
        "type": "tester",
        "status": "active",
        "capabilities": ["test_generation", "test_execution", "coverage_analysis"],
        "model": "gpt-4o-mini",
        "created_at": "2026-06-25T16:00:00Z",
        "execution_count": 678,
        "avg_execution_time_ms": 12000,
        "config": {
            "framework": "pytest",
            "coverage_threshold": 80,
            "parallel": True,
        },
    },
]

MOCK_WORKFLOWS = [
    {
        "id": "full-review",
        "name": "full-review",
        "display_name": "To'liq Kod Tekshiruvi",
        "description": "Kodni to'liq tekshiradi: sifat, xavfsizlik, unumdorlik.",
        "steps": [
            {"order": 1, "agent": "code-reviewer", "action": "review_code"},
            {"order": 2, "agent": "bug-fixer", "action": "find_bugs"},
            {"order": 3, "agent": "doc-writer", "action": "generate_report"},
        ],
        "status": "active",
        "created_at": "2026-06-01T10:00:00Z",
        "execution_count": 89,
        "avg_execution_time_ms": 25000,
    },
    {
        "id": "generate-and-test",
        "name": "generate-and-test",
        "display_name": "Yaratish va Sinov",
        "description": "Kod yaratadi va avtomatik sinovdan o'tkazadi.",
        "steps": [
            {"order": 1, "agent": "code-generator", "action": "generate_code"},
            {"order": 2, "agent": "test-runner", "action": "run_tests"},
            {"order": 3, "agent": "bug-fixer", "action": "fix_failures"},
        ],
        "status": "active",
        "created_at": "2026-06-10T12:00:00Z",
        "execution_count": 234,
        "avg_execution_time_ms": 45000,
    },
    {
        "id": "quick-fix",
        "name": "quick-fix",
        "display_name": "Tez Tuzatish",
        "description": "Xatolikni topadi va tuzatadi.",
        "steps": [
            {"order": 1, "agent": "bug-fixer", "action": "analyze_and_fix"},
        ],
        "status": "active",
        "created_at": "2026-06-15T08:00:00Z",
        "execution_count": 567,
        "avg_execution_time_ms": 8000,
    },
]

MOCK_EXECUTION_HISTORY = [
    {
        "id": "exec_001",
        "workflow": "full-review",
        "status": "completed",
        "triggered_by": "admin@aida.io",
        "started_at": "2026-07-04T09:00:00Z",
        "completed_at": "2026-07-04T09:00:22Z",
        "duration_ms": 22000,
        "steps_completed": 3,
        "result_summary": "3 ta muammo topildi, 2 tasi avtomatik tuzatildi.",
    },
    {
        "id": "exec_002",
        "workflow": "generate-and-test",
        "status": "completed",
        "triggered_by": "dev@aida.io",
        "started_at": "2026-07-04T08:30:00Z",
        "completed_at": "2026-07-04T08:30:41Z",
        "duration_ms": 41000,
        "steps_completed": 3,
        "result_summary": "8 ta test yaratildi, 7 tasi o'tdi.",
    },
    {
        "id": "exec_003",
        "workflow": "quick-fix",
        "status": "failed",
        "triggered_by": "admin@aida.io",
        "started_at": "2026-07-04T07:15:00Z",
        "completed_at": "2026-07-04T07:15:09Z",
        "duration_ms": 9000,
        "steps_completed": 0,
        "result_summary": "Xatolik: fayl topilmadi.",
        "error": "FileNotFoundError: src/utils/missing.py",
    },
    {
        "id": "exec_004",
        "workflow": "full-review",
        "status": "completed",
        "triggered_by": "dev@aida.io",
        "started_at": "2026-07-03T16:00:00Z",
        "completed_at": "2026-07-03T16:00:18Z",
        "duration_ms": 18000,
        "steps_completed": 3,
        "result_summary": "Muammolar topilmadi.",
    },
]

MOCK_MESSAGES = [
    {
        "id": "msg_001",
        "agent_id": "code-reviewer",
        "role": "assistant",
        "content": "Kodni tahlil qildim. 2 ta potentsial muammo topdim.",
        "timestamp": "2026-07-04T09:00:05Z",
        "tokens_used": 1250,
        "execution_time_ms": 4800,
    },
    {
        "id": "msg_002",
        "agent_id": "code-reviewer",
        "role": "assistant",
        "content": "1. src/auth.py:142 — SQL injection xavfi. 2. src/api.py:87 — N+1 query.",
        "timestamp": "2026-07-04T09:00:10Z",
        "tokens_used": 890,
        "execution_time_ms": 3200,
    },
    {
        "id": "msg_003",
        "agent_id": "code-generator",
        "role": "assistant",
        "content": "Foydalanuvchi modeli yaratildi. Pydantic schema qo'shildi.",
        "timestamp": "2026-07-04T08:30:15Z",
        "tokens_used": 2100,
        "execution_time_ms": 6500,
    },
]


class AgentsViewSet(viewsets.ViewSet):
    """
    Agent va workflow boshqarish.

    - GET    /agents/                       — Agentlar ro'yxati
    - GET    /agents/{id}/                  — Agent ma'lumotlari
    - POST   /agents/{id}/execute/          — Agent topshirig'ini bajarish
    - GET    /agents/{id}/messages/         — Agent xabarlari
    - GET    /workflows/                    — Workflow lar ro'yxati
    - POST   /workflows/{name}/execute/     — Workflow ni bajarish
    - GET    /workflows/history/            — Workflow tarixi
    """

    permission_classes = [IsAuthenticated]

    # ── Agents ─────────────────────────────────────────────────────────────────

    def list(self, request):
        """Agentlar ro'yxati."""
        agent_type = request.query_params.get("type")
        agents = MOCK_AGENTS[:]

        if agent_type:
            agents = [a for a in agents if a["type"] == agent_type]

        return Response(
            APIResponse.success(
                data=agents,
                metadata={"total": len(agents)},
            )
        )

    def retrieve(self, request, pk=None):
        """Agent ma'lumotlari."""
        agent = next((a for a in MOCK_AGENTS if a["id"] == pk), None)
        if not agent:
            return Response(
                APIResponse.not_found(message=f"Agent topilmadi: {pk}"),
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(APIResponse.success(data=agent))

    @action(detail=True, methods=["post"], url_path="execute")
    def execute_agent(self, request, pk=None):
        """Agent topshirig'ini bajarish."""
        agent = next((a for a in MOCK_AGENTS if a["id"] == pk), None)
        if not agent:
            return Response(
                APIResponse.not_found(message=f"Agent topilmadi: {pk}"),
                status=status.HTTP_404_NOT_FOUND,
            )

        task = request.data.get("task", "")
        if not task:
            return Response(
                APIResponse.bad_request(message="task kiritilishi shart."),
                status=status.HTTP_400_BAD_REQUEST,
            )

        execution = {
            "execution_id": f"exec_{pk}_001",
            "agent_id": pk,
            "task": task,
            "status": "completed",
            "started_at": datetime.utcnow().isoformat() + "Z",
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "duration_ms": 4500,
            "result": {
                "summary": f"Agent '{agent['name']}' topshirig'ini muvaffaqiyatli bajardi.",
                "output": f"Task '{task[:50]}...' bajarildi.",
                "tokens_used": 1850,
            },
        }

        return Response(
            APIResponse.success(
                data=execution,
                message=f"Agent '{agent['name']}' bajarildi.",
            )
        )

    @action(detail=True, methods=["get"], url_path="messages")
    def agent_messages(self, request, pk=None):
        """Agent xabarlari."""
        agent = next((a for a in MOCK_AGENTS if a["id"] == pk), None)
        if not agent:
            return Response(
                APIResponse.not_found(message=f"Agent topilmadi: {pk}"),
                status=status.HTTP_404_NOT_FOUND,
            )

        messages = [m for m in MOCK_MESSAGES if m["agent_id"] == pk]

        return Response(
            APIResponse.success(
                data=messages,
                metadata={"total": len(messages)},
            )
        )

    # ── Workflows ──────────────────────────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="workflows")
    def list_workflows(self, request):
        """Workflow lar ro'yxati."""
        return Response(
            APIResponse.success(
                data=MOCK_WORKFLOWS,
                metadata={"total": len(MOCK_WORKFLOWS)},
            )
        )

    @action(detail=False, methods=["post"], url_path=r"workflows/(?P<name>[^/.]+)/execute")
    def execute_workflow(self, request, name=None):
        """Workflow ni bajarish."""
        workflow = next((w for w in MOCK_WORKFLOWS if w["name"] == name), None)
        if not workflow:
            return Response(
                APIResponse.not_found(message=f"Workflow topilmadi: {name}"),
                status=status.HTTP_404_NOT_FOUND,
            )

        input_data = request.data.get("input", {})

        execution = {
            "execution_id": f"exec_wf_{name}_001",
            "workflow": name,
            "status": "completed",
            "triggered_by": request.user.email if hasattr(request.user, "email") else "unknown",
            "started_at": datetime.utcnow().isoformat() + "Z",
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "duration_ms": workflow["avg_execution_time_ms"],
            "steps_completed": len(workflow["steps"]),
            "steps_detail": [
                {
                    "order": step["order"],
                    "agent": step["agent"],
                    "action": step["action"],
                    "status": "completed",
                    "duration_ms": workflow["avg_execution_time_ms"] // len(workflow["steps"]),
                }
                for step in workflow["steps"]
            ],
            "result_summary": f"Workflow '{workflow['display_name']}' muvaffaqiyatli bajarildi.",
        }

        return Response(
            APIResponse.success(
                data=execution,
                message=f"Workflow '{workflow['display_name']}' bajarildi.",
            )
        )

    @action(detail=False, methods=["get"], url_path="workflows/history")
    def workflow_history(self, request):
        """Workflow tarixi."""
        workflow_name = request.query_params.get("workflow")
        history = MOCK_EXECUTION_HISTORY[:]

        if workflow_name:
            history = [h for h in history if h["workflow"] == workflow_name]

        return Response(
            APIResponse.success(
                data=history,
                metadata={"total": len(history)},
            )
        )
