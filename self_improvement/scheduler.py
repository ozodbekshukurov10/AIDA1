# -*- coding: utf-8 -*-
"""
AIDA Self-Improvement Scheduler
=================================
Har 24 soatda avtomatik o'rganish sikli:
1. Yomon baholangan topshiriqlarni tahlil qiladi
2. Strategiyalarni yangilaydi
3. Yangi bilimlar qo'shadi
4. Kuchaytirish jurnalini yozadi
"""
import logging
from django.db.models import Avg, Count
from django.utils import timezone
from .models import Task, Strategy, Evaluation, KnowledgeChunk, ImprovementLog
from .engine import run_task

logger = logging.getLogger("aida.scheduler")


def run_improvement_cycle(trigger: str = "scheduler"):
    """
    AIDA o'z-o'zini kuchaytirish sikli.
    """
    logger.info(f"[AIDA] Kuchaytirish sikli boshlandi. Sabab: {trigger}")

    # Oxirgi sikldan oldin o'rtacha ball
    avg_before = Evaluation.objects.aggregate(avg=Avg("score"))["avg"] or 0.0

    # 1. Muvaffaqiyatsiz topshiriqlarni qayta bajarish
    retrying_tasks = Task.objects.filter(status="retrying")
    retried = 0
    for task in retrying_tasks[:10]:  # Har siklda 10 tagacha
        run_task(task)
        retried += 1
        logger.info(f"  ? Qayta bajarildi: {task.id}")

    # 2. Zaif strategiyalarni o'chirish (success_rate < 0.2, ko'p ishlatilgan)
    removed = Strategy.objects.filter(
        success_rate__lt=0.2, usage_count__gt=5, is_active=True
    ).update(is_active=False)
    logger.info(f"  ? Zaif strategiyalar o'chirildi: {removed}")

    # 3. Yangi avtomatik strategiya qo'shish (yuqori ballli sohalar asosida)
    top_domains = (
        Evaluation.objects
        .filter(score__gte=0.8)
        .values("execution__task__domain")
        .annotate(cnt=Count("id"))
        .order_by("-cnt")[:3]
    )
    new_strategies = 0
    for d in top_domains:
        domain = d["execution__task__domain"]
        name = f"Auto Strategy [{domain}] {timezone.now().strftime('%Y%m%d')}"
        if not Strategy.objects.filter(name=name).exists():
            Strategy.objects.create(
                name=name,
                domain=domain,
                prompt_template=(
                    f"Siz AIDA — {domain} sohasida mutaxassisissiz.\n\n"
                    "TOPSHIRIQ: {{user_request}}\n"
                    "MAQSAD: {{goal}}\n\n"
                    "BILIMLAR:\n{{knowledge}}\n\n"
                    "Aniq, to'liq va professional javob bering:"
                ),
                success_rate=0.65,
            )
            new_strategies += 1

    # 4. Kam ishlatilgan bilimlarni tozalash (30 kundan eski, 0 marta ishlatilgan)
    cutoff = timezone.now() - timezone.timedelta(days=30)
    cleaned_knowledge = KnowledgeChunk.objects.filter(
        created_at__lt=cutoff, used_count=0, is_verified=False
    ).delete()[0]

    # Oxirgi sikldan keyin o'rtacha ball
    avg_after = Evaluation.objects.aggregate(avg=Avg("score"))["avg"] or 0.0

    # 5. Kuchaytirish jurnali
    last_log = ImprovementLog.objects.order_by("-cycle_number").first()
    cycle_num = (last_log.cycle_number + 1) if last_log else 1

    log = ImprovementLog.objects.create(
        cycle_number=cycle_num,
        trigger=trigger,
        tasks_analyzed=retried,
        strategies_updated=removed + new_strategies,
        knowledge_added=new_strategies,
        avg_score_before=round(avg_before, 4),
        avg_score_after=round(avg_after, 4),
        summary=(
            f"Sikl #{cycle_num}: {retried} topshiriq qayta bajarildi, "
            f"{removed} zaif strategiya o'chirildi, "
            f"{new_strategies} yangi strategiya qo'shildi, "
            f"{cleaned_knowledge} eski bilim tozalandi. "
            f"O'rtacha ball: {avg_before:.3f} ? {avg_after:.3f}"
        )
    )

    logger.info(f"[AIDA] Kuchaytirish sikli tugadi. {log.summary}")
    return log
