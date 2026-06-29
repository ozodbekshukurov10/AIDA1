from __future__ import annotations

import sys
import json
import time
from typing import List, Dict, Optional, Tuple

sys.stdout.reconfigure(encoding='utf-8', errors='replace') if hasattr(sys.stdout, 'reconfigure') else None

try:
    from .tools import execute, get_schemas, set_work_dir, TOOLS
except ImportError:
    from tools import execute, get_schemas, set_work_dir, TOOLS

OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "aida-beta:latest"
MAX_ITERATIONS = 15


class LLMClient:
    def __init__(self):
        self.url = f"{OLLAMA_URL}/api/chat"

    def _call(self, messages: List[Dict], tools: Optional[List[Dict]] = None) -> Dict:
        import urllib.request
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 4096, "num_ctx": 16384},
        }
        if tools:
            payload["tools"] = tools
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            self.url, data=data, headers={"Content-Type": "application/json"}
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    return json.loads(resp.read())
            except Exception as e:
                if attempt == 2:
                    return {"error": str(e)}
                time.sleep(1)
        return {"error": "Max retries"}

    def chat(self, messages: List[Dict]) -> str:
        result = self._call(messages)
        if "error" in result:
            return f"[LLM Error] {result['error']}"
        return result.get("message", {}).get("content", "")

    def chat_with_tools(self, messages: List[Dict]) -> Tuple[str, List[Dict]]:
        schemas = get_schemas()
        result = self._call(messages, schemas)
        if "error" in result:
            return f"[LLM Error] {result['error']}", []
        msg = result.get("message", {})
        content = msg.get("content", "")
        tool_calls_raw = msg.get("tool_calls", [])
        return content, tool_calls_raw


class Agent:
    def __init__(self):
        self.llm = LLMClient()
        self.plan: List[str] = []
        self.history: List[Dict] = []
        self.iteration = 0

    def run(self, user_input: str, work_dir: str = ".") -> str:
        from pathlib import Path
        set_work_dir(Path(work_dir).resolve())

        self.history = [{"role": "system", "content": self._system_prompt()}]
        self.history.append({"role": "user", "content": user_input})
        self.iteration = 0

        print(f"\n  ─── Agent ishga tushdi ───\n")

        while self.iteration < MAX_ITERATIONS:
            self.iteration += 1
            step_label = f"[{self.iteration}/{MAX_ITERATIONS}]"

            content, tool_calls = self.llm.chat_with_tools(self.history)

            if content and content.strip():
                print(f"  {step_label} {content[:200]}")
                self.history.append({"role": "assistant", "content": content})

            if not tool_calls:
                if content and content.strip():
                    return self._finalize(content)
                final = self.llm.chat(self.history)
                return self._finalize(final)

            for tc in tool_calls:
                fn_name = tc.get("function", {}).get("name", "")
                fn_args = tc.get("function", {}).get("arguments", {})
                if isinstance(fn_args, str):
                    try:
                        fn_args = json.loads(fn_args)
                    except json.JSONDecodeError:
                        fn_args = {}

                print(f"  {step_label} 🔧 {fn_name}({json.dumps(fn_args)[:100]})")
                result = execute(fn_name, **fn_args)
                result_preview = result[:300].replace("\n", "\\n")
                print(f"  {step_label} ✅ {fn_name} → {result_preview}")

                self.history.append({
                    "role": "assistant",
                    "content": content or "",
                    "tool_calls": [{
                        "function": {"name": fn_name, "arguments": fn_args}
                    }]
                })
                self.history.append({
                    "role": "tool",
                    "content": result,
                })

        return self._finalize("Maksimal iteratsiyaga yetildi.")

    def _finalize(self, content: str) -> str:
        self.history.append({
            "role": "user",
            "content": "Yuqoridagi barcha amallardan so'ng, yakuniy natijani qisqa, aniq qilib chiqar."
        })
        final = self.llm.chat(self.history)
        return final

    def _system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            f"  - {t.name}: {t.description}" for t in TOOLS
        )
        return f"""Sen AIDA Beta agenti — terminalda ishlaydigan kod yozish assistantisan.

## ISH JARAYONI
Foydalanuvchi so'rovini olganingdan so'ng, quyidagi bosqichlarni bajar:

1. **KONTEKST YIG'ISH** — context tool orqali loyiha holatini bil
2. **REJA TUZISH** — vazifani bosqichlarga ajrat (izoh sifatida yoz)
3. **BAJARISH** — har bir bosqich uchun mos tool ni chaqir
4. **TEKSHIRISH** — natijani tekshir, xato bo'lsa tuzat
5. **YAKUNLASH** — qisqa aniq natija chiqar

## MAVJUD TOOLS
{tool_descriptions}

## QOIDALAR
- Tool chaqirishda barcha kerakli argumentlarni to'ldir
- Agar xato bo'lsa, tuzatib qayta urin
- Katta fayllarni qismlab o'qish uchun offset/limit ishlat
- Kodni yozishdan oldin mavjud kodni o'qib tahlil qil
- Har bir qadamni qisqa tushuntirib bor
- Yakuniy javobda faqat natijani ko'rsat, ortiqcha izoh berma
"""
