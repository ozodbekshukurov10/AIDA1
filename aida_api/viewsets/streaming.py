"""
AIDA Enterprise API — Streaming ViewSet

AI javoblari uchun SSE streaming endpointlari.
"""
from __future__ import annotations
import json
import time
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..responses import APIResponse
from ..streaming.sse import SSEEvent, create_sse_response, text_stream, progress_stream


class StreamingViewSet(viewsets.ViewSet):
    """
    Streaming endpointlari.
    
    - POST /stream/chat/ — Chat streaming
    - POST /stream/execute/ — Agent task streaming
    - POST /stream/workflow/ — Workflow streaming
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="chat")
    def stream_chat(self, request):
        """Chat uchun streaming response."""
        prompt = request.data.get("prompt", "")
        model = request.data.get("model", "default")

        if not prompt:
            return Response(
                APIResponse.bad_request(message="Prompt kiritilishi shart.")
            )

        def generate():
            # Simulated streaming — haqiqiy LLM integration keyin qo'shiladi
            steps = [
                {"name": "Tahlil", "status": "completed", "detail": "So'rov tahlil qilindi"},
                {"name": "Qidiruv", "status": "completed", "detail": "Ma'lumotlar qidirildi"},
                {"name": "Generatsiya", "status": "running", "detail": "Javob yaratilmoqda..."},
            ]

            for step in steps:
                yield SSEEvent(
                    event="progress",
                    data=json.dumps(step)
                )
                time.sleep(0.1)

            # Simulated response text
            response_text = (
                f"Sizning so'rovingiz: {prompt}\n\n"
                "Bu streaming response misoli. "
                "Haqiqiy AI javobi bu yerda generatsiya qilinadi."
            )

            yield SSEEvent(
                event="text",
                data=json.dumps({"content": response_text})
            )

            yield SSEEvent(
                event="done",
                data=json.dumps({
                    "done": True,
                    "model": model,
                    "latency_ms": 150,
                })
            )

        return create_sse_response(generate())

    @action(detail=False, methods=["post"], url_path="execute")
    def stream_execute(self, request):
        """Agent task uchun streaming."""
        task = request.data.get("task", "")
        agent = request.data.get("agent", "general")

        if not task:
            return Response(
                APIResponse.bad_request(message="Task kiritilishi shart.")
            )

        def generate():
            steps = [
                {"name": "Vazifa tahlili", "status": "completed", "detail": f"Agent: {agent}"},
                {"name": "Bajarish", "status": "running", "detail": "Vazifa bajarilmoqda..."},
                {"name": "Natija", "status": "pending", "detail": ""},
            ]

            for step in steps:
                yield SSEEvent(
                    event="progress",
                    data=json.dumps(step)
                )
                time.sleep(0.15)

            yield SSEEvent(
                event="text",
                data=json.dumps({
                    "content": f"Agent '{agent}' vazifani bajaradi: {task}"
                })
            )

            yield SSEEvent(
                event="done",
                data=json.dumps({"done": True, "agent": agent})
            )

        return create_sse_response(generate())

    @action(detail=False, methods=["post"], url_path="workflow")
    def stream_workflow(self, request):
        """Workflow uchun streaming."""
        workflow = request.data.get("workflow", "full_project")
        params = request.data.get("params", {})

        def generate():
            if workflow == "full_project":
                steps = [
                    {"name": "Rejalashtirish", "status": "completed", "detail": "Loyiha rejasini tuzish"},
                    {"name": "Tadqiqot", "status": "completed", "detail": "Talablarni aniqlash"},
                    {"name": "Kod yozish", "status": "running", "detail": "Kod yaratilmoqda..."},
                    {"name": "Test", "status": "pending", "detail": "Testlar yozish"},
                    {"name": "Xavfsizlik", "status": "pending", "detail": "Tekshirish"},
                    {"name": "Hujjatlar", "status": "pending", "detail": "Dokumentatsiya"},
                ]
            else:
                steps = [
                    {"name": "Boshlash", "status": "running", "detail": f"Workflow: {workflow}"},
                ]

            for step in steps:
                yield SSEEvent(
                    event="progress",
                    data=json.dumps(step)
                )
                time.sleep(0.2)

            yield SSEEvent(
                event="done",
                data=json.dumps({"done": True, "workflow": workflow})
            )

        return create_sse_response(generate())
