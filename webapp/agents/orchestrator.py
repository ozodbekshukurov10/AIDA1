from __future__ import annotations
import asyncio
import json
import logging
import time
import uuid
from typing import Any

from ..llm.gateway import get_gateway
from ..llm.base import Message, MessageRole, Completion
from .base_agent import (
    BaseAgent, AgentContext, AgentResult, AgentStatus,
    AgentCapability, AgentMessage, MessageBus,
)
from .planner_agent import PlannerAgent
from .code_agent import CodeAgent
from .debug_agent import DebugAgent
from .research_agent import ResearchAgent
from .test_agent import TestAgent
from .security_agent import SecurityAgent
from .documentation_agent import DocumentationAgent
from .memory_agent import MemoryAgent
from .monitoring_agent import MonitoringAgent
from .deployment_agent import DeploymentAgent

logger = logging.getLogger("webapp.agents.orchestrator")

WORKFLOW_TEMPLATES: dict[str, list[dict]] = {
    "full_project": [
        {"agent": "planner", "description": "Loyihani vazifalarga ajratish"},
        {"agent": "research", "description": "Talablar va eng yaxshi amaliyotlarni tadqiq qilish"},
        {"agent": "code", "description": "Kodni ishlab chiqish", "depends_on": ["planner"]},
        {"agent": "test", "description": "Testlar yozish va tekshirish", "depends_on": ["code"]},
        {"agent": "debug", "description": "Topilgan muammolarni tuzatish", "depends_on": ["test"]},
        {"agent": "security", "description": "Xavfsizlik auditi", "depends_on": ["code"]},
        {"agent": "documentation", "description": "Hujjatlar yaratish", "depends_on": ["code"]},
        {"agent": "deployment", "description": "Joylashtirish konfiguratsiyasini yaratish", "depends_on": ["code", "security"]},
    ],
    "code_review": [
        {"agent": "code", "description": "Kodni ko'rib chiqish va yaxshilash"},
        {"agent": "security", "description": "Xavfsizlik tahlili", "depends_on": ["code"]},
        {"agent": "test", "description": "Test qamrovini tekshirish", "depends_on": ["code"]},
        {"agent": "documentation", "description": "Hujjatlarni yangilash", "depends_on": ["code"]},
    ],
    "bug_fix": [
        {"agent": "debug", "description": "Xatoni tahlil qilish va tuzatish"},
        {"agent": "test", "description": "Tuzatishni tekshirish", "depends_on": ["debug"]},
        {"agent": "monitoring", "description": "Tizim sog'ligini tekshirish", "depends_on": ["debug"]},
    ],
    "deploy": [
        {"agent": "security", "description": "Joylashtirishdan oldin xavfsizlik tekshiruvi"},
        {"agent": "deployment", "description": "Joylashtirish konfiguratsiyasini yaratish", "depends_on": ["security"]},
        {"agent": "monitoring", "description": "Monitoringni sozlash", "depends_on": ["deployment"]},
    ],
}


