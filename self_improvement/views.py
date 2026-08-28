# -*- coding: utf-8 -*-
"""
AIDA Self-Improvement â€” REST API Views
Protected with AIDA_SECURITY_TOKEN verification.
"""
import os
import json
import threading
import logging
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import Task, Strategy, KnowledgeChunk, Evaluation, ImprovementLog
from .engine import run_task
from .scheduler import run_improvement_cycle

logger = logging.getLogger("aida.views")


def check_security(request):
    """Token orqali xavfsizlikni tekshirish."""
    expected_token = os.environ.get("AIDA_SECURITY_TOKEN", "aida-super-secure-token-2026")
    token = request.headers.get("X-AIDA-Security-Token") or request.GET.get("security_token")
    if not token or token != expected_token:
        return JsonResponse({
            "status": 403,
            "success": False,
            "message": "Ruxsat etilmadi. Xavfsizlik tokeni noto'g'ri yoki taqdim etilmagan."
        }, status=403)
    return None


class SecureView(View):
    """Barcha metodlari token bilan himoyalangan Base View."""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        sec_err = check_security(request)
        if sec_err:
            return sec_err
        return super().dispatch(request, *args, **kwargs)


def _run_task_async(task):
    """Topshiriqni orqa fonda bajarish."""
    try:
        run_task(task)
    except Exception as e:
        logger.error(f"Task {task.id} xatosi: {e}")
        task.status = "failed"
        task.save(update_fields=["status"])


class TaskCreateView(SecureView):
    """POST /api/si/tasks/ â€” Yangi topshiriq yaratish va bajarish."""

    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON format noto'g'ri."}, status=400)

        user_request = data.get("user_request", "").strip()
        if not user_request:
            return JsonResponse({"error": "user_request majburiy."}, status=400)

        task = Task.objects.create(
            user_request=user_request,
            goal=data.get("goal", user_request),
            constraints=data.get("constraints", []),
            expected_output=data.get("expected_output", ""),
            difficulty=int(data.get("difficulty", 3)),
            domain=data.get("domain", "general"),
            source=data.get("source", "user"),
        )

        # Orqa fonda bajarish
        thread = threading.Thread(target=_run_task_async, args=(task,), daemon=True)
        thread.start()

        return JsonResponse({
            "task_id": str(task.id),
            "status": task.status,
            "message": "Topshiriq qabul qilindi va bajarilmoqda."
        }, status=201)

    def get(self, request):
        tasks = Task.objects.all()[:20]
        return JsonResponse({
            "tasks": [
                {
                    "id": str(t.id),
                    "domain": t.domain,
                    "status": t.status,
                    "difficulty": t.difficulty,
                    "retry_count": t.retry_count,
                    "request": t.user_request[:100],
                    "created_at": t.created_at.isoformat(),
                }
                for t in tasks
            ]
        })


