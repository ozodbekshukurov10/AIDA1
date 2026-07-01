from __future__ import annotations
import os

from ..base import ProviderConfig
from ..plugin import ModelPlugin, PluginMetadata, ProviderCapability
from .base import OpenAICompatibleProvider


class OpenAIProviderPlugin(OpenAICompatibleProvider, ModelPlugin):
    metadata = PluginMetadata(
        name="OpenAI",
        version="1.1.0",
        description="OpenAI API (GPT-4, GPT-4o, GPT-3.5, etc.)",
        website="https://openai.com",
        capabilities=[
            ProviderCapability.CHAT, ProviderCapability.STREAMING,
            ProviderCapability.FUNCTION_CALLING, ProviderCapability.VISION,
            ProviderCapability.JSON_MODE, ProviderCapability.EMBEDDINGS,
        ],
        requires_api_key=True,
        env_prefix="OPENAI_",
        config_schema={
            "model": {"type": "string", "default": "gpt-4o"},
            "api_key": {"type": "string", "required": True},
            "base_url": {"type": "string", "default": "https://api.openai.com"},
            "timeout": {"type": "integer", "default": 120},
        },
    )

    @classmethod
    def from_env(cls) -> OpenAIProviderPlugin | None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None
        return cls(ProviderConfig(
            name="openai",
            model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com"),
            api_key=api_key,
            timeout=int(os.environ.get("OPENAI_TIMEOUT", "120")),
        ))
