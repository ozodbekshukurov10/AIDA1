"""
Advanced Code Generation Engine for AIDA
Provides ChatGPT/Claude-level code generation with context awareness,
multi-step refinement, and intelligent model orchestration.
"""

import os
import json
import re
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor


class CodeTaskType(Enum):
    """Different types of code generation tasks."""
    FUNCTION = "function"
    CLASS = "class"
    API_ENDPOINT = "api_endpoint"
    COMPONENT = "component"
    MODULE = "module"
    REFACTOR = "refactor"
    DEBUG = "debug"
    OPTIMIZE = "optimize"
    TEST = "test"
    DOCUMENTATION = "documentation"


@dataclass
class CodeRequest:
    """Represents a code generation request."""
    task_type: CodeTaskType
    description: str
    language: str
    context: str = ""
    existing_code: str = ""
    requirements: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeResponse:
    """Represents a code generation response."""
    generated_code: str
    explanation: str
    imports: List[str]
    dependencies: List[str]
    quality_score: float
    suggestions: List[str] = field(default_factory=list)
    alternative_versions: List[str] = field(default_factory=list)


@dataclass
class CodeContext:
    """Represents project context for code generation."""
    project_structure: Dict[str, Any]
    related_files: List[str]
    patterns: List[str]
    conventions: Dict[str, Any]
    dependencies: Dict[str, str]
    recent_changes: List[str]


