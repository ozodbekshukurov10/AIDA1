#!/usr/bin/env python
"""
AIDA Agentic CLI — Mustaqil Loyiha Agenti
"""

from __future__ import annotations
import os
import sys
import json
import re
import urllib.request
import urllib.error
import subprocess

# Ensure terminal encoding is UTF-8 to prevent encoding errors on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

API_URL = "http://127.0.0.1:8001/api/chat/"

SYSTEM_PROMPT = """Sen AIDA Agentic CLI yordamchisisan. Sen hozirgi ishchi katalogda (directory) mustaqil ishlay oladigan dasturchisan.
Senda fayllarni o'qish, yozish, va terminal buyruqlarini bajarish imkoniyati bor.

Har bir qadamda fikringizni yozib, quyidagi formatda TOOL chaqirig'ini amalga oshirishingiz kerak:

THOUGHT: Keyingi qadam haqida fikringiz
TOOL: tool_nomi {"param1": "qiymat1"}

Foydalanish mumkin bo'lgan tool'lar:

1. file_read {"path": "fayl_yo'li"} - Faylni o'qish uchun.
2. file_write {"path": "fayl_yo'li", "content": "faylning to'liq tarkibi"} - Fayl yaratish yoki to'liq yangilash uchun.
3. shell {"command": "buyruq"} - Terminalda buyruq ishlatish uchun (masalan: pytest, git status, npm run build).
4. list_dir {"path": "."} - Papka ichidagi fayllarni ko'rish uchun.
5. finish {"message": "Bajarilgan ishlar haqida qisqacha o'zbekcha hisobot"} - Ishni tugatganda.

MUHIM QAIDALAR:
1. FAQAT O'ZBEK TILI!
2. Muloqot ohangi samimiy va hurmat bilan ("Siz" deb) bo'lishi shart.
3. Har bir qadamda faqat BITTA tool chaqiring. Chaqiriqdan keyin to'xtang va natijani kuting.
4. Kod yozishdan oldin loyiha tuzilishini va kerakli fayllarni o'qib oling.
"""

def make_request(prompt: str, history: list[str]) -> str:
    # Build complete conversation context
    history_block = "\n".join(history)
    full_prompt = f"{SYSTEM_PROMPT}\n\n## Tarix / Oldingi qadamlar:\n{history_block}\n\n## Yangi ma'lumot / So'nggi natija:\n{prompt}"
    
    payload = {
        "prompt": full_prompt,
        "session_id": "cli_agent_session",
        "mode": "pro",
        "research": False
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=700) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("message", "")
    except urllib.error.URLError as e:
        print(f"\n❌ Xato: AIDA backend serveriga ulanib bo'lmadi ({e}).")
        print("Iltimos, backend serveringiz http://127.0.0.1:8001 da ishlayotganiga ishonch hosil qiling.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Server so'rovida xatolik: {e}")
        sys.exit(1)

