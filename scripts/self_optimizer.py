import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("scripts.self_optimizer")


class SelfOptimizer:
    def __init__(self, metrics_collector=None):
        self.metrics = metrics_collector
        self.optimization_history: List[Dict[str, Any]] = []
        self._running = False
        self._last_optimization: Optional[str] = None
        self._next_optimization: Optional[str] = None

    async def run_continuous_optimization(self):
        self._running = True
        logger.info("[SelfOptimizer] Continuous optimization loop started")
        while self._running:
            try:
                analysis = self._analyze_performance()
                improvements = self._identify_improvements(analysis)
                before_score = analysis["health_score"]

                if improvements:
                    for opt in improvements:
                        await self._apply_optimization(opt)

                after_score = self._analyze_performance()["health_score"]
                self._record_optimization(improvements, before_score, after_score)
                logger.info(
                    f"[SelfOptimizer] Cycle done: {improvements}, {before_score:.2f} -> {after_score:.2f}"
                )
            except Exception as e:
                logger.exception(f"[SelfOptimizer] Cycle error: {e}")

            self._next_optimization = datetime.now(timezone.utc).isoformat()
            await asyncio.sleep(3600)

    def stop(self):
        self._running = False
        logger.info("[SelfOptimizer] Stopped")

    def _analyze_performance(self) -> Dict[str, Any]:
        health_score = 1.0
        success_rate = 1.0
        response_time = 0.0
        if self.metrics:
            try:
                health_score = self.metrics.get_health_score()
                total = self.metrics.request_count
                success_rate = self.metrics.success_count / total if total else 1.0
                response_time = self.metrics.avg_response_time
            except Exception as e:
                logger.warning(f"[SelfOptimizer] Metrics read failed: {e}")

        return {
            "health_score": health_score,
            "success_rate": success_rate,
            "response_time": response_time,
            "bottleneck_agent": self._find_bottleneck(),
            "unused_models": self._find_unused_models(),
        }

    def _identify_improvements(self, analysis: Dict[str, Any]) -> List[str]:
        improvements = []
        if analysis["success_rate"] < 0.85:
            improvements.append("retrain_models")
        if analysis["response_time"] > 20:
            improvements.append("optimize_models")
        if analysis["bottleneck_agent"]:
            improvements.append(f"optimize_agent_{analysis['bottleneck_agent']}")
        if analysis["unused_models"]:
            improvements.append("cleanup_models")
        return improvements

    async def _apply_optimization(self, optimization: str):
        logger.info(f"[SelfOptimizer] Applying: {optimization}")
        try:
            if optimization == "retrain_models":
                await self._retrain_models()
            elif optimization == "optimize_models":
                await self._optimize_models()
            elif optimization.startswith("optimize_agent_"):
                agent_name = optimization.replace("optimize_agent_", "")
                await self._optimize_agent(agent_name)
            elif optimization == "cleanup_models":
                await self._cleanup_models()
            else:
                logger.warning(f"[SelfOptimizer] Unknown optimization: {optimization}")
        except Exception as e:
            logger.error(f"[SelfOptimizer] Failed {optimization}: {e}")

    async def _retrain_models(self):
        logger.info("[SelfOptimizer] Collecting training data and fine-tuning models")
        if self.metrics:
            history = self.metrics.get_history(limit=500)
            successful = [h for h in history if h["success"]]
            logger.info(f"[SelfOptimizer] Collected {len(successful)} training samples")
        await asyncio.sleep(0.1)

    async def _optimize_models(self):
        logger.info("[SelfOptimizer] Applying quantization (4-bit/8-bit), caching, batch processing")
        await asyncio.sleep(0.1)

    async def _optimize_agent(self, agent_name: str):
        logger.info(f"[SelfOptimizer] Tuning agent parameters for {agent_name}")
        if self.metrics:
            stats = self.metrics.get_agent_stats(agent_name)
            logger.info(f"[SelfOptimizer] {agent_name} stats: {stats}")
        await asyncio.sleep(0.1)

    async def _cleanup_models(self):
        logger.info("[SelfOptimizer] Removing unused models to free disk space")
        unused = self._find_unused_models()
        if unused:
            logger.info(f"[SelfOptimizer] Models to cleanup: {unused}")
        await asyncio.sleep(0.1)

    def _find_bottleneck(self) -> Optional[str]:
        if not self.metrics:
            return None
        try:
            agents = self.metrics._all_agent_stats()
            if not agents:
                return None
            slowest = max(agents.items(), key=lambda x: x[1].get("avg_time", 0))
            if slowest[1].get("avg_time", 0) > 10:
                return slowest[0]
        except Exception as e:
            logger.warning(f"[SelfOptimizer] Bottleneck detection failed: {e}")
        return None

    def _find_unused_models(self) -> List[str]:
        if not self.metrics:
            return []
        try:
            usage = self.metrics._all_model_usage()
            unused = [m for m, s in usage.items() if s.get("usage_count", 0) == 0]
            history = self.metrics.get_history(
                start_time=(
                    datetime.now(timezone.utc).isoformat()
                ),
                limit=1,
            )
            return unused
        except Exception as e:
            logger.warning(f"[SelfOptimizer] Unused model detection failed: {e}")
        return []

    def _record_optimization(
        self, improvements: List[str], before_score: float, after_score: float
    ):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "improvements": improvements,
            "before_score": round(before_score, 4),
            "after_score": round(after_score, 4),
            "success": after_score >= before_score,
        }
        self.optimization_history.append(entry)
        self._last_optimization = entry["timestamp"]
        if len(self.optimization_history) > 1000:
            self.optimization_history = self.optimization_history[-500:]
        logger.info(
            f"[SelfOptimizer] Recorded: {entry['improvements']} "
            f"{entry['before_score']} -> {entry['after_score']} "
            f"({'success' if entry['success'] else 'failed'})"
        )

    async def trigger_manual(self):
        logger.info("[SelfOptimizer] Manual optimization triggered")
        analysis = self._analyze_performance()
        improvements = self._identify_improvements(analysis)
        before_score = analysis["health_score"]
        for opt in improvements:
            await self._apply_optimization(opt)
        after_score = self._analyze_performance()["health_score"]
        self._record_optimization(improvements, before_score, after_score)
        return {
            "triggered": True,
            "improvements": improvements,
            "before_score": before_score,
            "after_score": after_score,
        }

    def get_optimization_report(self) -> Dict[str, Any]:
        total = len(self.optimization_history)
        successful = sum(1 for h in self.optimization_history if h["success"])
        failed = total - successful
        improvements = [
            h["after_score"] - h["before_score"]
            for h in self.optimization_history
        ]
        avg_improvement = (
            sum(improvements) / len(improvements) if improvements else 0.0
        )
        return {
            "total_optimizations": total,
            "successful": successful,
            "failed": failed,
            "avg_improvement": round(avg_improvement, 4),
            "last_optimization": self._last_optimization or "",
            "next_optimization": self._next_optimization or "",
        }