class CodeGenerationEngine:
    """
    Advanced code generation engine with multi-model orchestration
    and context-aware generation.
    """
    
    def __init__(self, project_path: str = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.context_cache = {}
        self.model_strategies = {
            "codellama": self._generate_with_codellama,
            "ollama": self._generate_with_ollama,
            "lmstudio": self._generate_with_lmstudio,
            "gemini": self._generate_with_gemini,
        }
        self.quality_metrics = {
            "readability": 0.3,
            "correctness": 0.4,
            "efficiency": 0.2,
            "maintainability": 0.1,
        }
    
    def generate_code(self, request: CodeRequest, model: str = "codellama") -> CodeResponse:
        """
        Generate code based on the request using specified model.
        
        Args:
            request: Code generation request with all parameters
            model: Model to use for generation (codellama, ollama, lmstudio, gemini)
        
        Returns:
            CodeResponse with generated code and metadata
        """
        # Collect project context
        context = self._collect_context(request)
        
        # Select appropriate generation strategy
        strategy = self.model_strategies.get(model, self._generate_with_ollama)
        
        # Generate code with context
        response = strategy(request, context)
        
        # Refine and optimize
        refined_response = self._refine_code(request, response, context)
        
        # Quality assessment
        quality_score = self._assess_quality(refined_response, request)
        refined_response.quality_score = quality_score
        
        return refined_response
    
    def _collect_context(self, request: CodeRequest) -> CodeContext:
        """Collect relevant project context for code generation."""
        cache_key = self._generate_cache_key(request)
        
        if cache_key in self.context_cache:
            return self.context_cache[cache_key]
        
        context = CodeContext(
            project_structure=self._analyze_project_structure(),
            related_files=self._find_related_files(request),
            patterns=self._extract_patterns(request.language),
            conventions=self._detect_conventions(request.language),
            dependencies=self._get_dependencies(),
            recent_changes=self._get_recent_changes(),
        )
        
        self.context_cache[cache_key] = context
        return context
    
    def _analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze project structure and organization."""
        structure = {
            "directories": [],
            "files": [],
            "frameworks": [],
            "architecture": "unknown"
        }
        
        # Detect frameworks
        if (self.project_path / "package.json").exists():
            structure["frameworks"].append("React/Vite")
        if (self.project_path / "manage.py").exists():
            structure["frameworks"].append("Django")
        if (self.project_path / "requirements.txt").exists():
            structure["frameworks"].append("Python")
        
        # Analyze directory structure
        for item in self.project_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                structure["directories"].append(item.name)
            elif item.is_file() and not item.name.startswith("."):
                structure["files"].append(item.name)
        
        return structure
    
    def _find_related_files(self, request: CodeRequest) -> List[str]:
        """Find files related to the code generation request."""
        related_files = []
        
        # Language-specific file extensions
        extensions = {
            "python": [".py"],
            "javascript": [".js", ".jsx"],
            "typescript": [".ts", ".tsx"],
            "java": [".java"],
            "cpp": [".cpp", ".h"],
        }
        
        target_extensions = extensions.get(request.language, [])
        
        # Search for files with matching extensions
        for ext in target_extensions:
            for file_path in self.project_path.rglob(f"*{ext}"):
                # Skip node_modules and virtual environments
                if "node_modules" not in str(file_path) and ".venv" not in str(file_path):
                    related_files.append(str(file_path.relative_to(self.project_path)))
        
        return related_files[:10]  # Limit to 10 most relevant files
    
    def _extract_patterns(self, language: str) -> List[str]:
        """Extract common patterns used in the project for the given language."""
        patterns = []
        
        if language == "python":
            patterns.extend([
                "Django models and views",
                "Class-based views",
                "Function-based views",
                "Async/await patterns",
                "Type hints usage",
            ])
        elif language in ["javascript", "typescript"]:
            patterns.extend([
                "React functional components",
                "Hooks usage",
                "TypeScript interfaces",
                "Async/await patterns",
                "ES6+ syntax",
            ])
        
        return patterns
    
    def _detect_conventions(self, language: str) -> Dict[str, Any]:
        """Detect coding conventions used in the project."""
        conventions = {
            "naming": "snake_case" if language == "python" else "camelCase",
            "indentation": 4 if language == "python" else 2,
            "documentation": "docstrings" if language == "python" else "JSDoc",
            "testing": "pytest" if language == "python" else "jest",
        }
        
        return conventions
    
    def _get_dependencies(self) -> Dict[str, str]:
        """Get project dependencies."""
        dependencies = {}
        
        # Python dependencies
        requirements_file = self.project_path / "requirements.txt"
        if requirements_file.exists():
            try:
                content = requirements_file.read_text()
                for line in content.split("\n"):
                    if line and not line.startswith("#"):
                        parts = line.split("==")
                        dependencies[parts[0]] = parts[1] if len(parts) > 1 else "latest"
            except Exception:
                pass
        
        # Node.js dependencies
        package_json = self.project_path / "package.json"
        if package_json.exists():
            try:
                content = json.loads(package_json.read_text())
                deps = content.get("dependencies", {})
                dependencies.update(deps)
            except Exception:
                pass
        
        return dependencies
    
    def _get_recent_changes(self) -> List[str]:
        """Get recent git changes for context."""
        changes = []
        
        try:
            result = subprocess.run(
                ["git", "log", "-5", "--oneline"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                changes = result.stdout.strip().split("\n")
        except Exception:
            pass
        
        return changes
    
    def _generate_with_codellama(self, request: CodeRequest, context: CodeContext) -> CodeResponse:
        """Generate code using CodeLLaMA model."""
        # Build prompt with context
        prompt = self._build_prompt(request, context, model_specific="codellama")
        
        # Call CodeLLaMA through Ollama
        try:
            code = self._call_codellama_ollama(prompt, request.language)
            explanation = self._generate_explanation(code, request)
            imports = self._extract_imports(code, request.language)
            dependencies = self._identify_dependencies(code, request.language)
            
            return CodeResponse(
                generated_code=code,
                explanation=explanation,
                imports=imports,
                dependencies=dependencies,
                quality_score=0.0,  # Will be calculated later
            )
        except Exception as e:
            return CodeResponse(
                generated_code=f"# Code generation failed: {str(e)}",
                explanation=f"Xatolik yuz berdi: {str(e)}",
                imports=[],
                dependencies=[],
                quality_score=0.0,
            )
    
    def _generate_with_ollama(self, request: CodeRequest, context: CodeContext) -> CodeResponse:
        """Generate code using Ollama with code-focused models."""
        prompt = self._build_prompt(request, context, model_specific="ollama")
        
        try:
            code = self._call_ollama_api(prompt, request.language)
            explanation = self._generate_explanation(code, request)
            imports = self._extract_imports(code, request.language)
            dependencies = self._identify_dependencies(code, request.language)
            
            return CodeResponse(
                generated_code=code,
                explanation=explanation,
                imports=imports,
                dependencies=dependencies,
                quality_score=0.0,
            )
        except Exception as e:
            return CodeResponse(
                generated_code=f"# Code generation failed: {str(e)}",
                explanation=f"Xatolik yuz berdi: {str(e)}",
                imports=[],
                dependencies=[],
                quality_score=0.0,
            )
    
    def _generate_with_lmstudio(self, request: CodeRequest, context: CodeContext) -> CodeResponse:
        """Generate code using LM Studio."""
        prompt = self._build_prompt(request, context, model_specific="lmstudio")
        
        try:
            code = self._call_lmstudio_api(prompt, request.language)
            explanation = self._generate_explanation(code, request)
            imports = self._extract_imports(code, request.language)
            dependencies = self._identify_dependencies(code, request.language)
            
            return CodeResponse(
                generated_code=code,
                explanation=explanation,
                imports=imports,
                dependencies=dependencies,
                quality_score=0.0,
            )
        except Exception as e:
            return CodeResponse(
                generated_code=f"# Code generation failed: {str(e)}",
                explanation=f"Xatolik yuz berdi: {str(e)}",
                imports=[],
                dependencies=[],
                quality_score=0.0,
            )
    
    def _generate_with_gemini(self, request: CodeRequest, context: CodeContext) -> CodeResponse:
        """Generate code using Google Gemini."""
        prompt = self._build_prompt(request, context, model_specific="gemini")
        
        try:
            code = self._call_gemini_api(prompt, request.language)
            explanation = self._generate_explanation(code, request)
            imports = self._extract_imports(code, request.language)
            dependencies = self._identify_dependencies(code, request.language)
            
            return CodeResponse(
                generated_code=code,
                explanation=explanation,
                imports=imports,
                dependencies=dependencies,
                quality_score=0.0,
            )
        except Exception as e:
            return CodeResponse(
                generated_code=f"# Code generation failed: {str(e)}",
                explanation=f"Xatolik yuz berdi: {str(e)}",
                imports=[],
                dependencies=[],
                quality_score=0.0,
            )
    
    def _build_prompt(self, request: CodeRequest, context: CodeContext, model_specific: str = "") -> str:
        """Build comprehensive prompt for code generation."""
        
        # Base system prompt
        system_prompt = """Siz tajribali dasturchi yordamchisiz. Aniq, efficient va maintainable kod yozing.
Project context va existing code patterns ga amal qiling.
O'zbek tilida izohlar yozing, kod esa ingliz tilida bo'lsin."""
        
        # Context information
        context_info = f"""
PROJECT CONTEXT:
- Frameworks: {', '.join(context.frameworks)}
- Language: {request.language}
- Related files: {', '.join(context.related_files[:5])}
- Patterns used: {', '.join(context.patterns)}
- Conventions: {context.conventions}
"""
        
        # Task-specific instructions
        task_instructions = {
            CodeTaskType.FUNCTION: "Write a clean, well-documented function.",
            CodeTaskType.CLASS: "Create a class with proper encapsulation and methods.",
            CodeTaskType.API_ENDPOINT: "Build a REST API endpoint with proper error handling.",
            CodeTaskType.COMPONENT: "Create a reusable component with proper props.",
            CodeTaskType.MODULE: "Design a modular structure with clear responsibilities.",
            CodeTaskType.REFACTOR: "Refactor the code for better readability and performance.",
            CodeTaskType.DEBUG: "Identify and fix bugs in the code.",
            CodeTaskType.OPTIMIZE: "Optimize the code for better performance.",
            CodeTaskType.TEST: "Write comprehensive unit tests.",
            CodeTaskType.DOCUMENTATION: "Add detailed documentation and comments.",
        }
        
        # Build the complete prompt
        prompt = f"""{system_prompt}

{context_info}

TASK: {task_instructions.get(request.task_type, 'Generate code')}

DESCRIPTION:
{request.description}

REQUIREMENTS:
{chr(10).join(f'- {req}' for req in request.requirements)}

CONSTRAINTS:
{chr(10).join(f'- {const}' for const in request.constraints)}

EXISTING CODE (if any):
{request.existing_code}

"""
        
        # Model-specific adjustments
        if model_specific == "codellama":
            prompt += "\nGenerate code with proper syntax highlighting and comments."
        elif model_specific == "ollama":
            prompt += "\nUse best practices and modern language features."
        elif model_specific == "gemini":
            prompt += "\nEnsure code follows Google's style guidelines."
        
        return prompt
    
    def _call_codellama_ollama(self, prompt: str, language: str) -> str:
        """Call CodeLLaMA through Ollama API."""
        url = "http://localhost:11434/api/generate"
        
        # Select appropriate CodeLLaMA model
        model_map = {
            "python": "codellama:python",
            "javascript": "codellama:js",
            "typescript": "codellama:js",
            "java": "codellama:java",
            "cpp": "codellama:cpp",
        }
        
        model = model_map.get(language, "codellama:7b")
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": 2048,
            }
        }
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "")
        except Exception as e:
            raise Exception(f"CodeLLaMA API call failed: {str(e)}")
    
    def _call_ollama_api(self, prompt: str, language: str) -> str:
        """Call Ollama API for code generation."""
        url = "http://localhost:11434/api/generate"
        
        # Use appropriate model
        model = "llama3.2"  # Default fallback
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.4,
                "top_p": 0.9,
                "num_predict": 2048,
            }
        }
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "")
        except Exception as e:
            raise Exception(f"Ollama API call failed: {str(e)}")
    
    def _call_lmstudio_api(self, prompt: str, language: str) -> str:
        """Call LM Studio API for code generation."""
        url = "http://localhost:1234/v1/completions"
        
        payload = {
            "model": "local-model",
            "prompt": prompt,
            "max_tokens": 2048,
            "temperature": 0.4,
        }
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("choices", [{}])[0].get("text", "")
        except Exception as e:
            raise Exception(f"LM Studio API call failed: {str(e)}")
    
    def _call_gemini_api(self, prompt: str, language: str) -> str:
        """Call Google Gemini API for code generation."""
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key:
            raise Exception("GOOGLE_API_KEY not set")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 2048,
            }
        }
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            raise Exception(f"Gemini API call failed: {str(e)}")
    
    def _generate_explanation(self, code: str, request: CodeRequest) -> str:
        """Generate explanation for the generated code."""
        # Extract key parts of the code for explanation
        lines = code.split("\n")
        
        explanation_parts = [
            f"Task: {request.task_type.value}",
            f"Language: {request.language}",
        ]
        
        # Count lines of code
        code_lines = [line for line in lines if line.strip() and not line.strip().startswith("#")]
        explanation_parts.append(f"Generated {len(code_lines)} lines of code")
        
        # Add basic structure description
        if "def " in code:
            functions = [line for line in lines if "def " in line]
            explanation_parts.append(f"Functions: {len(functions)}")
        if "class " in code:
            classes = [line for line in lines if "class " in line]
            explanation_parts.append(f"Classes: {len(classes)}")
        
        return "\n".join(explanation_parts)
    
    def _extract_imports(self, code: str, language: str) -> List[str]:
        """Extract import statements from generated code."""
        imports = []
        lines = code.split("\n")
        
        if language == "python":
            for line in lines:
                if line.strip().startswith("import ") or line.strip().startswith("from "):
                    imports.append(line.strip())
        elif language in ["javascript", "typescript"]:
            for line in lines:
                if line.strip().startswith("import ") or line.strip().startswith("require("):
                    imports.append(line.strip())
        
        return imports
    
    def _identify_dependencies(self, code: str, language: str) -> List[str]:
        """Identify external dependencies in the code."""
        dependencies = []
        
        if language == "python":
            # Common library patterns
            common_libs = ["django", "flask", "requests", "numpy", "pandas", "tensorflow", "pytorch"]
            for lib in common_libs:
                if lib in code.lower():
                    dependencies.append(lib)
        elif language in ["javascript", "typescript"]:
            # Common npm packages
            common_packages = ["react", "vue", "angular", "lodash", "axios", "express"]
            for pkg in common_packages:
                if pkg in code.lower():
                    dependencies.append(pkg)
        
        return dependencies
    
    def _refine_code(self, request: CodeRequest, response: CodeResponse, context: CodeContext) -> CodeResponse:
        """Refine generated code based on context and best practices."""
        refined_code = response.generated_code
        
        # Apply language-specific refinements
        if request.language == "python":
            refined_code = self._refine_python_code(refined_code, context)
        elif request.language in ["javascript", "typescript"]:
            refined_code = self._refine_javascript_code(refined_code, context)
        
        response.generated_code = refined_code
        return response
    
    def _refine_python_code(self, code: str, context: CodeContext) -> str:
        """Apply Python-specific refinements."""
        # Add type hints if missing
        lines = code.split("\n")
        refined_lines = []
        
        for line in lines:
            refined_lines.append(line)
            # Add basic type hints for function definitions
            if "def " in line and "->" not in line and ":" in line:
                # Simple heuristic to add type hints
                func_name = line.split("def ")[1].split("(")[0]
                if func_name:  # This is a simplified version
                    pass  # Full implementation would parse and add proper type hints
        
        return "\n".join(refined_lines)
    
    def _refine_javascript_code(self, code: str, context: CodeContext) -> str:
        """Apply JavaScript/TypeScript-specific refinements."""
        # Ensure modern syntax
        refined_code = code.replace("var ", "const ")  # Basic replacement
        
        return refined_code
    
    def _assess_quality(self, response: CodeResponse, request: CodeRequest) -> float:
        """Assess the quality of generated code."""
        scores = {}
        
        # Readability assessment
        scores["readability"] = self._assess_readability(response.generated_code, request.language)
        
        # Correctness assessment (basic checks)
        scores["correctness"] = self._assess_correctness(response.generated_code, request.language)
        
        # Efficiency assessment
        scores["efficiency"] = self._assess_efficiency(response.generated_code, request.language)
        
        # Maintainability assessment
        scores["maintainability"] = self._assess_maintainability(response.generated_code, request.language)
        
        # Calculate weighted score
        quality_score = sum(
            scores[key] * self.quality_metrics[key] 
            for key in self.quality_metrics
        )
        
        return quality_score
    
    def _assess_readability(self, code: str, language: str) -> float:
        """Assess code readability."""
        score = 0.5  # Base score
        
        lines = code.split("\n")
        
        # Check for comments
        comment_lines = [line for line in lines if "#" in line or "//" in line or "/*" in line]
        if len(comment_lines) > len(lines) * 0.1:  # At least 10% comments
            score += 0.2
        
        # Check for reasonable line length
        long_lines = [line for line in lines if len(line) > 100]
        if len(long_lines) < len(lines) * 0.1:  # Less than 10% long lines
            score += 0.2
        
        # Check for proper indentation
        indented_lines = [line for line in lines if line.startswith("    ") or line.startswith("\t")]
        if len(indented_lines) > 0:
            score += 0.1
        
        return min(score, 1.0)
    
    def _assess_correctness(self, code: str, language: str) -> float:
        """Assess code correctness (basic syntax checks)."""
        score = 0.5  # Base score
        
        try:
            if language == "python":
                import ast
                ast.parse(code)
                score += 0.5  # Valid Python syntax
        except Exception:
            score -= 0.2  # Syntax error
        
        return max(0.0, min(score, 1.0))
    
    def _assess_efficiency(self, code: str, language: str) -> float:
        """Assess code efficiency."""
        score = 0.5  # Base score
        
        # Check for common anti-patterns
        if "O(n^2)" not in code:  # Simple heuristic
            score += 0.2
        
        # Check for proper use of data structures
        if language == "python":
            if "list" in code and "dict" in code:
                score += 0.2
        
        return min(score, 1.0)
    
    def _assess_maintainability(self, code: str, language: str) -> float:
        """Assess code maintainability."""
        score = 0.5  # Base score
        
        # Check for modular structure
        if "def " in code or "function " in code:
            score += 0.2
        
        # Check for error handling
        if "try:" in code or "catch" in code or "except" in code:
            score += 0.2
        
        # Check for documentation
        if '"""' in code or "'''" in code or "/**" in code:
            score += 0.1
        
        return min(score, 1.0)
    
    def _generate_cache_key(self, request: CodeRequest) -> str:
        """Generate cache key for context storage."""
        key_data = f"{request.task_type.value}_{request.language}_{request.description}"
        return hashlib.md5(key_data.encode()).hexdigest()


# Convenience functions for common use cases
def generate_function(description: str, language: str = "python", **kwargs) -> CodeResponse:
    """Generate a function with given description."""
    engine = CodeGenerationEngine()
    request = CodeRequest(
        task_type=CodeTaskType.FUNCTION,
        description=description,
        language=language,
        **kwargs
    )
    return engine.generate_code(request)


def generate_class(description: str, language: str = "python", **kwargs) -> CodeResponse:
    """Generate a class with given description."""
    engine = CodeGenerationEngine()
    request = CodeRequest(
        task_type=CodeTaskType.CLASS,
        description=description,
        language=language,
        **kwargs
    )
    return engine.generate_code(request)


def refactor_code(code: str, language: str = "python", **kwargs) -> CodeResponse:
    """Refactor existing code for better quality."""
    engine = CodeGenerationEngine()
    request = CodeRequest(
        task_type=CodeTaskType.REFACTOR,
        description="Refactor the following code for better readability and performance",
        language=language,
        existing_code=code,
        **kwargs
    )
    return engine.generate_code(request)


def generate_tests(code: str, language: str = "python", **kwargs) -> CodeResponse:
    """Generate unit tests for given code."""
    engine = CodeGenerationEngine()
    request = CodeRequest(
        task_type=CodeTaskType.TEST,
        description="Generate comprehensive unit tests for the following code",
        language=language,
        existing_code=code,
        **kwargs
    )
    return engine.generate_code(request)


if __name__ == "__main__":
    # Test the code generation engine
    print("Testing Code Generation Engine...")
    
    # Test function generation
    result = generate_function(
        "Create a function that sorts a list of dictionaries by a specific key",
        language="python"
    )
    print(f"Generated code:\n{result.generated_code}")
    print(f"Quality score: {result.quality_score}")