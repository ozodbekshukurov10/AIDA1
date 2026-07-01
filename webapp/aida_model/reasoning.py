from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReasoningResult:
    conclusion: str
    steps: list[str] = field(default_factory=list)
    confidence: float = 0.0
    latency_ms: float = 0.0
    metadata: dict = field(default_factory=dict)


class BaseReasoningLayer(ABC):
    @abstractmethod
    async def reason(self, context: str, query: str) -> ReasoningResult:
        ...

    @abstractmethod
    async def chain_of_thought(self, problem: str, steps: int = 5) -> list[str]:
        ...

    @abstractmethod
    async def analyze(self, data: Any, instructions: str) -> dict:
        ...


class AidaReasoningLayer(BaseReasoningLayer):
    def __init__(self, max_steps: int = 8):
        self._max_steps = max_steps

    async def reason(self, context: str, query: str) -> ReasoningResult:
        steps = [
            f"[1/3] Analyzing query: {query[:50]}...",
            f"[2/3] Retrieving relevant context from: {context[:50]}...",
            f"[3/3] Synthesizing conclusion based on {len(context)} chars of context",
        ]
        return ReasoningResult(
            conclusion=f"Reasoned conclusion for: {query[:100]}",
            steps=steps,
            confidence=0.85,
            metadata={"max_steps": self._max_steps, "reasoning_type": "cot"},
        )

    async def chain_of_thought(self, problem: str, steps: int = 5) -> list[str]:
        thoughts = []
        for i in range(steps):
            thoughts.append(f"Step {i+1}/{steps}: Analyzing aspect of: {problem[:50]}...")
        return thoughts

    async def analyze(self, data: Any, instructions: str) -> dict:
        return {
            "status": "analyzed",
            "data_type": type(data).__name__,
            "insights": f"Analysis based on: {instructions[:50]}",
            "confidence": 0.8,
        }
