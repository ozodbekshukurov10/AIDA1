"""
Model Manager — Ollama va LM Studio uchun unified interface.
Model list, select, load/unload, pull/remove, get info.
"""

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional, Any


OLLAMA_URL = "http://localhost:11434"
LMSTUDIO_URL = "http://localhost:1234"


def _http_get(url: str, timeout: int = 5) -> Any:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_post(url: str, data: dict, timeout: int = 30) -> Any:
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ──────────────────────────────────────────────
# OLLAMA
# ──────────────────────────────────────────────

def ollama_list() -> list[dict]:
    """Ollama'dagi barcha modellarni qaytaradi."""
    try:
        data = _http_get(f"{OLLAMA_URL}/api/tags")
        models = []
        for m in data.get("models", []):
            det = m.get("details", {}) or {}
            size = m.get("size", 0)
            models.append({
                "id": m.get("name", ""),
                "name": m.get("name", ""),
                "provider": "ollama",
                "size_gb": round(size / (1024**3), 2) if size else 0,
                "quantization": det.get("quantization_level"),
                "family": det.get("family"),
                "parameter_size": det.get("parameter_size"),
                "modified_at": m.get("modified_at"),
                "digest": m.get("digest"),
            })
        return models
    except Exception:
        return []


def ollama_pull(model_name: str) -> dict:
    """Modelni Ollama'ga yuklab oladi (pull)."""
    try:
        result = _http_post(f"{OLLAMA_URL}/api/pull", {"name": model_name}, timeout=300)
        return {"status": "ok", "model": model_name, "result": result.get("status", "downloaded")}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def ollama_delete(model_name: str) -> dict:
    """Modelni Ollama'dan o'chiradi."""
    try:
        result = _http_delete(f"{OLLAMA_URL}/api/delete", {"name": model_name})
        return {"status": "ok", "model": model_name}
    except Exception as e:
        if "409" in str(e):
            return {"status": "error", "error": "Model is in use. Stop it first."}
        return {"status": "error", "error": str(e)}


def ollama_show(model_name: str) -> dict:
    """Model haqida batafsil ma'lumot."""
    try:
        data = _http_post(f"{OLLAMA_URL}/api/show", {"name": model_name})
        modelfile = data.get("modelfile", "")
        details = {}
        for line in modelfile.split("\n"):
            if "TEMPLATE" in line or "PARAMETER" in line or "LICENSE" in line:
                key, _, val = line.partition(" ")
                details[key.lower()] = val.strip()
        return {
            "name": model_name,
            "provider": "ollama",
            "modelfile": modelfile[:2000],
            "details": details,
            "metadata": data,
        }
    except Exception as e:
        return {"error": str(e)}


def _http_delete(url: str, data: dict, timeout: int = 10) -> Any:
    """Ollama DELETE so'rovi (Ollama /api/delete DELETE metod bilan ishlaydi)."""
    import urllib.parse
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="DELETE",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        try:
            return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return {"status": "deleted"}


# ──────────────────────────────────────────────
# LM STUDIO
# ──────────────────────────────────────────────

def lmstudio_list() -> list[dict]:
    """LM Studio'dagi barcha modellarni qaytaradi (serverga yuklangan)."""
    try:
        data = _http_get(f"{LMSTUDIO_URL}/v1/models")
        models = []
        for m in data.get("data", []):
            mid = m.get("id", "") or m.get("name", "")
            models.append({
                "id": mid,
                "name": mid,
                "provider": "lmstudio",
                "object": m.get("object", "model"),
                "owned_by": m.get("owned_by", "local"),
            })
        return models
    except Exception:
        return []


