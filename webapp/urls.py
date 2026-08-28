from django.urls import path, re_path

# New clean API v2 endpoints
from .api.status import api_status
from .api.chat import api_chat, api_chat_stream
from .api.sessions import api_sessions_list, api_session_create, api_session_history
from .api.agents_api import (
    api_agents_status, api_agents_list, api_agent_execute,
    api_workflow_execute, api_workflows_list,
    api_agent_messages, api_workflow_history,
)
from .api.tools_api import api_tools_list, api_tools_execute, api_tools_permissions
from .api.memory_api import (
    api_memory_store, api_memory_search, api_memory_semantic_search,
    api_memory_get, api_memory_delete, api_memory_stats, api_memory_maintenance,
)
from .api.models_api import api_models_list as api_v2_models_list, api_models_switch
from .api.gateway_api import (
    api_gateway_status, api_gateway_switch, api_gateway_plugins,
    api_gateway_register, api_gateway_health,
)
from .api.knowledge_api import api_knowledge_add, api_knowledge_search, api_knowledge_list, api_knowledge_remove

# Legacy endpoints (views.py) â€” maintained for backward compatibility
from .views import (
    api_architecture_analyze, api_agent_stats, api_agent_submit, api_agent_queue,
    api_code_analyze, api_code_fix, api_code_generate, api_code_improve,
    api_code_optimize, api_code_preview, api_code_review, api_code_tests,
    api_debug_assist, api_docker_generate,
    api_feedback_analytics, api_feedback_analyze, api_feedback_submit,
    api_framework_generate, api_keys_create, api_keys_list,
    api_knowledge_suggest,
    api_kubernetes_generate, api_language_generate,
    api_manager_get, api_manager_list, api_manager_load, api_manager_pull,
    api_manager_remove, api_manager_select, api_manager_unload,
    api_models_discover, api_models_list as api_views_models_list, api_models_select,
    api_orchestrate_task, api_performance_tuning, api_platform_chat,
    api_project_close, api_project_current, api_project_git_clone,
    api_project_list, api_project_open,
    api_runtime_delete, api_runtime_files, api_runtime_read, api_runtime_run,
    api_runtime_save, api_runtime_server_output, api_runtime_server_start,
    api_runtime_server_stop,
    api_sandbox_create, api_sandbox_run, api_sandbox_file_write,
    api_sandbox_list, api_sandbox_destroy,
    api_servers_status,
    api_training_analyze, api_training_domain, api_training_save, api_training_stats,
    api_version_control,
    code_workspace, code_workspace_asset, dist_asset, login_page, spa_index,
    api_model_build, api_model_build_status,
    api_aida_beta_chat, api_aida_beta_status, api_aida_beta_remember,
)
from .model_management_views import (
    api_models_status, api_models_start, api_models_stop,
    api_models_switch as legacy_models_switch, api_models_list as legacy_models_list,
    api_models_install, api_models_pull,
)
from .model_views import (
    model_discover, manager_list, manager_get,
    manager_pull, manager_remove, manager_load, manager_unload, manager_select,
)


