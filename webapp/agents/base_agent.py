import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..orchestrator import Task

logger = logging.getLogger("webapp.agents.base_agent")


class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        model_name: str = "qwen2.5:3b",
        memory: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Any]] = None,
    ):
        self.name = name
        self.model_name = model_name
        self.memory: Dict[str, Any] = memory or {}
        self.tools: List[Any] = tools or []
        self.performance_metrics: Dict[str, Any] = {
            "total_calls": 0,
            "success_count": 0,
            "error_count": 0,
            "avg_response_time": 0.0,
            "total_response_time": 0.0,
        }

    @abstractmethod
    async def execute(self, task: Task) -> Dict[str, Any]:
        pass

    async def analyze_input(self, prompt: str) -> Dict[str, Any]:
        complexity = self._calculate_complexity(prompt)
        steps = self._identify_steps(prompt)
        estimated_time = self._estimate_time(prompt)
        confidence = self._calculate_confidence(prompt)
        return {
            "complexity": complexity,
            "required_steps": steps,
            "estimated_time": estimated_time,
            "confidence": confidence,
        }

    async def make_decision(self, options: List[str]) -> str:
        scored = [(opt, self._score_option(opt)) for opt in options]
        scored.sort(key=lambda x: x[1], reverse=True)
        chosen = scored[0][0] if scored else ""
        logger.info(f"[{self.name}] Decision: chose '{chosen}' from {len(options)} options")
        return chosen

    async def self_evaluate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        quality = result.get("quality", 0.5)
        correctness = result.get("correctness", 0.5)
        quality_score = (quality + correctness) / 2
        return {
            "quality_score": round(min(quality_score, 1.0), 2),
            "correctness_check": correctness >= 0.5,
            "improvement_areas": self._identify_improvements(result),
            "should_retry": quality_score < 0.4,
        }

    def record_performance(self, success: bool, response_time: float) -> None:
        m = self.performance_metrics
        m["total_calls"] += 1
        if success:
            m["success_count"] += 1
        else:
            m["error_count"] += 1
        m["total_response_time"] += response_time
        m["avg_response_time"] = round(m["total_response_time"] / m["total_calls"], 4)

    def _calculate_complexity(self, prompt: str) -> int:
        words = len(re.findall(r"\S+", prompt.strip()))
        return min(max(int(words / 10), 1), 10)

    def _identify_steps(self, prompt: str) -> List[str]:
        norm = prompt.lower()
        steps = []

        if any(kw in norm for kw in ["code", "kod", "function", "class", "script"]):
            steps.append("Analyze requirements")
            steps.append("Design solution")
            steps.append("Implement code")
            steps.append("Test and validate")
            steps.append("Optimize if needed")
        elif any(kw in norm for kw in ["debug", "xato", "error", "bug", "fix"]):
            steps.append("Reproduce error")
            steps.append("Identify root cause")
            steps.append("Implement fix")
            steps.append("Verify fix")
        elif any(kw in norm for kw in ["plan", "reja", "strategiya"]):
            steps.append("Define objectives")
            steps.append("Break down tasks")
            steps.append("Set timeline")
            steps.append("Allocate resources")
        elif any(kw in norm for kw in ["test", "tekshir", "sinov"]):
            steps.append("Understand requirements")
            steps.append("Write test cases")
            steps.append("Execute tests")
            steps.append("Report results")
        else:
            steps.append("Understand request")
            steps.append("Analyze context")
            steps.append("Formulate response")
            steps.append("Review output")

        return steps[:5]

    def _estimate_time(self, prompt: str) -> int:
        complexity = self._calculate_complexity(prompt)
        return complexity * 10

    def _calculate_confidence(self, prompt: str) -> float:
        norm = prompt.strip()
        if not norm:
            return 0.0
        word_count = len(re.findall(r"\S+", norm))
        clarity = min(word_count / 20, 1.0)
        has_structure = 0.3 if any(c in norm for c in ["?", "!", ":", ";", ","]) else 0.0
        return round(min(clarity + has_structure, 1.0), 2)

    def _score_option(self, option: str) -> float:
        norm = option.lower()
        score = 0.5
        if len(norm) > 10:
            score += 0.2
        if any(c in norm for c in [".", ":", "!"]):
            score += 0.1
        if any(kw in norm for kw in ["best", "optimal", "efficient", "recommended"]):
            score += 0.2
        return round(min(score, 1.0), 2)

    def _identify_improvements(self, result: Dict[str, Any]) -> List[str]:
        areas = []
        if result.get("errors"):
            areas.append("Error handling")
        if result.get("quality", 0) < 0.7:
            areas.append("Output quality")
        if result.get("completeness", 1) < 0.8:
            areas.append("Completeness")
        if not areas:
            areas.append("Performance optimization")
        return areas
