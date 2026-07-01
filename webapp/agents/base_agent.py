from __future__ import annotations
import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("webapp.agents")


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    DONE = "done"
    ERROR = "error"
    BLOCKED = "blocked"


class AgentCapability(str, Enum):
    PLAN = "plan"
    CODE = "code"
    DEBUG = "debug"
    RESEARCH = "research"
    TEST = "test"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    MEMORY = "memory"
    MONITORING = "monitoring"
    DEPLOYMENT = "deployment"


@dataclass
class AgentMessage:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    sender: str = ""
    recipient: str = ""  # "*" for broadcast
    subject: str = ""
    body: str = ""
    msg_type: str = "task"  # task, result, query, broadcast, error
    thread_id: str = ""
    metadata: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "subject": self.subject,
            "body": self.body,
            "msg_type": self.msg_type,
            "thread_id": self.thread_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentContext:
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    prompt: str = ""
    system_prompt: str = ""
    messages: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    tools: list[dict] = field(default_factory=list)
    max_iterations: int = 10
    thread_id: str = ""
    collaborators: list[str] = field(default_factory=list)


@dataclass
class AgentResult:
    task_id: str = ""
    content: str = ""
    status: AgentStatus = AgentStatus.DONE
    error: str | None = None
    iterations: int = 0
    latency_ms: int = 0
    usage: dict | None = None
    metadata: dict = field(default_factory=dict)
    messages: list[AgentMessage] = field(default_factory=list)


class MessageBus:
    _instance: MessageBus | None = None

    def __init__(self):
        self._queues: dict[str, asyncio.Queue] = {}
        self._history: list[AgentMessage] = []
        self._subscribers: dict[str, list[str]] = {}
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> MessageBus:
        if cls._instance is None:
            cls._instance = MessageBus()
        return cls._instance

    async def register_agent(self, agent_name: str):
        async with self._lock:
            if agent_name not in self._queues:
                self._queues[agent_name] = asyncio.Queue()

    async def subscribe(self, agent_name: str, subject: str = "*"):
        async with self._lock:
            if subject not in self._subscribers:
                self._subscribers[subject] = []
            self._subscribers[subject].append(agent_name)

    async def send(self, msg: AgentMessage):
        async with self._lock:
            self._history.append(msg)
            if msg.recipient == "*":
                for name, queue in self._queues.items():
                    if name != msg.sender:
                        await queue.put(msg)
            elif msg.recipient in self._queues:
                await self._queues[msg.recipient].put(msg)
            for subject, subscribers in self._subscribers.items():
                if subject == msg.subject or subject == "*":
                    for sub in subscribers:
                        if sub != msg.sender and sub in self._queues:
                            await self._queues[sub].put(msg)

    async def receive(self, agent_name: str, timeout: float = 5.0) -> AgentMessage | None:
        if agent_name not in self._queues:
            return None
        try:
            msg = await asyncio.wait_for(self._queues[agent_name].get(), timeout=timeout)
            return msg
        except asyncio.TimeoutError:
            return None

    async def broadcast(self, sender: str, subject: str, body: str, **kwargs):
        msg = AgentMessage(
            sender=sender, recipient="*", subject=subject,
            body=body, msg_type="broadcast", **kwargs,
        )
        await self.send(msg)

    def get_history(self, limit: int = 50) -> list[dict]:
        return [m.to_dict() for m in self._history[-limit:]]

    def get_thread(self, thread_id: str) -> list[dict]:
        return [m.to_dict() for m in self._history if m.thread_id == thread_id]


class BaseAgent(ABC):
    def __init__(self, name: str, model: str = ""):
        self.name = name
        self.model = model
        self.status = AgentStatus.IDLE
        self.metrics = {"calls": 0, "errors": 0, "total_latency_ms": 0, "tokens_used": 0}
        self.bus = MessageBus.get_instance()
        self.capabilities: list[AgentCapability] = []
        self._current_task_id: str = ""

    @abstractmethod
    async def execute(self, ctx: AgentContext) -> AgentResult:
        ...

    async def start(self):
        await self.bus.register_agent(self.name)
        self.status = AgentStatus.IDLE

    async def send_message(self, recipient: str, subject: str, body: str,
                           msg_type: str = "task", thread_id: str = "", **kwargs) -> str:
        msg = AgentMessage(
            sender=self.name, recipient=recipient, subject=subject,
            body=body, msg_type=msg_type, thread_id=thread_id, **kwargs,
        )
        await self.bus.send(msg)
        return msg.id

    async def broadcast(self, subject: str, body: str, **kwargs):
        await self.bus.broadcast(self.name, subject, body, **kwargs)

    async def receive(self, timeout: float = 5.0) -> AgentMessage | None:
        return await self.bus.receive(self.name, timeout=timeout)

    async def listen_loop(self, handler, timeout: float = 1.0):
        while self.status == AgentStatus.RUNNING:
            msg = await self.receive(timeout=timeout)
            if msg:
                await handler(msg)

    def get_spec(self) -> dict:
        return {
            "name": self.name,
            "model": self.model,
            "status": self.status.value,
            "capabilities": [c.value for c in self.capabilities],
            "metrics": self.metrics,
        }

    def _build_prompt(self, ctx: AgentContext, system_prompt: str) -> list:
        from ..llm.base import Message, MessageRole
        msgs = []
        if system_prompt:
            msgs.append(Message(role=MessageRole.SYSTEM, content=system_prompt))
        if ctx.prompt:
            msgs.append(Message(role=MessageRole.USER, content=ctx.prompt))
        return msgs

    def _run_async(self, coro):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import threading
                result = []
                exc = []
                def _run():
                    try:
                        result.append(asyncio.run(coro))
                    except Exception as e:
                        exc.append(e)
                t = threading.Thread(target=_run)
                t.start()
                t.join()
                if exc:
                    raise exc[0]
                return result[0] if result else None
            else:
                return asyncio.run(coro)
        except RuntimeError:
            return asyncio.run(coro)

    def _record(self, start: float, success: bool = True, tokens: int = 0):
        elapsed = int((time.monotonic() - start) * 1000)
        self.metrics["calls"] += 1
        if not success:
            self.metrics["errors"] += 1
        self.metrics["total_latency_ms"] += elapsed
        self.metrics["tokens_used"] += tokens