def execute_tool(tool_name: str, params: dict) -> str:
    path = params.get("path", "")
    content = params.get("content", "")
    command = params.get("command", "")
    
    if tool_name == "file_read":
        print(f"📖 O'qilmoqda: \033[94m{path}\033[0m")
        try:
            if not os.path.exists(path):
                return f"Xato: fayl topilmadi: {path}"
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()[:10000]
        except Exception as e:
            return f"Xato: {e}"
            
    elif tool_name == "file_write":
        print(f"✍️ Yozilmoqda: \033[92m{path}\033[0m")
        try:
            abs_path = os.path.abspath(path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Fayl muvaffaqiyatli yozildi: {path} ({len(content)} bayt)"
        except Exception as e:
            return f"Xato: {e}"
            
    elif tool_name == "shell":
        print(f"💻 Buyruq bajarilmoqda: \033[93m{command}\033[0m")
        try:
            res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
            out = res.stdout or ""
            err = res.stderr or ""
            return f"Exit Code: {res.returncode}\nStdout:\n{out[:4000]}\nStderr:\n{err[:1500]}"
        except subprocess.TimeoutExpired:
            return "Xato: buyruq vaqti tugadi (timeout)"
        except Exception as e:
            return f"Xato: {e}"
            
    elif tool_name == "list_dir":
        print(f"📁 Ro'yxat olinmoqda: \033[94m{path or '.'}\033[0m")
        try:
            target = path or "."
            if not os.path.exists(target):
                return f"Xato: yo'l topilmadi: {target}"
            entries = os.listdir(target)
            return "\n".join(entries)
        except Exception as e:
            return f"Xato: {e}"
            
    return f"Xato: noma'lum tool '{tool_name}'"

def main():
    if len(sys.argv) < 2:
        print("\033[95mAIDA Agentic CLI\033[0m v1.1.0")
        print("Foydalanish: aida \"so'rovingiz\"")
        print("Masalan: aida \"index.html yaratib, salom dunyo deb yoz va uni sinab ko'r\"")
        sys.exit(1)
        
    user_prompt = " ".join(sys.argv[1:])
    print("\n" + "═" * 60)
    print(f"🤖 \033[96mAIDA Agent loyihani boshqarishni boshladi...\033[0m")
    print(f"📁 Ishchi katalog: {os.getcwd()}")
    print(f"💬 Topshiriq: {user_prompt}")
    print("═" * 60 + "\n")
    
    history = []
    current_input = f"Boshlang'ich topshiriq: {user_prompt}"
    
    # Run autonomous loop up to 20 steps
    for step in range(20):
        print(f"\033[90m[Qadam {step+1}/20] Fikr yuritilmoqda...\033[0m")
        response = make_request(current_input, history)
        
        # Extract Thought if present
        thought_match = re.search(r"THOUGHT:\s*(.*?)(?=TOOL:|\Z)", response, re.DOTALL | re.IGNORECASE)
        if thought_match:
            thought = thought_match.group(1).strip()
            print(f"💭 \033[93mFikr:\033[0m {thought}")
            
        # Parse Tool Call
        tool_match = re.search(r"TOOL:\s*(\w+)\s*(\{.*\})", response, re.DOTALL)
        if tool_match:
            tool_name = tool_match.group(1).strip()
            param_str = tool_match.group(2).strip()
            
            try:
                params = json.loads(param_str)
            except Exception:
                # Attempt to extract JSON if formatted with markdown
                json_match = re.search(r"\{.*\}", param_str, re.DOTALL)
                if json_match:
                    try:
                        params = json.loads(json_match.group(0))
                    except Exception:
                        params = {}
                else:
                    params = {}
            
            # Record step history
            history.append(f"AIDA Fikr: {thought if 'thought' in locals() else ''}")
            history.append(f"AIDA Tool Call: {tool_name} {json.dumps(params)}")
            
            # Execute
            result = execute_tool(tool_name, params)
            
            history.append(f"Tizim Natija:\n{result}")
            current_input = f"Tool '{tool_name}' natijasi:\n{result}"
            
        elif "finish" in response.lower() or "TOOL: finish" in response:
            # Look for finish message parameters
            finish_match = re.search(r"finish\s*(\{.*\})", response, re.DOTALL | re.IGNORECASE)
            msg = ""
            if finish_match:
                try:
                    msg = json.loads(finish_match.group(1)).get("message", "")
                except Exception:
                    pass
            if not msg:
                msg = response
            print(f"\n✅ \033[92mTopshiriq bajarildi!\033[0m")
            print(f"📝 \033[96mHisobot:\033[0m {msg}\n")
            break
        else:
            # Fallback if no tool call but model returned general text
            print(f"\n💬 \033[96mAIDA:\033[0m {response}\n")
            break
    else:
        print("\n⚠️ Qadamlar limiti (20) tugadi.")

if __name__ == "__main__":
    main()