class TaskDetailView(SecureView):
    """GET /api/si/tasks/<id>/ â€” Topshiriq tafsilotlari."""

    def get(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return JsonResponse({"error": "Topshiriq topilmadi."}, status=404)

        executions = []
        for ex in task.executions.all():
            eval_data = None
            if hasattr(ex, "evaluation"):
                e = ex.evaluation
                eval_data = {
                    "score": e.score,
                    "relevance": e.relevance_score,
                    "clarity": e.clarity_score,
                    "accuracy": e.accuracy_score,
                    "error_type": e.error_type,
                    "feedback": e.feedback,
                }
            executions.append({
                "attempt": ex.attempt_number,
                "model": ex.model_used,
                "output": ex.output[:500],
                "time_ms": ex.time_taken_ms,
                "tokens": ex.token_count,
                "is_successful": ex.is_successful,
                "evaluation": eval_data,
            })

        return JsonResponse({
            "id": str(task.id),
            "user_request": task.user_request,
            "goal": task.goal,
            "domain": task.domain,
            "difficulty": task.difficulty,
            "status": task.status,
            "retry_count": task.retry_count,
            "executions": executions,
        })


class ImprovementCycleView(SecureView):
    """POST /api/si/improve/ â€” Kuchaytirish siklini boshlash."""

    def post(self, request):
        try:
            log = run_improvement_cycle(trigger="manual")
            return JsonResponse({
                "cycle": log.cycle_number,
                "summary": log.summary,
                "avg_score_before": log.avg_score_before,
                "avg_score_after": log.avg_score_after,
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def get(self, request):
        logs = ImprovementLog.objects.all()[:10]
        return JsonResponse({
            "logs": [
                {
                    "cycle": l.cycle_number,
                    "trigger": l.trigger,
                    "summary": l.summary,
                    "avg_before": l.avg_score_before,
                    "avg_after": l.avg_score_after,
                    "created_at": l.created_at.isoformat(),
                }
                for l in logs
            ]
        })


class StatsView(SecureView):
    """GET /api/si/stats/ â€” Statistika."""

    def get(self, request):
        from django.db.models import Avg
        stats = {
            "tasks": {
                "total": Task.objects.count(),
                "done": Task.objects.filter(status="done").count(),
                "failed": Task.objects.filter(status="failed").count(),
                "retrying": Task.objects.filter(status="retrying").count(),
            },
            "evaluations": {
                "total": Evaluation.objects.count(),
                "avg_score": round(Evaluation.objects.aggregate(avg=Avg("score"))["avg"] or 0, 3),
                "good": Evaluation.objects.filter(score__gte=0.75).count(),
            },
            "strategies": {
                "total": Strategy.objects.count(),
                "active": Strategy.objects.filter(is_active=True).count(),
            },
            "knowledge": {
                "total": KnowledgeChunk.objects.count(),
                "verified": KnowledgeChunk.objects.filter(is_verified=True).count(),
            },
            "improvement_cycles": ImprovementLog.objects.count(),
        }
        return JsonResponse(stats)


class DiagnosticsView(SecureView):
    """GET /api/si/diagnostics/ â€” Tizim diagnostikasi."""

    def get(self, request):
        from .diagnostics import run_full_diagnostics
        try:
            report = run_full_diagnostics()
            return JsonResponse(report, safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class AutoFixView(SecureView):
    """POST /api/si/autofix/ â€” Avtomatik to'g'irlash."""

    def post(self, request):
        from .diagnostics import run_full_diagnostics
        from .code_fixer import fix_all_errors
        try:
            logger.info("[AutoFix] Skanerlash boshlandi...")
            report = run_full_diagnostics()
            syntax_errors = report["syntax_errors"]

            if not syntax_errors:
                return JsonResponse({
                    "message": "Sintaksis xato topilmadi.",
                    "healthy": True,
                    "fixes": []
                })

            fix_results = fix_all_errors(syntax_errors)
            fixed = sum(1 for r in fix_results if r["fixed"])

            return JsonResponse({
                "message": f"{len(syntax_errors)} ta xato topildi, {fixed} ta to'g'irlandi.",
                "healthy": fixed == len(syntax_errors),
                "total_errors": len(syntax_errors),
                "fixed": fixed,
                "fixes": [
                    {
                        "file": r["filepath"].replace(str(__import__("pathlib").Path(__file__).resolve().parent.parent), ""),
                        "fixed": r["fixed"],
                        "attempts": r["attempts"],
                        "message": r["message"],
                    }
                    for r in fix_results
                ]
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class MonitorView(SecureView):
    """POST /api/si/monitor/ â€” Monitor daemoni boshqaruvi."""

    def post(self, request):
        from .monitor import start_monitor, get_monitor_status
        try:
            data = json.loads(request.body) if request.body else {}
            interval = int(data.get("interval_seconds", 60))
            start_monitor(interval_seconds=interval)
            return JsonResponse({
                "message": f"Monitor faollashtirildi. Interval: {interval}s",
                "status": get_monitor_status()
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def get(self, request):
        from .monitor import get_monitor_status
        return JsonResponse(get_monitor_status())


class LearnSkillView(SecureView):
    """POST /api/si/skills/learn/ — Yangi skill (strategiya) yaratish."""

    def post(self, request):
        from .skills_factory import learn_new_skill
        try:
            result = learn_new_skill()
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
