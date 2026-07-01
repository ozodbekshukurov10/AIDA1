from __future__ import annotations
import os
import time
from typing import AsyncIterator

from ..base import (
    ProviderConfig, Message, MessageRole, Completion,
    StreamingChunk, ProviderStatus,
)
from ..plugin import ModelPlugin, PluginMetadata, ProviderCapability


class AidaModelPlugin(ModelPlugin):
    metadata = PluginMetadata(
        name="AIDA Model",
        version="1.1.0",
        description="Future AIDA native model - intelligent code assistant",
        website="https://github.com/anomalyco/AIDA",
        capabilities=[
            ProviderCapability.CHAT, ProviderCapability.STREAMING,
            ProviderCapability.TOOL_USE, ProviderCapability.CODE,
            ProviderCapability.FUNCTION_CALLING, ProviderCapability.VISION,
        ],
        env_prefix="AIDA_MODEL_",
        config_schema={
            "model": {"type": "string", "default": "aida-core"},
            "base_url": {"type": "string", "default": "http://127.0.0.1:8500"},
            "api_key": {"type": "string", "default": ""},
            "timeout": {"type": "integer", "default": 120},
        },
    )

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._engine = None
        self._local_mode = os.environ.get("AIDA_MODEL_LOCAL", "false").lower() == "true"

    async def _get_engine(self):
        if self._engine is None:
            from ...aida_model.inference import AidaInferenceEngine
            from ...aida_model.config import AidaArchitectureConfig
            mini = AidaArchitectureConfig(vocab_size=256, hidden_dim=64, num_layers=2, num_heads=4, num_kv_heads=2)
            self._engine = AidaInferenceEngine(self.config.model or "aida-core", mini)
        return self._engine

    def _get_prompt(self, messages: list[Message]) -> str:
        parts = []
        for m in messages:
            role = m.role.value.upper()
            parts.append(f"<{role}>{m.content}</{role}>")
        return "\n".join(parts)

    async def chat(self, messages: list[Message], **kwargs) -> Completion:
        start = time.monotonic()
        if self._local_mode:
            engine = await self._get_engine()
            prompt = self._get_prompt(messages)
            result = await engine.generate(
                prompt,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
            )
            self.status = ProviderStatus.ONLINE
            return Completion(
                content=result.text,
                model=result.model,
                provider="aida",
                finish_reason=result.finish_reason,
                latency_ms=result.latency_ms,
            )

        try:
            import httpx
            client = httpx.AsyncClient(timeout=self.config.timeout)
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            payload = {
                "model": kwargs.get("model") or self.config.model,
                "messages": [m.to_dict() for m in messages],
            }
            resp = await client.post(
                f"{self.config.base_url}/v1/chat/completions",
                json=payload, headers=headers,
            )
            await client.aclose()
            if resp.status_code == 200:
                data = resp.json()
                choice = data["choices"][0]
                self.status = ProviderStatus.ONLINE
                return Completion(
                    content=choice["message"].get("content", ""),
                    model=data.get("model", self.config.model),
                    provider="aida",
                    usage=data.get("usage"),
                    finish_reason=choice.get("finish_reason", "stop"),
                    latency_ms=int((time.monotonic() - start) * 1000),
                )
        except Exception:
            pass

        self.status = ProviderStatus.OFFLINE
        engine = await self._get_engine()
        prompt = self._get_prompt(messages)
        result = await engine.generate(
            prompt,
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            temperature=kwargs.get("temperature", self.config.temperature),
        )
        return Completion(
            content=result.text,
            model=result.model,
            provider="aida",
            finish_reason=result.finish_reason,
            latency_ms=result.latency_ms,
        )

    async def chat_stream(self, messages: list[Message], **kwargs) -> AsyncIterator[StreamingChunk]:
        try:
            engine = await self._get_engine()
            prompt = self._get_prompt(messages)
            async for chunk in engine.generate_stream(
                prompt,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
            ):
                yield StreamingChunk(
                    content=chunk.text,
                    done=chunk.done,
                    finish_reason=chunk.finish_reason,
                )
        except Exception:
            yield StreamingChunk(
                content="AIDA Model is a future component. Placeholder architecture is ready at webapp/aida_model/",
                done=True,
            )

    async def check_health(self) -> bool:
        if self._local_mode:
            try:
                engine = await self._get_engine()
                self.status = ProviderStatus.ONLINE
                return True
            except Exception:
                self.status = ProviderStatus.OFFLINE
                return False
        try:
            import httpx
            client = httpx.AsyncClient(timeout=5)
            resp = await client.get(f"{self.config.base_url}/v1/models")
            await client.aclose()
            if resp.status_code == 200:
                self.status = ProviderStatus.ONLINE
                return True
        except Exception:
            pass
        self.status = ProviderStatus.OFFLINE
        return False

    async def list_models(self) -> list[str]:
        return ["aida-core", "aida-code", "aida-chat", "aida-light"]

    async def get_architecture_info(self) -> dict:
        from ...aida_model.config import AidaConfig
        return AidaConfig().to_dict()

    @classmethod
    def from_env(cls) -> AidaModelPlugin | None:
        if os.environ.get("AIDA_MODEL_ENABLED", "false").lower() != "true":
            return None
        return cls(ProviderConfig(
            name="aida",
            model=os.environ.get("AIDA_MODEL", "aida-core"),
            base_url=os.environ.get("AIDA_MODEL_URL", "http://127.0.0.1:8500"),
            api_key=os.environ.get("AIDA_MODEL_API_KEY", ""),
            timeout=int(os.environ.get("AIDA_MODEL_TIMEOUT", "120")),
        ))
