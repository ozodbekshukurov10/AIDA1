from __future__ import annotations
import os

from ..base import ProviderConfig
from ..plugin import ModelPlugin, PluginMetadata, ProviderCapability
from .base import OpenAICompatibleProvider


class VLLMPlugin(OpenAICompatibleProvider, ModelPlugin):
    metadata = PluginMetadata(
        name="vLLM",
        version="1.0.0",
        description="vLLM inference engine (high-throughput LLM serving)",
        website="https://github.com/vllm-project/vllm",
        capabilities=[
            ProviderCapability.CHAT, ProviderCapability.STREAMING,
            ProviderCapability.FUNCTION_CALLING, ProviderCapability.EMBEDDINGS,
        ],
        requires_base_url=True,
        env_prefix="VLLM_",
        config_schema={
            "model": {"type": "string", "default": ""},
            "base_url": {"type": "string", "required": True, "default": "http://127.0.0.1:8000"},
            "api_key": {"type": "string", "default": ""},
            "timeout": {"type": "integer", "default": 120},
        },
    )

    @classmethod
    def from_env(cls) -> VLLMPlugin | None:
        base_url = os.environ.get("VLLM_BASE_URL", os.environ.get("VLLM_URL", ""))
        if not base_url:
            return None
        return cls(ProviderConfig(
            name="vllm",
            model=os.environ.get("VLLM_MODEL", ""),
            base_url=base_url,
            api_key=os.environ.get("VLLM_API_KEY", ""),
            timeout=int(os.environ.get("VLLM_TIMEOUT", "120")),
        ))
