"""
Server Manager — Ollama va LM Studio'ni barcha OS'larda avtomatik boshlash.

Platformalar: macOS, Windows, Linux
Health check: HTTP API orqali tekshirish
Timeout/Retry: Har bir urinish 2s, maksimal 5 marta qayta urinish
"""

import os
import sys
import time
import platform
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional


SYSTEM = platform.system()
IS_WINDOWS = SYSTEM == "Windows"
IS_MAC = SYSTEM == "Darwin"
IS_LINUX = SYSTEM == "Linux"


def _http_get(url: str, timeout: int = 3) -> bool:
    """Berilgan URL ga GET so'rov yuborib, server jonli yoki yo'qligini tekshiradi."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def _find_exe(names: list[str]) -> Optional[str]:
    """Tizim PATH'idan yoki maʼlum manzillardan executable topadi."""
    for name in names:
        try:
            if IS_WINDOWS:
                result = subprocess.run(
                    ["where", name],
                    capture_output=True, text=True, timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                result = subprocess.run(
                    ["which", name],
                    capture_output=True, text=True, timeout=5,
                )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split("\n")[0]
        except Exception:
            pass
    return None


def _popen(args: list[str]) -> Optional[subprocess.Popen]:
    """Fonda jarayonni ishga tushiradi (oyna ko'rsatmaydi)."""
    try:
        kwargs = {
            "args": args,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if IS_WINDOWS:
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        return subprocess.Popen(**kwargs)
    except Exception:
        return None


class ServerManager:
    """
    Ollama va LM Studio serverlarini avtomatik topish, ishga tushirish va health check qilish.

    Misol:
        mgr = ServerManager()
        mgr.start_all_servers()          # ikkalasini birda boshlash
        mgr.is_ollama_running()           # True/False
        mgr.is_lmstudio_running()         # True/False
    """

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        lmstudio_url: str = "http://localhost:1234",
        max_retries: int = 5,
        retry_delay: float = 2.0,
    ):
        self.ollama_url = ollama_url.rstrip("/")
        self.lmstudio_url = lmstudio_url.rstrip("/")
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Executable'larni bir marta topib ol
        self._ollama_exe: Optional[str] = None
        self._lmstudio_exe: Optional[str] = None
        self._lms_cli: Optional[str] = None

    # ──────────────────────────────────────────────
    # OLLAMA
    # ──────────────────────────────────────────────

    def _find_ollama(self) -> Optional[str]:
        """Ollama executable ni topadi."""
        if self._ollama_exe:
            return self._ollama_exe

        paths = ["ollama"]
        if IS_WINDOWS:
            username = os.getenv("USERNAME", "")
            paths = [
                f"C:\\Users\\{username}\\AppData\\Local\\Programs\\Ollama\\ollama.exe",
                "ollama.exe",
            ] + paths
        elif IS_MAC:
            paths = [
                "/usr/local/bin/ollama",
                "/opt/homebrew/bin/ollama",
                "/usr/bin/ollama",
            ] + paths
        elif IS_LINUX:
            paths = [
                "/usr/local/bin/ollama",
                "/usr/bin/ollama",
            ] + paths

        for p in paths:
            if os.path.isfile(p):
                self._ollama_exe = p
                return p

        exe = _find_exe(["ollama", "ollama.exe"])
        if exe:
            self._ollama_exe = exe
        return self._ollama_exe

    def is_ollama_running(self) -> bool:
        """Ollama server jonli yoki yo'qligini tekshiradi."""
        return _http_get(f"{self.ollama_url}/api/tags")

    def start_ollama(self) -> bool:
        """Ollama server ni ishga tushiradi.
        Agar allaqachon ishlayotgan bo'lsa — True qaytaradi.
        """
        if self.is_ollama_running():
            return True

        exe = self._find_ollama()
        if not exe:
            print("[Ollama] executable topilmadi", file=sys.stderr)
            return False

        print(f"[Ollama] {exe} dan ishga tushirilmoqda...")
        proc = _popen([exe, "serve"])
        if proc is None:
            return False

        # Health check — retry loop
        for attempt in range(1, self.max_retries + 1):
            time.sleep(self.retry_delay)
            if self.is_ollama_running():
                print(f"[Ollama] {self.ollama_url} da ishga tushdi (urinish {attempt})")
                return True
            print(f"[Ollama] kutilyapti... ({attempt}/{self.max_retries})")

        print(f"[Ollama] {self.max_retries} ta urinishdan keyin ishga tushmadi", file=sys.stderr)
        return False

    # ──────────────────────────────────────────────
    # LM STUDIO
    # ──────────────────────────────────────────────

    def _find_lmstudio(self) -> Optional[str]:
        """LM Studio executable ni topadi."""
        if self._lmstudio_exe:
            return self._lmstudio_exe

        paths: list[str] = []
        if IS_WINDOWS:
            username = os.getenv("USERNAME", "")
            paths = [
                f"C:\\Users\\{username}\\AppData\\Local\\Programs\\LM Studio\\LM Studio.exe",
                "C:\\Program Files\\LM Studio\\LM Studio.exe",
                "C:\\Program Files (x86)\\LM Studio\\LM Studio.exe",
            ]
            # lms CLI
            self._lms_cli = _find_exe(["lms", "lms.exe"])
            if not self._lms_cli:
                for p in [
                    f"C:\\Users\\{username}\\AppData\\Local\\Programs\\LM Studio\\resources\\app\\.webpack\\lms.exe",
                    "C:\\Program Files\\LM Studio\\resources\\app\\.webpack\\lms.exe",
                ]:
                    if os.path.isfile(p):
                        self._lms_cli = p
                        break
        elif IS_MAC:
            paths = [
                "/Applications/LM Studio.app/Contents/MacOS/LM Studio",
                os.path.expanduser("~/Applications/LM Studio.app/Contents/MacOS/LM Studio"),
            ]
        elif IS_LINUX:
            paths = [
                "/usr/bin/lm-studio",
                "/usr/local/bin/lm-studio",
            ]

        for p in paths:
            if os.path.isfile(p):
                self._lmstudio_exe = p
                return p

        return None

    def is_lmstudio_running(self) -> bool:
        """LM Studio server API'si jonli yoki yo'qligini tekshiradi."""
        return _http_get(f"{self.lmstudio_url}/v1/models")

    def start_lmstudio(self) -> bool:
        """LM Studio server ni ishga tushiradi.
        Avval lms CLI orqali server start qilishga harakat qiladi.
        """
        if self.is_lmstudio_running():
            return True

        self._find_lmstudio()

        # 1) lms CLI orqali
        if self._lms_cli:
            print(f"[LM Studio] lms CLI ({self._lms_cli}) orqali server start...")
            _popen([self._lms_cli, "server", "start"])
            for attempt in range(1, self.max_retries + 1):
                time.sleep(self.retry_delay)
                if self.is_lmstudio_running():
                    print(f"[LM Studio] {self.lmstudio_url} da ishga tushdi (lms, {attempt})")
                    return True

        # 2) LM Studio GUI orqali (server rejimida)
        if self._lmstudio_exe:
            print(f"[LM Studio] {self._lmstudio_exe} ishga tushirilmoqda...")
            _popen([self._lmstudio_exe])
            for attempt in range(1, self.max_retries + 1):
                time.sleep(self.retry_delay)
                if self.is_lmstudio_running():
                    print(f"[LM Studio] {self.lmstudio_url} da ishga tushdi (GUI, {attempt})")
                    return True

        print(f"[LM Studio] executable topilmadi yoki ishga tushmadi", file=sys.stderr)
        return False

    # ──────────────────────────────────────────────
    # BIRDA boshlash
    # ──────────────────────────────────────────────

    def start_all_servers(self) -> dict[str, bool]:
        """Ikkala server ni parallel ishga tushiradi.
        Qaytaradi: {"ollama": True/False, "lmstudio": True/False}
        """
        import threading

        results: dict[str, bool] = {"ollama": False, "lmstudio": False}

        def _ollama():
            results["ollama"] = self.start_ollama()

        def _lmstudio():
            results["lmstudio"] = self.start_lmstudio()

        threads = [
            threading.Thread(target=_ollama, daemon=True),
            threading.Thread(target=_lmstudio, daemon=True),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        return results


# ──────────────────────────────────────────────
# Konsol orqali ishlatish
# ──────────────────────────────────────────────
if __name__ == "__main__":
    mgr = ServerManager()
    print("Ollama ishlayaptimi?", mgr.is_ollama_running())
    print("LM Studio ishlayaptimi?", mgr.is_lmstudio_running())
    print("\nIkkalasini birda boshlash...")
    res = mgr.start_all_servers()
    print(f"Natija: {res}")
