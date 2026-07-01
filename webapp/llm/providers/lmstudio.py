from __future__ import annotations
import os

from ..base import ProviderConfig
from ..plugin import ModelPlugin, PluginMetadata, ProviderCapability
from .base import OpenAICompatibleProvider


class LMStudioPlugin(OpenAICompatibleProvider, ModelPlugin):
    metadata = PluginMetadata(
        name="LM Studio",
        version="1.1.0",
        description="LM Studio local inference server",
        website="https://lmstudio.ai",
        capabilities=[
            ProviderCapability.CHAT, ProviderCapability.STREAMING,
        ],
        env_prefix="LMSTUDIO_",
        config_schema={
            "model": {"type": "string", "default": ""},
            "base_url": {"type": "string", "default": "http://127.0.0.1:1234"},
            "timeout": {"type": "integer", "default": 120},
        },
    )

    @classmethod
    def from_env(cls) -> LMStudioPlugin | None:
        if os.environ.get("LMSTUDIO_ENABLED", "true").lower() == "false":
            return None
        return cls(ProviderConfig(
            name="lmstudio",
            model=os.environ.get("LMSTUDIO_MODEL", ""),
            base_url=os.environ.get("LMSTUDIO_URL", "http://127.0.0.1:1234"),
            timeout=int(os.environ.get("LMSTUDIO_TIMEOUT", "120")),
        ))