def lmstudio_load(model_name: str) -> dict:
    """Modelni LM Studio'ga yuklaydi (lms CLI orqali)."""
    import subprocess, os, platform
    lms_cli = _find_lms_cli()
    if not lms_cli:
        return {"status": "error", "error": "lms CLI topilmadi"}
    try:
        kwargs = {
            "args": [lms_cli, "load", model_name],
            "stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "timeout": 60,
        }
        if platform.system() == "Windows":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        r = subprocess.run(**kwargs)
        out = r.stdout.decode("utf-8", errors="replace")[:500]
        err = r.stderr.decode("utf-8", errors="replace")[:500]
        if r.returncode == 0:
            return {"status": "ok", "model": model_name, "output": out}
        return {"status": "error", "error": err or out}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _find_lms_cli() -> Optional[str]:
    """lms CLI executable ni topish."""
    import os, platform
    paths = ["lms"]
    if platform.system() == "Windows":
        username = os.getenv("USERNAME", "")
        paths = [
            f"C:\\Users\\{username}\\AppData\\Local\\Programs\\LM Studio\\resources\\app\\.webpack\\lms.exe",
            "C:\\Program Files\\LM Studio\\resources\\app\\.webpack\\lms.exe",
            "lms.exe",
        ] + paths
    elif platform.system() == "Darwin":
        paths = [
            "/Applications/LM Studio.app/Contents/Resources/app/.webpack/lms",
            os.path.expanduser("~/Applications/LM Studio.app/Contents/Resources/app/.webpack/lms"),
        ] + paths
    for p in paths:
        if os.path.isfile(p):
            return p
    return None


def lmstudio_unload() -> dict:
    """LM Studio'dagi barcha modellarni tushiradi."""
    return lmstudio_load("")  # Bo'sh nom bilan chaqirish modelni tushiradi


# ──────────────────────────────────────────────
# UNIFIED INTERFACE
# ──────────────────────────────────────────────

class ModelManager:
    """Ollama + LM Studio uchun unified boshqaruvchi."""

    @staticmethod
    def list_all() -> dict:
        """Ikkala provider'dagi modellarni birlashtirgan ro'yxat."""
        import threading
        r = {"ollama": [], "lmstudio": []}
        def _o(): r["ollama"] = ollama_list()
        def _l(): r["lmstudio"] = lmstudio_list()
        threads = [threading.Thread(target=t, daemon=True) for t in (_o, _l)]
        for t in threads: t.start()
        for t in threads: t.join(timeout=8)
        combined = r["ollama"] + r["lmstudio"]
        return {
            "total": len(combined),
            "models": combined,
            "providers": {
                "ollama": {"count": len(r["ollama"]), "models": r["ollama"]},
                "lmstudio": {"count": len(r["lmstudio"]), "models": r["lmstudio"]},
            },
        }

    @staticmethod
    def get_model(model_id: str) -> dict:
        """Model ID bo'yicha batafsil ma'lumot."""
        if "/" in model_id or ":" in model_id:
            return ollama_show(model_id)
        if "." in model_id:
            # LM Studio model — faqat basic info
            all_m = lmstudio_list()
            for m in all_m:
                if m["id"] == model_id:
                    return {"name": model_id, "provider": "lmstudio", "details": m}
        return {"error": f"Model topilmadi: {model_id}"}

    @staticmethod
    def pull_model(model_name: str) -> dict:
        """Modelni yuklab oladi (faqat Ollama)."""
        return ollama_pull(model_name)

    @staticmethod
    def remove_model(model_name: str) -> dict:
        """Modelni o'chiradi (faqat Ollama)."""
        return ollama_delete(model_name)

    @staticmethod
    def load_model(model_name: str) -> dict:
        """Modelni yuklaydi (faqat LM Studio)."""
        return lmstudio_load(model_name)

    @staticmethod
    def unload_model() -> dict:
        """Modelni tushiradi (faqat LM Studio)."""
        return lmstudio_unload()

    @staticmethod
    def select_active(model_name: str) -> dict:
        """Modelni faollashtiradi — Ollama'da bormi? LM Studio'da yuklash."""
        if not model_name:
            return {"error": "Model nomi kerak"}

        # 1. Ollama'da tekshir
        ollama_models = ollama_list()
        for m in ollama_models:
            if m["id"] == model_name:
                return {"status": "ok", "provider": "ollama", "model": model_name,
                        "message": f"{model_name} Ollama'da mavjud va tayyor"}

        # 2. LM Studio'da yuklashga harakat
        lm_result = lmstudio_load(model_name)
        if lm_result.get("status") == "ok":
            return {"status": "ok", "provider": "lmstudio", "model": model_name,
                    "message": f"{model_name} LM Studio'ga yuklandi"}

        # 3. Ollama'ga pull qilishni taklif
        return {"status": "not_found", "model": model_name,
                "message": f"{model_name} topilmadi. Ollama'ga pull qiling: POST /api/manager/pull/"}
