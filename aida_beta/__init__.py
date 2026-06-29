"""AIDA Beta — Standalone Code Assistant.

Terminal-based AI coding agent (Claude Code / OpenAI Codex kabi).
Ollama backend bilan ishlaydi, lekin foydalanuvchi uchun butunlay mustaqil model.

Ishlatish:
    aida-beta                  # Interactive REPL
    aida-beta "Hello World"    # Bir martalik so'rov
    aida-beta --read file.py   # Fayl tahlil
    aida-beta --run "npm test" # Buyruq bajarish
"""

from .provider import AidaBetaProvider
from .memory import AidaBetaMemory

__version__ = "2.0.0"
__all__ = ["AidaBetaProvider", "AidaBetaMemory"]
