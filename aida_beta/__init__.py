"""AIDA Beta v2 — Standalone Code Assistant.

Claude Code / OpenAI Codex kabi terminal-based AI coding agent.

## Arxitektura:
  Foydalanuvchi → Kontekst → Reja → Vazifalar → Tools → Tekshirish → Natija

## Ishlatish:
  aida-beta                  # Interactive REPL (agent rejimi)
  aida-beta "Hello World"    # Bir martalik so'rov
  aida-beta --read file.py   # Fayl tahlil
  aida-beta --run "npm test" # Buyruq bajarish
"""

from .provider import AidaBetaProvider
from .memory import AidaBetaMemory
from .agent import Agent, LLMClient
from .tools import Tool, execute, TOOLS, set_work_dir

__version__ = "2.0.0"
__all__ = [
    "AidaBetaProvider", "AidaBetaMemory",
    "Agent", "LLMClient",
    "Tool", "execute", "TOOLS", "set_work_dir",
]
