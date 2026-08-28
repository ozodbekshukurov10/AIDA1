"""Unified settings — single source of truth for all configuration.

Loads from:
  1. Default values (lowest priority)
  2. .env file (if present)
  3. Environment variables
  4. Django settings (if available, highest priority)
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from aidaos.infrastructure.logging import get_logger

logger = get_logger("config")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _load_dotenv(path: str | Path | None = None) -> None:
    """Load .env file if python-dotenv is available."""
    try:
        from dotenv import load_dotenv
        env_path = Path(path or _PROJECT_ROOT / ".env")
        if env_path.exists():
            load_dotenv(env_path, override=False)
            logger.info(f"Loaded environment from {env_path}")
    except ImportError:
        logger.debug("python-dotenv not installed; skipping .env loading")


@dataclass
class DatabaseSettings:
    dsn: str = ""
    pool_size: int = 5
    pool_timeout: int = 30


@dataclass
class ProviderEndpoint:
    url: str = ""
    model: str = ""
    api_key: str = ""
    timeout: int = 120
    enabled: bool = True


@dataclass
class AIDASettings:
    """All AIDA configuration in one place. Reads from Django settings + env."""

    # Paths
    project_root: str = str(_PROJECT_ROOT)
    data_dir: str = "data"
    logs_dir: str = "logs"
    projects_dir: str = "projects"
    dist_dir: str = "dist"
    templates_dir: str = "templates"

    # LLM Providers
    default_provider: str = ""
    default_model: str = ""

    ollama: ProviderEndpoint = field(default_factory=lambda: ProviderEndpoint(
        url="http://localhost:11434", model="", timeout=120, enabled=True,
    ))
    openai: ProviderEndpoint = field(default_factory=lambda: ProviderEndpoint(
        url="https://api.openai.com/v1", model="gpt-4o", timeout=60,
    ))
    anthropic: ProviderEndpoint = field(default_factory=lambda: ProviderEndpoint(
        model="claude-3-opus-20240229",
    ))
    gemini: ProviderEndpoint = field(default_factory=lambda: ProviderEndpoint(
        model="gemini-2.0-flash",
    ))
    deepseek: ProviderEndpoint = field(default_factory=lambda: ProviderEndpoint(
        model="deepseek-chat",
    ))
    lmstudio: ProviderEndpoint = field(default_factory=lambda: ProviderEndpoint(
        url="http://localhost:1234", enabled=False,
    ))
    aida_model: ProviderEndpoint = field(default_factory=lambda: ProviderEndpoint(enabled=False))

    database: DatabaseSettings = field(default_factory=DatabaseSettings)

    # Security
    api_key: str = ""
    rate_limit: int = 60
    max_request_size: int = 100_000
    django_secret_key: str = ""
    allowed_hosts: str = "127.0.0.1,localhost"
    cors_origins: str = "http://127.0.0.1:8080"

    # System
    debug: bool = False
    log_level: str = "INFO"
    log_json: bool = False
    max_files: int = 5000
    max_file_size: int = 500_000

    def __post_init__(self):
        self._load_dotenv()

    def _load_dotenv(self):
        _load_dotenv()
        self._load_from_env()

    def _load_from_env(self):
        ollama = self.ollama
        ollama.url = os.getenv("OLLAMA_URL", ollama.url)
        ollama.model = os.getenv("OLLAMA_MODEL", ollama.model)
        ollama.timeout = int(os.getenv("OLLAMA_TIMEOUT", str(ollama.timeout)))
        ollama.enabled = os.getenv("OLLAMA_ENABLED", str(ollama.enabled)).lower() == "true"

        openai = self.openai
        openai.api_key = os.getenv("OPENAI_API_KEY", openai.api_key)
        openai.model = os.getenv("OPENAI_MODEL", openai.model)
        openai.url = os.getenv("OPENAI_BASE_URL", openai.url)
        openai.timeout = int(os.getenv("OPENAI_TIMEOUT", str(openai.timeout)))

        anthropic = self.anthropic
        anthropic.api_key = os.getenv("ANTHROPIC_API_KEY", anthropic.api_key)
        anthropic.model = os.getenv("ANTHROPIC_MODEL", anthropic.model)

        gemini = self.gemini
        gemini.api_key = os.getenv("GEMINI_API_KEY", gemini.api_key)
        gemini.model = os.getenv("GEMINI_MODEL", gemini.model)

        deepseek = self.deepseek
        deepseek.api_key = os.getenv("DEEPSEEK_API_KEY", deepseek.api_key)
        deepseek.model = os.getenv("DEEPSEEK_MODEL", deepseek.model)

        lmstudio = self.lmstudio
        lmstudio.url = os.getenv("LMSTUDIO_URL", lmstudio.url)
        lmstudio.enabled = os.getenv("LMSTUDIO_ENABLED", str(lmstudio.enabled)).lower() == "true"

        aida_model = self.aida_model
        aida_model.url = os.getenv("AIDA_MODEL_URL", aida_model.url)
        aida_model.api_key = os.getenv("AIDA_MODEL_API_KEY", aida_model.api_key)
        aida_model.enabled = os.getenv("AIDA_MODEL_ENABLED", str(aida_model.enabled)).lower() == "true"

        self.api_key = os.getenv("AIDA_API_KEY", self.api_key)
        self.debug = os.getenv("DJANGO_DEBUG", str(self.debug)).lower() == "true"
        self.default_provider = os.getenv("AIDA_PROVIDER", self.default_provider)
        self.default_model = os.getenv("AIDA_DEFAULT_MODEL", self.default_model)

        self.django_secret_key = os.getenv("DJANGO_SECRET_KEY", self.django_secret_key)
        self.allowed_hosts = os.getenv("DJANGO_ALLOWED_HOSTS", self.allowed_hosts)
        self.cors_origins = os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", self.cors_origins)
        self.log_level = os.getenv("AIDA_LOG_LEVEL", self.log_level).upper()

    @classmethod
    def load(cls) -> AIDASettings:
        return cls()

    @classmethod
    def from_django(cls) -> AIDASettings:
        try:
            from django.conf import settings as django_settings
            from django.core.exceptions import ImproperlyConfigured
            try:
                debug = django_settings.DEBUG
            except ImproperlyConfigured:
                return cls()
            inst = cls()
            inst.debug = debug
            inst.data_dir = str(getattr(django_settings, "DATA_DIR", _PROJECT_ROOT / inst.data_dir))
            inst.logs_dir = str(getattr(django_settings, "LOGS_DIR", _PROJECT_ROOT / inst.logs_dir))
            inst.allowed_hosts = ",".join(getattr(django_settings, "ALLOWED_HOSTS", ["127.0.0.1"]))
            return inst
        except ImportError:
            return cls()

    def to_dict(self) -> dict[str, Any]:
        return {
            "data_dir": self.data_dir,
            "default_provider": self.default_provider,
            "default_model": self.default_model,
            "debug": self.debug,
            "log_level": self.log_level,
            "ollama_enabled": self.ollama.enabled,
            "openai_configured": bool(self.openai.api_key),
            "anthropic_configured": bool(self.anthropic.api_key),
            "gemini_configured": bool(self.gemini.api_key),
            "deepseek_configured": bool(self.deepseek.api_key),
            "lmstudio_enabled": self.lmstudio.enabled,
            "aida_model_ready": self.aida_model.enabled and bool(self.aida_model.url),
        }

    def get_provider_config(self, name: str) -> ProviderEndpoint | None:
        return getattr(self, name, None)


settings: AIDASettings | None = None


def get_settings() -> AIDASettings:
    global settings
    if settings is None:
        settings = AIDASettings.load()
    return settings
