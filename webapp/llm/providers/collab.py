from __future__ import annotations
import json
import urllib.request
import time
import re
from typing import AsyncIterator

from ..base import (
    ProviderConfig, Message, Completion, StreamingChunk, ProviderStatus, MessageRole,
)
from ..plugin import ModelPlugin, PluginMetadata, ProviderCapability
from .ollama import OllamaPlugin
from .lmstudio import LMStudioPlugin


class CollabPlugin(ModelPlugin):
    metadata = PluginMetadata(
        name="collab",
        version="1.1.0",
        description="Unified Hybrid Elite Server (Ollama + LM Studio)",
        capabilities=[
            ProviderCapability.CHAT, ProviderCapability.STREAMING,
        ],
        config_schema={
            "ollama_url": {"type": "string", "default": "http://localhost:11434"},
            "lmstudio_url": {"type": "string", "default": "http://localhost:1234"},
        },
    )

    # Birlashgan tildan foydalanish yo'riqnomasi
    UZBEK_INSTRUCTION = (
        "\n\n## ⚠️ MUHIM YO'RIQNOMA (OHANG VA TIL QAIDALARI):\n"
        "1. Foydalanuvchi qaysi tilda murojaat qilsa (o'zbek, rus, ingliz va h.k.), doimo o'sha tilda javob qaytaring.\n"
        "2. Foydalanuvchiga doimo o'ta muloyim, samimiy va hurmat bilan ('Siz' deb) professional tarzda javob bering.\n"
        "3. Robottdek emas, balki samimiy va yordamga tayyor yordamchi kabi gapiring. Har bir so'roqqa aniq va to'liq javob bering.\n"
    )

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.ollama_url = "http://127.0.0.1:11434"
        self.lmstudio_url = "http://127.0.0.1:1234"
        self.status = ProviderStatus.ONLINE

    @classmethod
    def from_env(cls) -> CollabPlugin | None:
        return cls(ProviderConfig(name="collab"))

    def _detect_task_type(self, messages: list[Message]) -> str:
        # Prompt asosi - oxirgi foydalanuvchi xabari
        prompt = next((m.content for m in reversed(messages) if m.role == MessageRole.USER), "")
        
        # Extract actual user query/result from agent prompts to prevent false matching instructions
        actual_query = prompt
        if "## Yangi ma'lumot / So'nggi natija:" in prompt:
            actual_query = prompt.split("## Yangi ma'lumot / So'nggi natija:")[-1]
        elif "## Tarix / Oldingi qadamlar:" in prompt:
            actual_query = prompt.split("## Tarix / Oldingi qadamlar:")[-1]

        prompt_lower = actual_query.lower()
        code_keywords = [
            "code", "kod", "funksiya", "function", "class", "dastur", "program",
            "python", "javascript", "java", "cpp", "react", "api", "database",
            "sql", "algorithm", "algoritm", "debug", "xatolik", "bug", "fix",
            "implement", "yoz", "write", "app", "ilova", "dasturlash"
        ]
        has_code_kw = False
        for kw in code_keywords:
            if kw == "app":
                if re.search(r"\bapp\b", prompt_lower):
                    has_code_kw = True
                    break
            elif kw in prompt_lower:
                has_code_kw = True
                break
        if has_code_kw:
            return "code"
        return "general"

    def _get_ollama_models(self) -> list[str]:
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            return []

    async def chat(self, messages: list[Message], **kwargs) -> Completion:
        # Check active servers
        ollama_active = False
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                ollama_active = (resp.status == 200)
        except Exception:
            pass

        lmstudio_active = False
        try:
            req = urllib.request.Request(f"{self.lmstudio_url}/v1/models", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                lmstudio_active = (resp.status == 200)
        except Exception:
            pass

        task_type = self._detect_task_type(messages)

        # Inject Uzbek instruction into the system message or first user message
        modified_messages = []
        for m in messages:
            if m.role == MessageRole.SYSTEM:
                modified_messages.append(Message(role=MessageRole.SYSTEM, content=m.content + self.UZBEK_INSTRUCTION))
            else:
                modified_messages.append(m)

        if not any(m.role == MessageRole.SYSTEM for m in messages):
            modified_messages.insert(0, Message(role=MessageRole.SYSTEM, content=self.UZBEK_INSTRUCTION))

        # Route to appropriate provider
        if ollama_active and lmstudio_active:
            if task_type == "code":
                lm = LMStudioPlugin(ProviderConfig(name="lmstudio", base_url=self.lmstudio_url, model="qwen/qwen2.5-coder-14b", timeout=600))
                return await lm.chat(modified_messages, **kwargs)
            else:
                models = self._get_ollama_models()
                chosen = "aida:latest" if "aida:latest" in models else ("aida-beta:latest" if "aida-beta:latest" in models else "qwen2.5:3b")
                oll = OllamaPlugin(ProviderConfig(name="ollama", base_url=self.ollama_url, model=chosen, timeout=600))
                return await oll.chat(modified_messages, **kwargs)

        elif ollama_active:
            models = self._get_ollama_models()
            chosen = "aida:latest" if "aida:latest" in models else ("aida-beta:latest" if "aida-beta:latest" in models else "qwen2.5:3b")
            oll = OllamaPlugin(ProviderConfig(name="ollama", base_url=self.ollama_url, model=chosen, timeout=600))
            return await oll.chat(modified_messages, **kwargs)

        elif lmstudio_active:
            lm = LMStudioPlugin(ProviderConfig(name="lmstudio", base_url=self.lmstudio_url, model="qwen/qwen2.5-coder-14b", timeout=600))
            return await lm.chat(modified_messages, **kwargs)

        else:
            raise RuntimeError("Hech qaysi local model serveri faol emas.")

    async def chat_stream(self, messages: list[Message], **kwargs) -> AsyncIterator[StreamingChunk]:
        # Simple routing to stream
        ollama_active = False
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                ollama_active = (resp.status == 200)
        except Exception:
            pass

        lmstudio_active = False
        try:
            req = urllib.request.Request(f"{self.lmstudio_url}/v1/models", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                lmstudio_active = (resp.status == 200)
        except Exception:
            pass

        task_type = self._detect_task_type(messages)

        modified_messages = []
        for m in messages:
            if m.role == MessageRole.SYSTEM:
                modified_messages.append(Message(role=MessageRole.SYSTEM, content=m.content + self.UZBEK_INSTRUCTION))
            else:
                modified_messages.append(m)

        if not any(m.role == MessageRole.SYSTEM for m in messages):
            modified_messages.insert(0, Message(role=MessageRole.SYSTEM, content=self.UZBEK_INSTRUCTION))

        if ollama_active and lmstudio_active:
            if task_type == "code":
                lm = LMStudioPlugin(ProviderConfig(name="lmstudio", base_url=self.lmstudio_url, model="qwen/qwen2.5-coder-14b", timeout=600))
                async for chunk in lm.chat_stream(modified_messages, **kwargs):
                    yield chunk
            else:
                models = self._get_ollama_models()
                chosen = "aida:latest" if "aida:latest" in models else ("aida-beta:latest" if "aida-beta:latest" in models else "qwen2.5:3b")
                oll = OllamaPlugin(ProviderConfig(name="ollama", base_url=self.ollama_url, model=chosen, timeout=600))
                async for chunk in oll.chat_stream(modified_messages, **kwargs):
                    yield chunk
        elif ollama_active:
            models = self._get_ollama_models()
            chosen = "aida:latest" if "aida:latest" in models else ("aida-beta:latest" if "aida-beta:latest" in models else "qwen2.5:3b")
            oll = OllamaPlugin(ProviderConfig(name="ollama", base_url=self.ollama_url, model=chosen, timeout=600))
            async for chunk in oll.chat_stream(modified_messages, **kwargs):
                yield chunk
        elif lmstudio_active:
            lm = LMStudioPlugin(ProviderConfig(name="lmstudio", base_url=self.lmstudio_url, model="qwen/qwen2.5-coder-14b", timeout=600))
            async for chunk in lm.chat_stream(modified_messages, **kwargs):
                yield chunk
        else:
            yield StreamingChunk(content="Xatolik: Hech qaysi local model serveri faol emas.", done=True)

    async def check_health(self) -> bool:
        # True if at least one is active
        try:
            req = urllib.request.Request(self.ollama_url, method="GET")
            with urllib.request.urlopen(req, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        try:
            req = urllib.request.Request(self.lmstudio_url, method="GET")
            with urllib.request.urlopen(req, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        return False

    async def list_models(self) -> list[str]:
        # Return list of models from both providers
        models = []
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models.extend([m.get("name", "") for m in data.get("models", [])])
        except Exception:
            pass
        try:
            req = urllib.request.Request(f"{self.lmstudio_url}/v1/models", method="GET")
            with urllib.request.urlopen(req, timeout=1) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models.extend([m.get("id", "") for m in data.get("data", [])])
        except Exception:
            pass
        return list(set(models))
