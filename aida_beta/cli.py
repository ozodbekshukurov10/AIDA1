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
    from .agent import (Agent, LLMClient, SubAgent, AgentOrchestrator,
                        detect_task_type, TaskType, get_orchestrator,
                        ExecutionMode, PermissionManager)
    from .tools import execute, TOOLS, set_work_dir
    from .memory import AidaBetaMemory
    from .knowledge import get_knowledge_store, KnowledgeStore
    from .assistants import (CodeReviewBot, DebugAssistant, ArchitectureAssistant,
                             LanguageAssistant, FrameworkAssistant, VersionControlAssistant,
                             DockerAssistant, KubernetesAssistant, PerformanceTuningAssistant)
    from .learning import FeedbackLoop, ModelFineTuning, KnowledgeUpdater
except ImportError:
    from agent import (Agent, LLMClient, SubAgent, AgentOrchestrator,
                       detect_task_type, TaskType, get_orchestrator,
                       ExecutionMode, PermissionManager)
    from tools import execute, TOOLS, set_work_dir
    from memory import AidaBetaMemory
    from knowledge import get_knowledge_store, KnowledgeStore
    from assistants import (CodeReviewBot, DebugAssistant, ArchitectureAssistant,
                            LanguageAssistant, FrameworkAssistant, VersionControlAssistant,
                            DockerAssistant, KubernetesAssistant, PerformanceTuningAssistant)
    from learning import FeedbackLoop, ModelFineTuning, KnowledgeUpdater

OLLAMA_URL = "http://localhost:11434"
LM_STUDIO_URL = "http://localhost:1234"
MODEL_NAME = "aida-beta:latest"
HISTORY_FILE = Path.home() / ".aida_beta_history"


def _lmstudio_available() -> bool:
    import urllib.request
    try:
        with urllib.request.urlopen(f"{LM_STUDIO_URL}/v1/models", timeout=3) as r:
            return True
    except Exception:
        return False


def ensure_ollama() -> bool:
    """Ollama server va modelni avtomatik ishga tushiradi."""
    if _lmstudio_available():
        print("  LM Studio aniqlandi (14B model)")
        return True
    import urllib.request
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3) as r:
            models = json.loads(r.read()).get("models", [])
            for m in models:
                if "aida-beta" in m.get("name", ""):
                    return True
            print("  AIDA Beta modeli yaratilmoqda...")
            modelfile = Path(__file__).parent / "Modelfile"
            if modelfile.exists():
                import subprocess
                r = subprocess.run(
                    ["ollama", "create", "aida-beta", "-f", str(modelfile)],
                    capture_output=True, text=True, timeout=120
                )
                if r.returncode == 0:
                    print("  Model yaratildi: aida-beta:latest")
                    return True
                print(f"  Model yaratilmadi: {r.stderr}")
            return False
    except Exception:
        print("  Ollama server ishga tushirilmoqda...")
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from server_manager import ServerManager
            mgr = ServerManager()
            if mgr.start_ollama():
                print("  Ollama ishga tushdi!")
                return ensure_ollama()
        except Exception as e:
            print(f"  Ollama xatosi: {e}")
        return False


def print_banner():
    cols = shutil.get_terminal_size().columns
    banner = """
  \u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557
  \u2551         AIDA Beta v2 \u2014 Code Assistant             \u2551
  \u2551     Kontekst \u2192 Reja \u2192 Bajarish \u2192 Tekshirish    \u2551
  \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d
    """
    for line in banner.strip().split("\n"):
        print(line.center(cols))


def print_help():
    print("""
  Buyruqlar:
    /help          - Yordam
    /exit          - Chiqish
    /clear         - Ekranni tozalash
    /read FILE     - Fayl o'qish
    /write FILE    - Fayl yozish
    /run CMD       - Buyruq bajarish
    /plan          - Agent rejimi (default)
    /direct        - To'g'ridan-to'g'ri javob (agent yo'q)
    /mode          - Bajarish rejimi: plan|auto|approve
    /model         - Model ma'lumotlari
    /reset         - Suhbatni tozalash
    /save FILE     - Oxirgi javobni saqlash
    /context       - Kontekst ko'rish
    /sessions      - Sessiyalar ro'yxati
    /threads       - Threadlar ro'yxati
    /thclose       - Joriy threadni yopish
    /checkpoint    - Checkpoint saqlash
    /rollback N    - Checkpoint ga qaytish
    /review FILE   - Kodni code review qilish
    /debug ERR     - Xatolikni tahlil qilish
    /arch TXT      - Arxitektura tahlili
    /knowledge     - Bilimlar bazasi holati
    /feedback      - Feedback statistikasi
    /train PROMPT  - Training data ga qo'shish
    /agents        - Agentlar statistikasi
    /templates     - Sessiya template lari
    /memory        - Project memory (CLAUDE.md / AGENTS.md)
    /rules TOOL LVL- Tool ruxsat darajasi (always_ask|always_allow|never_allow)

  Rejimlar:
    plan    - Faqat reja tuzish, tool ishlatmaydi
    auto    - Avtomatik tool ishlatadi (default)
    approve- Har bir tool uchun ruxsat soraydi

  Agent avtomatik ishlaydi: kontekst -> reja -> bajarish -> tekshirish
    """)


