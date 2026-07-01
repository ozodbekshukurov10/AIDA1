"""Infrastructure adapter tests — tests that adapters wrap existing code correctly."""

import sys, asyncio, json
sys.path.insert(0, '.')
from aidaos.infrastructure.codebase.indexer import CodebaseIndexer
from aidaos.infrastructure.config.settings import AIDASettings
from aidaos.infrastructure.plugins import PluginLoader, ModelPluginAdapter, auto_register_plugins
from aidaos.presentation.api import APIResponse
from aidaos.infrastructure.agents import AgentRepoAdapter
from aidaos.infrastructure.tools import ToolRepoAdapter
from aidaos.infrastructure.llm import ProviderRepoAdapter
from aidaos.infrastructure.project import ProjectRepoAdapter
from aidaos.infrastructure.workflow import WorkflowRepoAdapter
from aidaos.infrastructure.persistence import (
    MemoryRepoAdapter, SessionRepoAdapter, KnowledgeRepoAdapter, MetricsRepoAdapter,
)
from aidaos import get_container

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL: {name}")


print("=== CodebaseIndexer Tests ===")
indexer = CodebaseIndexer()

r = indexer.index_file("aidaos/domain/entities.py")
check("Index returns dict", isinstance(r, dict))
check("Index has symbols", len(r.get("symbols", [])) > 0)
check("Index has classes", len(r.get("classes", [])) > 0)
check("Index has imports", len(r.get("imports", [])) > 0)

sr = indexer.search("AgentSpec")
check("Search returns results", len(sr) > 0)
check("Search has matches", sr[0].get("match_count", 0) > 0)

deps = indexer.get_dependencies("aidaos/domain/entities.py")
check("Dependencies exist", isinstance(deps, list))

r2 = indexer.index_project("aidaos")
check("Project index returns dict", isinstance(r2, dict))
check("Project index has count", r2.get("files_indexed", 0) >= 0)

stats = indexer.get_stats()
check("Stats has files_indexed", "files_indexed" in stats)

r3 = indexer.index_file("nonexistent.py")
check("Nonexistent file returns error", "error" in r3)

# Index JS-like content
import tempfile, os
with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
    f.write("function hello() {}\nclass MyClass {}\nimport { x } from 'lib';")
    js_path = f.name
r4 = indexer.index_file(js_path)
check("JS index works", r4.get("language") == "javascript")
os.unlink(js_path)


print("\n=== AIDASettings Tests ===")
settings = AIDASettings()
check("Settings has data_dir", settings.data_dir == "data")
check("Settings to_dict is dict", isinstance(settings.to_dict(), dict))
check("Settings has provider config", "ollama_enabled" in settings.to_dict())

from_django = AIDASettings.from_django()
check("Settings.from_django() works", isinstance(from_django, AIDASettings))


print("\n=== APIResponse Tests ===")
resp = APIResponse.ok({"status": "ok"})
check("OK response", resp.to_dict()["success"] is True)
check("OK status", resp.status == 200)

resp2 = APIResponse.created({"id": "123"})
check("Created response", resp2.status == 201)

resp3 = APIResponse.error("bad request", 400)
check("Error response", resp3.to_dict()["success"] is False)
check("Error status", resp3.status == 400)

resp4 = APIResponse.not_found()
check("Not found status", resp4.status == 404)

resp5 = APIResponse.server_error()
check("Server error status", resp5.status == 500)


print("\n=== Plugin System Tests ===")
loader = PluginLoader(plugin_dirs=["aidaos/infrastructure/plugins"])
plugins = loader.discover()
check("Plugin discovery", isinstance(plugins, list))

mod = loader.load("nonexistent_plugin_xyz")
check("Nonexistent plugin returns None", mod is None)


print("\n=== Container Registration Tests ===")
c = get_container()

# Register all adapters
c.register_agent_repo(AgentRepoAdapter())
check("Agent repo registered", "agent" in c._repos)

c.register_tool_repo(ToolRepoAdapter())
check("Tool repo registered", "tool" in c._repos)

c.register_provider_repo(ProviderRepoAdapter())
check("Provider repo registered", "provider" in c._repos)

c.register_memory_repo(MemoryRepoAdapter())
check("Memory repo registered", "memory" in c._repos)

c.register_session_repo(SessionRepoAdapter())
check("Session repo registered", "session" in c._repos)

c.register_metrics_repo(MetricsRepoAdapter())
check("Metrics repo registered", "metrics" in c._repos)

c.register_knowledge_repo(KnowledgeRepoAdapter())
check("Knowledge repo registered", "knowledge" in c._repos)

c.register_project_repo(ProjectRepoAdapter())
check("Project repo registered", "project" in c._repos)

c.register_workflow_repo(WorkflowRepoAdapter())
check("Workflow repo registered", "workflow" in c._repos)

check("All 9 repos registered", len(c._repos) == 9)

# Test use case resolution
chat_uc = c.chat_use_case()
check("Chat use case", chat_uc is not None)
check("Same instance cached", c.chat_use_case() is chat_uc)

agent_uc = c.agent_execute_use_case()
check("Agent execute use case", agent_uc is not None)

tool_uc = c.tool_execute_use_case()
check("Tool execute use case", tool_uc is not None)

check("Provider repo accessible", c._prov is not None)
check("Agent repo accessible", c._agent is not None)


print("\n=== Workflow Adapter Tests ===")
wf_repo = WorkflowRepoAdapter()
from aidaos.domain.entities import WorkflowTemplate
asyncio.run(wf_repo.register_template(
    WorkflowTemplate(name="test_tpl", description="Test", steps=["a", "b"])
))
tpl = asyncio.run(wf_repo.get_template("test_tpl"))
check("Template stored", tpl is not None)
check("Template name", tpl.name == "test_tpl")

templates = asyncio.run(wf_repo.list_templates())
check("Template list", len(templates) >= 1)


print("\n=== Project Adapter Tests ===")
proj_repo = ProjectRepoAdapter()
proj = asyncio.run(proj_repo.open("."))
check("Project opened", proj is not None)
check("Project name", proj.name is not None)

files = asyncio.run(proj_repo.get_files(proj.id))
check("Project has files", len(files) >= 1)

content = asyncio.run(proj_repo.read_file(proj.id, "aidaos/__init__.py"))
check("File read works", len(content) > 0)

closed = asyncio.run(proj_repo.close(proj.id))
check("Project closed", closed is True)

# Results
total = passed + failed
print(f"\n{'='*40}")
print(f"Results: {passed}/{total} passed, {failed} failed")
if failed > 0:
    sys.exit(1)
print("All infrastructure adapter tests passed!")
