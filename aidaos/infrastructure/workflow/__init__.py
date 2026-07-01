"""Workflow repository adapter — wraps the existing MultiAgentOrchestrator workflows."""

from __future__ import annotations
import logging
from typing import Any

from ...domain.entities import WorkflowTemplate
from ...domain.interfaces import WorkflowRepository

logger = logging.getLogger("aidaos.infrastructure.workflow")


class WorkflowRepoAdapter(WorkflowRepository):
    def __init__(self):
        self._templates: dict[str, WorkflowTemplate] = {}

    async def register_template(self, template: WorkflowTemplate) -> None:
        self._templates[template.name] = template
        logger.info(f"Workflow template '{template.name}' registered")

    async def get_template(self, name: str) -> WorkflowTemplate | None:
        return self._templates.get(name)

    async def list_templates(self) -> list[WorkflowTemplate]:
        return list(self._templates.values())

    async def execute(self, template_name: str, context: dict) -> Any:
        from ...application.use_cases.workflow import WorkflowUseCase
        uc = WorkflowUseCase.__new__(WorkflowUseCase)
        uc._agents = None
        uc._workflows = self
        return await uc.execute(template_name, context.get("prompt", ""),
                                thread_id=context.get("thread_id", ""))
