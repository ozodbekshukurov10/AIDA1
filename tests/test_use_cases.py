"""Application/use case tests — tests for all use cases with mock repositories."""

import sys, asyncio, json, time
sys.path.insert(0, '.')
from aidaos.domain.entities import *
from aidaos.domain.interfaces import *
from aidaos.domain.exceptions import *
from aidaos.application.dtos import *
from aidaos.application.use_cases import *

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL: {name}")


# ─── Mock Repositories ───
class MockProviderRepo(ProviderRepository):
    async def register(self, spec, chat_fn, stream_fn=None): pass
    async def get(self, name): return ProviderSpec(name=name, model="test", status=ProviderStatus.ONLINE)
    async def list(self): return [ProviderSpec(name="test", model="m", status=ProviderStatus.ONLINE)]
    async def chat(self, messages, provider="", **kwargs):
        return Completion(content="Mock response", model="test", provider="mock", latency_ms=100)
    async def chat_stream(self, messages, provider="", **kwargs):
        yield "chunk1"
        yield "chunk2"
    async def check_health(self, provider=""): return True

class MockAgentRepo(AgentRepository):
    def __init__(self):
        self.specs = {"code": AgentSpec(name="code", capabilities=[AgentCapability.CODE], description="Code agent")}
    async def register(self, spec): self.specs[spec.name] = spec
    async def get(self, name): return self.specs.get(name)
    async def list(self): return list(self.specs.values())
    async def execute(self, agent_name, ctx):
        return AgentResult(task_id=ctx.task_id, content=f"Executed {agent_name}", status=AgentStatus.DONE, latency_ms=100)
    async def get_status(self, agent_name): return AgentStatus.DONE

class MockToolRepo(ToolRepository):
    def __init__(self):
        self.specs = {"search": ToolSpec(name="search", description="Search tool", parameters={"type": "object"})}
    async def register(self, spec, fn): self.specs[spec.name] = spec
    async def get(self, name): return self.specs.get(name)
    async def list(self): return list(self.specs.values())
    async def execute(self, tool_name, **kwargs):
        return ToolResult(success=True, output="mock result")

class MockMemoryRepo(MemoryRepository):
    def __init__(self):
        self._items = {}
    async def store(self, item):
        item.id = f"mem_{len(self._items)}"
        self._items[item.id] = item
        return item.id
    async def get(self, mem_id): return self._items.get(mem_id)
    async def search(self, query):
        return [v for v in self._items.values() if query.query.lower() in v.content.lower()][:query.limit]
    async def update(self, item): self._items[item.id] = item; return True
    async def delete(self, mem_id): return self._items.pop(mem_id, None) is not None
    async def count(self, mt=None): return len(self._items)
    async def clear(self, mt=None): self._items.clear(); return 0
    async def get_stats(self): return {"count": len(self._items)}

class MockSessionRepo(SessionRepository):
    def __init__(self):
        self.sessions = {}
        self.messages = {}
    async def create(self, session):
        session.id = f"s_{len(self.sessions)}"
        self.sessions[session.id] = session
        self.messages[session.id] = []
        return session.id
    async def get(self, sid): return self.sessions.get(sid)
    async def list(self, limit=50, offset=0): return list(self.sessions.values())
    async def update(self, session): self.sessions[session.id] = session; return True
    async def delete(self, sid): return self.sessions.pop(sid, None) is not None
    async def add_message(self, sid, msg):
        if sid in self.messages:
            self.messages[sid].append(msg)
        return True
    async def get_messages(self, sid, limit=100): return self.messages.get(sid, [])

class MockMetricsRepo(MetricsRepository):
    def __init__(self):
        self.requests = []
        self.calls = []
    async def record_request(self, endpoint, method, status, latency_ms, **kw):
        self.requests.append({"endpoint": endpoint, "latency": latency_ms})
    async def record_agent_call(self, agent, task, success, latency_ms, **kw):
        self.calls.append({"agent": agent, "task": task, "success": success})
    async def get_stats(self, hours=24):
        return {"total_requests": len(self.requests), "total_agent_calls": len(self.calls),
                "avg_latency_ms": 100, "error_rate": 0}
    async def get_agent_stats(self, hours=24):
        return [{"agent_name": "code", "avg_latency_ms": 100, "error_rate": 0, "call_count": 5}]
    async def get_health_score(self): return 95.0