urlpatterns = [
    # â”€â”€ New Clean API v2 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    path("api/v2/status/", api_status, name="v2-status"),
    path("api/v2/chat/", api_chat, name="v2-chat"),
    path("api/v2/chat/stream/", api_chat_stream, name="v2-chat-stream"),
    path("api/v2/sessions/", api_sessions_list, name="v2-sessions-list"),
    path("api/v2/sessions/create/", api_session_create, name="v2-session-create"),
    path("api/v2/sessions/<str:session_id>/history/", api_session_history, name="v2-session-history"),
    path("api/v2/agents/", api_agents_status, name="v2-agents-status"),
    path("api/v2/agents/list/", api_agents_list, name="v2-agents-list"),
    path("api/v2/agents/execute/", api_agent_execute, name="v2-agent-execute"),
    path("api/v2/agents/messages/", api_agent_messages, name="v2-agent-messages"),
    path("api/v2/workflows/", api_workflows_list, name="v2-workflows-list"),
    path("api/v2/workflows/execute/", api_workflow_execute, name="v2-workflow-execute"),
    path("api/v2/workflows/history/", api_workflow_history, name="v2-workflow-history"),
    path("api/v2/tools/", api_tools_list, name="v2-tools-list"),
    path("api/v2/tools/list/", api_tools_list, name="v2-tools-list-alt"),
    path("api/v2/tools/execute/", api_tools_execute, name="v2-tools-execute"),
    path("api/v2/tools/permissions/", api_tools_permissions, name="v2-tools-permissions"),
    path("api/v2/models/", api_v2_models_list, name="v2-models-list"),
    path("api/v2/models/switch/", api_models_switch, name="v2-models-switch"),
    path("api/v2/gateway/", api_gateway_status, name="v2-gateway-status"),
    path("api/v2/gateway/switch/", api_gateway_switch, name="v2-gateway-switch"),
    path("api/v2/gateway/plugins/", api_gateway_plugins, name="v2-gateway-plugins"),
    path("api/v2/gateway/register/", api_gateway_register, name="v2-gateway-register"),
    path("api/v2/gateway/health/", api_gateway_health, name="v2-gateway-health"),
    path("api/v2/knowledge/add/", api_knowledge_add, name="v2-knowledge-add"),
    path("api/v2/knowledge/search/", api_knowledge_search, name="v2-knowledge-search"),
    path("api/v2/knowledge/", api_knowledge_list, name="v2-knowledge-list"),
    path("api/v2/knowledge/remove/", api_knowledge_remove, name="v2-knowledge-remove"),

    # â”€â”€ Static Assets â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    re_path(r"^assets/(?P<asset_path>.+)$", dist_asset, name="dist-asset"),
    re_path(r"^(?P<asset_path>.+\.(mp4|webm|png|jpg|jpeg|svg|ico|json))$", dist_asset, name="root-dist-asset"),
    path("code/", code_workspace, name="code-workspace"),
    path("code_workspace/<path:file_path>", code_workspace_asset, name="code-workspace-asset"),
    path("login/", login_page, name="login-page-alt"),
    path("app/", spa_index, name="spa-index"),
    path("", login_page, name="login-page"),

    # â”€â”€ Legacy API (backward compatible) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Keys
    path("api/keys/", api_keys_list, name="api-keys-list"),
    path("api/keys/create/", api_keys_create, name="api-keys-create"),

    # Status & Servers
    path("api/status/", api_status, name="api-status"),
    path("api/servers/status/", api_servers_status, name="api-servers-status"),

    # Chat
    path("api/chat/", api_chat, name="api-chat"),
    path("api/chat/stream/", api_chat_stream, name="api-chat-stream"),
    path("api/platform/chat/", api_platform_chat, name="api-platform-chat"),

    # Sessions
    path("api/sessions/", api_sessions_list, name="api-sessions-list"),
    path("api/sessions/create/", api_session_create, name="api-session-create"),
    path("api/sessions/<str:session_id>/history/", api_session_history, name="api-session-history"),

    # Code
    path("api/code/generate/", api_code_generate, name="api-code-generate"),
    path("api/code/analyze/", api_code_analyze, name="api-code-analyze"),
    path("api/code/preview/", api_code_preview, name="api-code-preview"),
    path("api/code/fix/", api_code_fix, name="api-code-fix"),
    path("api/code/optimize/", api_code_optimize, name="api-code-optimize"),
    path("api/code/tests/", api_code_tests, name="api-code-tests"),
    path("api/code/improve/", api_code_improve, name="api-code-improve"),
    path("api/code/review/", api_code_review, name="api-code-review"),

    # Debug & Architecture
    path("api/debug/assist/", api_debug_assist, name="api-debug-assist"),
    path("api/architecture/analyze/", api_architecture_analyze, name="api-architecture-analyze"),
    path("api/language/generate/", api_language_generate, name="api-language-generate"),
    path("api/framework/generate/", api_framework_generate, name="api-framework-generate"),
    path("api/version-control/", api_version_control, name="api-version-control"),
    path("api/docker/generate/", api_docker_generate, name="api-docker-generate"),
    path("api/kubernetes/generate/", api_kubernetes_generate, name="api-kubernetes-generate"),
    path("api/performance/tuning/", api_performance_tuning, name="api-performance-tuning"),

    # Feedback & Training
    path("api/feedback/submit/", api_feedback_submit, name="api-feedback-submit"),
    path("api/feedback/analytics/", api_feedback_analytics, name="api-feedback-analytics"),
    path("api/feedback/analyze/", api_feedback_analyze, name="api-feedback-analyze"),
    path("api/training/save/", api_training_save, name="api-training-save"),
    path("api/training/domain/", api_training_domain, name="api-training-domain"),
    path("api/training/stats/", api_training_stats, name="api-training-stats"),
    path("api/training/analyze/", api_training_analyze, name="api-training-analyze"),

    # Knowledge (legacy â€” maps to new)
    path("api/knowledge/suggest/", api_knowledge_suggest, name="api-knowledge-suggest"),
    path("api/knowledge/add/", api_knowledge_add, name="api-knowledge-add"),
    path("api/knowledge/search/", api_knowledge_search, name="api-knowledge-search"),
    path("api/knowledge/list/", api_knowledge_list, name="api-knowledge-list"),
    path("api/knowledge/remove/", api_knowledge_remove, name="api-knowledge-remove"),

    # Models (legacy)
    path("api/models/discover/", api_models_discover, name="api-models-discover"),
    path("api/models/list/", api_views_models_list, name="api-models-list"),
    path("api/models/select/", api_models_select, name="api-models-select"),
    path("api/models/status/", api_models_status, name="api-models-status"),
    path("api/models/start/<str:provider_name>/", api_models_start, name="api-models-start"),
    path("api/models/stop/<str:provider_name>/", api_models_stop, name="api-models-stop"),
    path("api/models/switch/<str:provider_name>/", legacy_models_switch, name="api-models-switch"),
    path("api/models/install/<str:provider_name>/", api_models_install, name="api-models-install"),
    path("api/models/pull/", api_models_pull, name="api-models-pull"),

    # Model Manager (legacy)
    path("api/manager/list/", api_manager_list, name="api-manager-list"),
    path("api/manager/get/<str:model_id>/", api_manager_get, name="api-manager-get"),
    path("api/manager/pull/", api_manager_pull, name="api-manager-pull"),
    path("api/manager/remove/", api_manager_remove, name="api-manager-remove"),
    path("api/manager/load/", api_manager_load, name="api-manager-load"),
    path("api/manager/unload/", api_manager_unload, name="api-manager-unload"),
    path("api/manager/select/", api_manager_select, name="api-manager-select"),

    # Runtime
    path("api/runtime/save/", api_runtime_save, name="api-runtime-save"),
    path("api/runtime/read/", api_runtime_read, name="api-runtime-read"),
    path("api/runtime/delete/", api_runtime_delete, name="api-runtime-delete"),
    path("api/runtime/files/", api_runtime_files, name="api-runtime-files"),
    path("api/runtime/run/", api_runtime_run, name="api-runtime-run"),
    path("api/runtime/server/start/", api_runtime_server_start, name="api-runtime-server-start"),
    path("api/runtime/server/stop/", api_runtime_server_stop, name="api-runtime-server-stop"),
    path("api/runtime/server/output/", api_runtime_server_output, name="api-runtime-server-output"),

    # Projects
    path("api/project/open/", api_project_open, name="api-project-open"),
    path("api/project/close/", api_project_close, name="api-project-close"),
    path("api/project/current/", api_project_current, name="api-project-current"),
    path("api/project/list/", api_project_list, name="api-project-list"),
    path("api/project/git-clone/", api_project_git_clone, name="api-project-git-clone"),

    # Agents (legacy)
    path("api/agent/stats/", api_agent_stats, name="api-agent-stats"),
    path("api/agent/submit/", api_agent_submit, name="api-agent-submit"),
    path("api/agent/queue/", api_agent_queue, name="api-agent-queue"),
    path("api/agents/status/", api_agents_status, name="api-agents-status"),
    path("api/orchestrate/task/", api_orchestrate_task, name="api-orchestrate-task"),

    # Tools (legacy â€” maps to new)
    path("api/tools/list/", api_tools_list, name="api-tools-list"),
    path("api/tools/execute/", api_tools_execute, name="api-tools-execute"),

    # Sandbox
    path("api/sandbox/create/", api_sandbox_create, name="api-sandbox-create"),
    path("api/sandbox/run/", api_sandbox_run, name="api-sandbox-run"),
    path("api/sandbox/file/write/", api_sandbox_file_write, name="api-sandbox-file-write"),
    path("api/sandbox/list/", api_sandbox_list, name="api-sandbox-list"),
    path("api/sandbox/destroy/", api_sandbox_destroy, name="api-sandbox-destroy"),

    # Memory API
    path("api/v2/memory/store/", api_memory_store, name="v2-memory-store"),
    path("api/v2/memory/search/", api_memory_search, name="v2-memory-search"),
    path("api/v2/memory/semantic-search/", api_memory_semantic_search, name="v2-memory-semantic"),
    path("api/v2/memory/get/<str:item_id>/", api_memory_get, name="v2-memory-get"),
    path("api/v2/memory/delete/", api_memory_delete, name="v2-memory-delete"),
    path("api/v2/memory/stats/", api_memory_stats, name="v2-memory-stats"),
    path("api/v2/memory/maintenance/", api_memory_maintenance, name="v2-memory-maintenance"),

    # Model Build
    path("api/model/build/", api_model_build, name="api-model-build"),
    path("api/model/status/", api_model_build_status, name="api-model-build-status"),

    # AIDA Beta Bridge
    path("api/aida-beta/chat/", api_aida_beta_chat, name="api-aida-beta-chat"),
    path("api/aida-beta/status/", api_aida_beta_status, name="api-aida-beta-status"),
    path("api/aida-beta/remember/", api_aida_beta_remember, name="api-aida-beta-remember"),

    # Model discovery and consolidated management (model_views.py)
    path("api/models/discover/", model_discover, name="model-discover"),
    path("api/models/manage/list/", manager_list, name="manager-list"),
    path("api/models/manage/get/<str:model_id>/", manager_get, name="manager-get"),
    path("api/models/manage/pull/", manager_pull, name="manager-pull"),
    path("api/models/manage/remove/", manager_remove, name="manager-remove"),
    path("api/models/manage/load/", manager_load, name="manager-load"),
    path("api/models/manage/unload/", manager_unload, name="manager-unload"),
    path("api/models/manage/select/", manager_select, name="manager-select"),
]
