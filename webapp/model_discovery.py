"""
Model Discovery — Ollama va LM Studio'dan barcha modellarni topish.
"""

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional


OLLAMA_API_URL = "http://localhost:11434"
LMSTUDIO_API_URL = "http://localhost:1234"


@dataclass
class ModelInfo:
    name: str
    provider: str          # "ollama" | "lmstudio"
    size_gb: Optional[float] = None
    quantization: Optional[str] = None
    family: Optional[str] = None
    parameter_size: Optional[str] = None
    modified_at: Optional[str] = None
    digest: Optional[str] = None
    details: dict = field(default_factory=dict)


def discover_ollama_models(url: str = OLLAMA_API_URL) -> list[ModelInfo]:
    """Ollama serverdan barcha modellarni topadi."""
    models: list[ModelInfo] = []
    try:
        req = urllib.request.Request(f"{url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return models

    for m in data.get("models", []):
        name = m.get("name", "")
        if not name:
            continue
        size = m.get("size", 0)
        size_gb = round(size / (1024**3), 2) if size else None
        details = m.get("details", {}) or {}
        models.append(ModelInfo(
            name=name,
            provider="ollama",
            size_gb=size_gb,
            quantization=details.get("quantization_level"),
            family=details.get("family"),
            parameter_size=details.get("parameter_size"),
            modified_at=m.get("modified_at"),
            digest=m.get("digest"),
            details=details,
        ))
    return models


def discover_lmstudio_models(url: str = LMSTUDIO_API_URL) -> list[ModelInfo]:
    """LM Studio serverdan barcha modellarni topadi."""
    models: list[ModelInfo] = []
    try:
        req = urllib.request.Request(f"{url}/v1/models", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return models

    for m in data.get("data", []):
        mid = m.get("id", "") or m.get("name", "")
        if not mid:
            continue
        models.append(ModelInfo(
            name=mid,
            provider="lmstudio",
            details=m,
        ))
    return models


def discover_all(ollama_url: str = OLLAMA_API_URL, lmstudio_url: str = LMSTUDIO_API_URL) -> dict:
    """Ikkala serverdan modellarni topib, birlashtirilgan ro'yxat qaytaradi."""
    import threading

    results = {"ollama": [], "lmstudio": []}

    def _ollama():
        results["ollama"] = discover_ollama_models(ollama_url)

    def _lmstudio():
        results["lmstudio"] = discover_lmstudio_models(lmstudio_url)

    threads = [
        threading.Thread(target=_ollama, daemon=True),
        threading.Thread(target=_lmstudio, daemon=True),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    all_models = results["ollama"] + results["lmstudio"]

    return {
        "total": len(all_models),
        "providers": {
            "ollama": {
                "count": len(results["ollama"]),
                "url": ollama_url,
                "models": [m.__dict__ for m in results["ollama"]],
            },
            "lmstudio": {
                "count": len(results["lmstudio"]),
                "url": lmstudio_url,
                "models": [m.__dict__ for m in results["lmstudio"]],
            },
        },
        "models": [m.__dict__ for m in all_models],
    }