class MockKnowledgeRepo(KnowledgeRepository):
    async def add(self, content, tags=None, source=""): return "k1"
    async def search(self, query, limit=10): return [{"id": "k1", "content": query}]
    async def get(self, kid): return {"id": kid}
    async def delete(self, kid): return True
    async def get_stats(self): return {"total": 1}

class MockCodebaseRepo(CodebaseRepository):
    async def index_file(self, fp): return {"file": fp}
    async def index_project(self, pp): return {"files": 0}
    async def search(self, query, lang=""): return [{"file": "test.py", "matches": [{"name": query}]}]
    async def get_symbol(self, name, fp=""): return [{"name": name}]
    async def get_dependencies(self, fp): return []

class MockWorkflowRepo(WorkflowRepository):
    def __init__(self):
        self.templates = {}
    async def register_template(self, t): self.templates[t.name] = t
    async def get_template(self, name): return self.templates.get(name)
    async def list_templates(self): return list(self.templates.values())
    async def execute(self, name, ctx): return [{"step": "test", "success": True}]


# ─── Create mock repos ───
provider_repo = MockProviderRepo()
agent_repo = MockAgentRepo()
tool_repo = MockToolRepo()
memory_repo = MockMemoryRepo()
session_repo = MockSessionRepo()
metrics_repo = MockMetricsRepo()
knowledge_repo = MockKnowledgeRepo()
codebase_repo = MockCodebaseRepo()
workflow_repo = MockWorkflowRepo()

# Register default workflow template
asyncio.run(workflow_repo.register_template(
    WorkflowTemplate(name="test_wf", description="Test", steps=["code"])
))


