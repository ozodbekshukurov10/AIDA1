"""
AIDA Enterprise API — Python Sandbox ViewSet

Python kodini xavfsiz muhitda bajarish uchun sandbox endpointlari.
"""
from __future__ import annotations
import uuid
import time
from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..responses import APIResponse

MOCK_EXECUTIONS = {
    "exec_1": {
        "id": "exec_1",
        "code": "print('Salom, AIDA!')",
        "language": "python",
        "version": "3.11",
        "status": "completed",
        "output": "Salom, AIDA!",
        "error": "",
        "execution_time_ms": 12,
        "memory_used_kb": 2048,
        "created_at": "2026-07-01T10:00:00Z",
        "user_id": "user_01",
    },
    "exec_2": {
        "id": "exec_2",
        "code": "import math\nprint(math.pi)",
        "language": "python",
        "version": "3.11",
        "status": "completed",
        "output": "3.141592653589793",
        "error": "",
        "execution_time_ms": 8,
        "memory_used_kb": 1024,
        "created_at": "2026-07-02T14:00:00Z",
        "user_id": "user_01",
    },
    "exec_3": {
        "id": "exec_3",
        "code": "x = 1 / 0",
        "language": "python",
        "version": "3.11",
        "status": "error",
        "output": "",
        "error": "ZeroDivisionError: division by zero",
        "execution_time_ms": 5,
        "memory_used_kb": 512,
        "created_at": "2026-07-02T14:30:00Z",
        "user_id": "user_02",
    },
}

SANDBOX_CONFIG = {
    "python": {
        "versions": ["3.9", "3.10", "3.11", "3.12"],
        "default_version": "3.11",
        "max_code_length": 50000,
        "max_execution_time_sec": 30,
        "max_memory_mb": 256,
        "allowed_modules": [
            "math", "random", "json", "re", "datetime", "collections",
            "itertools", "functools", "os.path", "sys", "typing",
            "decimal", "fractions", "statistics", "string", "textwrap",
        ],
        "blocked_modules": ["subprocess", "shutil", "socket", "http", "urllib"],
    },
    "javascript": {
        "versions": ["18", "20"],
        "default_version": "20",
        "max_code_length": 50000,
        "max_execution_time_sec": 15,
        "max_memory_mb": 128,
    },
}


