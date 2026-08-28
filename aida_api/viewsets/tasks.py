"""
AIDA Enterprise API — Tasks ViewSet

Vazifalarni boshqarish uchun CRUD va maxsus endpointlar.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..responses import APIResponse

MOCK_TASKS = {
    "task_1": {
        "id": "task_1",
        "title": "API integratsiyasini yaratish",
        "description": "Yangi REST API endpointlarini ishlab chiqish",
        "status": "in_progress",
        "priority": "high",
        "assignee": "dev_01",
        "project_id": "proj_1",
        "tags": ["backend", "api"],
        "created_at": "2026-01-15T10:00:00Z",
        "updated_at": "2026-07-01T14:30:00Z",
        "due_date": "2026-07-15T00:00:00Z",
        "estimated_hours": 40,
        "logged_hours": 24,
    },
    "task_2": {
        "id": "task_2",
        "title": "Frontend komponentlarini yaratish",
        "description": "React komponentlarini ishlab chiqish",
        "status": "todo",
        "priority": "medium",
        "assignee": "dev_02",
        "project_id": "proj_1",
        "tags": ["frontend", "react"],
        "created_at": "2026-01-20T09:00:00Z",
        "updated_at": "2026-07-02T11:00:00Z",
        "due_date": "2026-07-20T00:00:00Z",
        "estimated_hours": 60,
        "logged_hours": 0,
    },
    "task_3": {
        "id": "task_3",
        "title": "Ma'lumotlar bazasini migratsiya qilish",
        "description": "Yangi jadvallarni yaratish va eski ma'lumotlarni ko'chirish",
        "status": "done",
        "priority": "high",
        "assignee": "dev_01",
        "project_id": "proj_2",
        "tags": ["database", "migration"],
        "created_at": "2026-01-10T08:00:00Z",
        "updated_at": "2026-06-28T16:00:00Z",
        "due_date": "2026-06-30T00:00:00Z",
        "estimated_hours": 16,
        "logged_hours": 14,
    },
}


class TasksViewSet(viewsets.ViewSet):
    """
    Vazifalarni boshqarish.

    - GET    /tasks/                  — Vazifalar ro'yxati
    - POST   /tasks/                  — Yangi vazifa yaratish
    - GET    /tasks/{id}/             — Bitta vazifa
    - PUT    /tasks/{id}/             — Vazifani to'liq yangilash
    - PATCH  /tasks/{id}/             — Vazifani qisman yangilash
    - DELETE /tasks/{id}/             — Vazifani o'chirish
    - POST   /tasks/{id}/assign/      — Vazifani tayinlash
    - POST   /tasks/{id}/status/      — Vazifa holatini o'zgartirish
    - POST   /tasks/{id}/log-hours/   — Vaqt yozish
    - GET    /tasks/stats/            — Vazifalar statistikasi
    - GET    /tasks/my/               — Joriy foydalanuvchi vazifalari
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Vazifalar ro'yxati."""
        try:
            tasks = list(MOCK_TASKS.values())

            status_filter = request.query_params.get("status")
            if status_filter:
                tasks = [t for t in tasks if t["status"] == status_filter]

            priority_filter = request.query_params.get("priority")
            if priority_filter:
                tasks = [t for t in tasks if t["priority"] == priority_filter]

            project_filter = request.query_params.get("project_id")
            if project_filter:
                tasks = [t for t in tasks if t["project_id"] == project_filter]

            search = request.query_params.get("search")
            if search:
                tasks = [t for t in tasks if search.lower() in t["title"].lower()]

            return Response(APIResponse.success(data=tasks))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    def create(self, request):
        """Yangi vazifa yaratish."""
        try:
            title = request.data.get("title")
            if not title:
                return Response(APIResponse.bad_request(message="Title kiritilishi shart."))

            task_id = f"task_{uuid.uuid4().hex[:8]}"
            now = datetime.utcnow().isoformat() + "Z"

            task = {
                "id": task_id,
                "title": title,
                "description": request.data.get("description", ""),
                "status": "todo",
                "priority": request.data.get("priority", "medium"),
                "assignee": request.data.get("assignee", ""),
                "project_id": request.data.get("project_id", ""),
                "tags": request.data.get("tags", []),
                "created_at": now,
                "updated_at": now,
                "due_date": request.data.get("due_date", ""),
                "estimated_hours": request.data.get("estimated_hours", 0),
                "logged_hours": 0,
            }
            MOCK_TASKS[task_id] = task

            return Response(
                APIResponse.created(data=task, message="Vazifa yaratildi."),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    def retrieve(self, request, pk=None):
        """Bitta vazifani olish."""
        try:
            task = MOCK_TASKS.get(pk)
            if not task:
                return Response(APIResponse.not_found(message=f"Vazifa topilmadi: {pk}"))
            return Response(APIResponse.success(data=task))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    def update(self, request, pk=None):
        """Vazifani to'liq yangilash."""
        try:
            task = MOCK_TASKS.get(pk)
            if not task:
                return Response(APIResponse.not_found(message=f"Vazifa topilmadi: {pk}"))

            task.update({
                "title": request.data.get("title", task["title"]),
                "description": request.data.get("description", task["description"]),
                "status": request.data.get("status", task["status"]),
                "priority": request.data.get("priority", task["priority"]),
                "assignee": request.data.get("assignee", task["assignee"]),
                "project_id": request.data.get("project_id", task["project_id"]),
                "tags": request.data.get("tags", task["tags"]),
                "due_date": request.data.get("due_date", task["due_date"]),
                "estimated_hours": request.data.get("estimated_hours", task["estimated_hours"]),
                "updated_at": datetime.utcnow().isoformat() + "Z",
            })

            return Response(APIResponse.success(data=task, message="Vazifa yangilandi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    def partial_update(self, request, pk=None):
        """Vazifani qisman yangilash."""
        try:
            task = MOCK_TASKS.get(pk)
            if not task:
                return Response(APIResponse.not_found(message=f"Vazifa topilmadi: {pk}"))

            for key in ["title", "description", "status", "priority", "assignee",
                         "project_id", "tags", "due_date", "estimated_hours"]:
                if key in request.data:
                    task[key] = request.data[key]
            task["updated_at"] = datetime.utcnow().isoformat() + "Z"

            return Response(APIResponse.success(data=task, message="Vazifa yangilandi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    def destroy(self, request, pk=None):
        """Vazifani o'chirish."""
        try:
            task = MOCK_TASKS.pop(pk, None)
            if not task:
                return Response(APIResponse.not_found(message=f"Vazifa topilmadi: {pk}"))
            return Response(APIResponse.success(message="Vazifa o'chirildi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """Vazifani shaxsga tayinlash."""
        try:
            task = MOCK_TASKS.get(pk)
            if not task:
                return Response(APIResponse.not_found(message=f"Vazifa topilmadi: {pk}"))

            assignee = request.data.get("assignee")
            if not assignee:
                return Response(APIResponse.bad_request(message="Assignee kiritilishi shart."))

            task["assignee"] = assignee
            task["updated_at"] = datetime.utcnow().isoformat() + "Z"

            return Response(APIResponse.success(data=task, message=f"Vazifa {assignee} ga tayinlandi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["post"], url_path="status")
    def change_status(self, request, pk=None):
        """Vazifa holatini o'zgartirish."""
        try:
            task = MOCK_TASKS.get(pk)
            if not task:
                return Response(APIResponse.not_found(message=f"Vazifa topilmadi: {pk}"))

            new_status = request.data.get("status")
            valid_statuses = ["todo", "in_progress", "review", "done", "cancelled"]
            if new_status not in valid_statuses:
                return Response(
                    APIResponse.bad_request(
                        message=f"Noto'g'ri holat. Ruxsat etilgan: {', '.join(valid_statuses)}"
                    )
                )

            task["status"] = new_status
            task["updated_at"] = datetime.utcnow().isoformat() + "Z"

            return Response(APIResponse.success(data=task, message=f"Holat '{new_status}' ga o'zgartirildi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["post"], url_path="log-hours")
    def log_hours(self, request, pk=None):
        """Vazifaga vaqt yozish."""
        try:
            task = MOCK_TASKS.get(pk)
            if not task:
                return Response(APIResponse.not_found(message=f"Vazifa topilmadi: {pk}"))

            hours = request.data.get("hours")
            if hours is None or not isinstance(hours, (int, float)) or hours <= 0:
                return Response(APIResponse.bad_request(message="Musbat son kiriting."))

            task["logged_hours"] = task.get("logged_hours", 0) + hours
            task["updated_at"] = datetime.utcnow().isoformat() + "Z"

            return Response(
                APIResponse.success(
                    data=task,
                    message=f"{hours} soat qo'shildi. Jami: {task['logged_hours']} soat.",
                )
            )
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Vazifalar statistikasi."""
        try:
            tasks = list(MOCK_TASKS.values())
            total = len(tasks)
            by_status = {}
            by_priority = {}
            total_estimated = 0
            total_logged = 0

            for task in tasks:
                s = task["status"]
                by_status[s] = by_status.get(s, 0) + 1

                p = task["priority"]
                by_priority[p] = by_priority.get(p, 0) + 1

                total_estimated += task.get("estimated_hours", 0)
                total_logged += task.get("logged_hours", 0)

            stats = {
                "total": total,
                "by_status": by_status,
                "by_priority": by_priority,
                "estimated_hours_total": total_estimated,
                "logged_hours_total": total_logged,
                "completion_rate": round(total_logged / total_estimated * 100, 1) if total_estimated > 0 else 0,
            }

            return Response(APIResponse.success(data=stats))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=False, methods=["get"])
    def my(self, request):
        """Joriy foydalanuvchining vazifalari."""
        try:
            user_id = str(request.user.id) if hasattr(request.user, "id") else "dev_01"
            tasks = [t for t in MOCK_TASKS.values() if t["assignee"] == user_id]
            return Response(APIResponse.success(data=tasks))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))