class MultiAgentOrchestrator:
    _instance: MultiAgentOrchestrator | None = None

    def __init__(self):
        self.gateway = get_gateway()
        self.bus = MessageBus.get_instance()
        self.agents: dict[str, BaseAgent] = {}
        self._workflows: dict[str, dict] = {}
        self._register_all_agents()

    def _register_all_agents(self):
        agent_classes = [
            PlannerAgent, CodeAgent, DebugAgent, ResearchAgent,
            TestAgent, SecurityAgent, DocumentationAgent,
            MemoryAgent, MonitoringAgent, DeploymentAgent,
        ]
        for cls in agent_classes:
            agent = cls()
            self.agents[agent.name] = agent
            self._run_async(agent.start())

    def get_agent(self, name: str) -> BaseAgent | None:
        return self.agents.get(name)

    def list_agents(self) -> list[dict]:
        return [a.get_spec() for a in self.agents.values()]

    def list_workflows(self) -> list[str]:
        return list(WORKFLOW_TEMPLATES.keys())

    def detect_task_type(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        type_map = {
            "code": ["kod yoz", "kod", "yarat", "dastur", "function", "class", "write code", "create", "implement"],
            "debug": ["debug", "bug", "xato", "tuzat", "fix", "not working", "error", "muammo", "sabab"],
            "research": ["research", "qidir", "search", "find", "what is", "how to", "tadqiq", "ma'lumot"],
            "test": ["test", "unit test", "pytest", "sinov"],
            "security": ["security", "vulnerability", "xavfsiz", "owasp", "xavfsizlik"],
            "deploy": ["deploy", "docker", "ci/cd", "kubernetes", "deployment", "joylashtir"],
            "documentation": ["document", "readme", "doc", "docs", "hujjat"],
        }
        for task_type, keywords in type_map.items():
            for kw in keywords:
                if kw in prompt_lower:
                    return task_type
        return "general"

    def get_workflow_for_task(self, task_type: str) -> list[dict]:
        workflow_map = {
            "code": "full_project",
            "debug": "bug_fix",
            "security": "code_review",
            "deploy": "deploy",
            "test": "code_review",
        }
        template = workflow_map.get(task_type, "full_project")
        return WORKFLOW_TEMPLATES.get(template, WORKFLOW_TEMPLATES["full_project"])

    async def execute_workflow(self, prompt: str, workflow_name: str = "",
                               thread_id: str = "", **kwargs) -> list[AgentResult]:
        task_type = self.detect_task_type(prompt)
        if not workflow_name:
            workflow_name = self.get_workflow_for_task(task_type)
            if isinstance(workflow_name, list):
                steps = workflow_name
            else:
                steps = WORKFLOW_TEMPLATES.get(workflow_name, WORKFLOW_TEMPLATES["full_project"])
        else:
            steps = WORKFLOW_TEMPLATES.get(workflow_name, WORKFLOW_TEMPLATES["full_project"])

        if not thread_id:
            thread_id = uuid.uuid4().hex[:12]

        results: list[AgentResult] = []
        completed: set[str] = set()
        workflow_id = uuid.uuid4().hex[:12]

        wf_record = {
            "id": workflow_id,
            "prompt": prompt[:100],
            "workflow": workflow_name or "auto",
            "thread_id": thread_id,
            "steps": len(steps),
            "status": "running",
            "started_at": time.time(),
            "results": [],
        }
        self._workflows[workflow_id] = wf_record

        for step in steps:
            agent_name = step["agent"]
            agent = self.agents.get(agent_name)
            if not agent:
                logger.warning(f"Agent {agent_name} not found, skipping")
                continue

            deps = step.get("depends_on", [])
            missing_deps = [d for d in deps if d not in completed]
            if missing_deps:
                logger.info(f"Waiting for dependencies {missing_deps} before {agent_name}")
                await asyncio.sleep(0.5)

            logger.info(f"Executing step: {agent_name} - {step['description']}")
            ctx = AgentContext(
                prompt=prompt if agent_name == "planner" else step.get("description", prompt),
                thread_id=thread_id,
                collaborators=list(set(deps)),
                metadata={"workflow_id": workflow_id, "step": step["description"], **kwargs},
            )

            try:
                result = await agent.execute(ctx)
            except Exception as e:
                result = AgentResult(task_id=ctx.task_id, status=AgentStatus.ERROR, error=str(e))

            results.append(result)
            if result.status == AgentStatus.DONE:
                completed.add(agent_name)

        wf_record["status"] = "completed"
        wf_record["completed_at"] = time.time()
        wf_record["results"] = [{"agent": r.task_id, "status": r.status.value} for r in results]
        return results

    async def execute_single(self, agent_name: str, prompt: str, **kwargs) -> AgentResult:
        agent = self.agents.get(agent_name)
        if not agent:
            return AgentResult(status=AgentStatus.ERROR, error=f"Agent '{agent_name}' not found")
        ctx = AgentContext(prompt=prompt, **kwargs)
        return await agent.execute(ctx)

    async def chat(self, messages: list[Message], **kwargs) -> Completion:
        return await self.gateway.chat(messages, **kwargs)

    async def chat_stream(self, messages: list[Message], **kwargs):
        async for chunk in self.gateway.chat_stream(messages, **kwargs):
            yield chunk

    def get_status(self) -> dict:
        return {
            "agents": self.list_agents(),
            "workflows": list(WORKFLOW_TEMPLATES.keys()),
            "active_workflows": len(self._workflows),
            "bus_messages": len(self.bus.get_history()),
            "gateway": self.gateway.get_status(),
        }

    def get_workflow_history(self) -> list[dict]:
        return list(self._workflows.values())

    def get_message_history(self, limit: int = 50) -> list[dict]:
        return self.bus.get_history(limit=limit)

    def _run_async(self, coro):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(coro, loop)
                return future.result()
            else:
                return asyncio.run(coro)
        except RuntimeError:
            return asyncio.run(coro)


_orch_instance: MultiAgentOrchestrator | None = None


def get_orchestrator() -> MultiAgentOrchestrator:
    global _orch_instance
    if _orch_instance is None:
        _orch_instance = MultiAgentOrchestrator()
    return _orch_instance
