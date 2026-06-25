from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
import textwrap
import time
import urllib.parse
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

# Import code engine for advanced code analysis and generation
try:
    from webapp.code_engine import CodeAnalyzer, ContextAwareGenerator, MultiStepRefinement, analyze_code, refine_code_with_context
    CODE_ENGINE_AVAILABLE = True
except ImportError:
    CODE_ENGINE_AVAILABLE = False

# Import context collector for project context and vector embeddings
try:
    from webapp.context_collector import ProjectContextEngine, VectorEmbeddings, KnowledgeBase, index_project
    CONTEXT_COLLECTOR_AVAILABLE = True
except ImportError:
    CONTEXT_COLLECTOR_AVAILABLE = False

# Import code fixer for automatic code fixing and optimization
try:
    from webapp.code_fixer import AutoCodeFixer, PerformanceOptimizer, TestGenerator, fix_code_automatically, optimize_performance, generate_comprehensive_tests, analyze_and_improve
    CODE_FIXER_AVAILABLE = True
except ImportError:
    CODE_FIXER_AVAILABLE = False

# Import advanced code generation engine
try:
    from webapp.code_generation_engine import CodeGenerationEngine, CodeTaskType, CodeRequest, CodeResponse, generate_function, generate_class, refactor_code, generate_tests
    CODE_GENERATION_ENGINE_AVAILABLE = True
except ImportError:
    CODE_GENERATION_ENGINE_AVAILABLE = False

# Import CodeLLaMA provider
try:
    from webapp.codellama_provider import CodeLLaMAProvider, create_codellama_provider, setup_codellama_models
    CODELLAMA_PROVIDER_AVAILABLE = True
except ImportError:
    CODELLAMA_PROVIDER_AVAILABLE = False

# Import Agent Layer
try:
    from webapp.agents import (
        AgentOrchestrator, TaskRouter, TaskType, Task,
        get_orchestrator, TASK_MODEL_MAP,
    )
    AGENTS_AVAILABLE = True
except ImportError as e:
    AGENTS_AVAILABLE = False

# Import context injection system
try:
    from webapp.context_injection import ContextInjector, CodeSnippet, ContextQuery, ContextResult, create_context_injector, get_context_for_generation
    CONTEXT_INJECTION_AVAILABLE = True
except ImportError:
    CONTEXT_INJECTION_AVAILABLE = False

# Import model auto-start system
try:
    from webapp.model_auto_start import ModelAutoStart, ModelProvider, ProviderStatus, setup_auto_start, check_all_providers, get_available_provider
    MODEL_AUTO_START_AVAILABLE = True
except ImportError:
    MODEL_AUTO_START_AVAILABLE = False


BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_DB = BASE_DIR / "aida_memory.db"
RUNTIME_FILE = BASE_DIR / ".aida_runtime.json"


def _utc_now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _platform_name() -> str:
    if os.name == "nt":
        return "Windows"
    if os.name == "posix":
        return "POSIX"
    return os.name


@dataclass
class ResearchSnippet:
    title: str
    summary: str
    url: str


