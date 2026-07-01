from __future__ import annotations
import os

from ..base import ProviderConfig
from ..plugin import ModelPlugin, PluginMetadata, ProviderCapability
from .base import OpenAICompatibleProvider


class DeepSeekPlugin(OpenAICompatibleProvider, ModelPlugin):
    metadata = PluginMetadata(
        name="DeepSeek",
        version="1.0.0",
        description="DeepSeek API (DeepSeek-V3, DeepSeek-R1, DeepSeek-Coder)",
        website="https://deepseek.com",
        capabilities=[
            ProviderCapability.CHAT, ProviderCapability.STREAMING,
            ProviderCapability.FUNCTION_CALLING,
        ],
        requires_api_key=True,
        env_prefix="DEEPSEEK_",
        config_schema={
            "model": {"type": "string", "default": "deepseek-chat"},
            "api_key": {"type": "string", "required": True},
            "base_url": {"type": "string", "default": "https://api.deepseek.com"},
            "timeout": {"type": "integer", "default": 120},
        },
    )

    @classmethod
    def from_env(cls) -> DeepSeekPlugin | None:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            return None
        return cls(ProviderConfig(
            name="deepseek",
            model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            api_key=api_key,
            timeout=int(os.environ.get("DEEPSEEK_TIMEOUT", "120")),
        ))
