from __future__ import annotations
import os

from ..base import ProviderConfig
from ..plugin import ModelPlugin, PluginMetadata, ProviderCapability
from .base import OpenAICompatibleProvider


class TensorRTPlugin(OpenAICompatibleProvider, ModelPlugin):
    metadata = PluginMetadata(
        name="TensorRT-LLM",
        version="1.0.0",
        description="NVIDIA TensorRT-LLM (optimized LLM inference on NVIDIA GPUs)",
        website="https://github.com/NVIDIA/TensorRT-LLM",
        capabilities=[
            ProviderCapability.CHAT, ProviderCapability.STREAMING,
        ],
        requires_base_url=True,
        env_prefix="TENSORRT_",
        config_schema={
            "model": {"type": "string", "default": ""},
            "base_url": {"type": "string", "required": True, "default": "http://127.0.0.1:8001"},
            "api_key": {"type": "string", "default": ""},
            "timeout": {"type": "integer", "default": 120},
        },
    )

    @classmethod
    def from_env(cls) -> TensorRTPlugin | None:
        base_url = os.environ.get("TENSORRT_BASE_URL", os.environ.get("TENSORRT_URL", ""))
        if not base_url:
            return None
        return cls(ProviderConfig(
            name="tensorrt",
            model=os.environ.get("TENSORRT_MODEL", ""),
            base_url=base_url,
            api_key=os.environ.get("TENSORRT_API_KEY", ""),
            timeout=int(os.environ.get("TENSORRT_TIMEOUT", "120")),
        ))
