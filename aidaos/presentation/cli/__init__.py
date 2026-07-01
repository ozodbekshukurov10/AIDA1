"""CLI commands — use the container's use cases from the command line."""

from __future__ import annotations
import argparse
import asyncio
import json
import logging
import sys
from typing import Any

logger = logging.getLogger("aidaos.presentation.cli")


class AIDACLI:
    def __init__(self, container):
        self._container = container

    def run(self, argv: list[str] | None = None):
        parser = argparse.ArgumentParser(description="AIDA OS CLI")
        parser.add_argument("--json", action="store_true", help="Output as JSON")
        sub = parser.add_subparsers(dest="command")

        # Status
        p_status = sub.add_parser("status", help="System status")

        # Chat
        p_chat = sub.add_parser("chat", help="Send a chat message")
        p_chat.add_argument("message", nargs="+")
        p_chat.add_argument("--session", "-s", default="")

        # Agent
        p_agent = sub.add_parser("agent", help="Execute an agent")
        p_agent.add_argument("name")
        p_agent.add_argument("prompt", nargs="+")
        p_agent.add_argument("--thread", "-t", default="")

        # Tools
        p_tools = sub.add_parser("tools", help="List available tools")

        # Memory
        p_mem = sub.add_parser("memory", help="Memory operations")
        p_mem_sub = p_mem.add_subparsers(dest="mem_cmd")
        p_mem_store = p_mem_sub.add_parser("store")
        p_mem_store.add_argument("content", nargs="+")
        p_mem_search = p_mem_sub.add_parser("search")
        p_mem_search.add_argument("query", nargs="+")

        # Proposals
        p_prop = sub.add_parser("proposals", help="List improvement proposals")
        p_prop.add_argument("--approve", "-a", help="Approve proposal by ID")
        p_prop.add_argument("--reject", "-r", help="Reject proposal by ID")

        args = parser.parse_args(argv)
        asyncio.run(self._handle(args, argv))

    async def _handle(self, args, argv):
        result = None
        if args.command == "status":
            result = await self._cmd_status()
        elif args.command == "chat":
            result = await self._cmd_chat(args)
        elif args.command == "agent":
            result = await self._cmd_agent(args)
        elif args.command == "tools":
            result = await self._cmd_tools()
        elif args.command == "memory":
            result = await self._cmd_memory(args)
        elif args.command == "proposals":
            result = await self._cmd_proposals(args)
        else:
            print("Unknown command. Use: status, chat, agent, tools, memory, proposals")
            return

        if args and hasattr(args, 'json') and args.json:
            print(json.dumps(result, indent=2, default=str))
        elif isinstance(result, dict):
            print(json.dumps(result, indent=2, default=str)[:2000])

    async def _cmd_status(self):
        uc = self._container.improvement_use_case()
        report = await uc.get_report()
        return {
            "status": "running",
            "health_score": report.get("health_score", 0),
            "pending_proposals": report.get("pending_proposals", 0),
        }

    async def _cmd_chat(self, args):
        uc = self._container.chat_use_case()
        from ...application.dtos import ChatRequest
        req = ChatRequest(message=" ".join(args.message), session_id=args.session)
        resp = await uc.execute(req)
        return {"response": resp.content, "model": resp.model}

    async def _cmd_agent(self, args):
        uc = self._container.agent_execute_use_case()
        from ...application.dtos import AgentExecuteRequest
        req = AgentExecuteRequest(agent_name=args.name, prompt=" ".join(args.prompt), thread_id=args.thread)
        result = await uc.execute(req)
        return {"content": result.content[:500], "success": result.success}

    async def _cmd_tools(self):
        uc = self._container.tool_manage_use_case()
        tools = await uc.list_tools()
        return {"tools": [t["name"] for t in tools]}

    async def _cmd_memory(self, args):
        uc = self._container.memory_use_case()
        if args.mem_cmd == "store":
            result = await uc.store(" ".join(args.content))
            return result
        elif args.mem_cmd == "search":
            from ...application.dtos import MemorySearchRequest
            req = MemorySearchRequest(query=" ".join(args.query))
            items = await uc.search(req)
            return {"results": items[:5]}
        return {"error": "Unknown memory command"}

    async def _cmd_proposals(self, args):
        uc = self._container.improvement_use_case()
        if args.approve:
            result = await uc.approve_proposal(args.approve)
            return result
        if args.reject:
            result = await uc.reject_proposal(args.reject)
            return result
        proposals = await uc.get_pending_proposals()
        return {"proposals": [p.to_dict() for p in proposals]}
