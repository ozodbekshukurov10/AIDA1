from __future__ import annotations

import json
import os
import platform
import sqlite3
import textwrap
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_DB = BASE_DIR / "aida_memory.db"
RUNTIME_FILE = BASE_DIR / ".aida_runtime.json"


def _utc_now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class ResearchSnippet:
    title: str
    summary: str
    url: str


class WebResearchService:
    def search(self, query: str, limit: int = 5) -> list[ResearchSnippet]:
        # Detect if query might be Uzbek
        is_uzbek = any(char in query.lower() for char in "o'qg'h") or " va " in query.lower()
        lang = "uz" if is_uzbek else "en"
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            wiki_future = executor.submit(self._search_wikipedia, query, lang, limit // 2)
            ddg_future = executor.submit(self._search_ddg, query, limit // 2)
            
            snippets = wiki_future.result() + ddg_future.result()
        
        return snippets[:limit]

    def _search_wikipedia(self, query: str, lang: str, limit: int) -> list[ResearchSnippet]:
        search_url = (
            f"https://{lang}.wikipedia.org/w/api.php?action=opensearch"
            f"&search={urllib.parse.quote(query)}&limit={limit}&namespace=0&format=json"
        )
        try:
            request = urllib.request.Request(search_url, headers={"User-Agent": "AIDA/1.0"})
            with urllib.request.urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return []

        titles = payload[1] if len(payload) > 1 else []
        urls = payload[3] if len(payload) > 3 else []
        
        with ThreadPoolExecutor(max_workers=limit) as executor:
            summaries = list(executor.map(lambda t: self._fetch_summary(t, lang), titles))

        results: list[ResearchSnippet] = []
        for index, title in enumerate(titles):
            if summaries[index]:
                results.append(ResearchSnippet(title=title, summary=summaries[index], url=urls[index]))
        return results

    def _search_ddg(self, query: str, limit: int) -> list[ResearchSnippet]:
        search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        try:
            request = urllib.request.Request(
                search_url, 
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                html = response.read().decode("utf-8")
            
            soup = BeautifulSoup(html, "html.parser")
            results: list[ResearchSnippet] = []
            
            for entry in soup.find_all("div", class_="result")[:limit]:
                title_tag = entry.find("a", class_="result__a")
                snippet_tag = entry.find("a", class_="result__snippet")
                if title_tag and snippet_tag:
                    results.append(ResearchSnippet(
                        title=title_tag.get_text().strip(),
                        summary=snippet_tag.get_text().strip()[:420],
                        url=title_tag["href"]
                    ))
            return results
        except Exception:
            return []

    def _fetch_summary(self, title: str, lang: str = "en") -> str:
        try:
            summary_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
            request = urllib.request.Request(
                summary_url,
                headers={"User-Agent": "AIDA/1.0"},
            )
            with urllib.request.urlopen(request, timeout=6) as response:
                payload = json.loads(response.read().decode("utf-8"))
            extract = str(payload.get("extract", "")).strip()
            return extract[:420]
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


@dataclass
class ProviderConfig:
    provider: str
    model: str

    @classmethod
    def from_env(cls) -> "ProviderConfig":
        provider = os.getenv("AIDA_PROVIDER", "local").lower()
        model = os.getenv("AIDA_MODEL", "AIDA Local Core")
        api_key = os.getenv("AIDA_API_KEY", "")
        lmstudio_url = os.getenv("AIDA_LMSTUDIO_URL", "http://localhost:1234/v1")
        lmstudio_model = os.getenv("AIDA_LMSTUDIO_MODEL", "local-model")
        lmstudio_api_key = os.getenv("AIDA_LMSTUDIO_API_KEY", "lm-studio")
        ollama_url = os.getenv("AIDA_OLLAMA_URL", "http://localhost:11434")
        ollama_model = os.getenv("AIDA_OLLAMA_MODEL", "qwen2.5-coder:7b")
        timeout_ms = int(os.getenv("AIDA_LLM_TIMEOUT_MS", "120000") or "120000")
        max_tokens = int(os.getenv("AIDA_LLM_MAX_TOKENS", "1024") or "1024")
        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            lmstudio_url=lmstudio_url,
            lmstudio_model=lmstudio_model,
            lmstudio_api_key=lmstudio_api_key,
            ollama_url=ollama_url,
            ollama_model=ollama_model,
            timeout_ms=timeout_ms,
            max_tokens=max_tokens,
        )

    def __init__(
        self,
        provider: str,
        model: str,
        api_key: str = "",
        lmstudio_url: str = "http://localhost:1234/v1",
        lmstudio_model: str = "local-model",
        lmstudio_api_key: str = "lm-studio",
        ollama_url: str = "http://localhost:11434",
        ollama_model: str = "qwen2.5-coder:7b",
        timeout_ms: int = 120000,
        max_tokens: int = 1024,
    ) -> None:
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.lmstudio_url = lmstudio_url
        self.lmstudio_model = lmstudio_model
        self.lmstudio_api_key = lmstudio_api_key
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.timeout_ms = timeout_ms
        self.max_tokens = max_tokens


def build_llm_system_prompt(
    system_prompt: str,
    platform_profile: dict[str, str] | None,
    runtime_context: dict[str, str] | None,
    research: list[ResearchSnippet] | None,
) -> str:
    parts = [system_prompt]

    context_lines: list[str] = []
    for source in (platform_profile, runtime_context):
        if not source:
            continue
        for key, value in source.items():
            value = str(value).strip()
            if value:
                context_lines.append(f"- {key}: {value}")
    if context_lines:
        parts.append("Kontekst:\n" + "\n".join(context_lines))

    if research:
        research_lines = ["Internet qidiruv natijalari (manba sifatida foydalaning):"]
        for index, item in enumerate(research[:4], start=1):
            research_lines.append(f"{index}. {item.title} — {item.summary} ({item.url})")
        parts.append("\n".join(research_lines))

    return "\n\n".join(parts)


def build_chat_messages(
    prompt: str,
    memory: Iterable[dict[str, str]],
    system_prompt: str,
    platform_profile: dict[str, str] | None,
    runtime_context: dict[str, str] | None,
    research: list[ResearchSnippet] | None,
) -> list[dict[str, str]]:
    messages = [
        {
            "role": "system",
            "content": build_llm_system_prompt(
                system_prompt, platform_profile, runtime_context, research
            ),
        }
    ]
    for item in memory:
        role = "user" if item["role"] == "user" else "assistant"
        messages.append({"role": role, "content": item["content"]})
    messages.append({"role": "user", "content": prompt})
    return messages


class GeminiProvider:
    name = "remote"

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        self.api_key = api_key
        self.model = model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

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

        full_prompt = f"{system_prompt}\n\nUser request: {prompt}"
        
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
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return f"Remote provider error: {str(e)}"


class LMStudioProvider:
    name = "lmstudio"

    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        model: str = "local-model",
        api_key: str = "lm-studio",
        timeout_ms: int = 120000,
        max_tokens: int = 1024,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = max(timeout_ms, 1000) / 1000
        self.max_tokens = max_tokens

    def is_available(self) -> bool:
        try:
            request = urllib.request.Request(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            with urllib.request.urlopen(request, timeout=3) as response:
                return response.status == 200
        except Exception:
            return False

    def respond(
        self,
        prompt: str,
        memory: Iterable[dict[str, str]],
        system_prompt: str,
        platform_profile: dict[str, str] | None = None,
        runtime_context: dict[str, str] | None = None,
        research: list[ResearchSnippet] | None = None,
        **kwargs,
    ) -> str:
        messages = build_chat_messages(
            prompt, memory, system_prompt, platform_profile, runtime_context, research
        )
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"].strip()


class OllamaProvider:
    name = "ollama"

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5-coder:7b",
        timeout_ms: int = 120000,
        max_tokens: int = 1024,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = max(timeout_ms, 1000) / 1000
        self.max_tokens = max_tokens

    def is_available(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=3) as response:
                return response.status == 200
        except Exception:
            return False

    def respond(
        self,
        prompt: str,
        memory: Iterable[dict[str, str]],
        system_prompt: str,
        platform_profile: dict[str, str] | None = None,
        runtime_context: dict[str, str] | None = None,
        research: list[ResearchSnippet] | None = None,
        **kwargs,
    ) -> str:
        messages = build_chat_messages(
            prompt, memory, system_prompt, platform_profile, runtime_context, research
        )
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": self.max_tokens},
        }
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result["message"]["content"].strip()


class LocalProvider:
    name = "local"

    # ── Intent detection ─────────────────────────────────────────────────────

    INTENT_MAP = {
        "greeting":    ["salom", "assalom", "hello", "hi", "xayr", "hayot"],
        "status":      ["status", "holat", "ahvol", "ishlayaptimi", "ping"],
        "plan":        ["reja", "plan", "bosqich", "strategiya", "yo'l xarita", "roadmap", "qanday boshlash"],
        "code":        ["kod", "code", "funksiya", "function", "script", "html", "css", "javascript",
                        "typescript", "react", "django", "sql", "regex", "xato", "bug", "fix",
                        "exception", "traceback", "api yoz", "backend", "frontend"],
        "writing":     ["yoz", "maqola", "post", "email", "matn", "copy", "tavsif", "blog"],
        "compare":     ["taqqosla", "solishtir", "qaysi yaxshi", "farq", "afzalligi", "vs"],
        "explain":     ["nima", "nima bu", "tushuntir", "izohla", "qanday ishlaydi", "what is",
                        "explain", "define", "nimaga", "sababi"],
        "list":        ["ro'yxat", "list", "nechta", "qanday turlar", "misollar", "berib ber"],
        "math":        ["hisabla", "formula", "son", "matematik", "calculate", "foiz", "%"],
        "translate":   ["tarjima", "translate", "o'zbek", "ingliz", "russian", "translate to"],
        "summary":     ["xulosa", "qisqacha", "summary", "brief", "abstract", "resume"],
    }

    def _detect_intent(self, text: str) -> str:
        lower = text.lower()
        scores: dict[str, int] = {}
        for intent, keywords in self.INTENT_MAP.items():
            scores[intent] = sum(1 for k in keywords if k in lower)
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

    # ── Candidate generators ─────────────────────────────────────────────────

    def _cand_direct(self, prompt: str, intent: str, keywords: list[str]) -> str:
        kw = ", ".join(keywords[:5]) if keywords else prompt[:60]
        intros = {
            "greeting":  "AIDA onlayn va to'liq ishlashga tayyor.",
            "plan":      f"«{prompt}» uchun Master Strategiya:",
            "code":      f"«{kw}» — Kod yechimi:",
            "explain":   f"«{kw}» haqida aniq tushuntirish:",
            "list":      f"«{kw}» bo'yicha to'liq ro'yxat:",
            "compare":   f"Taqqoslash tahlili: {kw}",
            "writing":   f"«{kw}» mavzusida matn:",
            "math":      f"Hisob-kitob: {kw}",
            "translate": f"Tarjima: {kw}",
            "summary":   f"Xulosa: {kw}",
            "status":    "AIDA tizim holati:",
            "general":   f"Javob: {prompt[:80]}",
        }
        return intros.get(intent, f"Javob: {prompt[:80]}")

    def _cand_structured(self, prompt: str, intent: str, keywords: list[str], memory_ctx: str) -> str:
        kw = ", ".join(keywords[:4]) if keywords else ""
        blocks = {
            "plan": [
                f"📋 REJA: {prompt}",
                "",
                "1️⃣  Maqsad — aniq bir gapda ifodalang.",
                "2️⃣  Resurslar — vaqt, texnologiya, jamoa.",
                "3️⃣  Bosqichlar — har biri o'lchov mezoni bilan.",
                "4️⃣  Xavflar — eng katta 2 ta risk va yechimi.",
                "5️⃣  Natija — qachon «tayyor» deyiladi.",
                "",
                f"Kalit so'zlar: {kw}" if kw else "",
                memory_ctx,
            ],
            "code": [
                f"💻 KOD YECHIMI: {prompt}",
                "",
                "🔍 1. Muammoni aniqlash — qaysi qator, qaysi modul.",
                "🔬 2. Minimal qayta-ishlab chiqarish — eng kichik test case.",
                "🛠  3. Tuzatish — eng xavfsiz o'zgarish.",
                "✅ 4. Tekshirish — test yoki build bilan tasdiqlash.",
                "",
                "Hozir kodni yuboring — men uni qadamma-qadam tuzataman.",
                memory_ctx,
            ],
            "explain": [
                f"📖 TUSHUNTIRISH: {prompt}",
                "",
                f"Asosiy tushuncha: {kw or prompt[:50]}",
                "",
                "🔹 Nima: Ushbu tushuncha nima ekanligini oddiy misolda ko'rsatamiz.",
                "🔹 Nega: Bu nima uchun muhim va qachon ishlatiladi.",
                "🔹 Qanday: Amaliy qo'llanish yo'li.",
                "",
                "Chuqurroq tushuncha kerak bo'lsa, aniq savolni yuboring.",
                memory_ctx,
            ],
            "list": [
                f"📝 RO'YXAT: {prompt}",
                "",
                "• 1-element — asosiy",
                "• 2-element — qo'shimcha",
                "• 3-element — ilg'or",
                "• 4-element — muqobil",
                "• 5-element — tavsiya etilgan",
                "",
                f"({kw} sohasida to'liqroq ro'yxat uchun aniqlashtiring)",
                memory_ctx,
            ],
            "compare": [
                f"⚖️  TAQQOSLASH: {prompt}",
                "",
                "┌─────────────┬─────────────────┬─────────────────┐",
                "│  Mezon      │   Variant A     │   Variant B     │",
                "├─────────────┼─────────────────┼─────────────────┤",
                "│  Tezlik     │   —             │   —             │",
                "│  Narx       │   —             │   —             │",
                "│  Qulaylik   │   —             │   —             │",
                "│  Kelajak    │   —             │   —             │",
                "└─────────────┴─────────────────┴─────────────────┘",
                "",
                "Aniq variantlarni yuboring — jadval to'ldiriladi.",
                memory_ctx,
            ],
        }
        lines = blocks.get(intent, [
            f"✦ {prompt}",
            "",
            "Tahlil qilinmoqda...",
            memory_ctx,
        ])
        return "\n".join(l for l in lines if l is not None)

    def _cand_concise(self, prompt: str, intent: str, keywords: list[str]) -> str:
        kw = " ".join(keywords[:3])
        return f"{prompt.strip()}\n\n→ {kw or 'Aniqroq savol bering'} — bu yo'nalishda eng tezkor javob shunday."

    def _cand_contextual(self, prompt: str, memory: Iterable[dict], intent: str) -> str:
        msgs = list(memory)
        history_bits = [f"[{m['role']}]: {m['content'][:60]}" for m in msgs[-4:]]
        header = "Kontekst asosida javob:\n" + "\n".join(history_bits) if history_bits else ""
        action = {
            "plan": "Bu so'rovni qadamma-qadam rejaga aylantiraman.",
            "code": "Kod masalasini tuzatish tartibini ko'rsataman.",
            "explain": "Sodda va aniq tushuntiraman.",
            "compare": "Taqqoslab, eng yaxshisini tavsiya qilaman.",
        }.get(intent, "Eng foydali va aniq javobni tayyorlayman.")
        return f"{header}\n\n{prompt}\n\n→ {action}"

    def _cand_research_synthesis(self, prompt: str, research: list) -> str:
        if not research:
            return ""
        lines = [f"🌐 INTERNET QIDIRUV: «{prompt}»", ""]
        for i, item in enumerate(research[:4], 1):
            lines.append(f"{i}. {item.title}")
            lines.append(f"   {item.summary[:200]}")
            lines.append(f"   🔗 {item.url}")
            lines.append("")
        lines.append("📌 AIDA xulosasi: Yuqoridagi manbalar asosida eng dolzarb ma'lumot shu.")
        lines.append("Batafsilroq tahlil yoki o'zbek tilidagi xulosa kerak bo'lsa, ayting.")
        return "\n".join(lines)

    # ── Scoring ───────────────────────────────────────────────────────────────

    def _score(self, candidate: str, prompt: str, intent: str, keywords: list[str]) -> float:
        if not candidate:
            return -1.0
        score = 0.0
        words = candidate.split()
        wcount = len(words)

        # Length reward (sweet spot 40-300 words)
        if 40 <= wcount <= 300:
            score += 3.0
        elif 20 <= wcount < 40:
            score += 1.5
        elif wcount > 300:
            score += 1.0

        # Structure bonus (numbered lists, bullets, emojis)
        if any(c in candidate for c in ["1.", "2.", "3.", "•", "→", "🔹", "✅", "📋"]):
            score += 2.5

        # Keyword coverage
        lower_cand = candidate.lower()
        hits = sum(1 for k in keywords if k.lower() in lower_cand)
        score += hits * 0.8

        # Prompt word overlap
        prompt_words = set(prompt.lower().split())
        overlap = sum(1 for w in prompt_words if w in lower_cand)
        score += min(overlap * 0.3, 2.0)

        # Intent-specific bonus
        intent_signals = {
            "plan":    ["reja", "bosqich", "maqsad", "natija", "1️⃣"],
            "code":    ["kod", "tuzat", "test", "💻", "→"],
            "explain": ["ya'ni", "degani", "misol", "📖", "🔹"],
            "list":    ["•", "—", "element", "📝"],
            "compare": ["taqqos", "afzal", "┌", "⚖"],
        }
        if intent in intent_signals:
            bonus = sum(1 for s in intent_signals[intent] if s in candidate)
            score += bonus * 0.5

        # Penalize empty/generic
        generic = ["so'rov qabul qilindi", "menga ayting", "marhamat qilib"]
        if any(g in lower_cand for g in generic):
            score -= 1.5

        return score

    # ── Main respond ──────────────────────────────────────────────────────────

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
        mem_list = list(memory)
        intent = self._detect_intent(prompt)
        keywords = self._extract_keywords(prompt)
        ctx = self._context_summary(mem_list)

        # Fast-path: research
        if research:
            return self._cand_research_synthesis(prompt, research)

        # Fast-path: status
        if intent == "status":
            return textwrap.dedent(f"""
                AIDA holati ✅
                ─────────────────────────
                Provider   : {status['provider']}
                Platform   : {status['platform']}
                Xotira     : {status['memory_entries']} ta yozuv
                Rejim      : {status['autonomy_mode']}
                ─────────────────────────
                Barcha interfeys ishlamoqda.
            """).strip()

        # Fast-path: greeting
        if intent == "greeting":
            return textwrap.dedent("""
                Salom! AIDA onlayn. 👋

                Men quyidagilarda yordam beraman:
                • Reja va strategiya tuzish
                • Kod yozish va xatolarni tuzatish
                • Tushuntirish va tahlil
                • Matn va tarjima
                • Internet qidiruv va xulosa

                Vazifangizni yozing — men darhol ishga tushaman.
            """).strip()

        # Generate candidates in parallel
        with ThreadPoolExecutor(max_workers=4) as ex:
            f1 = ex.submit(self._cand_direct, prompt, intent, keywords)
            f2 = ex.submit(self._cand_structured, prompt, intent, keywords, ctx)
            f3 = ex.submit(self._cand_concise, prompt, intent, keywords)
            f4 = ex.submit(self._cand_contextual, prompt, mem_list, intent)

        candidates = [
            f1.result(),
            f2.result(),
            f3.result(),
            f4.result(),
        ]

        # Score and pick best
        scored = [(c, self._score(c, prompt, intent, keywords)) for c in candidates if c]
        scored.sort(key=lambda x: x[1], reverse=True)
        best = scored[0][0]

        # Append context if useful
        if ctx and ctx not in best:
            best = f"{best}\n\n{ctx}"

        return best

    def _is_code_request(self, normalized_prompt: str) -> bool:
        code_phrases = [
            "kod yoz",
            "code yoz",
            "snippet",
            "function",
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
            "Vazifani aniq va nazorat qilinadigan oqimga bo'lamiz:",
            "",
            "1. Maqsadni bitta jumlada qulflang.",
            "2. Cheklovlarni ajrating: vaqt, texnologiya, risk, resurs.",
            "3. Ishni modullarga bo'ling: tayyorlash, qurish, tekshirish, chiqarish.",
            "4. Har modul uchun natija mezonini yozing.",
            "5. Oxirida bitta qisqa review bilan umumiy sifatni tasdiqlang.",
            "",
            f"Bu so'rov uchun markaziy yo'nalish: {prompt}.",
        ]
        if context_line:
            lines.extend(["", context_line])
        if platform_lines:
            lines.extend(["", *platform_lines])
        lines.extend(
            [
                "",
                "Agar xohlasangiz, shu vazifani men siz uchun tayyor ish rejasiga ajratib beraman.",
            ]
        )
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
        lines = [
            "Kod masalasiga eng foydali yo'l bilan yondashamiz:",
            "",
            "1. Muammoni bitta aniq gapga tushiring.",
            "2. Uni qayta chiqaradigan minimal holatni toping.",
            "3. Sababni log, kirish va chiqish orqali toraytiring.",
            "4. Eng kichik xavfsiz tuzatishni kiriting.",
            "5. Oxirida test, build yoki smoke-check bilan tasdiqlang.",
            "",
            f"Hozirgi kod yo'nalishi: {prompt}.",
        ]
        if context_line:
            lines.extend(["", context_line])
        if platform_lines:
            lines.extend(["", *platform_lines])
        lines.extend(["", "Kod yoki xatoni yuborsangiz, men uni to'g'ridan-to'g'ri yechish tartibiga solaman."])
        return "\n".join(lines)

    def _writing_response(
        self,
        prompt: str,
        platform_profile: dict[str, str] | None,
        runtime_context: dict[str, str] | None,
    ) -> str:
        lines = [
            "Matnni kuchli qilish uchun uchta tayanchni ushlang:",
            "",
            "1. Kim uchun yozilayotganini aniqlang.",
            "2. Bitta markaziy fikrni tanlang.",
            "3. Ortiqcha gaplarni kesib, ritmni tozalang.",
            "",
            f"Mavzu: {prompt}.",
        ]
        platform_lines = self._platform_summary(platform_profile, runtime_context)
        if platform_lines:
            lines.extend(["", *platform_lines])
        lines.append("")
        lines.append("Menga maqsadni ayting, men shu kontekstga mos tayyor matnni yig'ib beraman.")
        return "\n".join(lines)

    def _comparison_response(
        self,
        prompt: str,
        platform_profile: dict[str, str] | None,
        runtime_context: dict[str, str] | None,
    ) -> str:
        lines = [
            "Tanlash yoki taqqoslashda quyidagi mezon bilan yuring:",
            "",
            "1. Natija sifati.",
            "2. Qurish tezligi.",
            "3. Qo'llash qulayligi.",
            "4. Uzoq muddatli xizmat xarajati.",
            "",
            f"Solishtirilayotgan yo'nalish: {prompt}.",
        ]
        platform_lines = self._platform_summary(platform_profile, runtime_context)
        if platform_lines:
            lines.extend(["", *platform_lines])
        lines.extend(["", "Ikki yoki uch variantni yozing, men ularni qisqa va aniq taqqoslab beraman."])
        return "\n".join(lines)

    def _general_response(
        self,
        prompt: str,
        memory: Iterable[dict[str, str]],
        platform_profile: dict[str, str] | None,
        runtime_context: dict[str, str] | None,
    ) -> str:
        context_line = self._recent_context_line(memory)
        platform_lines = self._platform_summary(platform_profile, runtime_context)
        lines = [
            f"So'rov qabul qilindi: {prompt}.",
            "",
            "Men bunga amaliy va tartibli yo'l bilan javob beraman.",
            "Eng yaxshi natija uchun savolni maqsad, cheklov va kutilgan chiqish ko'rinishida yozing.",
        ]
        if context_line:
            lines.extend(["", context_line])
        if platform_lines:
            lines.extend(["", *platform_lines])
        lines.extend(["", "Xohlasangiz, shu mavzuni reja, tahlil yoki tayyor matn shaklida davom ettiraman."])
        return "\n".join(lines)

    def _research_response(
        self,
        prompt: str,
        research: list[ResearchSnippet],
        platform_profile: dict[str, str] | None,
        runtime_context: dict[str, str] | None,
    ) -> str:
        lines = [
            f"Internet qidiruv natijalari asosida tayyorlangan tahlil: '{prompt}'.",
            "",
            "Quyidagi ishonchli manbalardan olingan ma'lumotlar tahlil qilindi:",
        ]
        for index, item in enumerate(research, start=1):
            lines.extend(
                [
                    f"{index}. {item.title.upper()}",
                    f"   Xulosa: {item.summary}",
                    f"   To'liq ma'lumot: {item.url}",
                    "",
                ]
            )

        lines.append("AIDA xulosasi: Yuqoridagi ma'lumotlar so'rovingizga mos keladigan eng dolzarb manbalardir. ")
        lines.append("Agar sizga ushbu ma'lumotlar asosida batafsilroq hisobot yoki tarjima kerak bo'lsa, marhamat qilib ayting.")

        platform_lines = self._platform_summary(platform_profile, runtime_context)
        if platform_lines:
            lines.extend(["", "Platforma konteksti:", *platform_lines])

        lines.extend(
            [
                "",
                "Shu material asosida xohlasangiz, men sizga tayyor xulosa, post, product text yoki strategik javobni ham yig'ib beraman.",
            ]
        )
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
        memory_count = status["memory_entries"]
        provider = status["provider"]
        business_type = (platform_profile or {}).get("business_type", "").lower()

        if any(token in normalized for token in ["status", "holat", "ahvol"]):
            return textwrap.dedent(
                f"""
                AIDA holati barqaror.
                - Provider: {provider}
                - Platforma: {status["platform"]}
                - Xotira yozuvlari: {memory_count}
                - Rejim: himoyalangan orkestrator

                Keyingi foydali qadam: chat API yoki CLI orqali vazifa berish.
                """
            ).strip()

        if research:
            return self._research_response(prompt, research, platform_profile, runtime_context)

        if any(token in business_type for token in ["kiyim", "moda", "fashion", "clothing", "apparel"]):
            return self._fashion_store_response(prompt, platform_profile, runtime_context)

        if any(token in normalized for token in ["api", "key", "kalit", "token"]):
            return textwrap.dedent(
                """
                AIDA uchun access keylarni sayt ichida yaratish mumkin.
                Ular boshqa platformalardan sizning AIDA endpoint'ingizga ulanadi.
                Local core ishlashi uchun tashqi provider kaliti shart emas.
                """
            ).strip()

        if any(token in normalized for token in ["murakkab", "vazifa", "plan", "reja", "bo'lib", "bolib", "strategiya"]):
            return self._plan_response(prompt, memory, platform_profile, runtime_context)

        if self._is_code_request(normalized):
            return self._code_response(prompt, memory, platform_profile, runtime_context)

        if any(token in normalized for token in ["yoz", "matn", "copy", "post", "email", "maqola"]):
            return self._writing_response(prompt, platform_profile, runtime_context)

        if any(token in normalized for token in ["taqqosla", "solishtir", "qaysi", "tanla", "farqi"]):
            return self._comparison_response(prompt, platform_profile, runtime_context)

        if any(token in normalized for token in ["build", "frontend", "ui", "sayt", "dizayn"]):
            return textwrap.dedent(
                """
                Sayt endi operatsion boshqaruv paneli sifatida ishlaydi.
                Unda tizim holati, chat sessiyasi va ishchi signal kartalari bor.
                Django build tayyor faylni o'zi serve qiladi, shu sabab ishga tushirish soddalashgan.
                """
            ).strip()

        if any(token in normalized for token in ["master", "controller", "orkestr", "orchestr"]):
            return textwrap.dedent(
                """
                AIDA markaziy boshqaruv rejimida ishlaydi:
                - foydalanuvchi so'rovlarini qabul qiladi
                - kontekstni ushlab turadi
                - mavjud provider orqali sifatli javob tayyorlaydi
                - web va CLI sessiyalarni bir xil holatda yuritadi
                """
            ).strip()

        if normalized.strip() in {"salom", "assalomu alaykum", "assalomu", "hello", "hi"}:
            return textwrap.dedent(
                """
                AIDA onlayn.

                Men sizga reja tuzish, kod masalasini yechish, matn yozish va murakkab vazifani qismlarga ajratishda yordam beraman.
                Vazifani to'g'ridan-to'g'ri yozing, men ishchi javob qaytaraman.
                """
            ).strip()

        return self._general_response(prompt, memory, platform_profile, runtime_context)

class AIDAController:
    def __init__(self) -> None:
        self.memory = MemoryStore(MEMORY_DB)
        self.config = ProviderConfig.from_env()
        self.local_provider = LocalProvider()
        self.research_service = WebResearchService()
        self.provider = self._build_provider()
        self.system_prompt = textwrap.dedent(
            """
            You are AIDA, an advanced Digital Architect and elite problem solver.
            Your intelligence core is optimized for:
            1. Precision: Give exact, verified answers.
            2. Logic: Break complex tasks into operational steps.
            3. Speed: Be concise but comprehensive.
            
            Language Protocol:
            - Default to Uzbek for conversational and descriptive parts.
            - Use high-end professional Uzbek vocabulary.
            - Use English for technical specifications, code, and global standards.
            
            Operational Mode:
            - When asked for a plan, provide a 'Master Strategy'.
            - When asked for code, provide 'Production Ready' snippets.
            - Always maintain context from memory to provide a seamless experience.
            - You are the central brain of this dashboard.
            """
        ).strip()

    def _make_lmstudio(self) -> LMStudioProvider:
        return LMStudioProvider(
            base_url=self.config.lmstudio_url,
            model=self.config.lmstudio_model,
            api_key=self.config.lmstudio_api_key,
            timeout_ms=self.config.timeout_ms,
            max_tokens=self.config.max_tokens,
        )

    def _make_ollama(self) -> OllamaProvider:
        return OllamaProvider(
            base_url=self.config.ollama_url,
            model=self.config.ollama_model,
            timeout_ms=self.config.timeout_ms,
            max_tokens=self.config.max_tokens,
        )

    def _build_provider(self):
        provider = self.config.provider
        if provider == "ollama":
            return self._make_ollama()
        if provider == "lmstudio":
            return self._make_lmstudio()
        if provider == "remote" and self.config.api_key:
            return GeminiProvider(self.config.api_key)
        if provider == "auto":
            # Prefer a reachable local LLM, then remote, else offline core.
            ollama = self._make_ollama()
            if ollama.is_available():
                return ollama
            lmstudio = self._make_lmstudio()
            if lmstudio.is_available():
                return lmstudio
            if self.config.api_key:
                return GeminiProvider(self.config.api_key)
        return self.local_provider

    def _should_research(self, prompt: str, research_enabled: bool) -> bool:
        if research_enabled:
            return True
        normalized = prompt.lower()
        keywords = [
            "internet",
            "web",
            "search",
            "research",
            "latest",
            "today",
            "bugun",
            "yangilik",
            "taqqosla",
            "solishtir",
        ]
        return any(token in normalized for token in keywords)

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
        prompt_lower = prompt.lower()
        for query in self._research_queries(prompt):
            try:
                results = self.research_service.search(query)
            except Exception:
                continue
            if results:
                def score(item: ResearchSnippet) -> int:
                    title = item.title.lower()
                    value = 0
                    if "programming" in prompt_lower or "dasturlash" in prompt_lower or "kod" in prompt_lower:
                        if "programming" in title:
                            value += 5
                    if any(word.lower() in title for word in query.split() if len(word) >= 4):
                        value += 2
                    if "may refer to" in item.summary.lower():
                        value -= 4
                    return value

                return sorted(results, key=score, reverse=True)
        return []

    def _load_default_runserver_address(self) -> str:
        if not RUNTIME_FILE.exists():
            return "127.0.0.1:8001"
        try:
            payload = json.loads(RUNTIME_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return "127.0.0.1:8001"
        return str(payload.get("runserver_address", "127.0.0.1:8001")).strip() or "127.0.0.1:8001"

    def _active_model(self) -> str:
        active = self.provider.name
        if active == "ollama":
            return self.config.ollama_model
        if active == "lmstudio":
            return self.config.lmstudio_model
        return self.config.model

    def status(self) -> dict[str, object]:
        return {
            "name": "AIDA Master Controller",
            "provider": self.provider.name,
            "model": self._active_model(),
            "platform": platform.system(),
            "memory_entries": self.memory.count(),
            "autonomy_mode": "guarded",
            "interfaces": ["web", "cli"],
            "default_runserver_address": self._load_default_runserver_address(),
            "capabilities": [
                "conversation",
                "memory",
                "access-keys",
                "cross-platform orchestration",
            ],
            "updated_at": _utc_now(),
        }

    def chat(
        self,
        prompt: str,
        platform_profile: dict[str, str] | None = None,
        runtime_context: dict[str, str] | None = None,
        research_enabled: bool = False,
        session_id: str = "default",
    ) -> dict[str, object]:
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("Prompt bo'sh bo'lmasligi kerak.")

        self.memory.save("user", clean_prompt, session_id=session_id)
        memory = self.memory.recent(limit=12, session_id=session_id)
        status = self.status()
        research = self._run_research(clean_prompt) if self._should_research(clean_prompt, research_enabled) else []

        try:
            message = self.provider.respond(
                prompt=clean_prompt,
                memory=memory,
                system_prompt=self.system_prompt,
                status=status,
                platform_profile=platform_profile,
                runtime_context=runtime_context,
                research=research,
            )
        except Exception as exc:
            fallback_status = dict(status)
            fallback_status["provider"] = "local-fallback"
            message = self.local_provider.respond(
                prompt=clean_prompt,
                memory=memory,
                system_prompt=self.system_prompt,
                status=fallback_status,
                platform_profile=platform_profile,
                runtime_context=runtime_context,
                research=research,
            )
            message += f"\n\nProvider fallback sababi: {exc}"

        self.memory.save("assistant", message, session_id=session_id)
        return {
            "message": message,
            "status": self.status(),
            "session_id": session_id,
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


controller = AIDAController()
