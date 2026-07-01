"""Domain exceptions — typed error hierarchy for the entire system."""

from __future__ import annotations


class AIDAError(Exception):
    """Base exception for all AIDA OS errors."""
    code: str = "AIDA_ERROR"
    status_code: int = 500

    def __init__(self, message: str = "", details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "details": self.details}


class AgentError(AIDAError):
    code = "AGENT_ERROR"
    status_code = 500


class AgentNotFoundError(AgentError):
    code = "AGENT_NOT_FOUND"
    status_code = 404


class AgentExecutionError(AgentError):
    code = "AGENT_EXECUTION_FAILED"


class ToolError(AIDAError):
    code = "TOOL_ERROR"
    status_code = 500


class ToolNotFoundError(ToolError):
    code = "TOOL_NOT_FOUND"
    status_code = 404


class ToolPermissionError(ToolError):
    code = "TOOL_PERMISSION_DENIED"
    status_code = 403


class ToolTimeoutError(ToolError):
    code = "TOOL_TIMEOUT"


class ProviderError(AIDAError):
    code = "PROVIDER_ERROR"
    status_code = 502


class ProviderNotFoundError(ProviderError):
    code = "PROVIDER_NOT_FOUND"
    status_code = 404


class ProviderOfflineError(ProviderError):
    code = "PROVIDER_OFFLINE"
    status_code = 503


class ProviderFallbackError(ProviderError):
    code = "ALL_PROVIDERS_FAILED"
    status_code = 502


class MemoryError(AIDAError):
    code = "MEMORY_ERROR"
    status_code = 500


class MemoryNotFoundError(MemoryError):
    code = "MEMORY_NOT_FOUND"
    status_code = 404


class MemoryStorageError(MemoryError):
    code = "MEMORY_STORAGE_FAILED"


class WorkflowError(AIDAError):
    code = "WORKFLOW_ERROR"
    status_code = 500


class WorkflowStepError(WorkflowError):
    code = "WORKFLOW_STEP_FAILED"


class SessionError(AIDAError):
    code = "SESSION_ERROR"
    status_code = 500


class SessionNotFoundError(SessionError):
    code = "SESSION_NOT_FOUND"
    status_code = 404


class ValidationError(AIDAError):
    code = "VALIDATION_ERROR"
    status_code = 400


class ConfigurationError(AIDAError):
    code = "CONFIG_ERROR"
    status_code = 500


class PluginError(AIDAError):
    code = "PLUGIN_ERROR"
    status_code = 500


class PluginNotFoundError(PluginError):
    code = "PLUGIN_NOT_FOUND"
    status_code = 404


class ProposalError(AIDAError):
    code = "PROPOSAL_ERROR"
    status_code = 400


class ProposalNotFoundError(ProposalError):
    code = "PROPOSAL_NOT_FOUND"
    status_code = 404


class CodeError(AIDAError):
    code = "CODE_ERROR"
    status_code = 400


class DatabaseError(AIDAError):
    code = "DATABASE_ERROR"
    status_code = 500