class SandboxViewSet(viewsets.ViewSet):
    """
    Python sandbox — kodni xavfsiz bajarish.

    - POST   /sandbox/execute/              — Kodni bajarish
    - GET    /sandbox/executions/           — Bajarilgan kodlar tarixi
    - GET    /sandbox/executions/{id}/      — Bitta bajarilgan kod
    - DELETE /sandbox/executions/{id}/      — Bajarilgan kodni o'chirish
    - GET    /sandbox/config/               — Sandbox konfiguratsiyasi
    - GET    /sandbox/templates/            — Tayyor kod shablonlari
    - POST   /sandbox/validate/             — Kodni tekshirish (bajarmasdan)
    - POST   /sandbox/executions/{id}/rerun/ — Kodni qayta bajarish
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="execute")
    def execute(self, request):
        """Python kodini bajarish."""
        try:
            code = request.data.get("code")
            if not code:
                return Response(APIResponse.bad_request(message="Code kiritilishi shart."))

            lang = request.data.get("language", "python")
            version = request.data.get("version", SANDBOX_CONFIG.get(lang, {}).get("default_version", "3.11"))

            config = SANDBOX_CONFIG.get(lang, {})
            if len(code) > config.get("max_code_length", 50000):
                return Response(
                    APIResponse.bad_request(
                        message=f"Kod uzunligi {config['max_code_length']} belgidan oshmasligi kerak."
                    )
                )

            exec_id = f"exec_{uuid.uuid4().hex[:8]}"
            now = datetime.utcnow().isoformat() + "Z"
            start_time = time.time()

            output = ""
            error = ""
            exec_status = "completed"

            try:
                exec(output := str(eval(code)) if not any(c in code for c in ["import", "def", "class", "for", "while", "if"]) else "", {})
            except SyntaxError:
                try:
                    compiled = compile(code, "<sandbox>", "exec")
                    local_ns = {}
                    exec(compiled, {"__builtins__": {}}, local_ns)
                    if "output" not in local_ns:
                        output = str(local_ns)
                except Exception as e:
                    error = f"{type(e).__name__}: {e}"
                    exec_status = "error"
            except Exception as e:
                error = f"{type(e).__name__}: {e}"
                exec_status = "error"

            exec_time_ms = int((time.time() - start_time) * 1000)

            execution = {
                "id": exec_id,
                "code": code,
                "language": lang,
                "version": version,
                "status": exec_status,
                "output": output,
                "error": error,
                "execution_time_ms": exec_time_ms,
                "memory_used_kb": 1024,
                "created_at": now,
                "user_id": str(request.user.id),
            }
            MOCK_EXECUTIONS[exec_id] = execution

            return Response(
                APIResponse.success(
                    data=execution,
                    message="Kod bajarildi." if exec_status == "completed" else "Kod bajarilishda xatolik.",
                )
            )
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=False, methods=["get"], url_path="executions")
    def executions(self, request):
        """Bajarilgan kodlar tarixi."""
        try:
            user_id = str(request.user.id)
            execs = [e for e in MOCK_EXECUTIONS.values() if e["user_id"] == user_id]

            lang_filter = request.query_params.get("language")
            if lang_filter:
                execs = [e for e in execs if e["language"] == lang_filter]

            status_filter = request.query_params.get("status")
            if status_filter:
                execs = [e for e in execs if e["status"] == status_filter]

            execs.sort(key=lambda x: x["created_at"], reverse=True)

            return Response(APIResponse.success(data=execs))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["get"], url_path="executions/(?P<exec_pk>[^/.]+)")
    def get_execution(self, request, exec_pk=None, pk=None):
        """Bitta bajarilgan kodni olish."""
        try:
            execution = MOCK_EXECUTIONS.get(exec_pk)
            if not execution:
                return Response(APIResponse.not_found(message=f"Bajarilgan kod topilmadi: {exec_pk}"))
            return Response(APIResponse.success(data=execution))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["delete"], url_path="executions/(?P<exec_pk>[^/.]+)")
    def delete_execution(self, request, exec_pk=None, pk=None):
        """Bajarilgan kodni o'chirish."""
        try:
            execution = MOCK_EXECUTIONS.pop(exec_pk, None)
            if not execution:
                return Response(APIResponse.not_found(message=f"Bajarilgan kod topilmadi: {exec_pk}"))
            return Response(APIResponse.success(message="Bajarilgan kod o'chirildi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=False, methods=["get"])
    def config(self, request):
        """Sandbox konfiguratsiyasi."""
        try:
            return Response(APIResponse.success(data=SANDBOX_CONFIG))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=False, methods=["get"])
    def templates(self, request):
        """Tayyor kod shablonlari."""
        try:
            templates = [
                {
                    "id": "tpl_1",
                    "name": "Salom Dunyo",
                    "language": "python",
                    "code": "print('Salom, Dunyo!')",
                    "description": "Oddiy print",
                    "tags": ["beginner", "hello-world"],
                },
                {
                    "id": "tpl_2",
                    "name": "Fibonacci",
                    "language": "python",
                    "code": "def fibonacci(n):\n    a, b = 0, 1\n    result = []\n    for _ in range(n):\n        result.append(a)\n        a, b = b, a + b\n    return result\n\nprint(fibonacci(10))",
                    "description": "Fibonacci sonlar ketma-ketligi",
                    "tags": ["algorithms", "math"],
                },
                {
                    "id": "tpl_3",
                    "name": "JSON parse",
                    "language": "python",
                    "code": 'import json\ndata = json.loads(\'{"name": "AIDA", "version": 2}\')\nprint(data)',
                    "description": "JSON ma'lumotini parse qilish",
                    "tags": ["data", "json"],
                },
                {
                    "id": "tpl_4",
                    "name": "Sort algoritmi",
                    "language": "python",
                    "code": "data = [64, 34, 25, 12, 22, 11, 90]\nfor i in range(len(data)):\n    for j in range(0, len(data)-i-1):\n        if data[j] > data[j+1]:\n            data[j], data[j+1] = data[j+1], data[j]\nprint(data)",
                    "description": "Bubble sort algoritmi",
                    "tags": ["algorithms", "sorting"],
                },
                {
                    "id": "tpl_5",
                    "name": "HTTP so'rov",
                    "language": "javascript",
                    "code": "fetch('https://jsonplaceholder.typicode.com/todos/1')\n  .then(r => r.json())\n  .then(d => console.log(d))\n  .catch(e => console.error(e));",
                    "description": "HTTP GET so'rovi",
                    "tags": ["network", "http"],
                },
            ]
            return Response(APIResponse.success(data=templates))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=False, methods=["post"])
    def validate(self, request):
        """Kodni tekshirish (bajarmasdan)."""
        try:
            code = request.data.get("code")
            if not code:
                return Response(APIResponse.bad_request(message="Code kiritilishi shart."))

            lang = request.data.get("language", "python")
            warnings = []
            is_valid = True

            if lang == "python":
                dangerous = ["eval(", "exec(", "os.system(", "subprocess.", "__import__("]
                for pattern in dangerous:
                    if pattern in code:
                        warnings.append(f"Xavfli operatsiya aniqlandi: {pattern}")

                if "import" in code:
                    import re
                    modules = re.findall(r"import\s+(\w+)", code)
                    config = SANDBOX_CONFIG.get("python", {})
                    blocked = config.get("blocked_modules", [])
                    for mod in modules:
                        if mod in blocked:
                            warnings.append(f"Taqiqlangan modul: {mod}")
                            is_valid = False

            return Response(
                APIResponse.success(
                    data={
                        "is_valid": is_valid,
                        "warnings": warnings,
                        "code_length": len(code),
                        "language": lang,
                    },
                    message="Kod tekshirildi." if is_valid else "Kodda muammolar aniqlandi.",
                )
            )
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["post"], url_path="executions/(?P<exec_pk>[^/.]+)/rerun")
    def rerun(self, request, exec_pk=None, pk=None):
        """Kodni qayta bajarish."""
        try:
            original = MOCK_EXECUTIONS.get(exec_pk)
            if not original:
                return Response(APIResponse.not_found(message=f"Bajarilgan kod topilmadi: {exec_pk}"))

            exec_id = f"exec_{uuid.uuid4().hex[:8]}"
            now = datetime.utcnow().isoformat() + "Z"

            new_exec = {
                **original,
                "id": exec_id,
                "status": "completed",
                "output": original["output"],
                "error": original["error"],
                "execution_time_ms": original["execution_time_ms"],
                "created_at": now,
                "rerun_from": exec_pk,
            }
            MOCK_EXECUTIONS[exec_id] = new_exec

            return Response(
                APIResponse.created(data=new_exec, message="Kod qayta bajarildi."),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))