def interactive_loop():
    agent = Agent(mode=ExecutionMode.AUTO)
    llm = LLMClient()
    memory = AidaBetaMemory()
    use_agent = True
    last_response = ""
    mode_map = {"plan": ExecutionMode.PLAN, "auto": ExecutionMode.AUTO, "approve": ExecutionMode.APPROVE}

    if readline and HISTORY_FILE.exists():
        readline.read_history_file(str(HISTORY_FILE))

    print_banner()
    print("  /help - yordam, /exit - chiqish")
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
                agent = Agent(mode=agent.permission.mode)
                history = []
                print("  Suhbat tozalandi.")
                continue
            elif prompt == "/model":
                print(f"  Model: {MODEL_NAME}")
                print(f"  Backend: Ollama ({OLLAMA_URL})")
                print(f"  Agent rejimi: {'aktiv' if use_agent else 'passiv'}")
                print(f"  Bajarish rejimi: {agent.permission.mode.value}")
                continue
            elif prompt == "/plan":
                use_agent = True
                agent = Agent(mode=ExecutionMode.AUTO)
                print("  Agent rejimi: aktiv")
                continue
            elif prompt == "/direct":
                use_agent = False
                print("  Agent rejimi: passiv (to'g'ridan-to'g'ri)")
                continue
            elif prompt.startswith("/mode"):
                parts = prompt.split()
                if len(parts) >= 2:
                    new_mode = parts[1].lower()
                    if new_mode in mode_map:
                        agent.permission.set_mode(mode_map[new_mode])
                        print(f"  Bajarish rejimi: {new_mode}")
                    else:
                        print(f"  Notog'ri rejim: {new_mode}. Plan | auto | approve")
                else:
                    print(f"  Joriy rejim: {agent.permission.mode.value}")
                continue
            elif prompt == "/context":
                print(execute("context"))
                continue
            elif prompt == "/sessions":
                sess = memory.sessions()
                if not sess:
                    print("  Sessiyalar mavjud emas.")
                else:
                    for s in sess[:10]:
                        print(f"  [{s['id']}] oxirgi aktivlik: {s['last_activity']}")
                continue
            elif prompt == "/threads":
                threads = memory.list_threads(agent.session_id)
                if not threads:
                    print("  Threadlar mavjud emas.")
                else:
                    for t in threads[:10]:
                        print(f"  [{t['thread_id'][:8]}] {t['message_count']} msgs, oxirgi: {t['last_activity']}")
                continue
            elif prompt == "/thclose":
                agent.close_thread()
                agent.thread_id = str(__import__('uuid').uuid4())
                print("  Joriy thread yopildi, yangi thread ochildi.")
                continue
            elif prompt.startswith("/checkpoint"):
                label = prompt.split(maxsplit=1)
                label = label[1] if len(label) > 1 else f"cp_{int(time.time())}"
                cpid = memory.save_checkpoint(label, {"time": time.time()}, agent.session_id)
                print(f"  Checkpoint saqlandi: #{cpid} ({label})")
                continue
            elif prompt.startswith("/rollback"):
                parts = prompt.split()
                if len(parts) < 2:
                    print("  /rollback CHECKPOINT_ID")
                    continue
                try:
                    cpid = int(parts[1])
                    cp = memory.load_checkpoint(cpid)
                    if cp:
                        print(f"  Checkpoint #{cpid} \"{cp['label']}\" ({cp['created_at']}) ga qaytildi.")
                        agent = Agent(mode=agent.permission.mode)
                    else:
                        print(f"  Checkpoint #{cpid} topilmadi.")
                except ValueError:
                    print("  Noto'g'ri ID.")
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
            elif prompt.startswith("/review "):
                path = prompt[8:].strip()
                content = execute("read", path=path)
                reviewer = CodeReviewBot()
                result = reviewer.review(content, language=path.split(".")[-1] if "." in path else "python")
                print(result)
                last_response = result
                continue
            elif prompt.startswith("/debug "):
                error = prompt[7:].strip()
                debugger = DebugAssistant()
                result = debugger.debug(error)
                print(result)
                last_response = result
                continue
            elif prompt.startswith("/arch "):
                desc = prompt[6:].strip()
                arch = ArchitectureAssistant()
                result = arch.analyze(desc)
                print(result)
                last_response = result
                continue
            elif prompt == "/knowledge":
                store = get_knowledge_store()
                docs = store.list_all()
                if not docs:
                    print("  Bilimlar bazasida malumot yo'q.")
                else:
                    print(f"  {len(docs)} ta hujjat:")
                    for d in docs[:10]:
                        print(f"  [{d['id']}] {d['content'][:80]}...")
                continue
            elif prompt == "/feedback":
                fb = FeedbackLoop()
                data = fb.analytics()
                print(f"  Baholar: {data['total_ratings']} (avg: {data['avg_rating']})")
                print(f"  Xatolar: {data['total_errors']}")
                print(f"  So'rovlar: {data['total_usage']} (7 kun: {data['usage_last_7d']})")
                continue
            elif prompt.startswith("/train "):
                text = prompt[7:].strip()
                mt = ModelFineTuning()
                result = mt.save_training_pair(prompt=text, response="(pending)", domain="general")
                print(f"  Training data ga qoshildi: {result}")
                continue
            elif prompt == "/agents":
                orch = get_orchestrator(mode=agent.permission.mode)
                stats = orch.get_agent_stats()
                for ttype, s in stats.items():
                    print(f"  [{ttype}] {s['task_count']} tasks, {s['error_count']} errors, busy={s['busy']}")
                continue
            elif prompt == "/templates":
                templates = memory.list_templates()
                if not templates:
                    print("  Template lar mavjud emas.")
                else:
                    for t in templates:
                        print(f"  [{t['name']}] {t['created_at']}")
                continue
            elif prompt == "/memory":
                sections = memory.get_project_sections()
                if not sections:
                    print("  Project memory bo'sh.")
                else:
                    for sec in sections:
                        items = memory.get_project_memory(sec)
                        print(f"  [{sec}]")
                        for k, v in list(items.items())[:5]:
                            print(f"    {k}: {v[:80]}")
                md_summary = agent.memory_md.get_summary()
                if md_summary:
                    print(f"  --- Memory MD fayllari ---")
                    print(f"  {md_summary[:500]}")
                continue
            elif prompt.startswith("/rules "):
                parts = prompt.split()
                if len(parts) < 3:
                    print("  /rules TOOL_NAME always_ask|always_allow|never_allow")
                    continue
                tool_name, level = parts[1], parts[2]
                if level in ("always_ask", "always_allow", "never_allow"):
                    from .agent import PermissionLevel
                    agent.permission.set_rule(tool_name, PermissionLevel(level))
                    print(f"  {tool_name} ruxsat darajasi: {level}")
                else:
                    print("  Notog'ri daraja. always_ask | always_allow | never_allow")
                continue

            if use_agent:
                try:
                    print()
                    final_result = ""
                    for event in agent.run_stream(prompt):
                        etype = event[0]
                        if etype == "status":
                            print(f"  --- {event[1]} ---")
                        elif etype == "plan_step":
                            print(f"  \u2022 {event[1]}")
                        elif etype == "thinking":
                            print(event[1], end="", flush=True)
                        elif etype == "tool_call":
                            fn_name, fn_args = event[1], event[2]
                            print(f"\n  \u2699 {fn_name}({json.dumps(fn_args)[:100]})")
                        elif etype == "tool_result":
                            fn_name, result = event[1], event[2]
                            preview = result[:200].replace("\n", "\\n")
                            print(f"  \u2713 {fn_name} -> {preview}")
                        elif etype == "reflection":
                            print(f"  \ud83d\udd0d {event[1][:200]}")
                        elif etype == "security":
                            print(f"\n  \u26a0 {event[1]}")
                        elif etype == "result":
                            final_result = event[1]
                        elif etype == "error":
                            print(f"\n  [Xato] {event[1]}")
                    if final_result:
                        print()
                        print("  \u2550\u2550\u2550 Yakuniy natija \u2550\u2550\u2550")
                        print(final_result)
                    else:
                        print()
                    last_response = final_result
                except Exception as e:
                    print(f"\n  [Agent xatosi] {e}")
            else:
                messages = [
                    {"role": "system", "content": "Sen AIDA Beta - kod yozish assistantisan. Qisqa, aniq javob ber."},
                    {"role": "user", "content": prompt},
                ]
                print()
                result = ""
                for token in llm.chat_stream(messages):
                    print(token, end="", flush=True)
                    result += token
                print()
                print()
                last_response = result

    except KeyboardInterrupt:
        print("\n  Hayr!")


