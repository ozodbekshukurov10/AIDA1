"""AidaBetaProvider — aida-beta:latest Ollama modeli uchun provider."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Iterable, List, Dict, Any

from .memory import AidaBetaMemory

_CONFIG_PATH = Path(__file__).parent / "config.json"
_SYSTEM_PROMPT_PATH = Path(__file__).parent / "system_prompt.txt"


def _load_config() -> Dict[str, Any]:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _load_system_prompt() -> str:
    return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()


class AidaBetaProvider:
    """
    OllamaProvider asosida, lekin aida-beta:latest modeliga xos:
    - config.json dan parametrlar
    - system_prompt.txt dan tizim prompti
    - AidaBetaMemory orqali xotira
    """
    name = "aida-beta"

    def __init__(self, mode: str = "pro") -> None:
        cfg = _load_config()
        self.model: str = cfg["model_name"]
        self.url: str = cfg["ollama_url"]
        mode_cfg = cfg["modes"].get(mode, cfg["modes"]["pro"])
        self.temperature: float = mode_cfg["temperature"]
        self.num_predict: int = mode_cfg["num_predict"]
        self.num_ctx: int = mode_cfg["num_ctx"]
        self.top_p: float = cfg["parameters"]["top_p"]
        self.repeat_penalty: float = cfg["parameters"]["repeat_penalty"]
        self.mode = mode
        self._system_prompt = _load_system_prompt()
        self.memory = AidaBetaMemory()

    def respond(
        self,
        prompt: str,
        memory: Iterable[Dict[str, str]],
        system_prompt: str = "",
        session_id: str = "default",
        **kwargs,
    ) -> str:
        sys = system_prompt or self._system_prompt

        # learned_facts ni system prompt ga inject qilish
        facts = self.memory.learned_facts(limit=8, session_id=session_id)
        if facts:
            sys += "\n\n## Eslab qolingan ma'lumotlar:\n" + "\n".join(f"- {f}" for f in facts)

        messages = [{"role": "system", "content": sys}]
        for m in memory:
            messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "repeat_penalty": self.repeat_penalty,
                "num_ctx": self.num_ctx,
                "num_predict": self.num_predict,
            },
        }
        timeout = 30 if self.mode == "flash" else 120
        try:
            req = urllib.request.Request(
                f"{self.url}/api/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("message", {}).get("content", "") or "AIDA Beta javob bermadi."
        except urllib.error.URLError:
            return "Ollama serverga ulanib bo'lmadi. `ollama serve` buyrug'ini bajaring."
        except Exception as e:
            return f"AIDA Beta xatosi: {e}"

    def is_available(self) -> bool:
        """Ollama da aida-beta modeli borligini tekshiradi."""
        try:
            with urllib.request.urlopen(f"{self.url}/api/tags", timeout=5) as r:
                models = json.loads(r.read()).get("models", [])
                return any("aida-beta" in m.get("name", "") for m in models)
        except Exception:
            return False