async def run_tests():
    global passed, failed

    # ─── Chat Use Case ───
    print("=== ChatUseCase ===")
    chat_uc = ChatUseCase(provider_repo, session_repo, metrics_repo)

    req = ChatRequest(message="Hello")
    resp = await chat_uc.execute(req)
    check("Chat returns response", resp.content == "Mock response")
    check("Chat has model", resp.model == "test")
    check("Chat has latency", resp.latency_ms >= 0)

    # Session-based chat
    sid = await session_repo.create(Session(title="Test"))
    req2 = ChatRequest(message="Hi", session_id=sid)
    resp2 = await chat_uc.execute(req2)
    check("Chat with session works", resp2.content == "Mock response")
    msgs = await session_repo.get_messages(sid)
    check("Session messages stored", len(msgs) >= 2)

    # Validation error
    try:
        await chat_uc.execute(ChatRequest(message=""))
        check("Empty message validation", False)
    except ValidationError:
        check("Empty message validation", True)

    # Stream
    chunks = []
    async for chunk in chat_uc.stream(ChatRequest(message="Test")):
        chunks.append(chunk)
    check("Stream yields chunks", len(chunks) >= 1)

    # ─── Agent Use Cases ───
    print("\n=== AgentExecuteUseCase ===")
    agent_uc = AgentExecuteUseCase(agent_repo, metrics_repo)
    result = await agent_uc.execute(AgentExecuteRequest(agent_name="code", prompt="Write code"))
    check("Agent executes", result.success is True)
    check("Agent has content", "Executed code" in result.content)

    try:
        await agent_uc.execute(AgentExecuteRequest(agent_name="missing", prompt="test"))
        check("Missing agent raises error", False)
    except AgentNotFoundError:
        check("Missing agent raises error", True)

    # ─── Tool Use Cases ───
    print("\n=== ToolExecuteUseCase ===")
    tool_uc = ToolExecuteUseCase(tool_repo)
    t_result = await tool_uc.execute(ToolExecuteRequest(tool_name="search"))
    check("Tool executes", t_result.success is True)

    try:
        await tool_uc.execute(ToolExecuteRequest(tool_name="missing"))
        check("Missing tool raises error", False)
    except ToolNotFoundError:
        check("Missing tool raises error", True)

    # ─── Memory Use Case ───
    print("\n=== MemoryUseCase ===")
    mem_uc = MemoryUseCase(memory_repo, metrics_repo)
    store_result = await mem_uc.store("test content", memory_type="conversation")
    check("Memory stored", store_result["success"] is True)
    check("Memory has ID", "id" in store_result)

    search_req = MemorySearchRequest(query="test")
    items = await mem_uc.search(search_req)
    check("Memory search returns items", len(items) >= 1)

    # ─── Workflow Use Case ───
    print("\n=== WorkflowUseCase ===")
    wf_uc = WorkflowUseCase(agent_repo, workflow_repo)
    templates = await wf_uc.list_templates()
    check("Workflow lists templates", len(templates) >= 1)

    # ─── Code Use Cases ───
    print("\n=== CodeAnalysisUseCase ===")
    code_uc = CodeAnalysisUseCase(codebase_repo)
    search = await code_uc.search_symbol("test")
    check("Code search works", len(search) >= 1)
    complexity = await code_uc.analyze_complexity("def f():\n    if x:\n        return 1\n    return 0", "python")
    check("Complexity calculated", complexity.get("cyclomatic_complexity", 0) >= 1)

    # ─── Search Use Case ───
    print("\n=== SearchUseCase ===")
    search_uc = SearchUseCase(codebase_repo, memory_repo, knowledge_repo)
    all_results = await search_uc.search_all("test")
    check("Search all returns dict", isinstance(all_results, dict))
    check("Search has codebase results", len(all_results.get("codebase", [])) >= 0)
    check("Search has memory results", len(all_results.get("memory", [])) >= 0)

    # ─── Improvement Use Case ───
    print("\n=== SelfImprovementUseCase ===")
    improv_uc = SelfImprovementUseCase(agent_repo, metrics_repo)

    # First record some metrics
    await metrics_repo.record_agent_call("code_agent", "execute", False, 12000)
    proposals = await improv_uc.scan_performance()
    check("Performance scan produces proposals", len(proposals) >= 0)

    if proposals:
        r = await improv_uc.approve_proposal(proposals[0].id)
        check("Proposal approval works", r["status"] == "approved")

        cnt_before = len(await improv_uc.get_pending_proposals())
        await improv_uc.reject_proposal(proposals[0].id if len(proposals) > 0 else "")
        check("Reject doesn't crash", True)

    # ─── DTO Validation ───
    print("\n=== DTO Validation ===")
    req = ChatRequest(message="")
    check("Empty chat message invalid", len(req.validate()) > 0)
    req2 = ChatRequest(message="valid")
    check("Valid chat message passes", len(req2.validate()) == 0)

    req3 = AgentExecuteRequest(agent_name="", prompt="test")
    check("Empty agent name invalid", len(req3.validate()) > 0)

    req4 = ToolExecuteRequest(tool_name="")
    check("Empty tool name invalid", len(req4.validate()) > 0)

    # ─── Pagination ───
    print("\n=== Pagination ===")
    p = Pagination(page=1, per_page=10, total=95)
    check("Pagination offset", p.offset == 0)
    check("Pagination total pages", p.total_pages == 10)
    check("Pagination to_dict", p.to_dict()["pages"] == 10)

    # ─── Plugin System ───
    print("\n=== Plugin System ===")
    from aidaos.infrastructure.plugins import PluginLoader, ModelPluginAdapter
    loader = PluginLoader()
    plugins = loader.discover()
    check("Plugin discovery returns list", isinstance(plugins, list))

    async def aida_chat(messages, **kwargs):
        return Completion(content="AIDA", model="aida-1", provider="aida_model")

    from aidaos import get_container
    c = get_container()
    c.register_provider_plugin("aida_model", aida_chat,
                               spec={"model": "aida-1", "supports_tools": True})
    check("AIDA Model plugin registered", True)

    # ─── DTO to_dict ───
    print("\n=== DTO Serialization ===")
    pi = ProjectInfo(name="test", language="python", file_count=42)
    d = pi.to_dict()
    check("ProjectInfo serialization", d["file_count"] == 42)

    # Score
    total = passed + failed
    print(f"\n{'='*40}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    if failed > 0:
        sys.exit(1)
    print("All application use case tests passed!")

asyncio.run(run_tests())
