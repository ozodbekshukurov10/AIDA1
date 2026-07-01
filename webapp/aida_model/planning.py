from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class PlanStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class PlanStep:
    id: str = ""
    action: str = ""
    description: str = ""
    depends_on: list[str] = field(default_factory=list)
    status: PlanStatus = PlanStatus.PENDING
    result: Any = None
    metadata: dict = field(default_factory=dict)


@dataclass
class Plan:
    goal: str = ""
    steps: list[PlanStep] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    status: PlanStatus = PlanStatus.PENDING
    current_step: int = 0


@dataclass
class StepResult:
    success: bool = False
    output: str = ""
    error: str | None = None
    next_steps: list[str] = field(default_factory=list)


class BasePlanningLayer(ABC):
    @abstractmethod
    async def create_plan(self, goal: str, context: dict | None = None) -> Plan:
        ...

    @abstractmethod
    async def execute_step(self, plan: Plan, step_index: int = 0) -> StepResult:
        ...

    @abstractmethod
    async def replan(self, plan: Plan, feedback: str) -> Plan:
        ...

    @abstractmethod
    async def get_progress(self, plan: Plan) -> dict:
        ...


class AidaPlanningLayer(BasePlanningLayer):
    def __init__(self, max_steps: int = 10):
        self._max_steps = max_steps

    async def create_plan(self, goal: str, context: dict | None = None) -> Plan:
        steps = [
            PlanStep(id="1", action="analyze", description=f"Analyze goal: {goal[:50]}...",
                     status=PlanStatus.PENDING),
            PlanStep(id="2", action="research", description="Gather required information",
                     depends_on=["1"], status=PlanStatus.PENDING),
            PlanStep(id="3", action="implement", description=f"Implement solution for: {goal[:50]}...",
                     depends_on=["2"], status=PlanStatus.PENDING),
            PlanStep(id="4", action="verify", description="Verify and validate results",
                     depends_on=["3"], status=PlanStatus.PENDING),
        ]
        return Plan(goal=goal, steps=steps, context=context or {})

    async def execute_step(self, plan: Plan, step_index: int = 0) -> StepResult:
        if step_index >= len(plan.steps):
            return StepResult(success=False, error="Step index out of range")
        step = plan.steps[step_index]
        step.status = PlanStatus.IN_PROGRESS
        result = StepResult(
            success=True,
            output=f"Executed step {step.id}: {step.action} - {step.description[:50]}...",
        )
        step.status = PlanStatus.COMPLETED
        step.result = result
        return result

    async def replan(self, plan: Plan, feedback: str) -> Plan:
        new_steps = list(plan.steps)
        new_steps.append(PlanStep(
            id=str(len(new_steps) + 1),
            action="replan",
            description=f"Replan based on feedback: {feedback[:50]}...",
        ))
        plan.steps = new_steps
        plan.status = PlanStatus.PENDING
        return plan

    async def get_progress(self, plan: Plan) -> dict:
        completed = sum(1 for s in plan.steps if s.status == PlanStatus.COMPLETED)
        total = len(plan.steps)
        return {
            "goal": plan.goal[:50],
            "total_steps": total,
            "completed": completed,
            "progress_pct": (completed / total * 100) if total else 0,
            "status": plan.status.value,
        }
