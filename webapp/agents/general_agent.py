import logging
import time
from typing import Any, Callable, Dict, List, Optional

from ..orchestrator import Task
from .base_agent import BaseAgent

logger = logging.getLogger("webapp.agents.general_agent")


class GeneralAgent(BaseAgent):
    def __init__(self, call_model_func: Optional[Callable] = None):
        super().__init__(name="GeneralAgent", model_name="qwen2.5:3b")
        self._call_model_func = call_model_func

    async def _call_model(self, prompt: str) -> str:
        if self._call_model_func:
            return await self._call_model_func(prompt)
        try:
            import httpx
            resp = httpx.post(
                "http://localhost:11434/api/generate",
                json={"model": self.model_name, "prompt": prompt, "stream": False},
                timeout=30,
            )
            return resp.json().get("response", "")
        except Exception as e:
            logger.warning(f"[GeneralAgent] Model call failed: {e}")
            return f"Javob: {prompt}"

    async def execute(self, task: Task) -> Dict[str, Any]:
        start = time.time()
        try:
            result = await self._call_model(task.prompt)
            elapsed = round(time.time() - start, 2)
            self.record_performance(True, elapsed)
            return {"status": "success", "response": result, "execution_time": elapsed}
        except Exception as e:
            elapsed = round(time.time() - start, 2)
            self.record_performance(False, elapsed)
            return {"status": "error", "response": "", "error": str(e), "execution_time": elapsed}
