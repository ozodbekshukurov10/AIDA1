import logging
import os
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

logger = logging.getLogger("webapp.sandbox")

BASE_DIR = Path(__file__).resolve().parent.parent
SANDBOX_DIR = BASE_DIR / ".aida_sandbox"


class Sandbox:
    def __init__(self, work_dir: str | Path = None):
        self.work_dir = Path(work_dir) if work_dir else SANDBOX_DIR
        self.work_dir.mkdir(exist_ok=True)
        self._lock = threading.Lock()
        self._active_boxes: dict[str, "SandboxSession"] = {}
        self._max_output = 10000

    def create_session(self, session_id: str = None) -> "SandboxSession":
        session_id = session_id or f"sandbox-{int(time.time())}"
        session_dir = self.work_dir / session_id
        session_dir.mkdir(exist_ok=True)
        session = SandboxSession(session_id, session_dir, self._max_output)
        with self._lock:
            self._active_boxes[session_id] = session
        return session

    def get_session(self, session_id: str) -> "SandboxSession | None":
        with self._lock:
            return self._active_boxes.get(session_id)

    def destroy_session(self, session_id: str):
        with self._lock:
            session = self._active_boxes.pop(session_id, None)
            if session:
                session.cleanup()

    def list_sessions(self) -> list[dict]:
        with self._lock:
            return [
                {"id": s.id, "file_count": len(list(s.dir.rglob("*"))),
                 "created_at": s.created_at}
                for s in self._active_boxes.values()
            ]


class SandboxSession:
    def __init__(self, session_id: str, session_dir: Path, max_output: int = 10000):
        self.id = session_id
        self.dir = session_dir
        self.max_output = max_output
        self.created_at = time.time()

    def write_file(self, path: str, content: str) -> str:
        full_path = self._resolve_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return f"Fayl saqlandi: {path} ({len(content)} bayt)"

    def read_file(self, path: str) -> str:
        full_path = self._resolve_path(path)
        if not full_path.exists():
            return f"Xato: fayl topilmadi — {path}"
        return full_path.read_text(encoding="utf-8")

    def delete_file(self, path: str) -> str:
        full_path = self._resolve_path(path)
        if full_path.exists():
            full_path.unlink()
            return f"Fayl o'chirildi: {path}"
        return f"Xato: fayl topilmadi — {path}"

    def list_files(self) -> list[dict]:
        files = []
        for p in self.dir.rglob("*"):
            if p.is_file():
                files.append({
                    "path": str(p.relative_to(self.dir)),
                    "size": p.stat().st_size,
                })
        return files

    def run_python(self, code: str, timeout: int = 10) -> dict:
        py_file = self.dir / "_run.py"
        py_file.write_text(code, encoding="utf-8")
        try:
            result = subprocess.run(
                [sys_executable(), str(py_file)],
                capture_output=True, text=True, timeout=timeout,
                cwd=str(self.dir),
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            out = (result.stdout or "")[:self.max_output]
            err = (result.stderr or "")[:self.max_output]
            return {
                "success": result.returncode == 0,
                "stdout": out,
                "stderr": err,
                "return_code": result.returncode,
                "timed_out": False,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "stdout": "", "stderr": "Timeout",
                    "return_code": -1, "timed_out": True}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e),
                    "return_code": -1, "timed_out": False}

    def run_shell(self, command: str, timeout: int = 15) -> dict:
        blocked = ["rm -rf", "del /f", "format", "shutdown"]
        if any(b in command.lower() for b in blocked):
            return {"success": False, "stdout": "", "stderr": "Xavfsizlik: buyruq bloklandi",
                    "return_code": -1, "timed_out": False}
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout,
                cwd=str(self.dir))
            return {
                "success": result.returncode == 0,
                "stdout": (result.stdout or "")[:self.max_output],
                "stderr": (result.stderr or "")[:self.max_output],
                "return_code": result.returncode,
                "timed_out": False,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "stdout": "", "stderr": f"Timeout ({timeout}s)",
                    "return_code": -1, "timed_out": True}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e),
                    "return_code": -1, "timed_out": False}

    def cleanup(self):
        if self.dir.exists():
            shutil.rmtree(str(self.dir), ignore_errors=True)

    def _resolve_path(self, path: str) -> Path:
        p = self.dir / path
        p = p.resolve()
        if not str(p).startswith(str(self.dir.resolve())):
            raise PermissionError(f"Ruxsat etilmagan yo'l: {path}")
        return p


def sys_executable() -> str:
    import sys
    return sys.executable


_sandbox: Sandbox | None = None
_sandbox_lock = threading.Lock()


def get_sandbox() -> Sandbox:
    global _sandbox
    if _sandbox is None:
        with _sandbox_lock:
            if _sandbox is None:
                _sandbox = Sandbox()
    return _sandbox
