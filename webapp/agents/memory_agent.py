from __future__ import annotations
import json
import logging
import time
import uuid

from .base_agent import BaseAgent, AgentContext, AgentResult, AgentStatus, AgentCapability, AgentMessage

logger = logging.getLogger("webapp.agents.memory")

MEMORY_PROMPT = """You are AIDA Memory Agent — the persistent knowledge curator.
Your job is to:
1. Extract key facts, decisions, and patterns from conversations
2. Store them in the knowledge base for future reference
3. Retrieve relevant context when needed
4. Detect and resolve conflicting information
5. Summarize conversation history

You maintain the long-term memory of the AIDA system."""


class MemoryAgent(BaseAgent):
    def __init__(self, model: str = ""):
        super().__init__("memory", model)
        self.capabilities = [AgentCapability.MEMORY]
        self._cache: dict[str, str] = {}

    async def execute(self, ctx: AgentContext) -> AgentResult:
        start = time.monotonic()
        self.status = AgentStatus.RUNNING
        self._current_task_id = ctx.task_id
        try:
            from ..llm.base import Message, MessageRole
            from ..llm.gateway import get_gateway
            from ..memory.knowledge import get_knowledge_store

            gw = get_gateway()
            store = get_knowledge_store()

            action = ctx.metadata.get("action", "store")
            if action == "retrieve":
                results = store.search(ctx.prompt, top_k=5)
                content = json.dumps([{"content": r["content"][:500], "score": r["score"]} for r in results])
            elif action == "forget":
                doc_id = ctx.metadata.get("doc_id", "")
                if doc_id:
                    store.delete(doc_id)
                    content = f"Deleted document {doc_id}"
                else:
                    content = "No doc_id provided"
            else:
                msgs = self._build_prompt(ctx, ctx.system_prompt or MEMORY_PROMPT)
                result = await gw.chat(msgs)
                content = result.content
                store.add(content, tags=ctx.metadata.get("tags", ["memory"]))

            self.status = AgentStatus.DONE
            self._record(start, True)

            await self.broadcast("memory_updated", content[:500],
                                 thread_id=ctx.thread_id,
                                 metadata={"task_id": ctx.task_id, "action": action})

            return AgentResult(
                task_id=ctx.task_id, content=content,
                status=AgentStatus.DONE, latency_ms=int((time.monotonic()-start)*1000),
            )
        except Exception as e:
            self.status = AgentStatus.ERROR
            self._record(start, False)
            return AgentResult(task_id=ctx.task_id, status=AgentStatus.ERROR, error=str(e))