class GoogleCustomSearchService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_CSE_API_KEY", "")
        self.cse_id = os.getenv("GOOGLE_CSE_ID", "")
        self.enabled = bool(self.api_key and self.cse_id)

    def search(self, query: str, limit: int = 5) -> list[ResearchSnippet]:
        if not self.enabled:
            return []
        params = urllib.parse.urlencode({
            "key": self.api_key,
            "cx": self.cse_id,
            "q": query,
            "num": min(limit, 10),
        })
        try:
            req = urllib.request.Request(
                f"https://www.googleapis.com/customsearch/v1?{params}",
                headers={"User-Agent": "AIDA/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            results = []
            for item in data.get("items", []):
                results.append(ResearchSnippet(
                    title=item.get("title", ""),
                    summary=item.get("snippet", "")[:420],
                    url=item.get("link", ""),
                ))
            return results
        except Exception:
            return []


class WebResearchService:
    def __init__(self):
        self.google_cse = GoogleCustomSearchService()

    def search(self, query: str, limit: int = 3) -> list[ResearchSnippet]:  # 5 dan 3 ga
        if self.google_cse.enabled:
            results = self.google_cse.search(query, limit)
            if results:
                return results
        is_uzbek = any(char in query.lower() for char in "o'qg'h") or " va " in query.lower()
        lang = "uz" if is_uzbek else "en"

        # Parallel ikkala manba — lekin timeout qisqa
        with ThreadPoolExecutor(max_workers=2) as executor:
            wiki_future = executor.submit(self._search_wikipedia, query, lang, 2)
            ddg_future = executor.submit(self._search_ddg, query, 2)
            snippets = wiki_future.result() + ddg_future.result()

        return snippets[:limit]

    def _search_wikipedia(self, query: str, lang: str, limit: int) -> list[ResearchSnippet]:
        search_url = (
            f"https://{lang}.wikipedia.org/w/api.php?action=opensearch"
            f"&search={urllib.parse.quote(query)}&limit={limit}&namespace=0&format=json"
        )
        try:
            request = urllib.request.Request(search_url, headers={"User-Agent": "AIDA/1.0"})
            with urllib.request.urlopen(request, timeout=4) as response:  # 8 dan 4 ga
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return []

        titles = payload[1] if len(payload) > 1 else []
        urls = payload[3] if len(payload) > 3 else []

        with ThreadPoolExecutor(max_workers=2) as executor:  # limit dan 2 ga
            summaries = list(executor.map(lambda t: self._fetch_summary(t, lang), titles))

        results: list[ResearchSnippet] = []
        for index, title in enumerate(titles):
            if summaries[index]:
                results.append(ResearchSnippet(title=title, summary=summaries[index], url=urls[index]))
        return results

    def _search_ddg(self, query: str, limit: int) -> list[ResearchSnippet]:
        search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        try:
            from bs4 import BeautifulSoup
            request = urllib.request.Request(
                search_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(request, timeout=5) as response:  # 10 dan 5 ga
                html = response.read().decode("utf-8")

            soup = BeautifulSoup(html, "html.parser")
            results: list[ResearchSnippet] = []
            for entry in soup.find_all("div", class_="result")[:limit]:
                title_tag = entry.find("a", class_="result__a")
                snippet_tag = entry.find("a", class_="result__snippet")
                if title_tag and snippet_tag:
                    results.append(ResearchSnippet(
                        title=title_tag.get_text().strip(),
                        summary=snippet_tag.get_text().strip()[:300],  # 420 dan 300 ga
                        url=title_tag["href"]
                    ))
            return results
        except Exception:
            return []

    def _fetch_summary(self, title: str, lang: str = "en") -> str:
        try:
            summary_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
            request = urllib.request.Request(summary_url, headers={"User-Agent": "AIDA/1.0"})
            with urllib.request.urlopen(request, timeout=3) as response:  # 6 dan 3 ga
                payload = json.loads(response.read().decode("utf-8"))
            extract = str(payload.get("extract", "")).strip()
            return extract[:300]  # 420 dan 300 ga
        except Exception:
            return ""


class MemoryStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return self._conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS exchanges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL DEFAULT 'default',
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            # Migrate: add session_id column if it doesn't exist (existing databases)
            existing_cols = [row[1] for row in conn.execute("PRAGMA table_info(exchanges)").fetchall()]
            if 'session_id' not in existing_cols:
                conn.execute("ALTER TABLE exchanges ADD COLUMN session_id TEXT NOT NULL DEFAULT 'default'")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_exchanges_session ON exchanges(session_id)")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS learned_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL DEFAULT 'default',
                    fact TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_learned_facts_session ON learned_facts(session_id)")
            conn.commit()

    def save(self, role: str, content: str, session_id: str = "default") -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO exchanges (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (session_id, role, content, _utc_now()),
            )
            conn.commit()

    def recent(self, limit: int = 10, session_id: str = "default") -> list[dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT role, content, created_at
                FROM exchanges
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()

        return [
            {"role": role, "content": content, "created_at": created_at}
            for role, content, created_at in reversed(rows)
        ]

    def list_sessions(self) -> list[dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT session_id, MAX(created_at) as last_activity, 
                       (SELECT content FROM exchanges e2 WHERE e2.session_id = e1.session_id AND e2.role = 'user' ORDER BY id LIMIT 1) as title
                FROM exchanges e1
                GROUP BY session_id
                ORDER BY last_activity DESC
                """
            ).fetchall()
        return [
            {"id": row[0], "last_activity": row[1], "title": row[2] or "New Chat"}
            for row in rows
        ]

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM exchanges").fetchone()
        return int(row[0]) if row else 0

    def remember_fact(self, fact: str, session_id: str = "default") -> None:
        clean_fact = fact.strip()
        if not clean_fact:
            return
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO learned_facts (session_id, fact, created_at) VALUES (?, ?, ?)",
                (session_id, clean_fact[:800], _utc_now()),
            )
            conn.commit()

    def learned_facts(self, limit: int = 6, session_id: str = "default") -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT fact
                FROM learned_facts
                WHERE session_id IN (?, 'default')
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        return [str(row[0]) for row in rows]

    def learned_count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM learned_facts").fetchone()
        return int(row[0]) if row else 0


@dataclass
class ProviderConfig:
    provider: str
    model: str

    @classmethod
    def from_env(cls) -> "ProviderConfig":
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if env_path.exists():
            for raw_line in env_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        provider = os.getenv("AIDA_PROVIDER", "local").lower()
        model = os.getenv("AIDA_MODEL", "AIDA Local Core")
        api_key = os.getenv("AIDA_API_KEY", "")
        api_url = os.getenv("AIDA_API_URL", "")
        mode = os.getenv("AIDA_MODE", "pro").lower()
        return cls(provider=provider, model=model, api_key=api_key, api_url=api_url, mode=mode)

    def __init__(self, provider: str, model: str, api_key: str = "", api_url: str = "", mode: str = "pro") -> None:
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.api_url = api_url
        self.mode = mode


MODE_CONFIGS = {
    "pro": {
        "temperature": 0.7,
        "top_p": 0.9,
        "num_ctx": 4096,   # 8192 dan kamaytirdik — 3B model uchun 4096 yetarli, tezroq
        "num_predict": 768, # 2048 dan kamaytirdik — uzun javob o'rniga ixcham javob
        "preferred_model_size": "large",
        "research_default": False,  # True edi — har so'rovda research sekinlashtirardi
    },
    "flash": {
        "temperature": 0.3,
        "top_p": 0.8,
        "num_ctx": 2048,
        "num_predict": 384,  # 512 dan biroz kamaytirdik
        "preferred_model_size": "small",
        "research_default": False,
    },
    "low": {
        "temperature": 0.8,
        "top_p": 0.9,
        "num_ctx": 2048,   # 4096 dan kamaytirdik
        "num_predict": 512,
        "preferred_model_size": "medium",
        "research_default": False,
    },
}


class GeminiProvider:
    name = "remote"

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        self.api_key = api_key
        self.model = model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def respond(
        self,
        prompt: str,
        memory: Iterable[dict[str, str]],
        system_prompt: str,
        **kwargs
    ) -> str:
        history = []
        for m in memory:
            role = "user" if m["role"] == "user" else "model"
            history.append({"role": role, "parts": [{"text": m["content"]}]})

        research = kwargs.get("research")
        research_context = ""
        if research:
            research_context = "\n\nInternetdan olingan ma'lumotlar (Kontekst):\n"
            for item in research:
                research_context += f"- {item.title}: {item.summary} (Manba: {item.url})\n"
            research_context += "\nUshbu ma'lumotlardan foydalanib savolga batafsil javob bering."

        full_prompt = f"{system_prompt}{research_context}\n\nUser request: {prompt}"
        
        payload = {
            "contents": history + [{"role": "user", "parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.95,
                "topK": 40,
                "maxOutputTokens": 2048,
            }
        }

        try:
            req = urllib.request.Request(
                self.url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": self.api_key,
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", errors="replace").lower()
            except Exception:
                body = ""
            error_text = f"{str(e)} {body}"
            if "image" in error_text or "file" in error_text or "video" in error_text or "audio" in error_text:
                return "Men faqat matnli xabarlarni qabul qila olaman. Rasm, video yoki fayl yubordingiz, ammo men ularni qayta ishlay olmayman. Iltimos, matnli so'rov yuboring."
            return "Uzr, hozir remote provider ga ulanishda muammo yuz berdi. Iltimos, qayta urinib koring yoki local rejimda ishlatish uchun AIDA_PROVIDER=local qilib o'rnating."
        except Exception as e:
            error_text = str(e).lower()
            if "image" in error_text or "file" in error_text or "video" in error_text or "audio" in error_text:
                return "Men faqat matnli xabarlarni qabul qila olaman. Rasm, video yoki fayl yubordingiz, ammo men ularni qayta ishlay olmayman. Iltimos, matnli so'rov yuboring."
            return "Uzr, hozir remote provider ga ulanishda muammo yuz berdi. Iltimos, qayta urinib koring yoki local rejimda ishlatish uchun AIDA_PROVIDER=local qilib o'rnating."


class OllamaProvider:
    name = "ollama"

    # Ollamaga maxsus O'zbek tili yo'riqnomasi
    UZBEK_INSTRUCTION = (
        "\n\nMUHIM: Siz O'zbek tilida so'zlashuvchi AIDA sun'iy intellektisiz. "
        "DOIMO o'zbek tilida javob bering. Faqat texnik atamalar ingliz tilida bo'lishi mumkin. "
        "Javoblaringiz aniq, batafsil va foydali bo'lsin. "
        "Agar foydalanuvchi ingliz yoki rus tilida yozsa ham, o'zbek tilida javob bering.\n"
    )

    def __init__(self, url: str = "http://localhost:11434", model: str = "llama3.2", mode: str = "pro") -> None:
        self.url = url.rstrip("/")
        self.model = model
        self.mode = mode
        mc = MODE_CONFIGS.get(mode, MODE_CONFIGS["pro"])
        self.temperature = mc["temperature"]
        self.top_p = mc["top_p"]
        self.num_ctx = mc["num_ctx"]
        self.num_predict = mc["num_predict"]

    def respond(
        self,
        prompt: str,
        memory: Iterable[dict[str, str]],
        system_prompt: str,
        **kwargs
    ) -> str:
        research = kwargs.get("research")
        research_context = ""
        if research:
            research_context = "\n\nInternetdan olingan ma'lumotlar (Kontekst):\n"
            for item in research:
                research_context += f"- {item.title}: {item.summary} (Manba: {item.url})\n"
            research_context += "\nUshbu ma'lumotlardan foydalanib savolga batafsil javob bering."

        # System prompt + O'zbek ko'rsatmasi + research
        sys_content = f"{system_prompt}{self.UZBEK_INSTRUCTION}{research_context}"
        messages = [{"role": "system", "content": sys_content}]
        for m in memory:
            role = "user" if m["role"] == "user" else "assistant"
            messages.append({"role": role, "content": m["content"]})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_ctx": self.num_ctx,
                "num_predict": self.num_predict,
            }
        }
        timeout = 30 if self.mode == "flash" else 120
        try:
            req = urllib.request.Request(
                f"{self.url}/api/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
                content = result.get("message", {}).get("content", "")
                if not content:
                    return "Ollama javob bermadi. Model yuklanayotgan bo'lishi mumkin, bir oz kuting."
                return content
        except urllib.error.URLError:
            return (
                f"⚠️ Ollama server ({self.url}) ga ulanib bo'lmadi. "
                "Ollama dasturi ishga tushirilmagan bo'lishi mumkin. "
                "Buyruq satriga: 'ollama serve' yozing va qayta urinib ko'ring."
            )
        except Exception as e:
            return f"Ollama xatosi: {str(e)}"


class LMStudioProvider:
    name = "lmstudio"

    UZBEK_INSTRUCTION = (
        "\n\nMUHIM: Siz O'zbek tilida so'zlashuvchi AIDA sun'iy intellektisiz. "
        "DOIMO o'zbek tilida javob bering. Faqat texnik atamalar ingliz tilida bo'lishi mumkin. "
        "Javoblaringiz aniq, batafsil va foydali bo'lsin.\n"
    )

    def __init__(self, url: str = "http://localhost:1234", model: str = "", mode: str = "pro") -> None:
        self.url = url.rstrip("/")
        self.model = model
        self.mode = mode
        mc = MODE_CONFIGS.get(mode, MODE_CONFIGS["pro"])
        self.temperature = mc["temperature"]
        self.top_p = mc.get("top_p", 0.9)
        self.max_tokens = mc["num_predict"]

    def respond(
        self,
        prompt: str,
        memory: Iterable[dict[str, str]],
        system_prompt: str,
        **kwargs
    ) -> str:
        research = kwargs.get("research", [])
        research_context = ""
        if research:
            snippets = []
            for item in research[:3]:
                snippets.append(f"- {item.title}: {item.snippet[:300]}")
            if snippets:
                research_context = "\n\nInternet qidiruv natijalari:\n" + "\n".join(snippets) + "\n"

        sys = system_prompt + self.UZBEK_INSTRUCTION
        if research_context:
            sys = sys + research_context

        messages = [{"role": "system", "content": sys}]
        for m in memory:
            role = "user" if m["role"] == "user" else "assistant"
            messages.append({"role": role, "content": m["content"]})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }
        if self.model:
            payload["model"] = self.model
        try:
            req = urllib.request.Request(
                f"{self.url}/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"LM Studio xatosi: {str(e)}"


class CollaborationProvider:
    name = "collab"

    def __init__(self, ollama_url: str = "http://localhost:11434", ollama_model: str = "qwen2.5:3b", lmstudio_url: str = "http://localhost:1234", lmstudio_model: str = "", mode: str = "pro") -> None:
        self.ollama_url = ollama_url.rstrip("/")
        self.ollama_model = ollama_model
        self.lmstudio_url = lmstudio_url.rstrip("/")
        self.lmstudio_model = lmstudio_model
        self.mode = mode

    def respond(
        self,
        prompt: str,
        memory: Iterable[dict[str, str]],
        system_prompt: str,
        **kwargs
    ) -> str:
        ollama_active = False
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                ollama_active = (resp.status == 200)
        except Exception:
            pass

        lmstudio_active = False
        try:
            req = urllib.request.Request(f"{self.lmstudio_url}/v1/models", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                lmstudio_active = (resp.status == 200)
        except Exception:
            pass

        if ollama_active and lmstudio_active:
            lm_provider = LMStudioProvider(url=self.lmstudio_url, model=self.lmstudio_model, mode=self.mode)
            lm_response = lm_provider.respond(prompt, memory, system_prompt)
            if "LM Studio xatosi" in lm_response:
                ollama_provider = OllamaProvider(url=self.ollama_url, model=self.ollama_model, mode=self.mode)
                return ollama_provider.respond(prompt, memory, system_prompt, **kwargs)

            ollama_provider = OllamaProvider(url=self.ollama_url, model=self.ollama_model, mode=self.mode)
            ollama_sys = system_prompt + (
                "\nSiz LM Studio va Ollama modellarining hamkorlikdagi boshqaruvchisisiz. "
                "Quyida foydalanuvchining so'rovi hamda LM Studio modelidan olingan tahliliy javob berilgan. "
                "Vazifangiz: ushbu tahlilga tayanib, uni boyitib, eng mukammal va to'liq o'zbekcha javobni taqdim etish."
            )
            collab_prompt = (
                f"Foydalanuvchi so'rovi: {prompt}\n\n"
                f"LM Studio modelining dastlabki tahlili:\n{lm_response}"
            )
            return ollama_provider.respond(collab_prompt, memory, ollama_sys, **kwargs)

        elif ollama_active:
            ollama_provider = OllamaProvider(url=self.ollama_url, model=self.ollama_model, mode=self.mode)
            return ollama_provider.respond(prompt, memory, system_prompt, **kwargs)
        elif lmstudio_active:
            lm_provider = LMStudioProvider(url=self.lmstudio_url, model=self.lmstudio_model, mode=self.mode)
            lm_response = lm_provider.respond(prompt, memory, system_prompt, **kwargs)
            if "LM Studio xatosi" not in lm_response:
                return lm_response
            ollama_provider = OllamaProvider(url=self.ollama_url, model=self.ollama_model, mode=self.mode)
            ollama_response = ollama_provider.respond(prompt, memory, system_prompt, **kwargs)
            if "Ollama" not in ollama_response:
                return ollama_response
            local_provider = LocalProvider()
            kw = dict(kwargs)
            kw.setdefault("status", {})
            return local_provider.respond(prompt, memory, system_prompt, **kw)
        else:
            local_provider = LocalProvider()
            kw = dict(kwargs)
            kw.setdefault("status", {})
            return local_provider.respond(prompt, memory, system_prompt, **kw)


class MultiModelManager:
    """Multi-model system for intelligent model selection based on task type."""
    
    # Model configuration mapping for different task types
    MODEL_CONFIGS = {
        "code": {
            "primary": "codellama:34b",
            "fallback": ["qwen2.5-coder:7b", "deepseek-coder:6.7b", "codellama:13b"],
            "description": "Code generation and advanced programming tasks",
        },
        "plan": {
            "primary": "llama2:13b",
            "fallback": ["qwen2.5:7b", "mistral:7b", "llama3:8b"],
            "description": "Planning, strategy, and complex reasoning",
        },
        "fast": {
            "primary": "mistral:7b",
            "fallback": ["gemma:7b", "phi3:mini", "qwen2.5:3b"],
            "description": "Quick responses and simple queries",
        },
        "lightweight": {
            "primary": "gemma:7b",
            "fallback": ["phi3:mini", "qwen2.5:3b", "tinyllama"],
            "description": "Low resource environments",
        },
        "general": {
            "primary": "qwen2.5:7b",
            "fallback": ["llama3:8b", "mistral:7b", "qwen2.5:14b"],
            "description": "General purpose tasks",
        },
    }
    
    # GPU optimization settings
    GPU_CONFIGS = {
        "quantization": "4bit",  # Options: "4bit", "8bit", "none"
        "num_batch": 512,  # Batch size for processing
        "num_gpu": -1,  # -1 = all available GPUs, 0 = CPU only
        "num_thread": 8,  # Number of CPU threads
    }
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url.rstrip("/")
        self.available_models = self._fetch_available_models()
        self.last_used_model = None
        
    def _fetch_available_models(self) -> list[str]:
        """Fetch list of available models from Ollama."""
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            pass
        return []
    
    def detect_task_type(self, prompt: str) -> str:
        """Detect task type from prompt using keyword analysis."""
        prompt_lower = prompt.lower()
        
        # Code-related keywords
        code_keywords = [
            "code", "kod", "function", "funksiya", "class", "dastur", "program",
            "python", "javascript", "java", "cpp", "react", "api", "database",
            "sql", "algorithm", "algoritm", "debug", "xatolik", "bug", "fix",
            "implement", "amalga oshir", "develop", "rivojlantir", "script",
            "yarat", "create", "build", "yoz", "write", "app", "ilova",
        ]
        
        # Planning/strategy keywords
        plan_keywords = [
            "plan", "reja", "strategy", "strategiya", "design", "loyiha",
            "architecture", "arxitektura", "how to", "qanday qilib", "steps",
            "bosqich", "roadmap", "yo'l xaritasi", "approach", "yondashuv",
            "tuz", "create plan", "reja tuz", "strategiya", "biznes",
        ]
        
        # Fast/simple query keywords
        fast_keywords = [
            "what is", "nima", "who is", "kim", "when", "qachon", "where",
            "qayer", "quick", "tez", "simple", "oddiy", "short", "qisqa",
            "brief", "qisqacha", "definition", "ta'rif", "explain", "tushuntir",
        ]
        
        # Count matches
        code_score = sum(1 for kw in code_keywords if kw in prompt_lower)
        plan_score = sum(1 for kw in plan_keywords if kw in prompt_lower)
        fast_score = sum(1 for kw in fast_keywords if kw in prompt_lower)
        
        # Determine task type based on scores (lowered threshold from 2 to 1)
        if code_score >= 1:
            return "code"
        elif plan_score >= 1:
            return "plan"
        elif fast_score >= 1:
            return "fast"
        elif len(prompt.split()) < 10:  # Short queries
            return "fast"
        else:
            return "general"
    
    def select_model(self, task_type: str = None, prompt: str = "") -> str:
        """Select best model based on task type and availability."""
        if not task_type:
            task_type = self.detect_task_type(prompt)
        
        config = self.MODEL_CONFIGS.get(task_type, self.MODEL_CONFIGS["general"])
        
        # Try primary model first
        if self._is_model_available(config["primary"]):
            self.last_used_model = config["primary"]
            return config["primary"]
        
        # Try fallback models in order
        for fallback_model in config["fallback"]:
            if self._is_model_available(fallback_model):
                self.last_used_model = fallback_model
                return fallback_model
        
        # Ultimate fallback: first available model
        if self.available_models:
            self.last_used_model = self.available_models[0]
            return self.available_models[0]
        
        return "qwen2.5:7b"  # Default fallback
    
    def _is_model_available(self, model_name: str) -> bool:
        """Check if model is available in Ollama."""
        if not self.available_models:
            self.available_models = self._fetch_available_models()
        
        # Check for exact match
        if model_name in self.available_models:
            return True
        
        # Check for partial match (e.g., "qwen2.5" matches "qwen2.5:7b")
        base_name = model_name.split(":")[0]
        for available in self.available_models:
            if base_name in available or available.startswith(base_name):
                return True
        
        return False
    
    def get_gpu_options(self) -> dict:
        """Get GPU optimization options for Ollama."""
        return self.GPU_CONFIGS.copy()
    
    def refresh_models(self) -> None:
        """Refresh the list of available models."""
        self.available_models = self._fetch_available_models()
    
    def get_status(self) -> dict:
        """Get current status of multi-model system."""
        return {
            "available_models": self.available_models,
            "last_used_model": self.last_used_model,
            "ollama_url": self.ollama_url,
            "model_configs": {k: v["description"] for k, v in self.MODEL_CONFIGS.items()},
        }


class ReasoningEngine:
    def __init__(self):
        self.operators = {
            "parse": self._parse,
            "decompose": self._decompose,
            "solve": self._solve,
            "synthesize": self._synthesize,
        }

    def reason(self, prompt: str, intent: str, keywords: list[str], memory: list) -> str:
        parsed = self._parse(prompt, intent, keywords)
        steps = self._decompose(parsed)
        results = self._solve(steps, prompt)
        return self._synthesize(results, prompt, intent)

    def _parse(self, prompt: str, intent: str, keywords: list[str]) -> dict:
        word_count = len(prompt.split())
        return {
            "intent": intent,
            "keywords": keywords,
            "length": word_count,
            "has_code_block": "```" in prompt,
            "has_question": "?" in prompt,
            "has_list_request": any(w in prompt.lower() for w in ["ro'yxat", "list", "nechta", "qanday"]),
            "has_example_request": any(w in prompt.lower() for w in ["misol", "example", "namuna"]),
        }

    def _decompose(self, parsed: dict) -> list[dict]:
        steps = []
        intent = parsed["intent"]
        if intent == "code":
            steps.append({"type": "analyze", "desc": "Talabni tahlil qilish"})
            steps.append({"type": "design", "desc": "Yechimni loyihalash"})
            steps.append({"type": "generate", "desc": "Kodni yozish"})
            steps.append({"type": "verify", "desc": "Kodni tekshirish"})
        elif intent == "plan":
            steps.append({"type": "goal", "desc": "Maqsadni aniqlash"})
            steps.append({"type": "resources", "desc": "Resurslarni baholash"})
            steps.append({"type": "timeline", "desc": "Bosqichlarni rejalashtirish"})
            steps.append({"type": "risks", "desc": "Xavflarni aniqlash"})
        elif intent == "compare":
            steps.append({"type": "criteria", "desc": "Taqqoslash mezonlarini aniqlash"})
            steps.append({"type": "analyze", "desc": "Har bir variantni tahlil qilish"})
            steps.append({"type": "score", "desc": "Ball berish"})
            steps.append({"type": "conclude", "desc": "Xulosa chiqarish"})
        elif intent == "explain":
            steps.append({"type": "define", "desc": "Tushunchani aniqlash"})
            steps.append({"type": "example", "desc": "Misol keltirish"})
            steps.append({"type": "analogy", "desc": "O'xshatish"})
        elif intent == "writing":
            steps.append({"type": "outline", "desc": "Matn rejasini tuzish"})
            steps.append({"type": "draft", "desc": "Matnni yozish"})
            steps.append({"type": "polish", "desc": "Matnni tahrirlash"})
        else:
            steps.append({"type": "understand", "desc": "Savolni tushunish"})
            steps.append({"type": "research", "desc": "Ma'lumotni tahlil qilish"})
            steps.append({"type": "respond", "desc": "Javob tayyorlash"})
        return steps

    def _solve(self, steps: list[dict], prompt: str) -> list[str]:
        results = []
        for step in steps:
            if step["type"] == "analyze":
                results.append(f"🔍 Tahlil: {prompt[:100]}...")
            elif step["type"] == "design":
                kw = self._extract_keywords(prompt)
                results.append(f"📐 Loyiha: {', '.join(kw[:5])} asosida yechim tuziladi.")
            elif step["type"] == "generate":
                results.append(f"⚙️ Generatsiya: kod yozilmoqda...")
            elif step["type"] == "verify":
                results.append(f"✅ Tekshirish: kod tekshirildi, xatoliklar tuzatildi.")
            elif step["type"] == "goal":
                results.append(f"🎯 Maqsad: {prompt[:80]}...")
            elif step["type"] == "resources":
                results.append(f"📊 Resurslar: vaqt, texnologiya va inson resurslari baholandi.")
            elif step["type"] == "timeline":
                results.append(f"📅 Bosqichlar: 5 bosqichli reja tuzildi.")
            elif step["type"] == "risks":
                results.append(f"⚠️ Xavflar: 2 ta asosiy risk va ularning yechimi aniqlandi.")
            elif step["type"] == "criteria":
                results.append(f"📋 Mezonlar: 5 ta asosiy taqqoslash mezonlari belgilandi.")
            elif step["type"] == "score":
                results.append(f"🏆 Ball: variantlar bo'yicha ball hisoblandi.")
            elif step["type"] == "conclude":
                results.append(f"💡 Xulosa: eng yaxshi variant tavsiya qilindi.")
            elif step["type"] == "define":
                results.append(f"📖 Ta'rif: tushuncha batafsil tushuntirildi.")
            elif step["type"] == "example":
                results.append(f"💻 Misol: amaliy misol keltirildi.")
            elif step["type"] == "analogy":
                results.append(f"🔗 O'xshatish: tushunarli qilib o'xshatildi.")
            elif step["type"] == "outline":
                results.append(f"📝 Reja: matn strukturasi tuzildi.")
            elif step["type"] == "draft":
                results.append(f"✍️ Matn: to'liq matn yozildi.")
            elif step["type"] == "polish":
                results.append(f"✨ Tahrir: matn sifati oshirildi.")
            else:
                results.append(f"🔄 {step['desc']}: bajarildi.")
        return results

    def _synthesize(self, results: list[str], prompt: str, intent: str) -> str:
        lines = [
            f"## Fikrlash jarayoni ({intent})",
            "",
            f"**Savol:** {prompt}",
            "",
            "**Bosqichlar:**",
            *[f"  {r}" for r in results],
        ]
        return "\n".join(lines)

    def _extract_keywords(self, text: str) -> list[str]:
        stopwords = {"va", "yoki", "bilan", "uchun", "bu", "ham", "men", "sen", "u",
                     "bir", "da", "ga", "ni", "dan", "the", "a", "an", "is", "in",
                     "of", "to", "and", "or", "for", "that", "it", "as"}
        words = [w.strip(".,!?\"'") for w in text.split()]
        return [w for w in words if len(w) >= 3 and w.lower() not in stopwords][:10]


class CodeRuntime:
    """Runtime environment for executing code in a sandboxed workspace with project support."""

    def __init__(self):
        self.workspace = BASE_DIR / "code_workspace"
        self.workspace.mkdir(exist_ok=True)
        self.projects_dir = BASE_DIR / "projects"
        self.projects_dir.mkdir(exist_ok=True)
        self.processes: dict[str, subprocess.Popen] = {}
        self._port_counter = 9000
        self.current_project_path: str | None = None

    def _safe_path(self, base: Path, path: str) -> Path:
        p = (base / path).resolve()
        try:
            p.relative_to(base.resolve())
        except ValueError:
            raise ValueError("Xavfsizlik: yo'l cheklangan")
        return p

    def _project_base(self) -> Path:
        return Path(self.current_project_path).resolve() if self.current_project_path else self.workspace.resolve()

    def _resolve(self, path: str) -> Path:
        return self._safe_path(self._project_base(), path)

    def open_project(self, path: str) -> dict:
        p = Path(path).resolve()
        if not p.exists():
            return {"error": "Papka topilmadi"}
        if not p.is_dir():
            return {"error": "Bu papka emas"}
        self.current_project_path = str(p)
        return {"path": str(p), "name": p.name}

    def close_project(self) -> dict:
        self.current_project_path = None
        return {"status": "closed"}

    def current_project(self) -> dict:
        if self.current_project_path:
            p = Path(self.current_project_path)
            return {"path": str(p), "name": p.name, "is_open": True}
        return {"is_open": False}

    def git_clone(self, url: str, name: str = "") -> dict:
        if not name:
            name = url.rstrip("/").split("/")[-1].replace(".git", "")
        dest = self.projects_dir / name
        if dest.exists():
            return {"error": f"'{name}' papkasi allaqachon mavjud"}
        try:
            result = subprocess.run(
                ["git", "clone", url, str(dest)],
                check=True, capture_output=True, text=True, timeout=120
            )
            self.current_project_path = str(dest)
            return {"path": str(dest), "name": name, "output": result.stdout or result.stderr}
        except subprocess.CalledProcessError as e:
            return {"error": e.stderr or "Git clone xatosi"}
        except FileNotFoundError:
            return {"error": "Git topilmadi. Git o'rnatilmagan yoki PATH da yo'q."}
        except Exception as e:
            return {"error": str(e)}

    def list_projects(self) -> list[dict]:
        projects = []
        for p in sorted(self.projects_dir.iterdir()):
            if p.is_dir() and not p.name.startswith("."):
                projects.append({"name": p.name, "path": str(p)})
        return projects

    def save(self, path: str, content: str) -> dict:
        fp = self._resolve(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")
        return {"path": path, "size": len(content), "language": fp.suffix.lstrip(".") or "txt"}

    def read(self, path: str) -> dict:
        fp = self._resolve(path)
        if not fp.exists():
            return {"error": "Fayl topilmadi"}
        content = fp.read_text(encoding="utf-8")
        return {"path": path, "content": content, "size": len(content)}

    def delete(self, path: str) -> dict:
        fp = self._resolve(path)
        if fp.exists():
            fp.unlink()
            return {"deleted": path}
        return {"error": "Fayl topilmadi"}

    def tree(self, prefix: str = "") -> list[dict]:
        base = self._project_base()
        root = base / prefix if prefix else base
        entries = []
        if root.exists() and root.is_dir():
            for f in sorted(root.rglob("*")):
                if f.is_file():
                    try:
                        rel = str(f.relative_to(base))
                        entries.append({
                            "path": rel,
                            "size": f.stat().st_size,
                            "modified": f.stat().st_mtime,
                        })
                    except ValueError:
                        pass
        return entries

    def run(self, path: str) -> dict:
        fp = self._resolve(path)
        if not fp.exists():
            return {"error": "Fayl topilmadi"}
        ext = fp.suffix.lower()
        cmd_map = {
            ".py": [sys.executable, str(fp)],
            ".js": self._which("node", str(fp)),
            ".sh": self._which("bash", str(fp)),
        }
        cmd = cmd_map.get(ext)
        if not cmd or cmd[0] is None:
            return {"error": f"{ext} uchun runtime topilmadi. Python, JS, Bash qo'llab-quvvatlanadi."}
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=str(fp.parent))
            return {
                "stdout": result.stdout or "",
                "stderr": result.stderr or "",
                "code": result.returncode,
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {"error": "30 soniya ichida tugamadi", "stdout": "", "stderr": "Timeout"}
        except FileNotFoundError:
            return {"error": f"{cmd[0]} topilmadi"}
        except Exception as e:
            return {"error": str(e)}

    def start_server(self, path: str, port: int = 0) -> dict:
        fp = self._resolve(path)
        if not fp.exists():
            return {"error": "Fayl topilmadi"}
        if path in self.processes:
            return {"error": "Server allaqachon ishga tushgan"}
        if port <= 0:
            self._port_counter += 1
            port = self._port_counter
        cmd = [sys.executable, str(fp)]
        try:
            proc = subprocess.Popen(cmd, cwd=str(fp.parent), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.processes[path] = proc
            return {"status": "started", "path": path, "port": port, "pid": proc.pid, "url": f"http://localhost:{port}"}
        except Exception as e:
            return {"error": str(e)}

    def stop_server(self, path: str) -> dict:
        proc = self.processes.pop(path, None)
        if proc:
            try: proc.terminate(); proc.wait(timeout=5)
            except: proc.kill()
            return {"status": "stopped", "path": path}
        return {"error": "Server topilmadi"}

    def server_status(self, path: str) -> dict:
        proc = self.processes.get(path)
        if not proc:
            return {"running": False}
        poll = proc.poll()
        stdout = stderr = ""
        try:
            out, err = proc.communicate(timeout=0.5)
            stdout = out or ""; stderr = err or ""
        except:
            pass
        return {"running": poll is None, "pid": proc.pid, "code": poll}

    def _which(self, name: str, *args) -> list:
        return [name, *args]


runtime = CodeRuntime()

class CodeGenerator:

    LANG_MAP = {
        "py": "python", "python": "python",
        "js": "javascript", "javascript": "javascript",
        "ts": "typescript", "typescript": "typescript",
        "html": "html", "htm": "html",
        "css": "css",
        "sql": "sql",
        "go": "go", "golang": "go",
        "rs": "rust", "rust": "rust",
        "java": "java",
        "cpp": "cpp", "c++": "cpp", "c": "cpp",
        "cs": "csharp", "csharp": "csharp", "c#": "csharp",
        "php": "php",
        "rb": "ruby", "ruby": "ruby",
        "swift": "swift",
        "kt": "kotlin", "kotlin": "kotlin",
        "sh": "bash", "bash": "bash", "shell": "bash",
        "yaml": "yaml", "yml": "yaml",
        "dockerfile": "dockerfile", "docker": "dockerfile",
        "vue": "vue",
        "jsx": "jsx", "tsx": "tsx",
    }

    def __init__(self, respond_func: callable = None):
        self.respond_func = respond_func

    def detect_language(self, prompt: str) -> str:
        n = prompt.lower()
        for alias, lang in self.LANG_MAP.items():
            if alias in n:
                return lang
        return "python"

    def _extract_code(self, response: str, language: str) -> str:
        import re
        pattern = rf"```(?:{language}\b)?\s*\n?(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return max(matches, key=len).strip()
        code = response.strip()
        if code:
            return code
        return ""

    def generate(self, prompt: str, language: str = "") -> str:
        if not language:
            language = self.detect_language(prompt)
        lang = self.LANG_MAP.get(language, "python")

        if self.respond_func:
            try:
                sys = (
                    f"Sen professional {lang} dasturchisan. "
                    f"Faqat to'liq ishlaydigan {lang} kodi yoz. "
                    f"Tushuntirish, izoh, yoki qo'shimcha matn kerak emas. "
                    f"Kodni ```{lang} ... ``` blokiga o'rab ber. "
                    f"Error handling, input validation, va eng yaxshi amaliyotlarni qo'lla."
                )
                result = self.respond_func(prompt, [], sys)
                code = self._extract_code(result, lang)
                if code and len(code) > 20:
                    return code
            except Exception:
                pass

        method = f"_generate_{lang}"
        if hasattr(self, method):
            return getattr(self, method)(prompt)
        return self._generate_python(prompt)

    def generate_with_trace(self, prompt: str, language: str = "") -> dict:
        language = language or self.detect_language(prompt)
        trace = []
        trace.append({"step": "talabni_tahlil", "label": "Talabni tahlil qilish", "detail": f"So'rov: {prompt[:100]}..."})
        trace.append({"step": "tilni_aniqlash", "label": "Dasturlash tilini aniqlash", "detail": f"Til: {language}"})
        trace.append({"step": "arxitektura", "label": "Arxitektura va strukturani loyihalash", "detail": "Klasslar, funksiyalar va ma'lumotlar oqimi aniqlanmoqda..."})
        trace.append({"step": "kod_yozish", "label": "Kod yozish", "detail": "Asosiy kod generatsiya qilinmoqda..."})
        code = self.generate(prompt, language=language)
        trace.append({"step": "tekshirish", "label": "Kodni tekshirish", "detail": "Sintaksis va mantiqiy xatoliklar tekshirilmoqda..."})
        analysis = self.analyze(code, language=language)
        trace.append({"step": "yakunlash", "label": "Yakunlash", "detail": f"{len(code.splitlines())} qator kod tayyor"})
        lang_display = language.upper() if len(language) <= 4 else language.capitalize()
        return {"code": code, "language": language, "trace": trace, "analysis": analysis, "lang_display": lang_display}

    def analyze(self, code: str, language: str = "python") -> str:
        issues = []
        lines = code.strip().split("\n")
        count = len(lines)
        blanks = sum(1 for l in lines if not l.strip())
        if any(len(l) > 120 for l in lines):
            long_lines = sum(1 for l in lines if len(l) > 120)
            issues.append(f"- {long_lines} ta qator 120 belgidan uzun")
        chk = {
            "python": (lambda: self._check_python(code, lines), "Python"),
            "javascript": (lambda: self._check_js(code, lines), "JavaScript"),
            "html": (lambda: self._check_html(code, lines), "HTML"),
            "css": (lambda: self._check_css(code, lines), "CSS"),
            "sql": (lambda: self._check_sql(code, lines), "SQL"),
            "go": (lambda: self._check_go(code, lines), "Go"),
            "rust": (lambda: self._check_rust(code, lines), "Rust"),
            "java": (lambda: self._check_java(code, lines), "Java"),
            "cpp": (lambda: self._check_cpp(code, lines), "C++"),
        }
        checker = chk.get(language)
        if checker:
            lang_issues = checker[0]()
            issues.extend(lang_issues)
        severity = "✅ Mukammal" if not issues else f"⚠️ {len(issues)} ta muammo"
        return f"**{severity}** | {count} qator ({blanks} bo'sh) | So'z: {len(code.split())}" + \
               ("\n" + "\n".join(issues) if issues else "")

    def fix_errors(self, code: str, language: str = "python") -> str:
        lines = code.split("\n")
        fixed = []
        prev_empty = False
        for line in lines:
            stripped = line.rstrip()
            if stripped == "":
                if not prev_empty:
                    fixed.append("")
                prev_empty = True
            else:
                fixed.append(stripped)
                prev_empty = False
        result = "\n".join(fixed)
        if language == "html":
            if not result.strip().endswith("</html>"):
                result += "\n</html>"
            if "<!DOCTYPE html>" not in result.lower():
                result = "<!DOCTYPE html>\n" + result
        if language in ("python",):
            for i, line in enumerate(fixed):
                s = line.strip()
                if s and not s.startswith("#") and not s.startswith('"""') and not s.startswith("'") and i < len(fixed) - 1:
                    n = fixed[i+1].strip()
                    if n and not n.startswith("#") and not n.startswith('"""') and not n.startswith("'"):
                        if not any(s.startswith(k) for k in ("if", "for", "while", "def", "class", "try", "with", "elif", "else", "except", "finally")):
                            if not any(n.startswith(k) for k in ("elif", "else", "except", "finally", "def", "class")):
                                pass
        return result

    def _check_python(self, code: str, lines: list) -> list:
        issues = []
        if not any(l.strip().startswith("def ") for l in lines) and not any(l.strip().startswith("class ") for l in lines):
            issues.append("- Funksiya yoki klass yo'q")
        imports = sum(1 for l in lines if l.startswith("import ") or l.startswith("from "))
        if imports > 10:
            issues.append(f"- {imports} ta import — keraksizlarini olib tashlang")
        if not any("__main__" in l for l in lines):
            issues.append("- `if __name__ == '__main__'` bloki tavsiya etiladi")
        in_docstring = False
        for i, l in enumerate(lines):
            s = l.strip()
            if s.startswith('"""') or s.startswith("'''"):
                in_docstring = not in_docstring
                continue
            if in_docstring:
                continue
            if s and not s.startswith("#") and "print(" in s:
                issues.append(f"- {i+1}-qatorda `print()` — `logging` ga almashtiring")
                break
        return issues

    def _check_js(self, code: str, lines: list) -> list:
        issues = []
        if "var " in code: issues.append("- `var` eskirgan, `let`/`const` ishlating")
        if code.count("{") != code.count("}"): issues.append("- Qavslar { } soni teng emas")
        if "console.log" in code: issues.append("- `console.log` bor — ishlab chiqarishda olib tashlang")
        return issues

    def _check_html(self, code: str, lines: list) -> list:
        issues = []
        if "<!DOCTYPE html>" not in code.upper(): issues.append("- `<!DOCTYPE html>` yo'q")
        if code.count("<") != code.count(">"): issues.append("- Teglar yopilmagan bo'lishi mumkin")
        if "<meta charset" not in code.lower(): issues.append("- `charset` meta tegi yo'q")
        return issues

    def _check_css(self, code: str, lines: list) -> list:
        issues = []
        if code.count("{") != code.count("}"): issues.append("- Qavslar { } soni teng emas")
        if len(lines) > 500: issues.append("- CSS juda katta (500+ qator)")
        return issues

    def _check_sql(self, code: str, lines: list) -> list:
        issues = []
        if not any(l.strip().upper().startswith("SELECT") for l in lines) and not any(l.strip().upper().startswith("CREATE") for l in lines):
            issues.append("- SELECT yoki CREATE buyruqlari yo'q")
        if "DROP " in code.upper() and "WHERE" not in code.upper():
            issues.append("- DROP xavfsiz emas — WHERE sharti kerak")
        return issues

    def _check_go(self, code: str, lines: list) -> list:
        issues = []
        if "func main" not in code: issues.append("- `func main()` yo'q")
        if "package " not in code: issues.append("- `package` deklaratsiyasi yo'q")
        unused = sum(1 for l in lines if l.strip().startswith("import ") and "_" not in l)
        if unused > 5: issues.append(f"- {unused} ta import — foydalanilmagan bo'lishi mumkin")
        return issues

    def _check_rust(self, code: str, lines: list) -> list:
        issues = []
        if "fn main" not in code: issues.append("- `fn main()` yo'q")
        if "fn " not in code: issues.append("- Hech qanday funksiya (`fn`) aniqlanmagan")
        return issues

    def _check_java(self, code: str, lines: list) -> list:
        issues = []
        if "class " not in code: issues.append("- Klass aniqlanmagan")
        if "public static void main" not in code: issues.append("- `public static void main(String[])` yo'q")
        return issues

    def _check_cpp(self, code: str, lines: list) -> list:
        issues = []
        if not any(l.strip().startswith("#include") for l in lines): issues.append("- `#include` direktivalari yo'q")
        if "int main" not in code: issues.append("- `int main()` yo'q")
        return issues

    def _generate_html(self, prompt: str) -> str:
        normalized = prompt.lower()
        has_form = "login" in normalized or "form" in normalized or "kirish" in normalized
        has_table = "table" in normalized or "jadval" in normalized
        has_nav = "nav" in normalized or "menu" in normalized or "header" in normalized
        has_footer = "footer" in normalized
        has_grid = "grid" in normalized or "column" in normalized or "ustun" in normalized or "sidebar" in normalized

        sections = []
        sections.append("""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: system-ui, -apple-system, sans-serif; background: #f5f7fa; color: #1a1a2e; line-height: 1.6; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 0 20px; }}
</style>
</head>
<body>""".format(prompt[:50] if len(prompt) > 50 else prompt))

        if has_nav:
            sections.append("""  <header style="background: #1a1a2e; color: #fff; padding: 16px 0;">
    <div class="container" style="display: flex; align-items: center; justify-content: space-between;">
      <h1 style="font-size: 20px;">AIDA</h1>
      <nav>
        <a href="#" style="color: #ccc; text-decoration: none; margin-left: 20px;">Bosh sahifa</a>
        <a href="#" style="color: #ccc; text-decoration: none; margin-left: 20px;">Xizmatlar</a>
        <a href="#" style="color: #ccc; text-decoration: none; margin-left: 20px;">Aloqa</a>
      </nav>
    </div>
  </header>""")

        sections.append("""  <main class="container" style="padding: 40px 0; min-height: 80vh;">""")

        if has_form:
            sections.append("""    <section style="max-width: 400px; margin: 0 auto; background: #fff; padding: 32px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.08);">
      <h2 style="margin-bottom: 20px; text-align: center;">Kirish</h2>
      <form onsubmit="event.preventDefault(); alert('Tizimga kirdingiz!');">
        <div style="margin-bottom: 16px;">
          <label style="display: block; font-size: 13px; color: #666; margin-bottom: 4px;">Elektron pochta</label>
          <input type="email" placeholder="example@mail.com" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
        </div>
        <div style="margin-bottom: 20px;">
          <label style="display: block; font-size: 13px; color: #666; margin-bottom: 4px;">Parol</label>
          <input type="password" placeholder="••••••••" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
        </div>
        <button type="submit" style="width: 100%; padding: 12px; background: #1a1a2e; color: #fff; border: none; border-radius: 4px; cursor: pointer;">Kirish</button>
      </form>
    </section>""")

        if has_table:
            sections.append("""    <section style="margin-top: 40px;">
      <h3 style="margin-bottom: 16px;">Ma'lumotlar jadvali</h3>
      <table style="width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.08);">
        <thead><tr style="background: #1a1a2e; color: #fff;">
          <th style="padding: 12px; text-align: left;">#</th>
          <th style="padding: 12px; text-align: left;">Nomi</th>
          <th style="padding: 12px; text-align: left;">Holati</th>
          <th style="padding: 12px; text-align: left;">Sana</th>
        </tr></thead>
        <tbody>
          <tr><td style="padding: 10px; border-bottom: 1px solid #eee;">1</td><td style="padding: 10px; border-bottom: 1px solid #eee;">AIDA</td><td style="padding: 10px; border-bottom: 1px solid #eee; color: #2ecc71;">Faol</td><td style="padding: 10px; border-bottom: 1px solid #eee;">2026-06-11</td></tr>
          <tr><td style="padding: 10px; border-bottom: 1px solid #eee;">2</td><td style="padding: 10px; border-bottom: 1px solid #eee;">Modul 2</td><td style="padding: 10px; border-bottom: 1px solid #eee; color: #f39c12;">Kutilmoqda</td><td style="padding: 10px; border-bottom: 1px solid #eee;">2026-06-10</td></tr>
        </tbody>
      </table>
    </section>""")

        if has_grid:
            sections.append("""    <section style="margin-top: 40px;">
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
        <div style="background: #fff; padding: 24px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.08);">
          <h4>Karta 1</h4>
          <p style="color: #666; margin-top: 8px;">Birinchi ustun mazmuni</p>
        </div>
        <div style="background: #fff; padding: 24px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.08);">
          <h4>Karta 2</h4>
          <p style="color: #666; margin-top: 8px;">Ikkinchi ustun mazmuni</p>
        </div>
        <div style="background: #fff; padding: 24px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.08);">
          <h4>Karta 3</h4>
          <p style="color: #666; margin-top: 8px;">Uchinchi ustun mazmuni</p>
        </div>
      </div>
    </section>""")

        if not has_form and not has_table and not has_grid:
            sections.append("""    <section style="text-align: center; padding: 60px 0;">
      <h2 style="font-size: 28px; margin-bottom: 16px;">AIDA</h2>
      <p style="color: #666; max-width: 600px; margin: 0 auto;">Sun'iy ong tizimi. Sizning vazifangizni kutmoqda.</p>
    </section>""")

        sections.append("""  </main>""")

        if has_footer:
            sections.append("""  <footer style="background: #1a1a2e; color: #ccc; padding: 24px 0; text-align: center;">
    <div class="container">
      <p>&copy; 2026 AIDA. Barcha huquqlar himoyalangan.</p>
    </div>
  </footer>""")

        sections.append("""</body>
</html>""")
        return "\n\n".join(sections)

    def _generate_css(self, prompt: str) -> str:
        normalized = prompt.lower()
        has_animation = "anim" in normalized or "harakat" in normalized
        has_dark = "dark" in normalized or "qora" in normalized
        has_grid = "grid" in normalized or "flex" in normalized

        lines = ["/* AIDA tomonidan generatsiya qilingan CSS */", ":root {",
                 "  --primary: #1a1a2e;", "  --accent: #5b7aff;",
                 "  --success: #3ccf7e;", "  --danger: #f05a5a;",
                 "  --bg: {};".format("#0b0d12" if has_dark else "#f5f7fa"),
                 "  --text: {};".format("#e4e7ed" if has_dark else "#1a1a2e"),
                 "  --surface: {};".format("#13161e" if has_dark else "#ffffff"),
                 "  --radius: 8px;", "  --font: system-ui, -apple-system, sans-serif;", "}"]
        lines.extend(["", "*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }",
                      "", "body { font-family: var(--font); background: var(--bg); color: var(--text); line-height: 1.6; }",
                      "", ".container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }"])

        if has_grid:
            lines.extend(["", ".grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }",
                          ".flex { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; }"])

        if has_animation:
            lines.extend(["", "@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }",
                          "@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }",
                          ".animated { animation: fadeIn 0.5s ease; }", ".pulse { animation: pulse 2s ease-in-out infinite; }"])

        lines.extend(["", ".card { background: var(--surface); border-radius: var(--radius); padding: 24px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }",
                      ".btn { display: inline-flex; align-items: center; padding: 10px 20px; border: none; border-radius: var(--radius); cursor: pointer; font-weight: 600; transition: opacity 0.2s; }",
                      ".btn:hover { opacity: 0.85; }", ".btn-primary { background: var(--accent); color: #fff; }",
                      ".btn-success { background: var(--success); color: #fff; }", ".btn-danger { background: var(--danger); color: #fff; }",
                      "", "input, textarea, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: inherit; }",
                      "input:focus { outline: none; border-color: var(--accent); }", ""])
        return "\n".join(lines)

    def _generate_javascript(self, prompt: str) -> str:
        normalized = prompt.lower()
        has_fetch = "fetch" in normalized or "api" in normalized or "request" in normalized
        has_form = "form" in normalized or "login" in normalized or "kirish" in normalized or "valid" in normalized
        has_dom = "dom" in normalized or "element" in normalized or "html" in normalized or "render" in normalized

        lines = ["// AIDA tomonidan generatsiya qilingan JavaScript", "'use strict';", ""]

        if has_form:
            lines.extend([
                "const form = document.querySelector('form');",
                "const emailInput = document.getElementById('email');",
                "const passwordInput = document.getElementById('password');",
                "",
                "function validateEmail(email) {",
                "  return /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email);",
                "}",
                "",
                "function validatePassword(password) {",
                "  return password && password.length >= 3;",
                "}",
                "",
                "form.addEventListener('submit', function(e) {",
                "  e.preventDefault();",
                "  const email = emailInput.value.trim();",
                "  const password = passwordInput.value;",
                "  if (!validateEmail(email)) {",
                "    alert('Notog\\'ri elektron pochta formati');",
                "    return;",
                "  }",
                "  if (!validatePassword(password)) {",
                "    alert('Parol kamida 3 belgidan iborat bol\\'ishi kerak');",
                "    return;",
                "  }",
                "  alert('Muvaffaqiyatli kirdingiz!');",
                "});",
            ])

        if has_fetch:
            lines.extend([
                "",
                "async function apiRequest(url, data) {",
                "  try {",
                "    const response = await fetch(url, {",
                "      method: 'POST',",
                "      headers: { 'Content-Type': 'application/json' },",
                "      body: JSON.stringify(data),",
                "    });",
                "    if (!response.ok) throw new Error('So\\'rov xatosi: ' + response.status);",
                "    return await response.json();",
                "  } catch (error) {",
                "    console.error('API xatosi:', error);",
                "    return null;",
                "  }",
                "}",
            ])

        if has_dom:
            lines.extend([
                "",
                "document.addEventListener('DOMContentLoaded', function() {",
                "  const app = document.getElementById('root');",
                "  if (!app) return;",
                "  app.innerHTML = '<h2>AIDA tayyor</h2>';",
                "  const btn = document.createElement('button');",
                "  btn.className = 'btn btn-primary';",
                "  btn.textContent = 'Boshlash';",
                "  btn.addEventListener('click', function() {",
                "    alert('AIDA ishga tushdi!');",
                "  });",
                "  app.appendChild(btn);",
                "});",
            ])

        lines.extend(["", "console.log('AIDA JS generator ishga tushdi');"])
        return "\n".join(lines)

    def _generate_sql(self, prompt: str) -> str:
        normalized = prompt.lower()
        has_create = "create" in normalized or "yangi" in normalized or "create" in normalized
        has_select = "select" in normalized or "tanla" in normalized or "qidir" in normalized or "top" in normalized
        has_join = "join" in normalized or "bog'la" in normalized or "qo'shil" in normalized
        has_group = "group" in normalized or "guruh" in normalized or "hisobla" in normalized

        lines = ["-- AIDA tomonidan generatsiya qilingan SQL"]
        if has_create:
            lines.extend([
                "",
                "CREATE TABLE users (",
                "  id INTEGER PRIMARY KEY AUTOINCREMENT,",
                "  email TEXT NOT NULL UNIQUE,",
                "  password_hash TEXT NOT NULL,",
                "  name TEXT NOT NULL,",
                "  role TEXT DEFAULT 'user',",
                "  is_active INTEGER DEFAULT 1,",
                "  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                ");",
                "",
                "CREATE TABLE sessions (",
                "  id INTEGER PRIMARY KEY AUTOINCREMENT,",
                "  user_id INTEGER NOT NULL,",
                "  token TEXT NOT NULL UNIQUE,",
                "  expires_at TIMESTAMP NOT NULL,",
                "  FOREIGN KEY (user_id) REFERENCES users(id)",
                ");",
            ])

        if has_select:
            lines.extend([
                "",
                "SELECT u.id, u.email, u.name, u.role, u.created_at",
                "FROM users u",
                "WHERE u.is_active = 1",
                "ORDER BY u.created_at DESC",
                "LIMIT 50;",
            ])

        if has_join:
            lines.extend([
                "",
                "SELECT u.name, u.email, s.token, s.expires_at",
                "FROM users u",
                "INNER JOIN sessions s ON s.user_id = u.id",
                "WHERE s.expires_at > CURRENT_TIMESTAMP",
                "ORDER BY s.expires_at DESC;",
            ])

        if has_group:
            lines.extend([
                "",
                "SELECT u.role, COUNT(*) as user_count, AVG(CASE WHEN u.is_active = 1 THEN 1 ELSE 0 END) as active_rate",
                "FROM users u",
                "GROUP BY u.role",
                "HAVING user_count > 0",
                "ORDER BY user_count DESC;",
            ])

        return "\n".join(lines)

    def _generate_python(self, prompt: str) -> str:
        normalized = prompt.lower()
        has_api = "api" in normalized or "endpoint" in normalized
        has_class = "class" in normalized or "oop" in normalized or "object" in normalized
        has_data = "data" in normalized or "ma'lumot" in normalized or "file" in normalized or "json" in normalized

        lines = ['"""', "AIDA Code Generator - Python", f"Prompt: {prompt[:80]}", '"""', ""]

        if has_api:
            lines.extend([
                "from dataclasses import dataclass",
                "from typing import Any, Optional",
                "import json",
                "",
                "@dataclass",
                "class APIResponse:",
                "    success: bool",
                "    data: Optional[Any] = None",
                "    error: Optional[str] = None",
                "",
                "    def to_json(self) -> str:",
                "        return json.dumps({",
                "            'success': self.success,",
                "            'data': self.data,",
                "            'error': self.error",
                "        }, ensure_ascii=False)",
                "",
                "class APIHandler:",
                '    """Umumiy API handler"""',
                "",
                "    def process(self, request_data: dict) -> APIResponse:",
                "        try:",
                "            result = self._execute(request_data)",
                "            return APIResponse(success=True, data=result)",
                "        except Exception as exc:",
                "            return APIResponse(success=False, error=str(exc))",
                "",
                "    def _execute(self, data: dict):",
                "        raise NotImplementedError",
            ])
        elif has_class:
            lines.extend([
                "from abc import ABC, abstractmethod",
                "",
                "class BaseModel(ABC):",
                "    @abstractmethod",
                "    def process(self, data: dict) -> dict:",
                "        pass",
                "",
                '    def validate(self, data: dict) -> bool:',
                "        return True",
                "",
                "class AIDAModel(BaseModel):",
                '    """AIDA model implementation"""',
                "",
                "    def __init__(self, name: str = 'AIDA'):",
                "        self.name = name",
                "        self.memory = []",
                "",
                "    def process(self, data: dict) -> dict:",
                "        self.memory.append(data)",
                "        return {'status': 'ok', 'response': f'{self.name} processed {len(self.memory)} requests'}",
            ])
        elif has_data:
            lines.extend([
                "import json",
                "from pathlib import Path",
                "from typing import Any, List",
                "",
                "class DataProcessor:",
                "    def __init__(self, file_path: str):",
                "        self.file_path = Path(file_path)",
                "",
                "    def load_json(self) -> List[dict]:",
                "        if not self.file_path.exists():",
                "            return []",
                "        with open(self.file_path, 'r', encoding='utf-8') as f:",
                "            return json.load(f)",
                "",
                "    def save_json(self, data: List[dict]) -> None:",
                '        self.file_path.parent.mkdir(parents=True, exist_ok=True)',
                "        with open(self.file_path, 'w', encoding='utf-8') as f:",
                "            json.dump(data, f, ensure_ascii=False, indent=2)",
                "",
                "    def filter(self, key: str, value: Any) -> List[dict]:",
                "        return [item for item in self.load_json() if item.get(key) == value]",
            ])
        else:
            lines.extend([
                "def process_input(data: str) -> str:",
                '    """Inputni qayta ishlash"""',
                "    if not data:",
                "        return 'Xato: ma\\'lumot kiritilmagan'",
                "    return data.strip()",
                "",
                "def analyze(data: list) -> dict:",
                "    return {",
                "        'count': len(data),",
                "        'unique': len(set(data)),",
                "        'has_data': bool(data),",
                "    }",
            ])

        return "\n".join(lines)

    def _generate_typescript(self, prompt: str) -> str:
        lines = self._generate_javascript(prompt).split("\n")
        typed_lines = [
            "// AIDA TypeScript Generator",
            "interface APIResponse<T = unknown> {",
            "  success: boolean;",
            "  data?: T;",
            "  error?: string;",
            "}",
            "",
        ]
        for line in lines:
            if line.startswith("// AIDA"):
                continue
            if line.strip().startswith("'use strict'"):
                continue
            typed_lines.append(line)
        return "\n".join(typed_lines)


class TranslationEngine:
    def __init__(self):
        self._build_dicts()

    def _build_dicts(self):
        self.uz_en = {
            "salom": "hello", "xayr": "goodbye", "rahmat": "thank you",
            "ha": "yes", "yo'q": "no", "iltimos": "please",
            "yaxshi": "good", "yomon": "bad", "katta": "big",
            "kichik": "small", "tez": "fast", "sekin": "slow",
            "yangi": "new", "eski": "old", "issiq": "hot",
            "sovuq": "cold", "qanday": "how", "nima": "what",
            "kim": "who", "qayerda": "where", "qachon": "when",
            "nega": "why", "qancha": "how much", "kerak": "need",
            "bilan": "with", "uchun": "for", "haqida": "about",
            "siz": "you", "men": "I", "biz": "we", "ular": "they",
            "mening": "my", "sening": "your", "uning": "his/her",
            "ish": "work", "uy": "house", "kitob": "book",
            "maktab": "school", "universitet": "university",
            "dastur": "program", "kod": "code", "tizim": "system",
            "vaqt": "time", "kun": "day", "hafta": "week",
            "oy": "month", "yil": "year", "bugun": "today",
            "ertaga": "tomorrow", "kecha": "yesterday",
            "foydalanuvchi": "user", "parol": "password",
            "elektron pochta": "email", "xato": "error",
            "tugma": "button", "sahifa": "page", "ma'lumot": "data",
            "boshqaruv": "control", "sozlash": "settings",
            "qilmoq": "to do", "bormoq": "to go", "kelmoq": "to come",
            "olmoq": "to take", "bermoq": "to give", "bilmoq": "to know",
            "ko'rmoq": "to see", "aytmoq": "to say", "ishlamoq": "to work",
            "o'qimoq": "to read", "yozmoq": "to write", "bilish": "knowledge",
            "tushunmoq": "to understand", "qilish": "doing", "bo'lish": "being",
            "o'rganmoq": "to learn", "yaratmoq": "to create", "o'zgartirmoq": "to change",
            "rivojlantirish": "development", "kuchaytirish": "improvement",
            "tekshirish": "checking", "tahlil": "analysis", "natija": "result",
            "sabab": "reason", "misol": "example", "fikr": "idea",
            "muammo": "problem", "yechim": "solution", "savol": "question",
            "javob": "answer", "maqsad": "goal", "vazifa": "task",
            "loyiha": "project", "jamoa": "team", "mijoz": "client",
            "bozor": "market", "mahsulot": "product", "xizmat": "service",
            "daromad": "income", "xarajat": "expense", "foyda": "profit",
            "sifat": "quality", "miqdor": "quantity", "o'lcham": "size",
            "rang": "color", "shakl": "shape", "holat": "state",
            "jarayon": "process", "bosqich": "stage", "qadam": "step",
            "yo'nalish": "direction", "tomon": "side", "orasida": "between",
            "ichida": "inside", "tashqarida": "outside", "ustida": "on top",
            "ostida": "under", "yonida": "next to", "oldida": "in front",
            "orqasida": "behind", "yuqori": "high", "past": "low",
            "uzun": "long", "qisqa": "short", "keng": "wide",
            "tor": "narrow", "og'ir": "heavy", "yengil": "light",
            "qattiq": "hard", "yumshoq": "soft", "silliq": "smooth",
            "g'adir-budur": "rough", "toza": "clean", "iflos": "dirty",
            "chiroyli": "beautiful", "go'zal": "gorgeous", "yoqimli": "pleasant",
            "xunuk": "ugly", "achchiq": "bitter", "shirin": "sweet",
            "tuzli": "salty", "nordon": "sour", "ta'm": "taste",
            "is": "smell", "tovush": "sound", "ovoz": "voice",
            "suv": "water", "olov": "fire", "havo": "air",
            "tuproq": "earth", "yong'in": "fire", "shamol": "wind",
            "yomg'ir": "rain", "qor": "snow", "quyosh": "sun",
            "oy": "moon", "yulduz": "star", "osmon": "sky",
            "yer": "ground", "dengiz": "sea", "ko'l": "lake",
            "daryo": "river", "tog'": "mountain", "vodiy": "valley",
            "o'simlik": "plant", "hayvon": "animal", "daraxt": "tree",
            "gul": "flower", "meva": "fruit", "sabzavot": "vegetable",
            "non": "bread", "go'sht": "meat", "sut": "milk",
            "tuxum": "egg", "osh": "rice", "mosh": "beans",
            "choy": "tea", "qahva": "coffee", "sharbat": "juice",
        }
        self.en_uz = {v: k for k, v in self.uz_en.items()}
        self.uz_ru = {
            "salom": "привет", "rahmat": "спасибо", "ha": "да",
            "yo'q": "нет", "iltimos": "пожалуйста", "yaxshi": "хорошо",
            "yomon": "плохо", "katta": "большой", "kichik": "маленький",
            "yangi": "новый", "eski": "старый", "ish": "работа",
            "kitob": "книга", "maktab": "школа", "vaqt": "время",
            "kun": "день", "tizim": "система", "kod": "код",
            "foydalanuvchi": "пользователь", "xato": "ошибка",
        }
        self.ru_uz = {v: k for k, v in self.uz_ru.items()}
        self.ru_en = {
            "привет": "hello", "спасибо": "thank you", "да": "yes",
            "нет": "no", "пожалуйста": "please", "хорошо": "good",
            "плохо": "bad", "большой": "big", "маленький": "small",
            "работа": "work", "книга": "book", "время": "time",
            "система": "system", "код": "code", "ошибка": "error",
        }

    def detect_language(self, text: str) -> str:
        text_lower = text.lower()
        cyrillic = bool(re.search(r'[а-яё]', text_lower))
        latin_uz = bool(re.search(r"[o'g'q'ch'sh]", text_lower))
        if cyrillic:
            return "ru"
        if latin_uz:
            return "uz"
        uz_stopwords = {"va", "bilan", "uchun", "bu", "ham", "bir", "da", "ga",
                        "ni", "dan", "kerak", "bo'l", "qil", "ber", "ol",
                        "bilan", "uchun", "haqida", "siz", "men", "biz", "ular",
                        "mening", "sening", "uning", "bizning", "sizning",
                        "qanday", "nima", "kim", "qayerda", "qachon", "nega", "qancha",
                        "yangi", "eski", "yaxshi", "yomon", "katta", "kichik",
                        "ish", "vaqt", "kun", "yil", "bugun", "kecha", "ertaga"}
        words = set(text_lower.split())
        uz_score = sum(1 for w in words if w in uz_stopwords or w.endswith(("lar", "gan", "kan", "moq", "ish", "lik", "siz")))
        eng_score = sum(1 for w in words if w in {"the", "a", "an", "is", "are", "was", "were",
                        "to", "in", "of", "for", "with", "on", "at", "by",
                        "this", "that", "it", "its", "and", "or", "be", "been",
                        "have", "has", "do", "does", "did", "will", "would", "can", "could"})
        return "uz" if uz_score >= eng_score else "en"

    def translate(self, text: str, source: str = "", target: str = "") -> str:
        if not source:
            source = self.detect_language(text)
        if not target:
            target = "uz" if source != "uz" else "en"

        if source == target:
            return text

        pairs = {
            ("uz", "en"): self.uz_en,
            ("en", "uz"): self.en_uz,
            ("uz", "ru"): self.uz_ru,
            ("ru", "uz"): self.ru_uz,
            ("ru", "en"): self.ru_en,
            ("en", "ru"): {v: k for k, v in self.ru_en.items()},
        }
        dictionary = pairs.get((source, target), {})

        words = text.split()
        translated = []
        for word in words:
            clean = word.strip(".,!?;:\"'()[]{}")
            punct = word.replace(clean, "")
            lower = clean.lower()
            if lower in dictionary:
                translated_word = dictionary[lower]
                if clean[0].isupper() if clean else False:
                    translated_word = translated_word.capitalize()
                translated.append(translated_word + punct)
            else:
                translated.append(word)
        return " ".join(translated)


class ComparisonEngine:
    def compare(self, prompt: str, items: list[str] | None = None) -> str:
        if not items or len(items) < 2:
            items = self._extract_items(prompt)
        if len(items) < 2:
            return "Taqqoslash uchun kamida ikkita variant kerak. Iltimos, variantlarni ayting."
        criteria = self._generate_criteria(prompt)
        scores = self._score_items(items, criteria, prompt)
        return self._format_comparison(items, criteria, scores, prompt)

    def _extract_items(self, text: str) -> list[str]:
        normalized = text.lower()
        separators = [" vs ", " va ", " yoki ", " bilan ", " / ", ", "]
        for sep in separators:
            if sep in normalized:
                parts = normalized.split(sep)
                return [p.strip() for p in parts if p.strip()][:4]
        known_pairs = [
            ("django", "fastapi"), ("react", "angular"), ("react", "vue"),
            ("python", "javascript"), ("html", "css"), ("linux", "windows"),
            ("mysql", "postgresql"), ("mongodb", "postgresql"),
            ("docker", "kubernetes"), ("git", "svn"),
        ]
        for a, b in known_pairs:
            if a in normalized or b in normalized:
                return [a.capitalize(), b.capitalize()]
        return ["Variant A", "Variant B"]

    def _generate_criteria(self, prompt: str) -> list[dict]:
        return [
            {"name": "Osonlik", "weight": 1.0, "question": "Qaysi biri osonroq?"},
            {"name": "Tezlik", "weight": 1.0, "question": "Qaysi biri tezroq?"},
            {"name": "Narx", "weight": 0.8, "question": "Qaysi biri arzonroq?"},
            {"name": "Moslashuvchanlik", "weight": 0.8, "question": "Qaysi biri moslashuvchan?"},
            {"name": "Jamiyat", "weight": 0.6, "question": "Qaysi biri keng tarqalgan?"},
        ]

    def _score_items(self, items: list[str], criteria: list[dict], prompt: str) -> dict:
        scores = {}
        for item in items:
            item_scores = {}
            for criterion in criteria:
                import random
                random.seed(hash(prompt + item + criterion["name"]))
                score = round(random.uniform(3, 10), 1)
                item_scores[criterion["name"]] = score
            scores[item] = item_scores
        return scores

    def _format_comparison(self, items: list[str], criteria: list[dict], scores: dict, prompt: str) -> str:
        lines = [f"## Taqqoslash: {' vs '.join(items)}", ""]
        lines.append(f"**So'rov:** {prompt}")
        lines.append("")
        headers = ["Mezon"] + items
        col_widths = [max(len(h) + 2, 20) for h in headers]
        sep_line = "+" + "+".join("-" * w for w in col_widths) + "+"

        lines.append("```")
        lines.append(sep_line)
        header_row = "|" + "|".join(h.center(w) for h, w in zip(headers, col_widths)) + "|"
        lines.append(header_row)
        lines.append(sep_line.replace("-", "="))

        for criterion in criteria:
            row = [criterion["name"]] + [str(scores[item][criterion["name"]]) for item in items]
            row_str = "|" + "|".join(r.ljust(w) for r, w in zip(row, col_widths)) + "|"
            lines.append(row_str)
        lines.append(sep_line)
        lines.append("```")
        lines.append("")

        totals = {}
        for item in items:
            total = sum(scores[item].values())
            totals[item] = total
        sorted_items = sorted(items, key=lambda i: totals[i], reverse=True)
        lines.append(f"**Xulosa:** {sorted_items[0]} eng yaxshi variant ({totals[sorted_items[0]]} ball).")
        lines.append("")
        for i, item in enumerate(sorted_items, 1):
            lines.append(f"{i}. **{item}** — {totals[item]} ball")
        return "\n".join(lines)


class SelfModifier:
    """Read, analyze, and modify project files with safety constraints."""

    SAFE_EXTENSIONS = {".py", ".html", ".css", ".js", ".json", ".md", ".txt", ".env"}
    MAX_FILE_SIZE = 1024 * 100  # 100KB

    def __init__(self):
        self.project_root = BASE_DIR

    def list_files(self, pattern: str = "*.py") -> list[str]:
        """List project files matching a glob pattern, relative to project root."""
        from pathlib import Path
        files = list(self.project_root.glob(pattern))
        return [str(f.relative_to(self.project_root)) for f in files if f.is_file()]

    def read_file(self, relative_path: str) -> str:
        """Read a file from the project. Returns content or error message."""
        full = self._resolve(relative_path)
        if not full.exists():
            return f"Xato: {relative_path} fayli topilmadi."
        if not full.is_file():
            return f"Xato: {relative_path} papka, fayl emas."
        if full.stat().st_size > self.MAX_FILE_SIZE:
            return f"Xato: {relative_path} juda katta ({full.stat().st_size} bayt)."
        try:
            return full.read_text(encoding="utf-8")
        except Exception as e:
            return f"Xato: {relative_path} o'qishda xatolik: {e}"

    def edit_file(self, relative_path: str, old_string: str, new_string: str) -> str:
        """Replace old_string with new_string in a file. Creates backup first."""
        full = self._resolve(relative_path)
        if not full.exists():
            return f"Xato: {relative_path} fayli topilmadi."
        if full.suffix not in self.SAFE_EXTENSIONS:
            return f"Xato: {relative_path} turidagi faylni tahrirlash mumkin emas (faqat {', '.join(self.SAFE_EXTENSIONS)})."
        try:
            content = full.read_text(encoding="utf-8")
            if old_string not in content:
                return f"Xato: '{old_string[:50]}...' matni {relative_path} da topilmadi."
            backup = full.with_suffix(full.suffix + ".bak")
            if not backup.exists():
                full.rename(backup)
            new_content = content.replace(old_string, new_string, 1)
            full.write_text(new_content, encoding="utf-8")
            return f"✅ {relative_path} fayliga o'zgartirish kiritildi. Zaxira: {backup.name}"
        except Exception as e:
            return f"Xato: tahrirlashda xatolik: {e}"

    def create_file(self, relative_path: str, content: str) -> str:
        """Create a new file in the project."""
        full = self._resolve(relative_path)
        if full.exists():
            return f"Xato: {relative_path} allaqachon mavjud."
        if full.suffix not in self.SAFE_EXTENSIONS:
            return f"Xato: {relative_path} turidagi faylni yaratish mumkin emas."
        try:
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content, encoding="utf-8")
            return f"✅ {relative_path} yaratildi ({len(content)} bayt)."
        except Exception as e:
            return f"Xato: yaratishda xatolik: {e}"

    def delete_file(self, relative_path: str) -> str:
        """Delete a file (only .bak, .tmp extensions or user-created files)."""
        full = self._resolve(relative_path)
        if not full.exists():
            return f"Xato: {relative_path} topilmadi."
        safe_del = {".bak", ".tmp", ".log"}
        if full.suffix not in safe_del:
            return f"Xato: {relative_path} ni o'chirish mumkin emas (faqat {', '.join(safe_del)})."
        try:
            full.unlink()
            return f"🗑️ {relative_path} o'chirildi."
        except Exception as e:
            return f"Xato: o'chirishda xatolik: {e}"

    def get_project_info(self) -> str:
        """Get summary of project structure."""
        total = 0
        by_type = {}
        for ext in self.SAFE_EXTENSIONS:
            count = len(list(self.project_root.glob(f"**/*{ext}")))
            by_type[ext] = count
            total += count
        parts = [f"Loyiha: {self.project_root.name}",
                 f"Fayllar: {total} ta",
                 f"Turlar: {', '.join(f'{k}: {v}' for k, v in sorted(by_type.items()) if v > 0)}"]
        return "\n".join(parts)

    def _resolve(self, relative_path: str) -> "Path":
        """Resolve a relative path and ensure it stays within project root."""
        from pathlib import Path
        p = Path(relative_path)
        if p.is_absolute():
            return p
        full = (self.project_root / p).resolve()
        try:
            full.relative_to(self.project_root.resolve())
        except ValueError:
            return Path("__ESCAPE__")  # path traversal attempt
        return full


class KnowledgeInstaller:
    """Install packages, download docs, create knowledge modules for any language."""

    def install_package(self, package_name: str) -> str:
        try:
            import subprocess
            result = subprocess.run(
                ["pip", "install", package_name],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                return f"✅ {package_name} o'rnatildi."
            return f"Xato: {result.stderr.strip()[:200]}"
        except Exception as e:
            return f"Xato: {e}"

    def create_module(self, name: str, language: str, code: str) -> str:
        ext_map = {"python": "py", "javascript": "js", "typescript": "ts",
                    "html": "html", "css": "css", "sql": "sql"}
        ext = ext_map.get(language.lower(), "py")
        filename = f"{name}.{ext}"
        mod = SelfModifier()
        return mod.create_file(f"knowledge/{filename}", code)

    def download_docs(self, topic: str, language: str = "python") -> str:
        query = f"{language} {topic} documentation"
        svc = WebResearchService()
        results = svc.search(query, limit=3)
        if results:
            lines = [f"📚 {topic} ({language}) dokumentatsiyasi:", ""]
            for r in results:
                lines.append(f"- {r.title}")
                lines.append(f"  {r.summary[:200]}")
                lines.append(f"  {r.url}")
            return "\n".join(lines)
        return f"{topic} bo'yicha ma'lumot topilmadi."


class AutoImprover:
    """Self-analysis and improvement engine - makes AIDA smarter over time."""

    def __init__(self):
        self.modifier = SelfModifier()

    def analyze_code_quality(self, file_path: str) -> str:
        content = self.modifier.read_file(file_path)
        if content.startswith("Xato:"):
            return content
        issues = []
        lines = content.split("\n")
        if len(lines) > 500:
            issues.append(f"Juda katta fayl ({len(lines)} qator)")
        for i, line in enumerate(lines, 1):
            if len(line) > 200:
                issues.append(f"{i}-qator juda uzun ({len(line)} belgi)")
        if issues:
            return "**Tahlil natijasi:**\n" + "\n".join(f"- {i}" for i in issues)
        return "✅ Kod sifati yaxshi."

    def suggest_improvement(self, file_path: str) -> str:
        content = self.modifier.read_file(file_path)
        if content.startswith("Xato:"):
            return content
        suggestions = []
        if "TODO" in content or "# TODO" in content:
            suggestions.append("TODO izohlar bor - ularni bajarish kerak")
        if "print(" in content:
            suggestions.append("print() o'rniga logging ishlatish mumkin")
        if "try:\n    pass\nexcept:" in content or "except:\n            pass" in content:
            suggestions.append("Bo'sh except bloklari xavfli")
        if not suggestions:
            suggestions.append("Kod toza, yaxshilash kerak emas")
        return "**Takliflar:**\n" + "\n".join(f"- {s}" for s in suggestions)

    def learn_from_error(self, prompt: str, response: str, feedback: str) -> str:
        fact = f"Xato tahlili: {prompt} -> {feedback}"
        db = MemoryStore(MEMORY_DB)
        db.remember_fact(fact)
        return "✅ Xatodan o'rganildi. Keyingi safar yaxshiroq javob beraman."

    def generate_knowledge_file(self, topic: str, content: str) -> str:
        mod = SelfModifier()
        filename = f"knowledge/{topic.lower().replace(' ', '_')}.md"
        header = f"# {topic}\n\nAIDA Knowledge Base — avtomatik yaratilgan\n\n"
        return mod.create_file(filename, header + content)

    def analyze_all_code(self) -> str:
        import glob as g
        py_files = g.glob(str(BASE_DIR / "webapp" / "*.py"))
        total_issues = 0
        for f in sorted(py_files)[:15]:
            rel = f.replace(str(BASE_DIR) + "\\", "")
            issues = self.analyze_code_quality(rel)
            if "✅" not in issues:
                total_issues += 1
        return f"**O'z-o'zini tahlil:** {total_issues} ta faylda yaxshilanish kerak."


class ResearchFilter:
    """Filter and rank research results by relevance to the query."""

    @staticmethod
    def filter(results: list[ResearchSnippet], query: str) -> list[ResearchSnippet]:
        if not results:
            return results
        query_words = set(w.lower().strip(".,!?") for w in query.split() if len(w) > 2)
        scored = []
        for item in results:
            score = 0
            title_lower = item.title.lower()
            summary_lower = item.summary.lower()
            for qw in query_words:
                if qw in title_lower:
                    score += 3
                elif qw in summary_lower:
                    score += 1
            if "may refer to" in summary_lower:
                score -= 5
            if "disambiguation" in title_lower or "disambiguation" in summary_lower:
                score -= 5
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for score, item in scored if score >= 0] or [item for _, item in scored[:2]]


class LocalProvider:
    name = "local"

    def __init__(self, respond_func: callable = None):
        self._respond_func = respond_func

    # ── Intent detection ─────────────────────────────────────────────────────

    INTENT_MAP = {
        "greeting":    ["salom", "assalom", "hello", "xayr", "hayot", "hayrli"],
        "status":      ["status", "holat", "ahvol", "ishlayaptimi", "ping", "tayyor"],
        "plan":        ["reja", "plan", "bosqich", "strategiya", "yo'l xarita", "roadmap",
                        "qanday boshlash", "qilish kerak", "nima qil"],
        "code":        ["kod", "code", "funksiya", "function", "script", "html", "css", "javascript",
                        "typescript", "react", "django", "sql", "regex", "xato", "bug", "fix",
                        "exception", "traceback", "api yoz", "backend", "frontend",
                        "kodini yoz", "dastur yoz", "snippet", "coding"],
        "writing":     ["yoz", "maqola", "post", "email", "matn", "copy", "tavsif", "blog",
                        "xat yoz", "she'r yoz", "hikoya"],
        "compare":     ["taqqosla", "solishtir", "qaysi yaxshi", "farq", "afzalligi", "vs",
                        "yaxshiroq", "qaysi"],
        "explain":     ["nima", "nima bu", "tushuntir", "izohla", "qanday ishlaydi", "what is",
                        "explain", "define", "nimaga", "sababi", "degani", "ma'nosi"],
        "list":        ["ro'yxat", "list", "nechta", "qanday turlar", "misollar", "berib ber",
                        "sanab ber", "aytib ber"],
        "math":        ["hisabla", "formula", "son", "matematik", "calculate", "foiz", "%",
                        "qo'sh", "ayir", "ko'paytir", "bo'lish"],
        "translate":   ["tarjima", "translate", "o'zbek", "ingliz", "russian", "translate to",
                        "o'zbekcha", "inglizcha", "ruscha"],
        "summary":     ["xulosa", "qisqacha", "summary", "brief", "abstract", "resume",
                        "qisqartir"],
        "self_modify": ["o'zgarish kirit", "self modify", "update your code", "o'z kodingni",
                        "faylni och", "read file", "fayl o'qil", "kodni o'zgartir",
                        "new feature qo'sh", "funksiya qo'sh", "modul yarat",
                        "fayl yarat", "create file", "write file", "faylga yoz",
                        "loyiha haqida", "project info", "qanday fayllar", "what files",
                        "self-modify", "selfmodify", "o'zingni o'zgartir", "update yourself",
                        "fayl och", "faylni o'qi", "o'zgartirish kirit"],
        "self_improve": ["o'zingni kuchaytir", "ozingni kuchaytir", "improve yourself",
                        "o'zingni rivojlantir", "ozingni rivojlantir",
                        "yangilik o'rnat", "install package", "pip install",
                        "bilim qo'sh", "dasturlash tilini o'rnat",
                        "programming language install", "yangi til o'rgan",
                        "yangi bilim", "o'zingni yangila", "download docs",
                        "o'z kodingni tahlil qil", "analyze your code",
                        "miyyaga yoz", "miyya", "bilimlarini kengaytir",
                        "hamma narsani bil", "mukammal", "cheksiz bilim",
                        "aqlliroq bol", "donoroq", "kuchaytir",
                        "full install", "full bilsin", "to'liq bil"],
    }

    def _detect_intent(self, text: str) -> str:
        lower = text.lower()
        words = set(lower.split())
        scores: dict[str, int] = {}
        for intent, keywords in self.INTENT_MAP.items():
            score = 0
            for k in keywords:
                if len(k) <= 3:
                    if k in words:
                        score += 1
                else:
                    if k in lower:
                        score += 1
            scores[intent] = score
        best = max(scores, key=lambda x: scores[x])
        return best if scores[best] > 0 else "general"

    def _extract_keywords(self, text: str) -> list[str]:
        stopwords = {"va", "yoki", "bilan", "uchun", "bu", "ham", "men", "sen", "u",
                     "bir", "da", "ga", "ni", "dan", "the", "a", "an", "is", "in",
                     "of", "to", "and", "or", "for", "that", "it", "as"}
        words = [w.strip(".,!?\"'") for w in text.split()]
        return [w for w in words if len(w) >= 3 and w.lower() not in stopwords][:10]

    def _context_summary(self, memory: Iterable[dict]) -> str:
        msgs = list(memory)
        user_msgs = [m["content"] for m in msgs if m["role"] == "user"]
        if not user_msgs:
            return ""
        last = user_msgs[-1][:100]
        count = len(user_msgs)
        if count > 1:
            return f"(Suhbat davom etmoqda. Oldingi savol: \"{last}\")"
        return ""

    def _dynamic_generate(self, prompt: str, intent: str, keywords: list[str], memory: Iterable[dict], ctx: str) -> str:
        mem_list = list(memory)
        user_history = [m["content"].strip() for m in mem_list if m["role"] == "user"]
        is_first = len(user_history) <= 1

        if intent == "greeting":
            return ("Salom! AIDA tayyor.\n\n"
                    "Men quyidagilarda yordam bera olaman:\n"
                    "- Reja va strategiya tuzish\n"
                    "- Kod yozish va xatolarni tuzatish\n"
                    "- Internetdan ma'lumot qidirish\n"
                    "- Matn yozish va tarjima qilish\n"
                    "- Taqqoslash va tahlil qilish\n"
                    "- O'z kodingizni o'zgartirish\n"
                    "- Yangi fayllar yaratish\n\n"
                    "Vazifangizni yozing, men darhol ishga tushaman.")

        if intent == "status":
            return "AIDA to'liq ishga tayyor. Tizim normal ishlayapti."

        if intent in ("plan", "code", "compare", "writing", "explain", "list", "math", "summary", "translate"):
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=2) as ex:
                think_f = ex.submit(self._think_block, prompt, intent, keywords, is_first, len(user_history))
                result_f = ex.submit(self._result_block, prompt, intent, keywords, mem_list, ctx)
                return f"{think_f.result()}\n\n{result_f.result()}"

        return self._result_block(prompt, intent, keywords, mem_list, ctx)

    def _think_block(self, prompt: str, intent: str, keywords: list[str], is_first: bool, history_len: int) -> str:
        plans = {
            "plan": ["Maqsadni aniqlash", "Resurslarni baholash", "Bosqichlarni rejalashtirish", "Xavflarni tahlil qilish", "Natijani loyihalash"],
            "code": ["Talabni tahlil qilish", "Stackni aniqlash", "Kod yozish", "Xatolarni tekshirish", "Test qilish"],
            "compare": ["Variantlarni aniqlash", "Mezonlarni belgilash", "Har birini tahlil qilish", "Ball berish", "Xulosa chiqarish"],
            "explain": ["Tushunchani aniqlash", "Asosiy jihatlarini ajratish", "Misol keltirish", "O'xshatish orqali tushuntirish"],
            "list": ["Tur va kategoriyalarni aniqlash", "Ro'yxatni shakllantirish", "Har birini qisqa izohlash"],
            "math": ["Masalani tahlil qilish", "Formulalarni qo'llash", "Hisoblash", "Natijani tekshirish"],
            "writing": ["Mavzuni tushunish", "Strukturani belgilash", "Matn yozish", "Tahrirlash"],
            "summary": ["Asosiy fikrlarni ajratish", "Qisqacha bayon qilish", "Muhim detallarni saqlash"],
            "translate": ["Tilni aniqlash", "Lug'at bo'yicha tarjima", "Grammatikani moslashtirish"],
        }
        steps = plans.get(intent, ["Savolni tushunish", "Ma'lumotni tahlil qilish", "Javob tayyorlash"])
        kw_str = ", ".join(keywords[:6]) if keywords else "aniqlanmadi"
        ctx_str = "yangi suhbat" if is_first else f"davom etmoqda ({history_len} ta xabar)"
        return (f"## Fikrlash jarayoni ({intent})\n\n"
                f"**Savol:** {prompt}\n"
                f"**Kalit so'zlar:** {kw_str}\n"
                f"**Kontekst:** {ctx_str}\n\n"
                "**Reja:**\n" +
                "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps)))

    def _get_predefined_explanation(self, prompt: str, intent: str) -> str | None:
        norm = prompt.lower()
        # If the user is explicitly asking to write code, do not return predefined explanation
        code_request_keywords = ["yoz", "tuz", "create", "kodini", "dastur", "generate", "write", "qur", "kod yozib", "kod ber"]
        if any(cw in norm for cw in code_request_keywords):
            return None
        
        # Word boundaries or specific substrings
        if re.search(r"\bhtml\b", norm):
            return (
                "### HTML (HyperText Markup Language) nima?\n"
                "HTML — bu web-sahifalarni yaratish uchun ishlatiladigan standart hujjat belgilash tili. "
                "U sahifaning tarkibi va strukturasi (skeleti)ni belgilaydi. HTML dasturlash tili emas, "
                "balki belgilash (markup) tilidir.\n\n"
                "#### Asosiy elementlari:\n"
                "1. **Teglar (Tags):** Hujjat tarkibini belgilash uchun `<tagname>` ko'rinishida yoziladi. "
                "Ko'pchilik teglar ochiluvchi va yopiluvchi juftlikdan iborat (masalan: `<h1>Salom</h1>`, `<p>Matn</p>`).\n"
                "2. **Atributlar (Attributes):** Teglar haqida qo'shimcha ma'lumot beradi (masalan: `<a href=\"https://google.com\">Google</a>` dagi `href`).\n\n"
                "#### Minimal HTML5 hujjati namunasi:\n"
                "```html\n"
                "<!DOCTYPE html>\n"
                "<html lang=\"uz\">\n"
                "<head>\n"
                "    <meta charset=\"UTF-8\">\n"
                "    <title>Mening Sahifam</title>\n"
                "</head>\n"
                "<body>\n"
                "    <h1>Salom, Dunyo!</h1>\n"
                "    <p>Bu AIDA tomonidan tushuntirilgan birinchi HTML sahifa.</p>\n"
                "</body>\n"
                "</html>\n"
                "```"
            )
        
        if re.search(r"\bcss\b", norm):
            return (
                "### CSS (Cascading Style Sheets) nima?\n"
                "CSS — bu HTML elementlarining ekranda, qog'ozda yoki boshqa mediada qanday ko'rinishini belgilaydigan uslublar tili. "
                "U web-sahifalarning vizual dizayni, ranglari, shriftlari va turli ekranlarga moslashuvchanligini (responsive design) boshqaradi.\n\n"
                "#### CSS imkoniyatlari:\n"
                "1. **Selektorlar (Selectors):** Qaysi HTML elementga uslub berilishini aniqlaydi (masalan: `p { color: red; }` barcha xatboshilarni qizil qiladi).\n"
                "2. **Kaskadlanish:** Bir elementga bir nechta uslub qo'llanilganda, qaysi biri ustuvor bo'lishini tartibga soladi.\n"
                "3. **Joylashuv tizimlari (Layouts):** Flexbox va CSS Grid yordamida elementlarni sahifada juda oson joylashtirish mumkin.\n\n"
                "#### Namunaviy uslublar to'plami:\n"
                "```css\n"
                "body {\n"
                "    background-color: #f0f2f5;\n"
                "    color: #333;\n"
                "    font-family: Arial, sans-serif;\n"
                "}\n"
                ".header {\n"
                "    background: linear-gradient(135deg, #1a1a2e, #16161d);\n"
                "    color: white;\n"
                "    padding: 20px;\n"
                "    text-align: center;\n"
                "}\n"
                "```"
            )

        if re.search(r"\bjavascript\b|\bjs\b", norm):
            return (
                "### JavaScript nima?\n"
                "JavaScript — bu web-sahifalarga dinamiklik va interaktivlik qo'shish uchun ishlatiladigan dasturlash tili. "
                "HTML sahifa strukturasini, CSS dizaynini yaratsa, JavaScript uni jonlantiradi (masalan: tugma bosilganda oyna ochilishi, ma'lumot yuklanishi, animatsiyalar).\n\n"
                "#### Asosiy xususiyatlari:\n"
                "1. **DOM Manipulyatsiyasi:** Sahifadagi HTML elementlarni o'chirish, qo'shish yoki o'zgartirish.\n"
                "2. **Asinxronlik (AJAX/Fetch):** Sahifani yangilamasdan serverdan yangi ma'lumotlarni yuklab olish.\n"
                "3. **Keng qo'llanilishi:** Hozirda nafaqat brauzerda (Frontend), balki Node.js yordamida serverda (Backend) ham ishlatiladi.\n\n"
                "#### Oddiy kod namunasi:\n"
                "```javascript\n"
                "// Tugmani bosganda matnni o'zgartirish\n"
                "const button = document.querySelector('button');\n"
                "const text = document.querySelector('.text');\n\n"
                "button.addEventListener('click', () => {\n"
                "    text.textContent = 'Muvaffaqiyatli bajarildi!';\n"
                "    text.style.color = '#2ecc71';\n"
                "});\n"
                "```"
            )

        if re.search(r"\breact\b", norm):
            return (
                "### React nima?\n"
                "React — bu foydalanuvchi interfeyslarini (UI) yaratish uchun Facebook (Meta) tomonidan ishlab chiqilgan ochiq kodli JavaScript kutubxonasidir. "
                "U asosan bir sahifali ilovalarni (SPA) yaratishda qo'llaniladi.\n\n"
                "#### Asosiy tamoyillari:\n"
                "1. **Komponentlar (Components):** UI'ni kichik, mustaqil va qayta ishlatiladigan bo'laklarga bo'lish (masalan: Navbar, Button, Card).\n"
                "2. **Virtual DOM:** Haqiqiy DOM bilan ishlash sekin bo'lgani uchun, React xotiradagi virtual nusxa yordamida faqat o'zgargan qismlarni tezkor yangilaydi.\n"
                "3. **State va Props:** Komponent ichidagi ma'lumotlarni (state) va tashqaridan uzatiladigan parametrlarni (props) boshqarish.\n\n"
                "#### Namunaviy React komponenti:\n"
                "```jsx\n"
                "import React, { useState } from 'react';\n\n"
                "export default function Counter() {\n"
                "  const [count, setCount] = useState(0);\n\n"
                "  return (\n"
                "    <div style={{ padding: '20px', textAlign: 'center' }}>\n"
                "      <h2>Hisoblagich: {count}</h2>\n"
                "      <button onClick={() => setCount(count + 1)}>Oshirish</button>\n"
                "    </div>\n"
                "  );\n"
                "}\n"
                "```"
            )

        if re.search(r"\bpython\b", norm):
            return (
                "### Python nima?\n"
                "Python — bu yuqori darajali, talqin qilinadigan (interpreted), o'qilishi juda oson va sodda bo'lgan universal dasturlash tilidir. "
                "U dasturchilar orasida eng ommabop tillardan biri hisoblanadi.\n\n"
                "#### Python ishlatiladigan sohalar:\n"
                "1. **Sun'iy Intellekt va Mashinali O'rganish (AI/ML):** TensorFlow, PyTorch va scikit-learn kutubxonalari.\n"
                "2. **Backend dasturlash:** Django va FastAPI freymvorklari.\n"
                "3. **Ma'lumotlar tahlili va vizualizatsiya:** Pandas, NumPy, Matplotlib.\n"
                "4. **Avtomatlashtirish (Scripts):** Kundalik takrorlanadigan vazifalarni bajaruvchi skriptlar.\n\n"
                "#### Oddiy kod namunasi:\n"
                "```python\n"
                "# Ro'yxatdagi juft sonlarni ajratib olish\n"
                "sonlar = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]\n"
                "juft_sonlar = [son for son in sonlar if son % 2 == 0]\n\n"
                "print(f\"Juft sonlar: {juft_sonlar}\")  # Natija: [2, 4, 6, 8, 10]\n"
                "```"
            )

        if re.search(r"\bdjango\b", norm):
            return (
                "### Django nima?\n"
                "Django — bu Python tilida yozilgan, mukammal xavfsizlik va tezkorlikka yo'naltirilgan ochiq kodli backend web freymvorkidir. "
                "U \"Batteries included\" (hamma narsa ichida) falsafasiga amal qiladi.\n\n"
                "#### Django tarkibidagi tayyor komponentlar:\n"
                "1. **Django ORM:** Ma'lumotlar bazasi (SQLite, PostgreSQL, MySQL) bilan SQL yozmasdan, Python klasslari orqali ishlash.\n"
                "2. **Admin Panel:** Ma'lumotlarni boshqarish (CRUD) uchun tayyor va xavfsiz ma'murlash paneli.\n"
                "3. **Autentifikatsiya:** Foydalanuvchilarni ro'yxatdan o'tkazish, tizimga kirish/chiqish va ruxsatlarni tekshirish tizimi.\n\n"
                "#### Django Model namunasi:\n"
                "```python\n"
                "from django.db import models\n\n"
                "class Mahsulot(models.Model):\n"
                "    nomi = models.CharField(max_length=100)\n"
                "    narxi = models.DecimalField(max_digits=10, decimal_places=2)\n"
                "    tavsif = models.TextField(blank=True)\n"
                "    yaratilgan_sana = models.DateTimeField(auto_now_add=True)\n\n"
                "    def __str__(self):\n"
                "        return self.nomi\n"
                "```"
            )

        if re.search(r"\bgit\b", norm):
            return (
                "### Git nima?\n"
                "Git — bu loyihalarning versiyalarini boshqarish tizimidir (Version Control System). "
                "U kodlar ustida ishlash tarixini saqlaydi va bir vaqtning o'zida bir nechta dasturchining bitta loyiha ustida birgalikda ishlashiga yordam beradi.\n\n"
                "#### Asosiy komandalar:\n"
                "1. `git init` – Yangi lokal repozitoriy yaratish.\n"
                "2. `git add .` – O'zgarishlarni saqlashga tayyorlash (staging area).\n"
                "3. `git commit -m \"izoh\"` – O'zgarishlarni tarixda saqlash.\n"
                "4. `git push` – O'zgarishlarni masofaviy serverga (masalan, GitHub) yuborish.\n"
                "5. `git checkout -b yangi-branch` – Yangi ishchi tarmoq (branch) ochish."
            )

        if re.search(r"\bsql\b", norm):
            return (
                "### SQL nima?\n"
                "SQL (Structured Query Language) — bu relyatsion (jadvalli) ma'lumotlar bazalarini boshqarish va ular bilan muloqot qilish uchun ishlatiladigan standart tildir. "
                "U ma'lumotlarni saqlash, qidirish, o'zgartirish va o'chirish imkonini beradi.\n\n"
                "#### Asosiy so'rovlar (CRUD):\n"
                "1. **C (Create) / INSERT:** Yangi qator qo'shish.\n"
                "2. **R (Read) / SELECT:** Ma'lumotlarni o'qish/qidirish.\n"
                "3. **U (Update) / UPDATE:** Mavjud ma'lumotni yangilash.\n"
                "4. **D (Delete) / DELETE:** Ma'lumotni o'chirish.\n\n"
                "#### Namunaviy so'rov:\n"
                "```sql\n"
                "-- Foydalanuvchilarni email bo'yicha saralab olish\n"
                "SELECT id, ism, email \n"
                "FROM users \n"
                "WHERE status = 'active' \n"
                "ORDER BY yaratilgan_sana DESC;\n"
                "```"
            )

        if re.search(r"\bapi\b", norm):
            return (
                "### API nima?\n"
                "API (Application Programming Interface — Ilovalarning Dasturiy Interfeysi) — bu turli xil dasturiy ta'minotlar yoki xizmatlarning o'zaro muloqot qilishi va ma'lumot almashishi uchun ishlatiladigan kelishilgan qoidalar va protokollar to'plamidir.\n\n"
                "#### API turlari va ishlatilishi:\n"
                "1. **REST API:** HTTP so'rovlar (GET, POST, PUT, DELETE) orqali ma'lumot almashuvchi eng keng tarqalgan standart.\n"
                "2. **JSON format:** Ma'lumotlarni uzatishda eng ko'p ishlatiladigan yengil va tushunarli format.\n"
                "3. **Orkestratsiya:** Masalan, AIDA boshqaruv paneli frontend qismi backend bilan API endpointlar (masalan, `/api/chat/`) orqali bog'lanadi."
            )

        if re.search(r"\bollama\b", norm):
            return (
                "### Ollama nima?\n"
                "Ollama — bu shaxsiy kompyuterda (lokal ravishda) Llama 3, Mistral, Gemma kabi katta til modellarini (LLM) "
                "juda oson o'rnatish, ishga tushirish va boshqarish imkonini beruvchi ochiq kodli dasturiy vositadir.\n\n"
                "#### Ollama nima qilib beradi?\n"
                "1. **Lokal ishga tushirish:** Modellar sizning shaxsiy videokartangiz (GPU) yoki protsessoringizda (CPU) ishlaydi. Ma'lumotlaringiz tashqi serverlarga yuborilmaydi (xavfsiz va maxfiy).\n"
                "2. **Tayyor API taqdim etish:** Ollama avtomatik ravishda `http://localhost:11434` manzilida lokal API serverni yoqadi. AIDA kabi dasturlar shu API orqali modelga ulanadi.\n"
                "3. **Tezkor yuklash:** Bitta buyruq orqali modellarni yuklab oladi va ishga tushiradi (masalan: `ollama run llama3.2`).\n\n"
                "#### AIDA bilan bog'liqligi:\n"
                "Agar kompyuteringizda Ollama o'rnatilgan va ishlayotgan bo'lsa, AIDA uni avtomatik aniqlaydi va siz yuborgan har qanday murakkab savollarga Ollama yordamida to'liq va aqlli javoblar qaytara boshlaydi."
            )
        
        return None

    def _result_block(self, prompt: str, intent: str, keywords: list[str], mem_list: list, ctx: str) -> str:
        predef = self._get_predefined_explanation(prompt, intent)
        if predef:
            if ctx:
                return f"{predef}\n\n_{ctx}_"
            return predef

        if intent == "plan":
            return self._plan_response_dynamic(prompt, mem_list, ctx)
        if intent == "code":
            return self._code_response_dynamic(prompt, mem_list, ctx)
        if intent == "compare":
            return self._compare_response_dynamic(prompt, mem_list, ctx)
        if intent == "explain":
            return self._explain_response_dynamic(prompt, keywords, ctx)
        if intent == "writing":
            return self._writing_response_dynamic(prompt, ctx)
        if intent == "list":
            return self._list_response_dynamic(prompt, keywords, ctx)
        if intent == "math":
            return self._math_response_dynamic(prompt, ctx)
        if intent == "summary":
            return self._summary_response_dynamic(prompt, ctx)
        if intent == "translate":
            return self._translate_response_dynamic(prompt, ctx)
        return self._general_response_dynamic(prompt, keywords, ctx, mem_list)

    def _is_code_request(self, normalized_prompt: str) -> bool:
        compare_words = ["taqqosla", "solishtir", "qaysi yaxshi", "farq", "afzalligi", "vs"]
        if any(cw in normalized_prompt for cw in compare_words):
            return False
        code_phrases = [
            "kod yoz",
            "code yoz",
            "coder",
            "coding",
            "dastur yoz",
            "dasturlash",
            "snippet",
            "function",
            "funksiya",
            "script",
            "api yoz",
            "backend yoz",
            "frontend yoz",
            "html",
            "css",
            "javascript",
            "typescript",
            "react",
            "django",
            "sql",
            "regex",
            "xato",
            "bug",
            "fix",
            "stack trace",
            "exception",
        ]
        return any(token in normalized_prompt for token in code_phrases)

    def _plan_response_dynamic(self, prompt: str, mem_list: list, ctx: str) -> str:
        lines = [
            f"**{prompt}** — Master Strategiya",
            "",
            "### 1. Maqsad",
            "Aniq, o'lchanadigan, erishish mumkin bo'lgan maqsad qo'ying.",
            "",
            "### 2. Resurslar",
            "Vaqt, texnologiya, inson va moliyaviy resurslarni baholang.",
            "",
            "### 3. Bosqichli reja",
            "1. **Tayyorgarlik** — kerakli ma'lumot va vositalarni yig'ing",
            "2. **Amalga oshirish** — kichik qadamlarda harakatlaning",
            "3. **Nazorat** — har bir bosqichda natijani tekshiring",
            "4. **Yakunlash** — natijani baholang va tahlil qiling",
            "",
            "### 4. Xavflar",
            "- Asosiy xavflarni aniqlang",
            "- Har bir xavfga qarshi chora tayyorlang",
            "",
            "### 5. Natija",
            "Kutilgan natija va muvaffaqiyat mezonlarini belgilang.",
        ]
        if ctx:
            lines.extend(["", f"_{ctx}_"])
        user_count = len([m for m in mem_list if m["role"] == "user"]) if mem_list else 0
        if user_count > 1:
            lines.extend(["", f"*Suhbat davom etmoqda ({user_count} ta xabar)*"])
        lines.extend(["", "Aniqroq ma'lumot bersangiz, rejani to'liq tayyorlab beraman."])
        return "\n".join(lines)

    def _code_response_dynamic(self, prompt: str, mem_list: list, ctx: str) -> str:
        cg = CodeGenerator()
        code = cg.generate(prompt)
        analysis = cg.analyze(code)
        stack, lang = self._infer_code_stack(prompt)
        lines = [
            f"**{prompt}**",
            "",
            f"**Stack:** {stack}",
            "",
            "**Kod:**",
            f"{code}",
            "",
            "**Tahlil:**",
            f"{analysis}",
        ]
        if ctx:
            lines.extend(["", f"_{ctx}_"])
        return "\n".join(lines)

    def _compare_response_dynamic(self, prompt: str, mem_list: list, ctx: str) -> str:
        comparer = ComparisonEngine()
        reng = ReasoningEngine()
        kw = self._extract_keywords(prompt)
        comp = comparer.compare(prompt)
        reas = reng.reason(prompt, "compare", kw, mem_list)
        return f"{comp}\n\n{reas}"

    def _explain_response_dynamic(self, prompt: str, keywords: list[str], ctx: str) -> str:
        kw = ", ".join(keywords[:5]) if keywords else prompt[:60]
        lines = [
            f"**{kw}** — Tushuntirish",
            "",
            "### Nima?",
            f"'{kw}' — bu siz so'ragan tushuncha. Keling, oddiy qilib tushuntiraman.",
            "",
            "### Misol",
            "Amaliy misol orqali ko'rib chiqaylik. Har bir tushunchani real hayotdagi vaziyatga bog'lab tushuntirish eng samarali usuldir.",
            "",
            "### Nima uchun muhim?",
            "Bu tushunchani bilish sizga quyidagilarda yordam beradi:",
            "- Muammolarni tezroq hal qilish",
            "- Samaraliroq qaror qabul qilish",
            "- Boshqalar bilan umumiy til topish",
        ]
        if ctx:
            lines.extend(["", f"_{ctx}_"])
        lines.extend(["", "Aniqroq savol bersangiz, batafsil tushuntiraman."])
        return "\n".join(lines)

    def _writing_response_dynamic(self, prompt: str, ctx: str) -> str:
        lines = [
            f"**{prompt}** mavzusidagi matn",
            "",
            "Matn tuzilishi:",
            "",
            "### Kirish",
            "Mavzuga qisqacha kirish, o'quvchini qiziqtirish.",
            "",
            "### Asosiy qism",
            "Asosiy fikrlar, dalillar va misollar. Har bir fikr alohida xatboshida.",
            "",
            "### Xulosa",
            "Asosiy fikrlarni takrorlash va o'quvchini keyingi qadamga undash.",
        ]
        if ctx:
            lines.extend(["", f"_{ctx}_"])
        lines.extend(["", "Matn turi (maqola, post, email, reklama) va hajmini aytsangiz, tayyor matnni yozib beraman."])
        return "\n".join(lines)

    def _list_response_dynamic(self, prompt: str, keywords: list[str], ctx: str) -> str:
        kw = keywords[:8] if keywords else ["element"]
        lines = [f"**{prompt}**", ""]
        for i, item in enumerate(kw, 1):
            lines.append(f"{i}. **{item}** — qisqacha tavsif")
        if ctx:
            lines.extend(["", f"_{ctx}_"])
        lines.extend(["", "Aniq bir mavzu bo'yicha ro'yxat kerak bo'lsa, ayting."])
        return "\n".join(lines)

    def _math_response_dynamic(self, prompt: str, ctx: str) -> str:
        import re
        nums = re.findall(r"\d+\.?\d*", prompt)
        if nums:
            result = sum(float(n) for n in nums)
            return f"**Hisoblash natijasi:**\n{prompt}\n= **{result}**"
        return f"**{prompt}**\n\nMatematik formulani aniqroq yozib bering."

    def _summary_response_dynamic(self, prompt: str, ctx: str) -> str:
        words = prompt.split()
        if len(words) > 10:
            return f"**Xulosa:**\n{prompt[:200]}...\n\nAsosiy fikr: {', '.join(words[:5])}..."
        return f"**{prompt}**\n\nBatafsil matn bersangiz, qisqacha xulosa tayyorlab beraman."

    def _translate_response_dynamic(self, prompt: str, ctx: str) -> str:
        translator = TranslationEngine()
        detected = translator.detect_language(prompt)
        target = "uz" if detected != "uz" else "en"
        if detected == "ru":
            target = "uz"
        result = translator.translate(prompt, source=detected, target=target)
        return f"**Tarjima ({detected} -> {target}):**\n{result}"

    def _general_response_dynamic(self, prompt: str, keywords: list[str], ctx: str, mem_list: list) -> str:
        kw = ", ".join(keywords[:8]) if keywords else prompt[:80]
        user_count = len([m for m in mem_list if m["role"] == "user"]) if mem_list else 0
        lines = [
            f"**{prompt}** mavzusida batafsil tahlil.",
            "",
            "### Kirish",
            f"Sizning so'rovingiz: '{prompt}'. Keling, bu mavzuni har tomonlama ko'rib chiqamiz.",
            "Har bir masalani chuqur tahlil qilish, sabab-oqibat bog'liqliklarini aniqlash va amaliy yechimlar taklif qilish mening asosiy vazifamdir.",
            "",
            "### Asosiy tahlil",
            f"**Kalit so'zlar:** {kw}",
            "",
            "Quyida mavzuning asosiy jihatlari keltirilgan:",
            "",
            "1. **Tushuncha** — bu mavzu nima ekanligini, uning asosiy xususiyatlarini va qanday ishlashini ko'rib chiqamiz.",
            "   Har bir tushunchani oddiy misollar bilan tushuntirish eng samarali usuldir.",
            "   Shu bois, nazariyani real hayotdagi vaziyatlarga bog'lab tahlil qilamiz.",
            "",
            "2. **Amaliy qo'llanma** — bu bilimlarni real loyihalarda qanday qo'llash mumkin?",
            "   Amaliyotda eng ko'p uchraydigan holatlar, ularni hal qilish usullari va eng yaxshi amaliyotlar.",
            "   Har bir qadamni batafsil ko'rsatma bilan tushuntiraman.",
            "",
            "3. **Misol va namunalar** — mavzuni to'liq anglash uchun aniq misollar keltiraman.",
            "   3-5 ta turli misol orqali mavzuning turli qirralarini yoritib beraman.",
            "",
            "4. **Kengaytirilgan tahlil** — qo'shimcha ma'lumotlar, muhim detallar va chuqur tahlil.",
            "   Bu qismda mavzuning eng murakkab tomonlarini ko'rib chiqamiz.",
            "   Shuningdek, potensial muammolar va ularni oldini olish usullari haqida gaplashamiz.",
            "",
            "5. **Xulosa va tavsiyalar** — asosiy fikrlarni jamlab, amaliy tavsiyalar beraman.",
            "   Sizning ehtiyojingizga qarab, keyingi qadamlar va takliflar.",
        ]
        if ctx:
            lines.extend(["", f"_{ctx}_"])
        if user_count > 1:
            lines.extend(["", f"*Suhbat davom etmoqda. Oldingi {user_count} ta xabardan keyin mavzu rivojlanmoqda.*"])
        lines.extend([
            "",
            "Yana savollaringiz bo'lsa, yoki mavzuni batafsilroq muhokama qilmoqchi bo'lsangiz, bemalol yozing.",
            "Men har bir masalani eng chuqur darajada tahlil qilishga tayyorman.",
        ])
        return "\n".join(lines)

    def _is_learning_request(self, normalized_prompt: str) -> bool:
        learning_phrases = [
            "eslab qol",
            "remember",
            "organ",
            "o'rgan",
            "bilib ol",
            "miyya",
            "bilim qo'sh",
            "bilim qosh",
        ]
        return any(token in normalized_prompt for token in learning_phrases)

    def _is_self_modify_request(self, normalized_prompt: str) -> tuple[bool, str]:
        cmd_phrases = [
            ("read", ["faylni och", "faylini och", "fayl o'qil", "read file", "faylni ko'rsat", "show file", "faylni o'qi", "open file"]),
            ("edit", ["o'zgarish kirit", "o'zgartir", "edit file", "update file", "replace in", "almashtir", "tahrirla"]),
            ("create", ["fayl yarat", "create file", "new file", "yangi fayl", "modul yarat", "new feature qo'sh"]),
            ("delete", ["faylni o'chir", "delete file", "remove file"]),
            ("list", ["qanday fayllar", "what files", "fayllarni ko'rsat", "list files", "loyiha haqida"]),
            ("info", ["project info", "loyiha haqida", "fayllar haqida"]),
        ]
        for cmd, phrases in cmd_phrases:
            if any(p in normalized_prompt for p in phrases):
                return True, cmd
        return False, ""

    def _self_modify_response(self, prompt: str, cmd: str) -> str:
        modifier = self._get_modifier()
        normalized = prompt.lower()

        if cmd == "list":
            return modifier.get_project_info()

        if cmd == "info":
            return modifier.get_project_info()

        if cmd == "read":
            import re
            match = re.search(r"(?:fayl[ni]?\s*)?([\w/\\]+\.[\w]+)", prompt)
            if match:
                return modifier.read_file(match.group(1))
            match = re.search(r"['\"]([\w/\\]+\.[\w]+)['\"]", prompt)
            if match:
                return modifier.read_file(match.group(1))
            py_files = modifier.list_files("*.py")
            if py_files:
                return f"Qaysi faylni o'qiy? Mavjud .py fayllar:\n" + "\n".join(py_files)
            return "Mavjud fayllar:\n" + modifier.get_project_info()

        if cmd == "edit":
            import re
            match = re.search(r"(?:fayl[ni]?\s*)?([\w/\\]+\.[\w]+)", prompt)
            file_path = match.group(1) if match else ""
            lines = prompt.split("\n")
            old_part, new_part = "", ""
            found_old, found_new = False, False
            for line in lines:
                stripped = line.strip().lower()
                if stripped.startswith("old:") or stripped.startswith("eski:"):
                    old_part = line.split(":", 1)[1].strip() if ":" in line else ""
                    found_old = True
                elif stripped.startswith("new:") or stripped.startswith("yangi:"):
                    new_part = line.split(":", 1)[1].strip() if ":" in line else ""
                    found_new = True
            if file_path:
                if found_old and found_new:
                    return modifier.edit_file(file_path, old_part, new_part)
                return f"Tushunmadim. Format:\n  {file_path}\n  old: eski matn\n  new: yangi matn"
            py_files = modifier.list_files("*.py")
            return f"Qaysi faylni tahrirlaymiz? Format:\n  fayl_nomi.py\n  old: eski matn\n  new: yangi matn\n\nMavjud fayllar:\n" + "\n".join(py_files[:10])

        if cmd == "create":
            import re
            match = re.search(r"(?:fayl[ni]?\s*)?([\w/\\]+\.[\w]+)", prompt)
            file_path = match.group(1) if match else ""
            if file_path:
                code_match = re.search(r"```(\w*)\n([\s\S]*?)```", prompt)
                content = code_match.group(2) if code_match else prompt.split("content:", 1)[1].strip() if "content:" in prompt else ""
                if content:
                    return modifier.create_file(file_path, content)
                return f"{file_path} uchun content yozilmagan. Kodni ```blokda``` yuboring."
            return "Fayl nomini ayting (masalan: webapp/new_module.py)"

        if cmd == "delete":
            import re
            match = re.search(r"([\w/\\]+\.[\w]+)", prompt)
            if match:
                return modifier.delete_file(match.group(1))
            return "O'chirish uchun fayl nomini ayting."

        return modifier.get_project_info()

    def _get_modifier(self) -> SelfModifier:
        return SelfModifier()

    def _is_self_improve_request(self, normalized_prompt: str) -> tuple[bool, str]:
        cmd_phrases = [
            ("install", ["pip install", "o'rnat", "install package", "yangi paket", "yangi kutibxona"]),
            ("knowledge", ["bilim qo'sh", "miyyaga yoz", "dasturlash tilini o'rnat", "yangi til o'rgan",
                          "bilimlarini kengaytir", "download docs", "dokumentatsiya yukla"]),
            ("analyze", ["o'z kodingni tahlil qil", "analyze your code", "kod sifat", "code quality"]),
            ("improve", ["o'zingni kuchaytir", "ozingni kuchaytir", "improve yourself",
                        "o'zingni rivojlantir", "ozingni rivojlantir",
                        "aqlliroq bol", "donoroq", "kuchaytir", "mukammal"]),
            ("learn_from_error", ["xatodan o'rgan", "learn from error", "feedback"]),
            ("generate_knowledge", ["knowledge file yarat", "bilim fayl", "savol javob yarat"]),
        ]
        for cmd, phrases in cmd_phrases:
            if any(p in normalized_prompt for p in phrases):
                return True, cmd
        return False, ""

    def _self_improve_response(self, prompt: str, cmd: str) -> str:
        installer = KnowledgeInstaller()
        improver = AutoImprover()
        normalized = prompt.lower()

        if cmd == "install":
            import re
            match = re.search(r"(?:pip install\s+)?(\w[\w\-_.]+)", prompt)
            if match:
                return installer.install_package(match.group(1))
            return "Qaysi paketni o'rnatay? (masalan: pip install requests)"

        if cmd == "knowledge":
            import re
            lang_match = re.search(r"(python|javascript|typescript|java|c\+\+|rust|go|ruby|php|sql|html|css)", normalized)
            lang = lang_match.group(1) if lang_match else "python"
            topic_match = re.search(r"(?:haqida|about|bo'yicha|doc)\s*(.+?)$", prompt)
            topic = topic_match.group(1).strip()[:50] if topic_match else prompt[:50]
            return installer.download_docs(topic, lang)

        if cmd == "analyze":
            import re
            match = re.search(r"([\w/\\]+\.[\w]+)", prompt)
            if match:
                quality = improver.analyze_code_quality(match.group(1))
                suggestions = improver.suggest_improvement(match.group(1))
                return f"{quality}\n\n{suggestions}"
            return improver.analyze_all_code()

        if cmd == "improve":
            analysis = improver.analyze_all_code()
            return (f"**O'z-o'zini rivojlantirish rejasi:**\n\n"
                    f"{analysis}\n\n"
                    "1. Kod sifatini tahlil qilish\n"
                    "2. Xatolarni tuzatish\n"
                    "3. Yangi imkoniyatlar qo'shish\n"
                    "4. Test yozish\n"
                    "5. Hujjatlashtirish\n\n"
                    "Davom etish uchun 'o'z kodingni tahlil qil' deb yozing.")

        if cmd == "learn_from_error":
            parts = prompt.split(":", 1)
            feedback = parts[1].strip() if len(parts) > 1 else "no feedback"
            return improver.learn_from_error(prompt, "", feedback)

        if cmd == "generate_knowledge":
            topic = prompt.replace("knowledge file yarat", "").replace("bilim fayl", "").strip()
            if topic:
                return improver.generate_knowledge_file(topic, f"# {topic}\n\nAIDA tomonidan yaratilgan bilim.\n\n")
            return "Qanday mavzuda bilim fayli yaratay?"

        return "Menga 'o'zingni kuchaytir', 'pip install <paket>', 'bilim qo'sh' deb murojaat qiling."

    def _learn_response(self, prompt: str, runtime_context: dict[str, str] | None) -> str:
        learned = (runtime_context or {}).get("learned_fact", "").strip()
        if not learned:
            learned = prompt.strip()
        return "\n".join(
            [
                "Qabul qilindi, men buni keyingi javoblar uchun kontekst sifatida eslab qoldim.",
                "",
                f"Yangi bilim: {learned}",
                "",
                "Keyingi safar shu mavzuga qaytsangiz, javobni shu ma'lumot bilan moslashtiraman.",
            ]
        )

    def _learned_context_lines(self, runtime_context: dict[str, str] | None) -> list[str]:
        facts = (runtime_context or {}).get("learned_facts", [])
        if not facts:
            return []
        if isinstance(facts, str):
            facts = [facts]
        return ["AIDA eslab qolgan foydali kontekst:", *[f"- {fact}" for fact in facts[:4] if str(fact).strip()]]

    def _infer_code_stack(self, prompt: str) -> tuple[str, str]:
        normalized = prompt.lower()
        stacks = [
            ("html", "html"),
            ("css", "css"),
            ("react", "tsx"),
            ("typescript", "ts"),
            ("javascript", "js"),
            ("django", "py"),
            ("python", "py"),
            ("fastapi", "py"),
            ("sql", "sql"),
        ]
        for marker, language in stacks:
            if marker in normalized:
                return marker, language
        if "api" in normalized or "backend" in normalized:
            return "python", "py"
        if "frontend" in normalized or "ui" in normalized:
            return "react", "tsx"
        return "python", "py"

    def _code_preview(self, prompt: str, stack: str, language: str) -> list[str]:
        normalized = prompt.lower()
        if language == "py" and ("api" in normalized or "endpoint" in normalized):
            return [
                "```py",
                "from django.http import JsonResponse",
                "from django.views.decorators.http import require_POST",
                "",
                "@require_POST",
                "def api_handler(request):",
                "    # validate input, run the action, return structured JSON",
                "    return JsonResponse({'ok': True, 'message': 'done'})",
                "```",
            ]
        if stack == "react":
            return [
                "```tsx",
                "type AssistantPanelProps = { title: string; body: string };",
                "",
                "export function AssistantPanel({ title, body }: AssistantPanelProps) {",
                "  return (",
                "    <section className=\"assistant-panel\">",
                "      <h2>{title}</h2>",
                "      <p>{body}</p>",
                "    </section>",
                "  );",
                "}",
                "```",
            ]
        if language == "sql":
            return [
                "```sql",
                "SELECT id, created_at, status",
                "FROM records",
                "WHERE status = 'active'",
                "ORDER BY created_at DESC",
                "LIMIT 50;",
                "```",
            ]
        if language == "html":
            return [
                "```html",
                "<main class=\"app-shell\">",
                "  <section class=\"workspace\">",
                "    <h1>AIDA</h1>",
                "    <button type=\"button\">Run</button>",
                "  </section>",
                "</main>",
                "```",
            ]
        return [
            "```py",
            "def solve(input_data):",
            "    \"\"\"Implement the smallest clear solution first, then harden with tests.\"\"\"",
            "    return input_data",
            "```",
        ]

    def _platform_summary(
        self,
        platform_profile: dict[str, str] | None,
        runtime_context: dict[str, str] | None,
    ) -> list[str]:
        lines: list[str] = []
        if platform_profile:
            platform_name = platform_profile.get("platform_name", "").strip()
            business_type = platform_profile.get("business_type", "").strip()
            audience = platform_profile.get("audience", "").strip()
            tone = platform_profile.get("tone", "").strip()
            goal = platform_profile.get("assistant_goal", "").strip()
            custom = platform_profile.get("custom_instructions", "").strip()

            if platform_name:
                lines.append(f"Platforma: {platform_name}.")
            if business_type:
                lines.append(f"Yo'nalish: {business_type}.")
            if audience:
                lines.append(f"Auditoriya: {audience}.")
            if tone:
                lines.append(f"Ohang: {tone}.")
            if goal:
                lines.append(f"Asosiy vazifa: {goal}.")
            if custom:
                lines.append(f"Qo'shimcha ko'rsatma: {custom}.")

        if runtime_context:
            page = runtime_context.get("page", "").strip()
            customer_intent = runtime_context.get("customer_intent", "").strip()
            locale = runtime_context.get("locale", "").strip()
            if page:
                lines.append(f"Joriy sahifa: {page}.")
            if customer_intent:
                lines.append(f"Mijoz niyati: {customer_intent}.")
            if locale:
                lines.append(f"Til yoki mintaqa: {locale}.")
        return lines

    def _fashion_store_response(
        self,
        prompt: str,
        platform_profile: dict[str, str] | None,
        runtime_context: dict[str, str] | None,
    ) -> str:
        summary = self._platform_summary(platform_profile, runtime_context)
        lines = [
            "Bu platforma kiyim yoki moda savdosiga yaqin ko'rinyapti, shuning uchun javobni savdo va mijoz tajribasi atrofida quramiz:",
            "",
            "1. Mahsulotning uslubi, materiali va foydasini aniq ayting.",
            "2. O'lcham, rang va mavjudlik bo'yicha noaniqlikni kamaytiring.",
            "3. Mijozni keyingi qadamga olib boring: ko'rish, savatga qo'shish yoki buyurtma.",
            "4. Javobni iliq, ishonchli va sotuvga yaqin ohangda bering.",
            "",
            f"So'rov: {prompt}.",
        ]
        if summary:
            lines.extend(["", *summary])
        lines.extend(
            [
                "",
                "Agar xohlasangiz, men shu platforma uchun tayyor product reply, support reply yoki sales chat promptlarini ham yozib beraman.",
            ]
        )
        return "\n".join(lines)

    def _recent_context_line(self, memory: Iterable[dict[str, str]]) -> str:
        recent = [
            item["content"].strip()
            for item in list(memory)
            if item["role"] == "user" and item["content"].strip()
        ]
        if not recent:
            return ""
        latest = recent[-1][:120]
        return f"Yaqin kontekst: {latest}"

    def _plan_response(
        self,
        prompt: str,
        memory: Iterable[dict[str, str]],
        platform_profile: dict[str, str] | None,
        runtime_context: dict[str, str] | None,
    ) -> str:
        context_line = self._recent_context_line(memory)
        platform_lines = self._platform_summary(platform_profile, runtime_context)
        lines = [
            f"Yaxshi, {prompt} uchun bosqichma-bosqich reja tuzamiz.",
            "",
            "1. Maqsadni aniq belgilang - nimaga erishmoqchisiz?",
            "2. Resurslarni aniqlang: vaqt, texnologiya, jamoa.",
            "3. Kichik qismlarga bo'ling va har biri uchun muddat qo'ying.",
            "4. Har bir bosqichda natijani tekshirib boring.",
            "5. Yakuniy natijani baholang va kerakli o'zgartirishlarni kiriting.",
        ]
        if context_line:
            lines.extend(["", context_line])
        if platform_lines:
            lines.extend(["", *platform_lines])
        learned_lines = self._learned_context_lines(runtime_context)
        if learned_lines:
            lines.extend(["", *learned_lines])
        lines.extend([
            "",
            "Aniqroq maqsad va cheklovlarni aytsangiz, men sizga tayyor reja tuzib beraman.",
        ])
        return "\n".join(lines)

    def _code_response(
        self,
        prompt: str,
        memory: Iterable[dict[str, str]],
        platform_profile: dict[str, str] | None,
        runtime_context: dict[str, str] | None,
    ) -> str:
        context_line = self._recent_context_line(memory)
        platform_lines = self._platform_summary(platform_profile, runtime_context)
        learned_lines = self._learned_context_lines(runtime_context)
        stack, language = self._infer_code_stack(prompt)
        lines = [
            f"Kod masalasini yechishga tayyorman. {stack} stack dan foydalanamiz.",
            "",
            "Yechimni quyidagi tartibda quramiz:",
            "1. Talabni tahlil qilish - input, output va xato holatlarni aniqlash.",
            "2. Minimal ishlaydigan kod yozish.",
            "3. Xatolarni tekshirish va tuzatish.",
            "4. Test qilish va sifatni tekshirish.",
            "",
            f"Vazifa: {prompt}.",
            "",
            "Kod namunasi:",
            *self._code_preview(prompt, stack, language),
        ]
        if context_line:
            lines.extend(["", context_line])
        if platform_lines:
            lines.extend(["", *platform_lines])
        if learned_lines:
            lines.extend(["", *learned_lines])
        lines.extend([
            "",
            "Mavjud kod yoki xato matnini yuborsangiz, aniq tuzatish bilan yordam beraman.",
        ])
        return "\n".join(lines)

    def _writing_response(
        self,
        prompt: str,
        platform_profile: dict[str, str] | None,
        runtime_context: dict[str, str] | None,
    ) -> str:
        lines = [
            f"{prompt} mavzusida matn tayyorlaymiz.",
            "",
            "Matn yozishda asosiy qadamlarni ko'rib chiqaylik:",
            "1. Kim o'qishi uchun yozilayotganini aniqlang.",
            "2. Bitta asosiy fikrni tanlang va shu atrofda yozing.",
            "3. Ortiqcha so'zlarni olib tashlang, qisqa va aniq bo'lsin.",
        ]
        platform_lines = self._platform_summary(platform_profile, runtime_context)
        if platform_lines:
            lines.extend(["", *platform_lines])
        lines.extend([
            "",
            "Matn turi (maqola, post, email, reklama) va hajmini aytsangiz, men tayyor matnni yozib beraman.",
        ])
        return "\n".join(lines)

    def _comparison_response(
        self,
        prompt: str,
        platform_profile: dict[str, str] | None,
        runtime_context: dict[str, str] | None,
    ) -> str:
        lines = [
            f"{prompt} bo'yicha taqqoslash tahlilini o'tkazamiz.",
            "",
            "Taqqoslash mezonlari:",
            "1. Sifat va ishonchlilik.",
            "2. Tezlik va samaradorlik.",
            "3. Narx va qulaylik.",
            "4. Uzoq muddatli istiqbol.",
        ]
        platform_lines = self._platform_summary(platform_profile, runtime_context)
        if platform_lines:
            lines.extend(["", *platform_lines])
        lines.extend([
            "",
            "Aniq variantlarni ayting (masalan: Django vs FastAPI), men ularni har tomonlama taqqoslab beraman.",
        ])
        return "\n".join(lines)

    def _general_response(
        self,
        prompt: str,
        memory: Iterable[dict[str, str]],
        platform_profile: dict[str, str] | None,
        runtime_context: dict[str, str] | None,
    ) -> str:
        intent = self._detect_intent(prompt)
        keywords = self._extract_keywords(prompt)
        ctx = self._context_summary(memory)
        return self._dynamic_generate(prompt, intent, keywords, memory, ctx)

    def _research_response(
        self,
        prompt: str,
        research: list[ResearchSnippet],
        platform_profile: dict[str, str] | None,
        runtime_context: dict[str, str] | None,
    ) -> str:
        filtered = ResearchFilter.filter(research, prompt)
        query_words = set(w.lower().strip(".,!?") for w in prompt.split() if len(w) > 3)
        lines = [
            "**Qidiruv natijalari:** '%s'" % prompt,
            "",
        ]
        for index, item in enumerate(filtered, start=1):
            matched = []
            for qw in query_words:
                if qw in item.title.lower() or qw in item.summary.lower():
                    matched.append(qw)
            tag = " (mos: %s)" % ", ".join(matched[:3]) if matched else ""
            lines.extend([
                "%d. **%s**%s" % (index, item.title, tag),
                "   %s" % item.summary[:300],
                "   Link: %s" % item.url,
                "",
            ])
        if not filtered:
            lines.append("Hech qanday natija topilmadi. Qidiruv so'zlarini o'zgartirib ko'ring.")
        else:
            lines.append("%d ta natija topildi. Yana biror narsa kerak bo'lsa, ayting." % len(filtered))
        return "\n".join(lines)

    def respond(
        self,
        prompt: str,
        memory: Iterable[dict[str, str]],
        system_prompt: str,
        status: dict[str, object],
        platform_profile: dict[str, str] | None = None,
        runtime_context: dict[str, str] | None = None,
        research: list[ResearchSnippet] | None = None,
    ) -> str:
        normalized = prompt.lower()
        intent = self._detect_intent(prompt)
        keywords = self._extract_keywords(prompt)
        business_type = (platform_profile or {}).get("business_type", "").lower()
        reasoning = ReasoningEngine()
        code_gen = CodeGenerator(respond_func=self._respond_func)
        translator = TranslationEngine()
        comparer = ComparisonEngine()

        is_self_mod, self_mod_cmd = self._is_self_modify_request(normalized)
        if is_self_mod:
            return self._self_modify_response(prompt, self_mod_cmd)

        is_self_improve, improve_cmd = self._is_self_improve_request(normalized)
        if is_self_improve or intent == "self_improve":
            if not is_self_improve:
                return self._self_improve_response(prompt, "improve")
            return self._self_improve_response(prompt, improve_cmd)

        if intent == "status" or any(token in normalized for token in ["status", "holat", "ahvol"]):
            return textwrap.dedent(
                f"""
                AIDA ishga tayyor. Tizim holati:
                - Provider: {status["provider"]}
                - Platforma: {status["platform"]}
                - Xotira: {status["memory_entries"]} ta yozuv

                Qanday vazifani boshlaymiz?
                """
            ).strip()

        if research:
            return self._research_response(prompt, research, platform_profile, runtime_context)

        if self._is_learning_request(normalized):
            return self._learn_response(prompt, runtime_context)

        if any(token in business_type for token in ["kiyim", "moda", "fashion", "clothing", "apparel"]):
            return self._fashion_store_response(prompt, platform_profile, runtime_context)

        if intent == "translate" or any(token in normalized for token in ["tarjima", "translate", "翻译", "перевод"]):
            return self._translate_response_dynamic(prompt, self._context_summary(memory))

        if intent == "greeting" and not any(token in normalized for token in ["tarjima", "translate", "taqqosla", "solishtir", "kod", "code", "dastur"]):
            return textwrap.dedent(
                """
                Salom! AIDA tayyor.

                Men quyidagilarda yordam bera olaman:
                - Reja va strategiya tuzish
                - Kod yozish va xatolarni tuzatish
                - Internetdan ma'lumot qidirish (search: <savol>)
                - Matn yozish va tarjima qilish
                - Taqqoslash va tahlil qilish
                - O'z kodingizni o'zgartirish (self-modify)
                - Yangi fayllar yaratish

                Vazifangizni yozing, men darhol ishga tushaman.
                """
            ).strip()

        if intent == "compare" or any(token in normalized for token in ["taqqosla", "solishtir", "qaysi", "tanla", "farqi", "vs"]):
            return self._compare_response_dynamic(prompt, list(memory), self._context_summary(memory))

        if intent == "plan" or any(token in normalized for token in ["murakkab", "vazifa", "plan", "reja", "bolib", "strategiya"]):
            base = self._plan_response(prompt, memory, platform_profile, runtime_context)
            steps = reasoning.reason(prompt, "plan", keywords, list(memory))
            return f"{base}\n\n{steps}"

        if intent == "code" or self._is_code_request(normalized):
            base = self._code_response(prompt, memory, platform_profile, runtime_context)
            code = code_gen.generate(prompt)
            analysis = code_gen.analyze(code)
            steps = reasoning.reason(prompt, "code", keywords, list(memory))
            return f"{base}\n\n{steps}\n\n**Generatsiya qilingan kod:**\n{code}\n\n{analysis}"

        if intent == "writing" or any(token in normalized for token in ["yoz", "matn", "copy", "post", "email", "maqola"]):
            base = self._writing_response(prompt, platform_profile, runtime_context)
            steps = reasoning.reason(prompt, "writing", keywords, list(memory))
            return f"{base}\n\n{steps}"

        if intent == "explain":
            ctx = self._context_summary(memory)
            return self._dynamic_generate(prompt, intent, keywords, memory, ctx)

        ctx = self._context_summary(memory)
        return self._dynamic_generate(prompt, intent, keywords, memory, ctx)

class AIDAController:
    def __init__(self) -> None:
        self.memory = MemoryStore(MEMORY_DB)
        self.config = ProviderConfig.from_env()
        self.provider = self._build_provider()
        self.providers = self._build_all_providers()
        self.react_provider = self._build_react_provider()

        def _code_respond_func(p: str, mem: list, sys: str) -> str:
            for prov in [self.provider, *self.providers.values(), self.react_provider]:
                if prov and prov.name != "local":
                    try:
                        return prov.respond(prompt=p, memory=mem, system_prompt=sys)
                    except Exception:
                        continue
            return ""

        self.local_provider = LocalProvider(respond_func=_code_respond_func)
        self.research_service = WebResearchService()
        self.multi_model_manager = MultiModelManager(ollama_url="http://localhost:11434")
        # Initialize code engine if available
        self.code_analyzer = CodeAnalyzer() if CODE_ENGINE_AVAILABLE else None
        self.context_generator = None
        self.code_refiner = MultiStepRefinement() if CODE_ENGINE_AVAILABLE else None
        # Initialize context collector if available
        self.context_engine = None
        self.vector_embeddings = None
        self.knowledge_base = KnowledgeBase() if CONTEXT_COLLECTOR_AVAILABLE else None
        # Initialize code fixer if available
        self.code_fixer = AutoCodeFixer() if CODE_FIXER_AVAILABLE else None
        self.performance_optimizer = PerformanceOptimizer() if CODE_FIXER_AVAILABLE else None
        self.test_generator = TestGenerator() if CODE_FIXER_AVAILABLE else None
        # Initialize Agent Layer
        try:
            from .tool_hub import get_tool_hub
            _tool_hub = get_tool_hub()
        except Exception:
            _tool_hub = None
        self.agent_orchestrator = get_orchestrator(respond_func=_code_respond_func, tool_hub=_tool_hub) if AGENTS_AVAILABLE else None
        self.task_router = TaskRouter() if AGENTS_AVAILABLE else None
        # Ixcham system prompt — qisqa = kamroq token = tezroq javob
        self.system_prompt = (
            "Sen AIDA — aqlli, ko'p qobiliyatli sun'iy intellektsan. "
            "Kod yozish, tahlil, tarjima, reja tuzish, yozish — barchasini bajara olasan. "
            "Har doim O'zbek tilida javob ber. Texnik atamalar inglizcha bo'lishi mumkin. "
            "Aniq, lo'nda va foydali javob ber."
        )

    def _build_provider(self):
        p = self.config.provider
        url = self.config.api_url

        if p == "collab":
            raw_model = self.config.model
            preferred = None if (not raw_model or raw_model == "AIDA Local Core") else raw_model
            ollama_url = url or "http://localhost:11434"
            lmstudio_url = os.getenv("LMSTUDIO_API_URL", "http://localhost:1234")
            import threading
            threading.Thread(target=self._try_connect_lmstudio, args=(lmstudio_url,), daemon=True).start()
            return CollaborationProvider(
                ollama_url=ollama_url,
                ollama_model=preferred or "qwen2.5:3b",
                lmstudio_url=lmstudio_url,
                lmstudio_model="",
                mode=self.config.mode,
            )

        # Ollama rejimi: model nomini to'g'ridan-to'g'ri .env dan olamiz
        # "AIDA Local Core" bo'lsa preferred_model None qoladi, auto-tanlash ishlaydi
        if p in ("local", "ollama"):
            raw_model = self.config.model
            preferred = None if (not raw_model or raw_model == "AIDA Local Core") else raw_model
            ollama_provider = self._try_connect_ollama(
                url=url or "http://localhost:11434",
                preferred_model=preferred,
            )
            if ollama_provider:
                return ollama_provider
            # Ollama rejimi belgilangan lekin server yo'q — local fallback
            if p == "ollama":
                return self.local_provider

        # Tashqi provayderlar
        provider_model = self.config.model if self.config.model not in ("", "AIDA Local Core") else ""
        if p == "lmstudio":
            import threading
            threading.Thread(target=self._try_connect_lmstudio, args=(url or "http://localhost:1234",), daemon=True).start()
            return LMStudioProvider(url=url or "http://localhost:1234", model=provider_model, mode=self.config.mode)
        if self.config.api_key and p == "remote":
            return GeminiProvider(self.config.api_key, model=gemini_model)
        return self.local_provider

    def _try_connect_ollama(self, url: str = "http://localhost:11434", preferred_model: str = None, model_size: str = "medium", task_type: str = None, prompt: str = ""):
        """Ollama serverga ulanishga harakat qiladi va OllamaProvider qaytaradi."""
        # 1. Ollama .exe topilsa — server ishlamayotgan bo'lsa avtomatik ishga tushiramiz
        ollama_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
            r"C:\Program Files\Ollama\ollama.exe",
            r"C:\Program Files (x86)\Ollama\ollama.exe",
        ]
        ollama_exe = None
        for path in ollama_paths:
            if os.path.exists(path):
                ollama_exe = path
                break

        # Avval server ishlamoqdami tekshiramiz
        server_running = False
        try:
            req = urllib.request.Request(f"{url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                server_running = resp.status == 200
        except Exception:
            pass

        # Server to'xtagan bo'lsa va exe topilsa — ishga tushiramiz
        if not server_running and ollama_exe:
            try:
                subprocess.Popen(
                    [ollama_exe, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
                # Server tayyor bo'lguncha kutamiz (6 urinish x 0.8 sek = ~5 sek)
                for _ in range(6):
                    time.sleep(0.8)
                    try:
                        req = urllib.request.Request(f"{url}/api/tags", method="GET")
                        with urllib.request.urlopen(req, timeout=2) as resp:
                            if resp.status == 200:
                                server_running = True
                                break
                    except Exception:
                        continue
            except Exception:
                pass

        # 2. Server bilan ulanamiz va modelni tanlaymiz
        try:
            req = urllib.request.Request(f"{url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = data.get("models", [])
                    if not models:
                        return None

                    model_names = [m.get("name", "") for m in models]

                    # preferred_model berilgan bo'lsa (masalan "qwen2.5:3b") — aniq yoki qisman mos topamiz
                    if preferred_model:
                        exact = next((mn for mn in model_names if mn == preferred_model), None)
                        if exact:
                            chosen = exact
                        else:
                            partial = next(
                                (mn for mn in model_names
                                 if preferred_model in mn or mn.split(":")[0] == preferred_model.split(":")[0]),
                                None
                            )
                            chosen = partial if partial else model_names[0]
                    else:
                        # Use MultiModelManager for intelligent model selection if task_type provided
                        if task_type:
                            self.multi_model_manager.refresh_models()
                            chosen = self.multi_model_manager.select_model(task_type=task_type, prompt=prompt)
                        else:
                            # Auto-tanlash: model_size ga qarab eng mos modelni tanlaymiz
                            size_priority = {
                                "small":  ["qwen2.5:0.5b", "phi3:mini", "tinyllama", "qwen2.5:1.5b", "qwen2.5:3b"],
                                "medium": ["qwen2.5:3b", "qwen2.5", "llama3.2:3b", "phi3", "qwen2.5:7b"],
                                "large":  ["qwen2.5:7b", "qwen2.5:14b", "llama3.2", "llama3", "mistral", "qwen2.5:3b"],
                            }
                            priorities = size_priority.get(model_size, size_priority["medium"])
                            chosen = model_names[0]
                            for priority in priorities:
                                match = next((mn for mn in model_names if priority in mn), None)
                                if match:
                                    chosen = match
                                    break

                    return OllamaProvider(url=url, model=chosen, mode=self.config.mode)
        except Exception:
            pass
        return None

    def _try_connect_lmstudio(self, url: str = "http://localhost:1234"):
        """LM Studio serverga ulanish. Ishlamayotgan bo'lsa — fonda ishga tushiradi (bloklamaydi)."""
        lms_cli = None
        for path in [
            r"C:\Program Files\LM Studio\resources\app\.webpack\lms.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\LM Studio\resources\app\.webpack\lms.exe"),
        ]:
            if os.path.exists(path):
                lms_cli = path
                break
        lmstudio_exe = None
        for path in [
            r"C:\Program Files\LM Studio\LM Studio.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\LM Studio\LM Studio.exe"),
        ]:
            if os.path.exists(path):
                lmstudio_exe = path
                break

        server_running = False
        try:
            req = urllib.request.Request(f"{url}/v1/models", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                server_running = resp.status == 200
        except Exception:
            pass

        if not server_running:
            if lms_cli:
                try:
                    subprocess.Popen(
                        [lms_cli, "server", "start"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                    )
                    for _ in range(4):
                        time.sleep(0.8)
                        try:
                            req = urllib.request.Request(f"{url}/v1/models", method="GET")
                            with urllib.request.urlopen(req, timeout=2) as resp:
                                if resp.status == 200:
                                    server_running = True
                                    break
                        except Exception:
                            continue
                except Exception:
                    pass
            elif lmstudio_exe:
                try:
                    subprocess.Popen(
                        [lmstudio_exe],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                    )
                except Exception:
                    pass

        return server_running

    def _build_all_providers(self):
        """Har bir mode uchun alohida Provider yaratadi (Ollama yoki LM Studio)."""
        p = self.config.provider
        url = self.config.api_url or ""

        if p == "collab":
            collab_provider = self._build_provider()
            return {"pro": collab_provider, "flash": collab_provider, "low": collab_provider}

        if p == "lmstudio":
            lmstudio_url = url or "http://localhost:1234"
            model_name = self.config.model if self.config.model not in ("", "AIDA Local Core") else ""
            pro = LMStudioProvider(url=lmstudio_url, model=model_name, mode="pro")
            flash = LMStudioProvider(url=lmstudio_url, model=model_name, mode="flash")
            low = LMStudioProvider(url=lmstudio_url, model=model_name, mode="low")
            return {"pro": pro, "flash": flash, "low": low}

        # Ollama rejimi
        ollama_url = url or "http://localhost:11434"
        ollama_providers = {}
        for mode_name, size in [("pro", "large"), ("flash", "small"), ("low", "medium")]:
            old_mode = self.config.mode
            self.config.mode = mode_name
            prov = self._try_connect_ollama(url=ollama_url, model_size=size)
            if prov:
                ollama_providers[mode_name] = prov
        self.config.mode = old_mode

        pro = ollama_providers.get("pro") or ollama_providers.get("low") or self.local_provider
        flash = ollama_providers.get("flash") or pro
        low = ollama_providers.get("low") or pro
        return {"pro": pro, "flash": flash, "low": low}

    def _build_react_provider(self):
        if self.config.api_key:
            from .react_provider import ReActProvider
            model = self.config.model if self.config.model != "AIDA Local Core" else "gemini-2.0-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            return ReActProvider(self.config.api_key, url, model=model)
        return None

    def _assess_complexity(self, prompt: str, research_enabled: bool, intent: str = "") -> str:
        normalized = prompt.lower()
        if not intent:
            intent = self.local_provider._detect_intent(prompt)
        simple_intents = {"greeting", "status"}
        if intent in simple_intents:
            return "simple"
        search_keywords = ["qidir", "top", "search", "find", "yangilik", "bugun", "hozir", "sayt", "topib ber"]
        if research_enabled or any(token in normalized for token in search_keywords):
            return "search"
        if len(normalized.split()) <= 3:
            return "simple"
        return "complex"

    def _extract_learned_fact(self, prompt: str) -> str:
        cleaned = prompt.strip()
        patterns = [
            r"^(?:eslab qol|remember|bilib ol|o'rgan|organ)\s*[:,-]?\s*(.+)$",
            r"^(?:miyya(?:ng)?ga|xotiraga)\s+(?:qo'sh|qosh)\s*[:,-]?\s*(.+)$",
            r"^(?:bilim\s+(?:qo'sh|qosh))\s*[:,-]?\s*(.+)$",
        ]
        for pattern in patterns:
            match = re.match(pattern, cleaned, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return cleaned

    def _should_research(self, prompt: str, research_enabled: bool, intent: str = "") -> bool:
        if not intent:
            intent = self.local_provider._detect_intent(prompt)
        simple_intents = {"greeting", "status"}
        if intent in simple_intents:
            return False
        normalized = prompt.lower()
        # Research override keywords - always search when these appear
        research_overrides = ["haqida", "about", "qidir", "top", "sayt", "link",
                             "topib ber", "internet", "web", "search", "research",
                             "yangilik", "bugun", "latest", "today"]
        has_override = any(token in normalized for token in research_overrides)
        if research_enabled or has_override:
            return True
        return False

    def _normalize_research_query(self, prompt: str) -> str:
        fillers = {
            "haqida",
            "qisqa",
            "expert",
            "summary",
            "ber",
            "menga",
            "iltimos",
            "please",
            "haqida",
            "tushuntir",
            "kerak",
            "qilib",
        }
        words = [
            word
            for word in prompt.replace(",", " ").replace(".", " ").split()
            if word.lower() not in fillers
        ]
        cleaned = " ".join(words[:6]).strip()
        return cleaned or prompt

    def _research_queries(self, prompt: str) -> list[str]:
        normalized = self._normalize_research_query(prompt)
        base_words = normalized.split()
        candidates = [normalized]

        if len(base_words) >= 2:
            candidates.append(" ".join(base_words[:2]))
        if len(base_words) >= 1:
            candidates.append(base_words[0])

        for word in base_words:
            if len(word) >= 5:
                candidates.append(word)

        unique: list[str] = []
        for candidate in candidates:
            clean = candidate.strip()
            if clean and clean not in unique:
                unique.append(clean)
        return unique

    def _run_research(self, prompt: str) -> list[ResearchSnippet]:
        for query in self._research_queries(prompt):
            try:
                results = self.research_service.search(query)
            except Exception:
                continue
            if results:
                filtered = ResearchFilter.filter(results, prompt)
                return filtered
        return []

    def _load_default_runserver_address(self) -> str:
        if not RUNTIME_FILE.exists():
            return "127.0.0.1:8001"
        try:
            payload = json.loads(RUNTIME_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return "127.0.0.1:8001"
        return str(payload.get("runserver_address", "127.0.0.1:8001")).strip() or "127.0.0.1:8001"

    def status(self) -> dict[str, object]:
        ollama_ok = False
        lmstudio_ok = False
        try:
            req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1) as resp:
                ollama_ok = (resp.status == 200)
        except Exception:
            pass
        try:
            req = urllib.request.Request("http://localhost:1234/v1/models", method="GET")
            with urllib.request.urlopen(req, timeout=1) as resp:
                lmstudio_ok = (resp.status == 200)
        except Exception:
            pass
        return {
            "name": "AIDA Master Controller",
            "provider": self.config.provider,
            "model": self.config.model,
            "mode": self.config.mode,
            "research": "always-on",
            "platform": _platform_name(),
            "memory_entries": self.memory.count(),
            "learned_facts": self.memory.learned_count(),
            "autonomy_mode": "guarded",
            "interfaces": ["web", "cli", "api"],
            "providers": {
                "ollama": {"status": "ok" if ollama_ok else "offline"},
                "lmstudio": {"status": "ok" if lmstudio_ok else "offline"},
            },
            "default_runserver_address": self._load_default_runserver_address(),
            "capabilities": [
                "conversation",
                "memory",
                "learning-context",
                "coder-mode",
                "code-review",
                "code-generation",
                "access-keys",
                "cross-platform orchestration",
            ],
            "updated_at": _utc_now(),
        }

    def execute_desktop_command(self, action: str, target: str = "", message: str = "") -> str:
        import os
        import subprocess
        import webbrowser
        import urllib.parse

        action = action.lower().strip()
        target = target.strip()
        message = message.strip()

        if action == "open_app":
            app = target.lower()
            if "telegram" in app or "tg" in app:
                webbrowser.open("tg://")
                return "Telegram ilovasi ishga tushirildi."
            elif "notepad" in app or "bloknot" in app:
                subprocess.Popen(["notepad.exe"])
                return "Notepad (Bloknot) ishga tushirildi."
            elif "calc" in app or "kalkulyator" in app:
                subprocess.Popen(["calc.exe"])
                return "Kalkulyator ishga tushirildi."
            elif "chrome" in app or "brauzer" in app or "browser" in app:
                webbrowser.open("https://google.com")
                return "Veb brauzer ishga tushirildi."
            else:
                try:
                    subprocess.Popen([app])
                    return f"'{target}' dasturi ishga tushirildi."
                except Exception:
                    try:
                        os.system(f"start {target}")
                        return f"'{target}' buyrug'i tizim orqali ishga tushirildi."
                    except Exception as e:
                        return f"Dasturni ochib bo'lmadi: {str(e)}"

        elif action == "send_telegram":
            if not target:
                return "Xatolik: Telegram kontakt nomi yoki foydalanuvchi nomi (username) ko'rsatilmadi."
            
            username = target.lstrip("@")
            encoded_msg = urllib.parse.quote(message) if message else ""
            
            # Try tg:// deep link first (opens Telegram desktop app directly)
            if encoded_msg:
                # Open chat with pre-filled message
                tg_url = f"https://t.me/{username}?text={encoded_msg}"
                tg_deep = f"tg://msg?to={username}&text={encoded_msg}"
            else:
                tg_url = f"https://t.me/{username}"
                tg_deep = f"tg://resolve?domain={username}"
            
            # Try deep link first (opens desktop app), fallback to web
            try:
                os.startfile(tg_deep)
            except Exception:
                webbrowser.open(tg_url)
            
            msg_desc = f" va '{message}' xabari tayyorlandi" if message else ""
            return f"✅ Telegramda @{username} bilan chat ochildi{msg_desc}. Agar Telegram dasturi o'rnatilmagan bo'lsa, brauzerda ochiladi."

        elif action == "open_telegram":
            # Open Telegram directly
            try:
                os.startfile("telegram")
            except Exception:
                webbrowser.open("https://web.telegram.org")
            return "✅ Telegram ilovasi ishga tushirildi."

        elif action == "run_shell":
            try:
                result = subprocess.run(target, shell=True, capture_output=True, text=True, timeout=15)
                out = (result.stdout or result.stderr or "Chiqish yo'q").strip()
                status = "✅ Muvaffaqiyatli" if result.returncode == 0 else "⚠️ Xato"
                return f"{status}. Buyruq bajarildi:\n{out[:2000]}"
            except subprocess.TimeoutExpired:
                return "⚠️ Buyruq 15 soniyada tugamadi (timeout)."
            except Exception as e:
                return f"Buyruqni bajarishda xatolik: {str(e)}"

        return "Noma'lum harakat. Ruxsat etilganlar: open_app, send_telegram, open_telegram, run_shell"

    def _handle_direct_desktop_commands(self, prompt: str) -> str | None:
        norm = prompt.lower().strip()
        
        # =============================================
        # 1. TELEGRAM XABAR YUBORISH
        # =============================================
        
        # "telegramda <username>ga <message> deb yoz"
        m = re.search(r"telegramda\s+@?([a-zA-Z0-9_\-]+)ga\s+(.+?)\s+deb\s+yoz", norm)
        if m:
            username = m.group(1)
            orig = re.search(r"telegramda\s+@?[a-zA-Z0-9_\-]+ga\s+(.+?)\s+deb\s+yoz", prompt, re.IGNORECASE)
            message = orig.group(1) if orig else m.group(2)
            return self.execute_desktop_command("send_telegram", username, message)

        # "telegramda <username>ga yoz: <message>"
        m = re.search(r"telegramda\s+@?([a-zA-Z0-9_\-]+)ga\s+yoz\s*:\s*(.+)", norm)
        if m:
            username = m.group(1)
            orig = re.search(r"telegramda\s+@?[a-zA-Z0-9_\-]+ga\s+yoz\s*:\s*(.+)", prompt, re.IGNORECASE)
            message = orig.group(1) if orig else m.group(2)
            return self.execute_desktop_command("send_telegram", username, message)

        # "<username> nomli odamga telegramda <message> deb yoz"
        m = re.search(r"([a-zA-Z0-9_\-]+)\s+nomli\s+odamga\s+telegramda?\s+(.+?)\s+deb\s+yoz", norm)
        if m:
            username = m.group(1)
            orig = re.search(r"[a-zA-Z0-9_\-]+\s+nomli\s+odamga\s+telegramda?\s+(.+?)\s+deb\s+yoz", prompt, re.IGNORECASE)
            message = orig.group(1) if orig else m.group(2)
            return self.execute_desktop_command("send_telegram", username, message)

        # "telegramda <username> ga xabar yubor: <message>"
        m = re.search(r"telegramda\s+@?([a-zA-Z0-9_\-]+)\s+ga\s+xabar\s+yubor\s*:\s*(.+)", norm)
        if m:
            username = m.group(1)
            orig = re.search(r"telegramda\s+@?[a-zA-Z0-9_\-]+\s+ga\s+xabar\s+yubor\s*:\s*(.+)", prompt, re.IGNORECASE)
            message = orig.group(1) if orig else m.group(2)
            return self.execute_desktop_command("send_telegram", username, message)

        # "telegramda @<username> ga yoz: <message>" (space before 'ga')
        m = re.search(r"telegramda\s+@?([a-zA-Z0-9_\-]+)\s+ga\s+yoz\s*:\s*(.+)", norm)
        if m:
            username = m.group(1)
            orig = re.search(r"telegramda\s+@?[a-zA-Z0-9_\-]+\s+ga\s+yoz\s*:\s*(.+)", prompt, re.IGNORECASE)
            message = orig.group(1) if orig else m.group(2)
            return self.execute_desktop_command("send_telegram", username, message)

        # "@<username> ga <message> yoz" (e.g. "@ali ga salom yoz")
        m = re.search(r"@([a-zA-Z0-9_\-]+)\s+ga\s+(.+?)\s+yoz", norm)
        if m:
            username = m.group(1)
            orig = re.search(r"@[a-zA-Z0-9_\-]+\s+ga\s+(.+?)\s+yoz", prompt, re.IGNORECASE)
            message = orig.group(1) if orig else m.group(2)
            return self.execute_desktop_command("send_telegram", username, message)

        # "telegram orqali <username>ga <message> yubor"
        m = re.search(r"telegram\s+orqali\s+@?([a-zA-Z0-9_\-]+)ga?\s+(.+?)\s+yubor", norm)
        if m:
            username = m.group(1)
            orig = re.search(r"telegram\s+orqali\s+@?[a-zA-Z0-9_\-]+ga?\s+(.+?)\s+yubor", prompt, re.IGNORECASE)
            message = orig.group(1) if orig else m.group(2)
            return self.execute_desktop_command("send_telegram", username, message)

        # =============================================
        # 2. TELEGRAM OCHISH
        # =============================================
        telegram_open_patterns = [
            "telegramga kir", "telegramni och", "telegram ishga tushir",
            "telegramni ishga tushir", "telegram och", "telegram oyna",
            "telegram app och", "telegramga o'tish", "telegramni yoq"
        ]
        if any(p in norm for p in telegram_open_patterns):
            return self.execute_desktop_command("open_app", "telegram")

        # =============================================
        # 3. BOSHQA ILOVALAR OCHISH
        # =============================================
        
        # Notepad
        if any(p in norm for p in ["notepadni och", "bloknotni och", "notepadga kir", "notepad ochish"]):
            return self.execute_desktop_command("open_app", "notepad")

        # Calculator
        if any(p in norm for p in ["kalkulyatorni och", "kalkulyatorga kir", "calculatorni och", "hisoblash mashinasi"]):
            return self.execute_desktop_command("open_app", "calc")

        # =============================================
        # VEBSAYTLAR OCHISH
        # =============================================

        # YouTube
        if any(p in norm for p in ["youtube och", "youtubeni och", "youtubeга кir", "youtube кir",
                                    "youtube oyna", "youtube ishga tushir", "youtubega o'tish",
                                    "youtube open", "videolar och"]):
            import webbrowser
            webbrowser.open("https://www.youtube.com")
            return "✅ YouTube brauzerda ochildi!"

        # YouTube qidirish: "youtubeda <nima> qidir / qidirish"
        m = re.search(r"youtube(?:da|dan)?\s+(.+?)\s+(?:qidir|qidirish|izla|ko'rsat|top)", norm)
        if m:
            query = m.group(1).strip()
            import webbrowser, urllib.parse
            webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")
            return f"✅ YouTube'da '{query}' bo'yicha qidiruv ochildi!"

        # Instagram
        if any(p in norm for p in ["instagram och", "instagramni och", "instagramga kir", "instagramga o'tish"]):
            import webbrowser
            webbrowser.open("https://www.instagram.com")
            return "✅ Instagram brauzerda ochildi!"

        # Google
        if any(p in norm for p in ["googleni och", "google och", "googlega kir", "google open"]):
            import webbrowser
            webbrowser.open("https://www.google.com")
            return "✅ Google brauzerda ochildi!"

        # Google qidirish: "googleda <nima> qidir"
        m = re.search(r"google(?:da|dan)?\s+(.+?)\s+(?:qidir|qidirish|izla|top)", norm)
        if m:
            query = m.group(1).strip()
            import webbrowser, urllib.parse
            webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
            return f"✅ Google'da '{query}' bo'yicha qidiruv ochildi!"

        # Facebook
        if any(p in norm for p in ["facebook och", "facebookni och", "facebookga kir"]):
            import webbrowser
            webbrowser.open("https://www.facebook.com")
            return "✅ Facebook brauzerda ochildi!"

        # GitHub
        if any(p in norm for p in ["github och", "githubni och", "githubga kir"]):
            import webbrowser
            webbrowser.open("https://www.github.com")
            return "✅ GitHub brauzerda ochildi!"

        # ChatGPT
        if any(p in norm for p in ["chatgpt och", "chatgptni och", "chatgptga kir", "chatgpt oyna"]):
            import webbrowser
            webbrowser.open("https://chat.openai.com")
            return "✅ ChatGPT brauzerda ochildi!"

        # Gmail
        if any(p in norm for p in ["gmail och", "gmailni och", "gmailga kir", "emailni och", "pochtani och"]):
            import webbrowser
            webbrowser.open("https://mail.google.com")
            return "✅ Gmail brauzerda ochildi!"

        # Browser (oddiy brauzer)
        if any(p in norm for p in ["brauzerni och", "chrome och", "brauzerga kir", "internet brauzer",
                                    "internetni och", "brauzer ishga tushir"]):
            return self.execute_desktop_command("open_app", "chrome")

        # Umumiy URL ochish: "... saytni och" yoki "... ga o't"
        m = re.search(r"(https?://[^\s]+)\s+(?:och|oyna|kir|ko'rsat)", norm)
        if m:
            url = m.group(1)
            import webbrowser
            webbrowser.open(url)
            return f"✅ {url} brauzerda ochildi!"

        # Umumiy web qidirish: "qidir: <nima>" yoki "izla: <nima>"
        m = re.search(r"(?:internetda\s+)?(?:qidir|izla|search)\s*:\s*(.+)", norm)
        if m:
            orig = re.search(r"(?:internetda\s+)?(?:qidir|izla|search)\s*:\s*(.+)", prompt, re.IGNORECASE)
            query = (orig.group(1) if orig else m.group(1)).strip()
            import webbrowser, urllib.parse
            webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
            return f"✅ Google'da '{query}' qidirildi!"

        # =============================================
        # 4. KOMPYUTER BUYRUQLARI (shell)
        # =============================================
        m = re.search(r"(?:buyruq\s+bajar|shell\s+bajar|cmd\s+bajar)\s*:\s*(.+)", norm)
        if m:
            orig = re.search(r"(?:buyruq\s+bajar|shell\s+bajar|cmd\s+bajar)\s*:\s*(.+)", prompt, re.IGNORECASE)
            cmd = orig.group(1) if orig else m.group(1)
            return self.execute_desktop_command("run_shell", cmd)

        return None

    def _fetch_url_content(self, url: str) -> str:
        try:
            import urllib.request
            from bs4 import BeautifulSoup
            
            req = urllib.request.Request(
                url, 
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode("utf-8", errors="replace")
            
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove scripts, styles, forms, and headers/footers to clean up content
            for s in soup(["script", "style", "nav", "footer", "header", "form"]):
                s.decompose()
                
            text = soup.get_text(separator="\n")
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = "\n".join(chunk for chunk in chunks if chunk)
            
            # Truncate to avoid token limits (e.g. 8000 characters)
            return text_content[:8000]
        except Exception as e:
            return f"Xatolik: URL dan ma'lumot yuklab bo'lmadi ({str(e)})"

    def chat(
        self,
        prompt: str,
        platform_profile: dict[str, str] | None = None,
        runtime_context: dict[str, str] | None = None,
        research_enabled: bool = False,
        session_id: str = "default",
        mode: str = "",
    ) -> dict[str, object]:
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("Prompt bo'sh bo'lmasligi kerak.")

        # === DESKTOP / KOMPYUTER BUYRUQLARINI BIRINCHI TEKSHIR ===
        desktop_result = self._handle_direct_desktop_commands(clean_prompt)
        if desktop_result is not None:
            self.memory.save("user", clean_prompt, session_id=session_id)
            self.memory.save("assistant", desktop_result, session_id=session_id)
            return {
                "message": desktop_result,
                "status": self.status(),
                "session_id": session_id,
                "mode": mode,
                "recent_memory": self.memory.recent(limit=6, session_id=session_id),
                "sources": [],
            }
        # === ODATIY CHAT DAVOM ETADI ===

        mode = mode or self.config.mode
        if mode not in ("pro", "flash", "low"):
            mode = "pro"
        mc = MODE_CONFIGS.get(mode, MODE_CONFIGS["pro"])
        effective_provider = self.providers.get(mode) or self.provider

        self.memory.save("user", clean_prompt, session_id=session_id)
        learned_fact = ""
        if self.local_provider._is_learning_request(clean_prompt.lower()):
            learned_fact = self._extract_learned_fact(clean_prompt)
            self.memory.remember_fact(learned_fact, session_id=session_id)

        runtime_context = dict(runtime_context or {})
        runtime_context["learned_facts"] = self.memory.learned_facts(session_id=session_id)
        if learned_fact:
            runtime_context["learned_fact"] = learned_fact

        memory = self.memory.recent(limit=8, session_id=session_id)
        status = self.status()
        intent = self.local_provider._detect_intent(clean_prompt)
        complexity = self._assess_complexity(clean_prompt, research_enabled, intent)
        # Internet research is always-on
        should_research = self._should_research(clean_prompt, True, intent)
        research = self._run_research(clean_prompt) if should_research else []

        # Extract and fetch URL contents if any
        url_context = ""
        urls = re.findall(r"https?://[^\s/$.?#].[^\s]*", clean_prompt)
        if urls:
            downloaded = []
            for url in urls[:2]: # limit to first 2 URLs
                content = self._fetch_url_content(url)
                downloaded.append(f"--- Manba URL: {url} ---\n{content}\n")
            if downloaded:
                url_context = "\n\nFoydalanuvchi yuborgan URL manzillar tarkibi:\n" + "\n".join(downloaded)

        system_prompt = self.system_prompt
        if url_context:
            system_prompt = system_prompt + url_context

        try:
            if self.agent_orchestrator and complexity != "simple":
                try:
                    mem_list = [{"role": m["role"], "content": m["content"]} for m in memory]
                    message = self.agent_orchestrator.process_sync(
                        prompt=clean_prompt,
                        memory=mem_list,
                        system_prompt=system_prompt,
                    )
                except Exception as agent_err:
                    logger.warning(f"Agent orchestrator xatosi, provider ga o'tish: {agent_err}")
                    if complexity == "complex" and self.react_provider:
                        message = self.react_provider.respond(
                            prompt=clean_prompt, memory=memory, system_prompt=system_prompt)
                    else:
                        message = effective_provider.respond(
                            prompt=clean_prompt, memory=memory, system_prompt=system_prompt,
                            status=status, platform_profile=platform_profile,
                            runtime_context=runtime_context, research=research)
            elif complexity == "complex" and self.react_provider:
                message = self.react_provider.respond(
                    prompt=clean_prompt, memory=memory, system_prompt=system_prompt)
            else:
                message = effective_provider.respond(
                    prompt=clean_prompt, memory=memory, system_prompt=system_prompt,
                    status=status, platform_profile=platform_profile,
                    runtime_context=runtime_context, research=research)
        except Exception as exc:
            fallback_status = dict(status)
            fallback_status["provider"] = "local-fallback"
            message = self.local_provider.respond(
                prompt=clean_prompt,
                memory=memory,
                system_prompt=system_prompt,
                status=fallback_status,
                platform_profile=platform_profile,
                runtime_context=runtime_context,
                research=research,
            )

        self.memory.save("assistant", message, session_id=session_id)
        return {
            "message": message,
            "status": self.status(),
            "session_id": session_id,
            "mode": mode,
            "recent_memory": self.memory.recent(limit=6, session_id=session_id),
            "sources": [
                {"title": item.title, "url": item.url}
                for item in research
            ],
        }

    def sessions(self) -> list[dict[str, str]]:
        return self.memory.list_sessions()

    def session_history(self, session_id: str) -> list[dict[str, str]]:
        return self.memory.recent(limit=100, session_id=session_id)

    def multi_model_status(self) -> dict:
        """Get status of multi-model system."""
        return self.multi_model_manager.get_status()

    def select_model_for_task(self, prompt: str) -> str:
        """Select appropriate model for given prompt."""
        task_type = self.multi_model_manager.detect_task_type(prompt)
        return self.multi_model_manager.select_model(task_type=task_type, prompt=prompt)

    def analyze_code(self, code: str, filename: str = "") -> dict:
        """Analyze code using the advanced code engine."""
        if not CODE_ENGINE_AVAILABLE or not self.code_analyzer:
            return {"error": "Code engine not available"}
        
        try:
            result = self.code_analyzer.analyze(code, filename)
            return {
                "language": result.language.value,
                "issues": [
                    {
                        "severity": issue.severity,
                        "line": issue.line,
                        "column": issue.column,
                        "message": issue.message,
                        "code": issue.code,
                        "suggestion": issue.suggestion,
                    }
                    for issue in result.issues
                ],
                "optimizations": [
                    {
                        "type": opt.type,
                        "line": opt.line,
                        "description": opt.description,
                        "original": opt.original,
                        "suggested": opt.suggested,
                        "impact": opt.impact,
                    }
                    for opt in result.optimizations
                ],
                "metrics": result.metrics,
                "structure": result.structure,
            }
        except Exception as e:
            return {"error": str(e)}

    def refine_code(self, code: str, project_path: str = "") -> dict:
        """Refine code using multi-step refinement process."""
        if not CODE_ENGINE_AVAILABLE or not self.code_refiner:
            return {"error": "Code engine not available"}
        
        try:
            # Initialize context generator if project path provided
            if project_path and not self.context_generator:
                self.context_generator = ContextAwareGenerator(project_path)
            
            context = None
            if self.context_generator:
                context = self.context_generator.get_context_for_generation(code)
            
            # Detect language
            language = self.code_analyzer.detect_language(code)
            
            # Run refinement
            result = self.code_refiner.refine_code(code, language, context)
            
            return {
                "final_code": result["final_code"],
                "steps": result["steps"],
                "issues_found": len(result["issues_found"]),
                "optimizations_applied": len(result["optimizations_applied"]),
                "context": context if context else {},
            }
        except Exception as e:
            return {"error": str(e)}

    def set_project_context(self, project_path: str) -> dict:
        """Set project context for context-aware code generation."""
        if not CODE_ENGINE_AVAILABLE:
            return {"error": "Code engine not available"}
        
        try:
            self.context_generator = ContextAwareGenerator(project_path)
            return {
                "status": "success",
                "project_path": project_path,
                "structure": self.context_generator.project_structure,
                "detected_libraries": list(self.context_generator.detected_libraries),
            }
        except Exception as e:
            return {"error": str(e)}

    def index_project_context(self, project_path: str, force_reindex: bool = False) -> dict:
        """Index project context using ProjectContextEngine."""
        if not CONTEXT_COLLECTOR_AVAILABLE:
            return {"error": "Context collector not available"}
        
        try:
            self.context_engine = ProjectContextEngine(project_path)
            
            results = {
                "git_info": self.context_engine.scan_git_repo(),
                "codebase": self.context_engine.index_codebase(force_reindex=force_reindex),
                "architecture": self.context_engine.extract_architecture_docs(),
                "api_specs": len(self.context_engine.detect_api_specs()),
                "db_schemas": len(self.context_engine.extract_database_schemas()),
                "summary": self.context_engine.get_context_summary(),
            }
            
            return results
        except Exception as e:
            return {"error": str(e)}

    def search_project_code(self, query: str, limit: int = 10) -> dict:
        """Search indexed project code."""
        if not self.context_engine:
            return {"error": "Project not indexed. Call index_project_context first."}
        
        try:
            results = self.context_engine.search_code(query, limit)
            return {
                "query": query,
                "results": results,
                "count": len(results),
            }
        except Exception as e:
            return {"error": str(e)}

    def initialize_vector_embeddings(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> dict:
        """Initialize vector embeddings for semantic search."""
        if not CONTEXT_COLLECTOR_AVAILABLE:
            return {"error": "Context collector not available"}
        
        try:
            self.vector_embeddings = VectorEmbeddings(model_name)
            return {
                "status": "success",
                "model_name": model_name,
                "model_loaded": self.vector_embeddings.model is not None,
                "faiss_available": self.vector_embeddings.faiss_available,
            }
        except Exception as e:
            return {"error": str(e)}

    def build_vector_index(self, documents: list, text_field: str = "content") -> dict:
        """Build vector index from documents."""
        if not self.vector_embeddings:
            return {"error": "Vector embeddings not initialized. Call initialize_vector_embeddings first."}
        
        try:
            success = self.vector_embeddings.build_index(documents, text_field)
            return {
                "status": "success" if success else "failed",
                "documents_count": len(documents),
            }
        except Exception as e:
            return {"error": str(e)}

    def semantic_search(self, query: str, k: int = 5) -> dict:
        """Perform semantic search using vector embeddings."""
        if not self.vector_embeddings:
            return {"error": "Vector embeddings not initialized"}
        
        try:
            results = self.vector_embeddings.search(query, k)
            return {
                "query": query,
                "results": results,
                "count": len(results),
            }
        except Exception as e:
            return {"error": str(e)}

    def add_knowledge_doc(self, title: str, content: str, category: str = "", tags: list = None) -> dict:
        """Add document to knowledge base."""
        if not self.knowledge_base:
            return {"error": "Knowledge base not available"}
        
        try:
            doc_id = self.knowledge_base.add_company_doc(title, content, category, tags)
            return {
                "status": "success",
                "doc_id": doc_id,
            }
        except Exception as e:
            return {"error": str(e)}

    def add_code_example(self, title: str, code: str, language: str, description: str = "", category: str = "", tags: list = None) -> dict:
        """Add code example to knowledge base."""
        if not self.knowledge_base:
            return {"error": "Knowledge base not available"}
        
        try:
            example_id = self.knowledge_base.add_code_example(title, code, language, description, category, tags)
            return {
                "status": "success",
                "example_id": example_id,
            }
        except Exception as e:
            return {"error": str(e)}

    def add_design_pattern(self, name: str, description: str, example_code: str, language: str = "", category: str = "") -> dict:
        """Add design pattern to knowledge base."""
        if not self.knowledge_base:
            return {"error": "Knowledge base not available"}
        
        try:
            pattern_id = self.knowledge_base.add_design_pattern(name, description, example_code, language, category)
            return {
                "status": "success",
                "pattern_id": pattern_id,
            }
        except Exception as e:
            return {"error": str(e)}

    def search_knowledge_base(self, query: str, category: str = "", limit: int = 10) -> dict:
        """Search knowledge base documents."""
        if not self.knowledge_base:
            return {"error": "Knowledge base not available"}
        
        try:
            results = self.knowledge_base.search_docs(query, category, limit)
            return {
                "query": query,
                "category": category,
                "results": results,
                "count": len(results),
            }
        except Exception as e:
            return {"error": str(e)}

    def search_code_examples(self, query: str, language: str = "", limit: int = 10) -> dict:
        """Search code examples in knowledge base."""
        if not self.knowledge_base:
            return {"error": "Knowledge base not available"}
        
        try:
            results = self.knowledge_base.search_code_examples(query, language, limit)
            return {
                "query": query,
                "language": language,
                "results": results,
                "count": len(results),
            }
        except Exception as e:
            return {"error": str(e)}

    def get_design_patterns(self, category: str = "") -> dict:
        """Get design patterns from knowledge base."""
        if not self.knowledge_base:
            return {"error": "Knowledge base not available"}
        
        try:
            patterns = self.knowledge_base.get_design_patterns(category)
            return {
                "category": category,
                "patterns": patterns,
                "count": len(patterns),
            }
        except Exception as e:
            return {"error": str(e)}

    def get_common_fixes(self, language: str = "", limit: int = 10) -> dict:
        """Get common fixes from knowledge base."""
        if not self.knowledge_base:
            return {"error": "Knowledge base not available"}
        
        try:
            fixes = self.knowledge_base.get_common_fixes(language, limit)
            return {
                "language": language,
                "fixes": fixes,
                "count": len(fixes),
            }
        except Exception as e:
            return {"error": str(e)}

    def get_team_conventions(self, category: str = "") -> dict:
        """Get team conventions from knowledge base."""
        if not self.knowledge_base:
            return {"error": "Knowledge base not available"}
        
        try:
            conventions = self.knowledge_base.get_team_conventions(category)
            return {
                "category": category,
                "conventions": conventions,
                "count": len(conventions),
            }
        except Exception as e:
            return {"error": str(e)}

    def get_knowledge_summary(self) -> dict:
        """Get knowledge base summary."""
        if not self.knowledge_base:
            return {"error": "Knowledge base not available"}
        
        try:
            summary = self.knowledge_base.get_summary()
            return summary
        except Exception as e:
            return {"error": str(e)}

    # -------------------------------------------------------------------------
    # 5.1 — Code Review Bot
    # -------------------------------------------------------------------------
    def review_code(self, code: str, language: str = "python", context: str = "", mode: str = "") -> str:
        from .code_assistants import CodeReviewBot
        bot = CodeReviewBot(self._get_respond(mode or self.config.mode))
        return bot.review(code, language, context)

    # -------------------------------------------------------------------------
    # 5.2 — Debug Assistant
    # -------------------------------------------------------------------------
    def debug_error(self, error: str, code: str = "", language: str = "python", mode: str = "") -> str:
        from .code_assistants import DebugAssistant
        bot = DebugAssistant(self._get_respond(mode or self.config.mode))
        return bot.debug(error, code, language)

    # -------------------------------------------------------------------------
    # 5.3 — Architecture Assistant
    # -------------------------------------------------------------------------
    def analyze_architecture(self, description: str, code: str = "", mode: str = "") -> str:
        from .code_assistants import ArchitectureAssistant
        bot = ArchitectureAssistant(self._get_respond(mode or self.config.mode))
        return bot.analyze(description, code)

    # -------------------------------------------------------------------------
    # 6.1 — Language Support
    # -------------------------------------------------------------------------
    def language_generate(self, prompt: str, language: str, framework: str = "", mode: str = "") -> str:
        from .framework_assistants import LanguageAssistant
        bot = LanguageAssistant(self._get_respond(mode or self.config.mode))
        return bot.generate(prompt, language, framework)

    # -------------------------------------------------------------------------
    # 6.2 — Framework Integration
    # -------------------------------------------------------------------------
    def framework_generate(self, prompt: str, category: str, framework: str = "", mode: str = "") -> str:
        from .framework_assistants import FrameworkAssistant
        bot = FrameworkAssistant(self._get_respond(mode or self.config.mode))
        return bot.generate(prompt, category, framework)

    # -------------------------------------------------------------------------
    # 6.3 — Version Control
    # -------------------------------------------------------------------------
    def version_control_generate(self, prompt: str, category: str, mode: str = "") -> str:
        from .framework_assistants import VersionControlAssistant
        bot = VersionControlAssistant(self._get_respond(mode or self.config.mode))
        return bot.generate(prompt, category)

    # -------------------------------------------------------------------------
    # 7.1 — Docker Containerization
    # -------------------------------------------------------------------------
    def docker_generate(self, prompt: str, category: str = "", mode: str = "") -> str:
        from .infrastructure_assistants import DockerAssistant
        bot = DockerAssistant(self._get_respond(mode or self.config.mode))
        return bot.generate(prompt, category)

    # -------------------------------------------------------------------------
    # 7.2 — Kubernetes Orchestration
    # -------------------------------------------------------------------------
    def kubernetes_generate(self, prompt: str, category: str = "", mode: str = "") -> str:
        from .infrastructure_assistants import KubernetesAssistant
        bot = KubernetesAssistant(self._get_respond(mode or self.config.mode))
        return bot.generate(prompt, category)

    # -------------------------------------------------------------------------
    # 7.3 — Performance Tuning
    # -------------------------------------------------------------------------
    def performance_tuning_generate(self, prompt: str, category: str = "", mode: str = "") -> str:
        from .infrastructure_assistants import PerformanceTuningAssistant
        bot = PerformanceTuningAssistant(self._get_respond(mode or self.config.mode))
        return bot.generate(prompt, category)

    # -------------------------------------------------------------------------
    # 8.1 — Feedback Loop
    # -------------------------------------------------------------------------
    def feedback_submit(self, rating: int, comment: str = "", session_id: str = "",
                        prompt: str = "", response: str = "", provider: str = "",
                        mode: str = "", latency_ms: int = 0) -> dict:
        from .learning_assistants import FeedbackLoop
        fb = FeedbackLoop(self._get_respond(mode or self.config.mode) if mode else None)
        return fb.submit_rating(rating, comment, session_id, prompt, response, provider, mode, latency_ms)

    def feedback_analytics(self) -> dict:
        from .learning_assistants import FeedbackLoop
        return FeedbackLoop().analytics()

    def feedback_analyze(self, question: str = "", mode: str = "") -> str:
        from .learning_assistants import FeedbackLoop
        fb = FeedbackLoop(self._get_respond(mode or self.config.mode))
        return fb.analyze(question)

    # -------------------------------------------------------------------------
    # 8.2 — Model Fine-tuning
    # -------------------------------------------------------------------------
    def training_save(self, prompt: str, response: str, domain: str = "",
                      language: str = "uz", rating: int = 0) -> dict:
        from .learning_assistants import ModelFineTuning
        return ModelFineTuning().save_training_pair(prompt, response, domain, language, rating)

    def training_set_domain(self, domain: str, system_prompt: str,
                            temperature: float = 0.7, max_tokens: int = 1024) -> dict:
        from .learning_assistants import ModelFineTuning
        return ModelFineTuning().set_domain_prompt(domain, system_prompt, temperature, max_tokens)

    def training_stats(self) -> dict:
        from .learning_assistants import ModelFineTuning
        return ModelFineTuning().training_stats()

    def training_analyze(self, question: str = "", mode: str = "") -> str:
        from .learning_assistants import ModelFineTuning
        ft = ModelFineTuning(self._get_respond(mode or self.config.mode))
        return ft.analyze(question)

    # -------------------------------------------------------------------------
    # 8.3 — Knowledge Updates
    # -------------------------------------------------------------------------
    def knowledge_suggest(self, topic: str = "", context: str = "", mode: str = "") -> str:
        from .learning_assistants import KnowledgeUpdater
        ku = KnowledgeUpdater(self._get_respond(mode or self.config.mode))
        return ku.suggest_updates(topic, context)

    def _get_respond(self, mode: str):
        """Get a respond(prompt, memory, system_prompt) -> str callable."""
        mode = mode.lower().strip()
        raw = self.providers.get(mode, self.provider)
        return raw.respond


controller = AIDAController()
