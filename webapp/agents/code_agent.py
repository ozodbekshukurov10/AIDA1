import ast
import logging
import time
from typing import Any, Dict, List, Optional, Callable

from ..orchestrator import Task
from .base_agent import BaseAgent

logger = logging.getLogger("webapp.agents.code_agent")

PLAN_PROMPT = "Bu kod masalasi uchun eng yaxshi yondashuv nima? Masala: {prompt} Javob: Qadamma-qadam reja"

CODE_PROMPT = "Production-ready kod yoz: Talabalar: {prompt} Kod (faqat kod):"

FIX_PROMPT = "Ushbu kodni tuzat: Masalalar: {analysis} KOD: {code} TUZATILGAN KOD:"

TEST_PROMPT = "Ushbu kod uchun unit tests yoz (pytest): KOD: {code} TEST KOD:"

EXPLAIN_PROMPT = "Ushbu kodni UZBEKCHA sodda tilda tushuntir: KOD: {code} TUSHUNTIRISH:"


class CodeAgent(BaseAgent):
    def __init__(
        self,
        model_name: str = "codellama:34b",
        memory: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Any]] = None,
        call_model_func: Optional[Callable] = None,
    ):
        super().__init__(name="CodeAgent", model_name=model_name, memory=memory, tools=tools)
        self.code_history: List[Dict[str, Any]] = []
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
            data = resp.json()
            return data.get("response", "")
        except Exception as e:
            logger.warning(f"[CodeAgent] Model call failed: {e}")
            return f"# Model placeholder for: {prompt[:60]}..."

    async def execute(self, task: Task) -> Dict[str, Any]:
        start = time.time()
        try:
            input_analysis = await self.analyze_input(task.prompt)

            plan = await self._plan_approach(task.prompt)

            code = await self._generate_code(task.prompt)

            code_analysis = await self._analyze_code(code)

            if code_analysis.get("issues"):
                fixed = await self._auto_fix(code, code_analysis)
                if fixed.strip():
                    code = fixed

            tests = await self._generate_tests(code)

            explanation = await self._generate_explanation(code)

            quality_score = self._evaluate_quality(code, tests)
            correctness = self._verify_correctness(code)
            eval_result = await self.self_evaluate({
                "quality": quality_score,
                "correctness": 1.0 if correctness else 0.0,
                "errors": code_analysis.get("issues", []),
            })

            elapsed = time.time() - start
            self.record_performance(eval_result["quality_score"] >= 0.5, elapsed)

            self.code_history.append({
                "prompt": task.prompt,
                "code": code,
                "tests": tests,
                "quality": eval_result["quality_score"],
                "timestamp": time.time(),
            })

            status = "success" if eval_result["quality_score"] >= 0.5 else "partial"
            return {
                "status": status,
                "code": code,
                "tests": tests,
                "explanation": explanation,
                "quality_score": eval_result["quality_score"],
                "suggestions": eval_result["improvement_areas"],
                "execution_time": round(elapsed, 2),
            }
        except Exception as e:
            elapsed = time.time() - start
            self.record_performance(False, elapsed)
            logger.exception(f"[CodeAgent] execute failed: {e}")
            return {
                "status": "error",
                "code": "",
                "tests": "",
                "explanation": f"Xatolik yuz berdi: {e}",
                "quality_score": 0.0,
                "suggestions": ["Error handling", "Debug execution"],
                "execution_time": round(elapsed, 2),
            }

    async def _plan_approach(self, prompt: str) -> str:
        return await self._call_model(PLAN_PROMPT.format(prompt=prompt))

    async def _generate_code(self, prompt: str) -> str:
        return await self._call_model(CODE_PROMPT.format(prompt=prompt))

    async def _analyze_code(self, code: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "valid": False,
            "issues": [],
            "complexity": 0,
            "node_count": 0,
            "depth": 0,
        }
        if not code.strip():
            result["issues"].append("Empty code")
            return result

        try:
            tree = ast.parse(code)
            result["valid"] = True
        except SyntaxError as e:
            result["issues"].append(f"Syntax error: {e}")
            return result

        result["node_count"] = sum(1 for _ in ast.walk(tree))
        result["depth"] = self._ast_depth(tree)

        lines = code.strip().split("\n")
        avg_line_len = sum(len(l) for l in lines) / len(lines) if lines else 0
        if avg_line_len > 100:
            result["issues"].append("Lines too long (>100 chars)")
        if result["node_count"] > 200:
            result["issues"].append("High complexity (too many nodes)")
        if result["depth"] > 10:
            result["issues"].append("Deep nesting (depth > 10)")

        for node in ast.walk(tree):
            if isinstance(node, ast.Try) and not node.handlers and not node.finalbody:
                result["issues"].append("Bare try block without except/finally")
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                result["issues"].append("Bare except clause (no exception type)")
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "abstractmethod":
                        for stmt in node.body:
                            if isinstance(stmt, ast.Pass):
                                result["issues"].append(f"Abstract method {node.name} has no docstring")

        result["complexity"] = min(result["node_count"] // 10, 10)
        return result

    async def _auto_fix(self, code: str, analysis: Dict[str, Any]) -> str:
        prompt = FIX_PROMPT.format(analysis=analysis, code=code)
        return await self._call_model(prompt)

    async def _generate_tests(self, code: str) -> str:
        prompt = TEST_PROMPT.format(code=code)
        return await self._call_model(prompt)

    async def _generate_explanation(self, code: str) -> str:
        prompt = EXPLAIN_PROMPT.format(code=code)
        return await self._call_model(prompt)

    def _score_option(self, option: str) -> float:
        norm = option.lower()
        score = 0.5
        if len(norm) > 15:
            score += 0.15
        if any(c in norm for c in [".", ":", "!", "?"]):
            score += 0.1
        if any(kw in norm for kw in ["python", "fast", "clean", "simple", "readable"]):
            score += 0.15
        if any(kw in norm for kw in ["best", "optimal", "efficient", "recommended"]):
            score += 0.1
        return round(min(score, 1.0), 2)

    def _evaluate_quality(self, code: str, tests: str) -> float:
        score = 0.0
        if code.strip():
            score += 0.8
        if self._verify_correctness(code):
            score += 0.1
        if tests.strip():
            score += 0.1
        return round(min(score, 1.0), 2)

    def _verify_correctness(self, code: str) -> bool:
        if not code.strip():
            return False
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def _identify_improvements(self, result: Dict[str, Any]) -> List[str]:
        areas = []
        if result.get("errors"):
            areas.append("Error handling")
        if result.get("quality", 0) < 0.7:
            areas.append("Output quality")
        if hasattr(result, "get") and result.get("completeness", 1) < 0.8:
            areas.append("Completeness")
        if not areas:
            areas.append("Performance optimization")
        return areas

    def _should_retry(self, result: Dict[str, Any]) -> bool:
        code = result.get("code", "") if isinstance(result, dict) else ""
        return not self._verify_correctness(code)

    def _ast_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        if not hasattr(node, "body") or not node.body:
            return current_depth
        max_depth = current_depth + 1
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                                   ast.For, ast.While, ast.If, ast.With, ast.Try)):
                max_depth = max(max_depth, self._ast_depth(child, current_depth + 1))
        return max_depth
