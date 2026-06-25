import asyncio
import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger("webapp.models.model_manager")

OLLAMA_API_URL = "http://localhost:11434"
LMSTUDIO_API_URL = "http://localhost:1234"

MODEL_TYPE_MAP: Dict[str, str] = {
    "code": "code",
    "qwen": "code",
    "deepseek": "code",
    "codellama": "code",
    "llama": "general",
    "mistral": "fast",
    "gemma": "light",
    "phi": "light",
}

TASK_TO_MODEL_TYPE: Dict[str, str] = {
    "code_generation": "code",
    "code_analysis": "code",
    "planning": "general",
    "debugging": "code",
    "testing": "code",
    "optimization": "fast",
}

CACHE_TTL = 300


class ModelManager:
    def __init__(
        self,
        ollama_url: str = None,
        lmstudio_url: str = None,
    ):
        self.ollama_url = (ollama_url or os.getenv("OLLAMA_URL", OLLAMA_API_URL)).rstrip("/")
        self.lmstudio_url = (lmstudio_url or os.getenv("LMSTUDIO_URL", LMSTUDIO_API_URL)).rstrip("/")

        self.current_model: str = os.getenv("AIDA_DEFAULT_MODEL", "qwen2.5:3b")
        self._model_list: Dict[str, Dict[str, Any]] = {}
        self._cache_time: float = 0.0
        self._ollama_running: Optional[bool] = None
        self._lmstudio_running: Optional[bool] = None

    def get_all_models(self) -> Dict[str, Dict[str, Any]]:
        if time.time() - self._cache_time < CACHE_TTL and self._model_list:
            return self._model_list

        models: Dict[str, Dict[str, Any]] = {}

        for provider, discover_fn in [("ollama", self._discover_ollama), ("lmstudio", self._discover_lmstudio)]:
            try:
                discovered = discover_fn()
                for info in discovered:
                    name = info.get("name", "")
                    if not name:
                        continue
                    key = f"{provider}:{name}"
                    models[key] = {
                        "name": name,
                        "provider": provider,
                        "type": self._get_model_type(name),
                        "size": info.get("parameter_size", info.get("size", "unknown")),
                    }
            except Exception as e:
                logger.warning(f"[ModelManager] {provider} discovery failed: {e}")

        self._model_list = models
        self._cache_time = time.time()
        return models

    def set_current_model(self, model_name: str) -> bool:
        models = self.get_all_models()
        for key, info in models.items():
            if info["name"] == model_name or key == model_name:
                self.current_model = info["name"]
                logger.info(f"[ModelManager] Current model set to: {self.current_model}")
                return True
        logger.warning(f"[ModelManager] Model '{model_name}' not found")
        return False

    def get_current_model(self) -> str:
        return self.current_model

    async def call_model(self, prompt: str, system_prompt: str = "") -> str:
        model_name = self.current_model
        provider = self._detect_provider(model_name)

        if provider == "lmstudio":
            return await self._call_lmstudio(model_name, prompt, system_prompt)
        return await self._call_ollama(model_name, prompt, system_prompt)

    async def _call_ollama(self, model: str, prompt: str, system: str) -> str:
        url = f"{self.ollama_url}/api/generate"
        body = json.dumps({
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "temperature": 0.7,
        }).encode("utf-8")

        for attempt in range(2):
            try:
                req = urllib.request.Request(url, data=body, method="POST")
                req.add_header("Content-Type", "application/json")
                loop = asyncio.get_event_loop()
                resp = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=120))
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response", "")
            except Exception as e:
                logger.warning(f"[Ollama] Attempt {attempt+1} failed: {e}")
                if attempt == 0:
                    await asyncio.sleep(1)
        raise RuntimeError(f"Ollama call failed after retries: {model}")

    async def _call_lmstudio(self, model: str, prompt: str, system: str) -> str:
        url = f"{self.lmstudio_url}/chat/completions"
        body = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 2048,
        }).encode("utf-8")

        for attempt in range(2):
            try:
                req = urllib.request.Request(url, data=body, method="POST")
                req.add_header("Content-Type", "application/json")
                req.add_header("Authorization", "Bearer lm-studio")
                loop = asyncio.get_event_loop()
                resp = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=120))
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                logger.warning(f"[LMStudio] Attempt {attempt+1} failed: {e}")
                if attempt == 0:
                    await asyncio.sleep(1)
        raise RuntimeError(f"LM Studio call failed after retries: {model}")

    def _detect_provider(self, model_name: str) -> str:
        models = self.get_all_models()
        for key in models:
            if models[key]["name"] == model_name or key == model_name:
                return models[key]["provider"]
        return "ollama"

    def _get_model_type(self, model_name: str) -> str:
        lower = model_name.lower()
        for key, mtype in MODEL_TYPE_MAP.items():
            if key in lower:
                return mtype
        return "general"

    def select_best_model(self, task_type: str) -> str:
        target = TASK_TO_MODEL_TYPE.get(task_type, "general")
        models = self.get_all_models()

        for key, info in models.items():
            if info["type"] == target:
                return info["name"]

        fallback_order = ["code", "general", "fast", "light"]
        for fb in fallback_order:
            for key, info in models.items():
                if info["type"] == fb:
                    return info["name"]

        return self.current_model

    def get_status(self) -> Dict[str, Any]:
        self._ollama_running = self._check_server(self.ollama_url + "/api/tags")
        self._lmstudio_running = self._check_server(self.lmstudio_url + "/v1/models")

        models = self.get_all_models()
        return {
            "current_model": self.current_model,
            "available_models": [info["name"] for info in models.values()],
            "ollama_running": self._ollama_running,
            "lmstudio_running": self._lmstudio_running,
        }

    def _discover_ollama(self) -> List[Dict[str, Any]]:
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data.get("models", [])
        except Exception:
            return []

    def _discover_lmstudio(self) -> List[Dict[str, Any]]:
        try:
            req = urllib.request.Request(f"{self.lmstudio_url}/v1/models", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data.get("data", [])
        except Exception:
            return []

    def _check_server(self, url: str) -> bool:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=3):
                return True
        except Exception:
            return False
