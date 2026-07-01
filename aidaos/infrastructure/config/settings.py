"""Unified settings — single source of truth for all configuration."""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AIDASettings:
    """All AIDA configuration in one place. Reads from Django settings + env."""

    # Paths
    data_dir: str = "data"
    logs_dir: str = "logs"
    projects_dir: str = "projects"
    dist_dir: str = "dist"
    templates_dir: str = "templates"

    # LLM Providers
    default_provider: str = ""
    default_model: str = ""

    # Ollama
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = ""
    ollama_timeout: int = 120
    ollama_enabled: bool = True

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_timeout: int = 60

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-opus-20240229"

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-pro"

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"

    # LM Studio
    lmstudio_url: str = "http://localhost:1234"
    lmstudio_model: str = ""
    lmstudio_enabled: bool = False

    # AIDA Model (future)
    aida_model_url: str = ""
    aida_model_api_key: str = ""
    aida_model_enabled: bool = False

    # Security
    api_key: str = ""
    rate_limit: int = 60
    max_request_size: int = 100000

    # System
    debug: bool = False
    log_level: str = "INFO"
    max_files: int = 5000
    max_file_size: int = 500000

    def __post_init__(self):
        self._load_from_env()

    def _load_from_env(self):
        self.ollama_url = os.getenv("OLLAMA_URL", self.ollama_url)
        self.ollama_model = os.getenv("OLLAMA_MODEL", self.ollama_model)
        self.ollama_timeout = int(os.getenv("OLLAMA_TIMEOUT", str(self.ollama_timeout)))
        self.ollama_enabled = os.getenv("OLLAMA_ENABLED", str(self.ollama_enabled)).lower() == "true"

        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.openai_model = os.getenv("OPENAI_MODEL", self.openai_model)
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", self.openai_base_url)

        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", self.anthropic_api_key)
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", self.anthropic_model)

        self.gemini_api_key = os.getenv("GEMINI_API_KEY", self.gemini_api_key)
        self.gemini_model = os.getenv("GEMINI_MODEL", self.gemini_model)

        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", self.deepseek_api_key)
        self.deepseek_model = os.getenv("DEEPSEEK_MODEL", self.deepseek_model)

        self.lmstudio_url = os.getenv("LMSTUDIO_URL", self.lmstudio_url)
        self.lmstudio_enabled = os.getenv("LMSTUDIO_ENABLED", str(self.lmstudio_enabled)).lower() == "true"

        self.aida_model_url = os.getenv("AIDA_MODEL_URL", self.aida_model_url)
        self.aida_model_api_key = os.getenv("AIDA_MODEL_API_KEY", self.aida_model_api_key)
        self.aida_model_enabled = os.getenv("AIDA_MODEL_ENABLED", str(self.aida_model_enabled)).lower() == "true"

        self.api_key = os.getenv("AIDA_API_KEY", self.api_key)
        self.debug = os.getenv("DJANGO_DEBUG", str(self.debug)).lower() == "true"
        self.default_provider = os.getenv("AIDA_PROVIDER", "")
        self.default_model = os.getenv("AIDA_DEFAULT_MODEL", "")

    @classmethod
    def from_django(cls) -> AIDASettings:
        try:
            from django.conf import settings
            s = cls()
            if hasattr(settings, "DATA_DIR"):
                s.data_dir = settings.DATA_DIR
            if hasattr(settings, "LOGS_DIR"):
                s.logs_dir = settings.LOGS_DIR
            if hasattr(settings, "DEBUG"):
                s.debug = settings.DEBUG
            return s
        except Exception:
            return cls()

    def to_dict(self) -> dict:
        return {
            "data_dir": self.data_dir,
            "default_provider": self.default_provider,
            "default_model": self.default_model,
            "debug": self.debug,
            "log_level": self.log_level,
            "ollama_enabled": self.ollama_enabled,
            "openai_configured": bool(self.openai_api_key),
            "anthropic_configured": bool(self.anthropic_api_key),
            "gemini_configured": bool(self.gemini_api_key),
            "deepseek_configured": bool(self.deepseek_api_key),
            "lmstudio_enabled": self.lmstudio_enabled,
            "aida_model_ready": self.aida_model_enabled and bool(self.aida_model_url),
        }