def cmd_mode(args: argparse.Namespace, mode: ExecutionMode = ExecutionMode.AUTO):
    agent = Agent(mode=mode)
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
        description="AIDA Beta v2 - Terminal-based Code Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Misollar:
  aida-beta                      # Interactive REPL (agent rejimi)
  aida-beta "Hello World yoz"    # Bir martalik so'rov
  aida-beta --read file.py       # Faylni tahlil qil
  aida-beta --run "npm test"     # Buyruq bajar + tahlil
  aida-beta --mode approve ...   # Ruxsat sorab ishlash
        """
    )
    parser.add_argument("command", nargs="*", help="Bir martalik so'rov")
    parser.add_argument("--read", type=str, help="Fayl o'qish va tahlil qilish")
    parser.add_argument("--run", type=str, help="Buyruq bajarish va tahlil qilish")
    parser.add_argument("--mode", type=str, default="auto",
                        choices=["plan", "auto", "approve"],
                        help="Bajarish rejimi: plan|auto|approve")
    args = parser.parse_args()

    if not ensure_ollama():
        sys.exit(1)

    set_work_dir(Path.cwd())
    mode = ExecutionMode(args.mode)

    if args.read:
        cmd_read_mode(args.read)
    elif args.run:
        cmd_run_mode(args.run)
    elif args.command:
        cmd_mode(args, mode)
    else:
        interactive_loop()


if __name__ == "__main__":
    main()
