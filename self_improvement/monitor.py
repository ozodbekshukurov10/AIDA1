# -*- coding: utf-8 -*-
"""
AIDA Self-Healing Monitor
==========================
Butun tizimni doimiy nazorat qiladi:
1. Har X daqiqada diagnostics ishlatadi
2. Xato topilsa - code_fixer orqali avtomatik to'g'irlaydi
3. Improvement siklini ishlatadi
4. Barcha hodisalarni DB ga yozadi
"""
import os, logging, threading, time
from datetime import datetime
from .diagnostics import run_full_diagnostics
from .code_fixer import fix_all_errors
from .scheduler import run_improvement_cycle

logger = logging.getLogger("aida.monitor")

_monitor_thread = None
_running = False
_interval_seconds = 300  # 5 daqiqa


def _monitor_loop():
    """Orqa fonda ishlaydi."""
    global _running
    logger.info("[MONITOR] AIDA Self-Healing Monitor ishga tushdi.")
    cycle = 0

    while _running:
        cycle += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"[MONITOR] Sikl #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*60}")

        try:
            # 1. Diagnostics
            report = run_full_diagnostics()
            summary = report["summary"]

            logger.info(
                f"[MONITOR] Diagnostics: "
                f"Sintaksis xatolar={summary['syntax_errors']} | "
                f"API={summary['api_ok']}/{summary['api_total']} | "
                f"DB={summary['db_ok']}"
            )

            # 2. Auto-fix syntax errors
            if summary["syntax_errors"] > 0:
                logger.warning(
                    f"[MONITOR] {summary['syntax_errors']} ta sintaksis xato topildi! "
                    f"Auto-fix boshlanmoqda..."
                )
                fix_results = fix_all_errors(report["syntax_errors"])
                fixed_count = sum(1 for r in fix_results if r["fixed"])
                logger.info(
                    f"[MONITOR] Auto-fix natija: {fixed_count}/{len(fix_results)} ta to'g'irlandi."
                )

                # Fix natijasini DB ga yozish
                try:
                    from .models import ImprovementLog, Task
                    last = ImprovementLog.objects.order_by("-cycle_number").first()
                    ImprovementLog.objects.create(
                        cycle_number=(last.cycle_number + 1) if last else 1,
                        trigger="auto_fix",
                        tasks_analyzed=0,
                        strategies_updated=0,
                        knowledge_added=0,
                        avg_score_before=0,
                        avg_score_after=0,
                        summary=(
                            f"Auto-fix sikli #{cycle}: "
                            f"{summary['syntax_errors']} xato topildi, "
                            f"{fixed_count} ta to'g'irlandi."
                        )
                    )
                except Exception as e:
                    logger.error(f"[MONITOR] DB yozish xatosi: {e}")

            # 3. Strategy improvement (har 5 siklda)
            if cycle % 5 == 0:
                logger.info("[MONITOR] Strategy improvement sikli boshlandi...")
                try:
                    log = run_improvement_cycle(trigger="monitor")
                    logger.info(f"[MONITOR] Improvement: {log.summary}")
                except Exception as e:
                    logger.error(f"[MONITOR] Improvement xatosi: {e}")

        except Exception as e:
            logger.error(f"[MONITOR] Monitor sikl xatosi: {e}")

        # Keyingi sikl kutish
        logger.info(f"[MONITOR] Keyingi skanerlash {_interval_seconds}s dan keyin...")
        time.sleep(_interval_seconds)

    logger.info("[MONITOR] AIDA Self-Healing Monitor to'xtatildi.")


def start_monitor(interval_seconds: int = 300):
    """Monitorigni orqa fonda ishga tushurish."""
    global _monitor_thread, _running, _interval_seconds
    if _running:
        logger.warning("[MONITOR] Monitor allaqachon ishlayapti.")
        return

    _interval_seconds = interval_seconds
    _running = True
    _monitor_thread = threading.Thread(target=_monitor_loop, daemon=True, name="AIDA-Monitor")
    _monitor_thread.start()
    logger.info(f"[MONITOR] Monitor ishga tushdi. Interval: {interval_seconds}s")


def stop_monitor():
    """Monitorigni to'xtatish."""
    global _running
    _running = False
    logger.info("[MONITOR] Monitor to'xtatilmoqda...")


def get_monitor_status() -> dict:
    """Monitor holati."""
    return {
        "running": _running,
        "interval_seconds": _interval_seconds,
        "thread_alive": _monitor_thread.is_alive() if _monitor_thread else False,
    }
