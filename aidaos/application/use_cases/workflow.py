"""Workflow use case — orchestrates multi-step agent workflows."""

from __future__ import annotations
import logging
import time
from typing import Any

from ...domain.entities import WorkflowTemplate, AgentContext, AgentResult
from ...domain.exceptions import WorkflowError, WorkflowStepError
from ...domain.interfaces import AgentRepository, WorkflowRepository

logger = logging.getLogger("aidaos.application.workflow")


class WorkflowUseCase:
    def __init__(self, agent_repo: AgentRepository, workflow_repo: WorkflowRepository):
        self._agents = agent_repo
        self._workflows = workflow_repo
        self._builtin_templates = self._default_templates()

    def _default_templates(self) -> dict[str, WorkflowTemplate]:
        return {
            "full_project": WorkflowTemplate(
                name="full_project",
                description="Complete project workflow: plan → research → code → test → debug → security → docs",
                steps=["planner", "research", "code", "test", "debug", "security", "documentation"],
            ),
            "code_review": WorkflowTemplate(
                name="code_review",
                description="Code review: code → security → test → documentation",
                steps=["code", "security", "test", "documentation"],
            ),
            "bug_fix": WorkflowTemplate(
                name="bug_fix",
                description="Bug fix: debug → test → monitoring",
                steps=["debug", "test", "monitoring"],
            ),
            "deploy": WorkflowTemplate(
                name="deploy",
                description="Deployment: security → deployment → monitoring",
                steps=["security", "deployment", "monitoring"],
            ),
        }

    async def list_templates(self) -> list[dict]:
        templates = list(self._builtin_templates.values())
        try:
            registered = await self._workflows.list_templates()
            templates.extend(registered)
        except Exception:
            pass
        return [t.to_dict() for t in templates]

    async def execute(self, template_name: str, prompt: str, thread_id: str = "",
                      metadata: dict = None) -> list[dict]:
        template = self._builtin_templates.get(template_name)
        if not template:
            try:
                template = await self._workflows.get_template(template_name)
            except Exception:
                pass
        if not template:
            raise WorkflowError(f"Workflow template '{template_name}' not found")

        results = []
        for i, step_name in enumerate(template.steps):
            logger.info(f"Workflow step {i+1}/{len(template.steps)}: {step_name}")
            ctx = AgentContext(
                task_id=f"wflow_{template_name}_{i}",
                prompt=f"[Step {i+1}/{len(template.steps)}: {step_name}]\n{prompt}",
                thread_id=thread_id,
                metadata={**(metadata or {}), "workflow": template_name, "step": i},
            )

            try:
                result = await self._agents.execute(step_name, ctx)
                results.append({
                    "step": step_name,
                    "index": i,
                    "success": result.success,
                    "content": result.content[:500] if result.content else "",
                    "error": result.error,
                    "latency_ms": result.latency_ms,
                })
                if not result.success and result.error:
                    logger.warning(f"Step '{step_name}' failed: {result.error}")
            except Exception as e:
                results.append({
                    "step": step_name, "index": i,
                    "success": False, "error": str(e),
                })

        return results

    async def register_template(self, template: WorkflowTemplate) -> dict:
        await self._workflows.register_template(template)
        return {"success": True, "template": template.name}
