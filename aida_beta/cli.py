"""AIDA Beta CLI — terminal-based code assistant (Claude Code / Codex kabi)."""
from __future__ import annotations

import sys
import os
import json
import time
import shutil
import argparse
from pathlib import Path
from typing import Optional

sys.stdout.reconfigure(encoding='utf-8', errors='replace') if hasattr(sys.stdout, 'reconfigure') else None

try:
    import readline
except ImportError:
    readline = None

try:
    from .agent import Agent, LLMClient
    from .tools import execute, TOOLS, set_work_dir
except ImportError:
    from agent import Agent, LLMClient
    from tools import execute, TOOLS, set_work_dir

OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "aida-beta:latest"
HISTORY_FILE = Path.home() / ".aida_beta_history"


def check_ollama() -> bool:
    import urllib.request
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5) as r:
            models = json.loads(r.read()).get("models", [])
            for m in models:
                if "aida-beta" in m.get("name", ""):
                    return True
            print("  AIDA Beta modeli topilmadi. Ishga tushiring: ollama create aida-beta -f aida_beta/Modelfile")
            return False
    except Exception:
        print("  Ollama server ishlamayapti. Ishga tushiring: ollama serve")
        return False


def print_banner():
    cols = shutil.get_terminal_size().columns
    banner = """
  ╔═══════════════════════════════════════════════════╗
  ║         AIDA Beta v2 — Code Assistant             ║
  ║     Foydalanuvchi → Kontekst → Reja → Bajarish    ║
  ╚═══════════════════════════════════════════════════╝
    """
    for line in banner.strip().split("\n"):
        print(line.center(cols))


def print_help():
    print("""
  Buyruqlar:
    /help        — Yordam
    /exit        — Chiqish
    /clear       — Ekranni tozalash
    /read FILE   — Fayl o'qish
    /write FILE  — Fayl yozish
    /run CMD     — Buyruq bajarish
    /plan        — Agent rejimi (default)
    /direct      — To'g'ridan-to'g'ri javob (agent yo'q)
    /model       — Model ma'lumotlari
    /reset       — Suhbatni tozalash
    /save FILE   — Oxirgi javobni saqlash
    /context     — Kontekst ko'rish

  Agent avtomatik ishlaydi: kontekst → reja → bajarish → tekshirish
    """)


def interactive_loop():
    agent = Agent()
    llm = LLMClient()
    use_agent = True
    last_response = ""

    if readline and HISTORY_FILE.exists():
        readline.read_history_file(str(HISTORY_FILE))

    print_banner()
    print("  /help — yordam, /exit — chiqish")
    print("  Agent rejimi: aktiv (avtomatik reja + tool ishlatadi)")
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
                print("  Hayr!")
                break
            elif prompt == "/help":
                print_help()
                continue
            elif prompt == "/clear":
                print("\033[2J\033[H", end="")
                continue
            elif prompt == "/reset":
                agent = Agent()
                history = []
                print("  Suhbat tozalandi.")
                continue
            elif prompt == "/model":
                print(f"  Model: {MODEL_NAME}")
                print(f"  Backend: Ollama ({OLLAMA_URL})")
                print(f"  Agent rejimi: {'aktiv' if use_agent else 'passiv'}")
                continue
            elif prompt == "/plan":
                use_agent = True
                print("  Agent rejimi: aktiv")
                continue
            elif prompt == "/direct":
                use_agent = False
                print("  Agent rejimi: passiv (to'g'ridan-to'g'ri)")
                continue
            elif prompt == "/context":
                print(execute("context"))
                continue
            elif prompt.startswith("/read "):
                path = prompt[6:].strip()
                result = execute("read", path=path)
                print(result)
                last_response = result
                continue
            elif prompt.startswith("/write "):
                args = prompt[7:].strip().split(maxsplit=1)
                if len(args) < 1:
                    print("  /write FILE deb yozing")
                    continue
                path = args[0]
                print("  Kontentni kiriting (oxirida '.'):")
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
                result = execute("write", path=path, content=content)
                print(result)
                last_response = result
                continue
            elif prompt.startswith("/run "):
                cmd = prompt[5:].strip()
                print(f"  $ {cmd}")
                result = execute("run", command=cmd)
                print(result)
                last_response = result
                continue
            elif prompt.startswith("/save "):
                path = prompt[6:].strip()
                if last_response:
                    Path(path).write_text(last_response, encoding="utf-8")
                    print(f"  Saqlandi: {path}")
                else:
                    print("  Saqlash uchun javob yo'q.")
                continue

            if use_agent:
                try:
                    result = agent.run(prompt)
                    print()
                    print("  ═══ Yakuniy natija ═══")
                    print(result)
                    print()
                    last_response = result
                except Exception as e:
                    print(f"\n  [Agent xatosi] {e}")
            else:
                messages = [
                    {"role": "system", "content": "Sen AIDA Beta — kod yozish assistantisan. Qisqa, aniq javob ber."},
                    {"role": "user", "content": prompt},
                ]
                result = llm.chat(messages)
                print()
                print(f"  {result}")
                print()
                last_response = result

    except KeyboardInterrupt:
        print("\n  Hayr!")


def cmd_mode(args: argparse.Namespace):
    agent = Agent()
    try:
        result = agent.run(" ".join(args.command))
        print(result)
    except Exception as e:
        print(f"Xato: {e}", file=sys.stderr)


def cmd_read_mode(path: str):
    agent = Agent()
    content = execute("read", path=path)
    prompt = f"Faylni tahlil qil: {path}\n\n{content}"
    try:
        result = agent.run(prompt)
        print(result)
    except Exception as e:
        print(f"Xato: {e}", file=sys.stderr)


def cmd_run_mode(command: str):
    agent = Agent()
    output = execute("run", command=command)
    prompt = f"Buyruq natijasini tahlil qil: {command}\n\n{output}"
    try:
        result = agent.run(prompt)
        print(result)
    except Exception as e:
        print(f"Xato: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="AIDA Beta v2 — Terminal-based Code Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Misollar:
  aida-beta                      # Interactive REPL (agent rejimi)
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

    set_work_dir(Path.cwd())

    if args.read:
        cmd_read_mode(args.read)
    elif args.run:
        cmd_run_mode(args.run)
    elif args.command:
        cmd_mode(args)
    else:
        interactive_loop()


if __name__ == "__main__":
    main()
