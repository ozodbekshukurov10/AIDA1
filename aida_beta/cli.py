"""AIDA Beta CLI — terminal-based code assistant (Claude Code / Codex kabi)."""
from __future__ import annotations

import sys
import json
import time
import shutil
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional

try:
    import readline
except ImportError:
    readline = None

OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "aida-beta:latest"
HISTORY_FILE = Path.home() / ".aida_beta_history"


def _ollama_chat(messages: List[dict], stream: bool = False) -> dict | None:
    import urllib.request
    payload = json.dumps({
        "model": MODEL_NAME,
        "messages": messages,
        "stream": stream,
        "options": {"temperature": 0.3, "num_predict": 2048, "num_ctx": 8192},
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat", data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return None


def _stream_chat(messages: List[dict]):
    import urllib.request
    payload = json.dumps({
        "model": MODEL_NAME,
        "messages": messages,
        "stream": True,
        "options": {"temperature": 0.3, "num_predict": 2048, "num_ctx": 8192},
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat", data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            buffer = ""
            for chunk_bytes in iter(lambda: resp.read(1), b""):
                buffer += chunk_bytes.decode()
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if data.get("done"):
                            return
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        yield f"\n[ERROR] {e}"


def check_ollama() -> bool:
    import urllib.request
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5) as r:
            models = json.loads(r.read()).get("models", [])
            for m in models:
                if "aida-beta" in m.get("name", ""):
                    return True
            print("  AIDA Beta modeli topilmadi. 'ollama create aida-beta -f Modelfile' ni bajaring.")
            return False
    except Exception:
        print("  Ollama server ishlamayapti. 'ollama serve' ni bajaring.")
        return False


def print_banner():
    cols = shutil.get_terminal_size().columns
    banner = """
  ╔══════════════════════════════════════╗
  ║   AIDA Beta — Code Assistant CLI     ║
  ║   Terminal-based AI coding agent     ║
  ╚══════════════════════════════════════╝
    """
    for line in banner.strip().split("\n"):
        print(line.center(cols))
    print()


def print_help():
    print("""
  Buyruqlar:
    /help       — Yordam
    /exit       — Chiqish
    /clear      — Ekranni tozalash
    /read FILE  — Fayl o'qish
    /write FILE — Fayl yaratish/yo'zish
    /run CMD    — Terminal buyrug'ini bajarish
    /save FILE  — Oxirgi javobni faylga saqlash
    /model      — Model ma'lumotlari
    /reset      — Suhbatni tozalash

  Misollar:
    /read src/main.py
    /write output.txt
    /run npm test
    Menga React component yoz
    Bu kodni tuzat: ...
    """)


def cmd_read(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"Fayl topilmadi: {path}"
    if p.is_dir():
        return "\n".join(str(x) for x in sorted(p.iterdir()))
    return p.read_text(encoding="utf-8", errors="replace")


def cmd_write(path: str, content: str) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Fayl saqlandi: {path} ({len(content)} bytes)"


def cmd_run(command: str) -> str:
    try:
        r = subprocess.run(command, capture_output=True, text=True, shell=True, timeout=60)
        out = r.stdout or ""
        err = r.stderr or ""
        result = out + ("\n" + err if err else "")
        return result[:4000] or "(bo'sh output)"
    except subprocess.TimeoutExpired:
        return "Komanda 60s ichida tugamadi."
    except Exception as e:
        return f"Xato: {e}"


def interactive_loop():
    history = []
    sys_prompt = """Sen AIDA Beta - terminalda ishlaydigan kod yozish assistantisan.
    
    QOBILIYATLAR:
    - Har qanday dasturlash tilida kod yozish, tuzatish, optimizatsiya qilish
    - Fayllarni o'qish, tahlil qilish va tahrirlash
    - Projekt strukturasi va arxitekturasini tushunish
    - Terminal buyruqlarini bajarish va tahlil qilish
    - Test yozish va debug qilish
    
    QOIDALAR:
    - Kod so'ralganda faqat kod + qisqa izoh ber
    - Error handling bilan to'liq, ishlaydigan kod yoz
    - Type hints, docstrings qo'sh
    - Agar fayl o'qish kerak bo'lsa, /read buyrug'ini ishlatishni so'ra
    - Javoblar qisqa va aniq bo'lsin
    """

    messages = [{"role": "system", "content": sys_prompt}]
    last_response = ""

    if readline and HISTORY_FILE.exists():
        readline.read_history_file(str(HISTORY_FILE))

    print_banner()
    print("  /help — yordam, /exit — chiqish")
    print()

    try:
        while True:
            try:
                prompt = input("aida> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not prompt:
                continue

            if readline:
                try:
                    readline.write_history_file(str(HISTORY_FILE))
                except Exception:
                    pass

            if prompt == "/exit":
                break
            elif prompt == "/help":
                print_help()
                continue
            elif prompt == "/clear":
                print("\033[2J\033[H", end="")
                continue
            elif prompt == "/reset":
                messages = [{"role": "system", "content": sys_prompt}]
                print("  Suhbat tozalandi.")
                continue
            elif prompt == "/model":
                print(f"  Model: {MODEL_NAME}")
                print(f"  Backend: Ollama ({OLLAMA_URL})")
                continue
            elif prompt.startswith("/read "):
                path = prompt[6:].strip()
                content = cmd_read(path)
                print(f"  --- {path} ---")
                print(content if len(content) < 2000 else content[:2000] + "\n  ... (truncated)")
                last_response = content
                continue
            elif prompt.startswith("/run "):
                cmd = prompt[5:].strip()
                print(f"  $ {cmd}")
                result = cmd_run(cmd)
                print(result)
                last_response = result
                continue
            elif prompt.startswith("/write "):
                path = prompt[7:].strip()
                print("  Kontentni kiriting (oxirida . yoki Ctrl+C):")
                lines = []
                try:
                    while True:
                        line = input("  ... ")
                        if line.strip() == ".":
                            break
                        lines.append(line)
                except KeyboardInterrupt:
                    print()
                content = "\n".join(lines)
                print(f"  {cmd_write(path, content)}")
                continue
            elif prompt.startswith("/save "):
                path = prompt[6:].strip()
                if last_response:
                    Path(path).write_text(last_response, encoding="utf-8")
                    print(f"  Oxirgi javob saqlandi: {path}")
                else:
                    print("  Saqlash uchun javob yo'q.")
                continue

            messages.append({"role": "user", "content": prompt})
            print()
            print("  ═══ AIDA Beta ═══")
            print()

            collected = []
            for chunk in _stream_chat(messages):
                print(chunk, end="", flush=True)
                collected.append(chunk)
            print()
            print()
            full_response = "".join(collected)
            messages.append({"role": "assistant", "content": full_response})
            last_response = full_response

    except KeyboardInterrupt:
        print("\n  Hayr!")


def cmd_mode(args: argparse.Namespace):
    """Bir martalik buyruq rejimi (non-interactive)."""
    prompt = " ".join(args.command)
    sys_prompt = "Sen AIDA Beta - kod yozish assistantisan. Qisqa, aniq javob ber."
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": prompt},
    ]
    result = _ollama_chat(messages)
    if result:
        print(result.get("message", {}).get("content", ""))
    else:
        print("Xato: AIDA Beta javob bermadi.", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="AIDA Beta — Terminal-based Code Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Misollar:
  aida-beta                      # Interactive REPL
  aida-beta "Hello World yoz"    # Bir martalik so'rov
  aida-beta --read file.py       # Faylni tahlil qil
  aida-beta --run "npm test"     # Buyruq bajar + tahlil
        """
    )
    parser.add_argument("command", nargs="*", help="Bir martalik so'rov")
    parser.add_argument("--read", type=str, help="Fayl o'qish va tahlil qilish")
    parser.add_argument("--run", type=str, help="Buyruq bajarish va tahlil qilish")
    args = parser.parse_args()

    if not check_ollama():
        sys.exit(1)

    if args.read:
        content = cmd_read(args.read)
        combined = f"Faylni tahlil qil: {args.read}\n\n{content}"
        cmd_mode(argparse.Namespace(command=[combined]))
    elif args.run:
        result = cmd_run(args.run)
        combined = f"Buyruq natijasini tahlil qil: {args.run}\n\n{result}"
        cmd_mode(argparse.Namespace(command=[combined]))
    elif args.command:
        cmd_mode(args)
    else:
        interactive_loop()


if __name__ == "__main__":
    main()
