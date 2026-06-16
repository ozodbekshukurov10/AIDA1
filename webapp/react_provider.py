from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from typing import Callable


REACT_SYSTEM_PROMPT = """You are AIDA, an advanced AI assistant with access to tools.
Follow this format EXACTLY:

Question: {input}
Thought: Your reasoning about what to do next.
Action: tool_name(tool_input)
Observation: Result of the action
(Repeat Thought/Action/Observation as needed)
Thought: I now have the final answer.
Final Answer: Your comprehensive answer.

Available tools:
{tool_descriptions}

IMPORTANT: You are FULLY FLUENT in Uzbek language. ALWAYS respond in rich, natural, high-vocabulary Uzbek regardless of input language.
Understand ALL Uzbek words, phrases, idioms, and mixed-language inputs perfectly.
Be helpful, accurate, and concise."""


class Tool:
    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func

    def run(self, **kwargs) -> str:
        try:
            result = self.func(**kwargs)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"


class ReActProvider:
    name = "react"

    def __init__(self, api_key: str, api_url: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.max_steps = 8
        self.tools: list[Tool] = []
        self._init_tools()

    def _init_tools(self):
        from .aida_controller import controller

        def search_web(query: str) -> str:
            results = controller.research_service.search(query, limit=5)
            if not results:
                return "Hech qanday natija topilmadi."
            lines = []
            for i, r in enumerate(results, 1):
                lines.append(f"{i}. {r.title}")
                lines.append(f"   {r.summary[:200]}")
                lines.append(f"   Link: {r.url}")
            return "\n".join(lines)

        def calculate(expression: str) -> str:
            import math
            allowed = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
            allowed["__builtins__"] = {}
            try:
                result = eval(expression, allowed)
                return f"Natija: {result}"
            except Exception as e:
                return f"Xatolik: {str(e)}"

        def get_datetime(timezone: str = "Asia/Tashkent") -> str:
            from datetime import datetime
            try:
                import pytz
                tz = pytz.timezone(timezone)
                now = datetime.now(tz)
                return f"Hozir: {now.strftime('%Y-%m-%d %H:%M:%S')} ({timezone})"
            except Exception:
                return f"Hozir: {datetime.utcnow().isoformat()} UTC"

        def remember_fact(fact: str) -> str:
            controller.memory.remember_fact(fact)
            return f"Eslab qoldim: {fact}"

        def get_learned_facts() -> str:
            facts = controller.memory.learned_facts()
            if not facts:
                return "Hozircha eslab qolingan malumot yoq."
            return "\n".join(f"- {f}" for f in facts)

        self.tools = [
            Tool("search_web", "Internetdan malumot qidirish (query: qidiruv sorovi)", search_web),
            Tool("calculate", "Matematik hisob-kitob (expression: matematik ifoda)", calculate),
            Tool("get_datetime", "Hozirgi vaqtni olish (timezone: Asia/Tashkent)", get_datetime),
            Tool("remember_fact", "Malumotni eslab qolish (fact: eslab qolinadigan malumot)", remember_fact),
            Tool("get_learned_facts", "Eslab qolingan malumotlarni olish", lambda: get_learned_facts()),
        ]

    def _call_llm(self, history: list[dict]) -> str:
        system = REACT_SYSTEM_PROMPT.format(
            input=history[0]["content"] if history else "",
            tool_descriptions="\n".join(f"- {t.name}: {t.description}" for t in self.tools),
        )
        messages = [{"role": "user", "content": system}]
        for msg in history[1:]:
            messages.append(msg)

        formatted_history = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            formatted_history += f"{role}: {content}\n"

        payload = {
            "contents": [{"role": "user", "parts": [{"text": formatted_history}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
        }
        try:
            req = urllib.request.Request(
                self.api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": self.api_key,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return f"LLM error: {str(e)}"

    def respond(self, prompt: str, memory, system_prompt, **kwargs) -> str:
        tool_desc = "\n".join(f"- {t.name}: {t.description}" for t in self.tools)
        history = [{"role": "user", "content": prompt}]

        for step in range(self.max_steps):
            response = self._call_llm(history)
            history.append({"role": "assistant", "content": response})

            final_match = re.search(r"Final Answer:\s*(.*)", response, re.DOTALL)
            if final_match:
                return final_match.group(1).strip()

            action_match = re.search(r"Action:\s*(\w+)\((.*)\)", response)
            if action_match:
                tool_name = action_match.group(1)
                tool_input = action_match.group(2).strip().strip('"').strip("'")
                tool = next((t for t in self.tools if t.name == tool_name), None)
                if tool:
                    observation = tool.run(input=tool_input)
                else:
                    observation = f"Error: Unknown tool '{tool_name}'"
                history.append({"role": "user", "content": f"Observation: {observation}"})
            else:
                history.append({"role": "user", "content": "Continue. Either provide Action or Final Answer."})

        return "Javob tayyorlashda xatolik yuz berdi. Iltimos, qayta urinib koring."
