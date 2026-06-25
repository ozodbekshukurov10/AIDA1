"""
CodeLLaMA Provider for AIDA
Specialized provider for CodeLLaMA models through Ollama
Provides advanced code generation capabilities with context awareness.
"""

import os
import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class CodeLLaMAModel(Enum):
    """Available CodeLLaMA models."""
    PYTHON = "codellama:python"
    JAVASCRIPT = "codellama:js"
    INSTRUCT = "codellama:instruct"
    BASE_7B = "codellama:7b"
    BASE_13B = "codellama:13b"
    BASE_34B = "codellama:34b"


@dataclass
class CodeGenerationConfig:
    """Configuration for code generation."""
    temperature: float = 0.3
    top_p: float = 0.9
    max_tokens: int = 2048
    num_predict: int = 2048
    repeat_penalty: float = 1.0
    stop_sequences: List[str] = None
    
    def __post_init__(self):
        if self.stop_sequences is None:
            self.stop_sequences = []


class CodeLLaMAProvider:
    """
    Provider for CodeLLaMA models through Ollama.
    Supports code generation, completion, and explanation tasks.
    """
    
    name = "codellama"
    
    # Uzbek language instruction for CodeLLaMA
    UZBEK_INSTRUCTION = (
        "\n\nMUHIM: Siz O'zbek tilida so'zlashuvchi AIDA sun'iy intellektisiz. "
        "DOIMO o'zbek tilida javob bering. Kod yozishda izohlarni o'zbek tilida yozing, "
        "kod o'zi esa ingliz tilida bo'lsin. Aniq, efficient va maintainable kod yozing."
    )
    
    def __init__(
        self,
        url: str = "http://localhost:11434",
        model: str = "codellama:python",
        config: CodeGenerationConfig = None
    ):
        """
        Initialize CodeLLaMA provider.
        
        Args:
            url: Ollama server URL
            model: CodeLLaMA model to use
            config: Code generation configuration
        """
        self.url = url.rstrip("/")
        self.model = model
        self.config = config or CodeGenerationConfig()
        
    def respond(
        self,
        prompt: str,
        memory: List[Dict[str, str]],
        system_prompt: str,
        **kwargs
    ) -> str:
        """
        Generate response using CodeLLaMA.
        
        Args:
            prompt: User prompt
            memory: Conversation history
            system_prompt: System prompt
            **kwargs: Additional parameters (research, context, etc.)
        
        Returns:
            Generated response
        """
        # Extract research context if available
        research = kwargs.get("research")
        research_context = ""
        if research:
            research_context = "\n\nInternetdan olingan ma'lumotlar (Kontekst):\n"
            for item in research:
                research_context += f"- {item.title}: {item.summary} (Manba: {item.url})\n"
            research_context += "\nUshbu ma'lumotlardan foydalanib savolga batafsil javob bering."
        
        # Extract code context if available
        code_context = kwargs.get("code_context", "")
        if code_context:
            research_context += f"\n\nCODE CONTEXT:\n{code_context}\n"
        
        # Build system prompt with Uzbek instruction
        sys_content = f"{system_prompt}{self.UZBEK_INSTRUCTION}{research_context}"
        
        # Build message history
        messages = [{"role": "system", "content": sys_content}]
        for msg in memory:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})
        
        # Generate response
        try:
            response = self._generate_chat_completion(messages)
            return response
        except Exception as e:
            return f"CodeLLaMA xatosi: {str(e)}"
    
    def generate_code(
        self,
        description: str,
        language: str = "python",
        context: str = "",
        existing_code: str = ""
    ) -> str:
        """
        Generate code based on description.
        
        Args:
            description: Description of code to generate
            language: Programming language
            context: Additional context
            existing_code: Existing code to modify/refactor
        
        Returns:
            Generated code
        """
        # Build code generation prompt
        prompt = self._build_code_prompt(description, language, context, existing_code)
        
        try:
            response = self._generate_completion(prompt)
            return self._extract_code_from_response(response)
        except Exception as e:
            return f"# Code generation failed: {str(e)}"
    
    def explain_code(self, code: str, language: str = "python") -> str:
        """
        Explain given code.
        
        Args:
            code: Code to explain
            language: Programming language
        
        Returns:
            Explanation of the code
        """
        prompt = f"""Quyidagi {language} kodini tushuntiring. 
Kod qanday ishlashini, qanday muammolarni hal qilishini va 
qanday yaxshilash mumkinligini o'zbek tilida tushuntiring.

```{language}
{code}
```

Tushuntirish:"""
        
        try:
            return self._generate_completion(prompt)
        except Exception as e:
            return f"Code explanation failed: {str(e)}"
    
    def refactor_code(self, code: str, language: str = "python") -> str:
        """
        Refactor code for better quality.
        
        Args:
            code: Code to refactor
            language: Programming language
        
        Returns:
            Refactored code
        """
        prompt = f"""Quyidagi {language} kodini refactoring qiling.
Kodni o'qishni oson, efficient va maintainable qiling.
Comments qo'shing va best practices ga amal qiling.

```{language}
{code}
```

Refactored code:"""
        
        try:
            response = self._generate_completion(prompt)
            return self._extract_code_from_response(response)
        except Exception as e:
            return f"# Refactoring failed: {str(e)}"
    
    def complete_code(self, code: str, language: str = "python") -> str:
        """
        Complete incomplete code.
        
        Args:
            code: Incomplete code
            language: Programming language
        
        Returns:
            Completed code
        """
        prompt = f"""Quyidagi {language} kodini to'ldiring.
Kod mantiqan to'g'ri bo'lishi va best practices ga amal qilishi kerak.

```{language}
{code}
```

Completed code:"""
        
        try:
            response = self._generate_completion(prompt)
            return self._extract_code_from_response(response)
        except Exception as e:
            return f"# Code completion failed: {str(e)}"
    
    def _build_code_prompt(
        self,
        description: str,
        language: str,
        context: str,
        existing_code: str
    ) -> str:
        """Build prompt for code generation."""
        prompt = f"""Write {language} code for the following task:

Task: {description}

"""
        
        if context:
            prompt += f"Context:\n{context}\n\n"
        
        if existing_code:
            prompt += f"Existing code to modify:\n```{language}\n{existing_code}\n```\n\n"
        
        prompt += f"""Requirements:
- Write clean, efficient, and maintainable code
- Add comments in Uzbek language
- Follow best practices and modern language features
- Include proper error handling
- Add type hints where appropriate

Generate the code:"""
        
        return prompt
    
    def _generate_chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """Generate chat completion using Ollama API."""
        url = f"{self.url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "num_predict": self.config.num_predict,
                "repeat_penalty": self.config.repeat_penalty,
            }
        }
        
        if self.config.stop_sequences:
            payload["options"]["stop"] = self.config.stop_sequences
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
                content = result.get("message", {}).get("content", "")
                if not content:
                    return "CodeLLaMA javob bermadi. Model yuklanayotgan bo'lishi mumkin."
                return content
        except urllib.error.URLError:
            return (
                f"⚠️ Ollama server ({self.url}) ga ulanib bo'lmadi. "
                "Ollama dasturi ishga tushirilmagan bo'lishi mumkin. "
                "Buyruq satriga: 'ollama serve' yozing va qayta urinib ko'ring."
            )
        except Exception as e:
            raise Exception(f"CodeLLaMA chat completion failed: {str(e)}")
    
    def _generate_completion(self, prompt: str) -> str:
        """Generate completion using Ollama API."""
        url = f"{self.url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "num_predict": self.config.num_predict,
                "repeat_penalty": self.config.repeat_penalty,
            }
        }
        
        if self.config.stop_sequences:
            payload["options"]["stop"] = self.config.stop_sequences
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
                content = result.get("response", "")
                if not content:
                    return "CodeLLaMA javob bermadi. Model yuklanayotgan bo'lishi mumkin."
                return content
        except urllib.error.URLError:
            return (
                f"⚠️ Ollama server ({self.url}) ga ulanib bo'lmadi. "
                "Ollama dasturi ishga tushirilmagan bo'lishi mumkin."
            )
        except Exception as e:
            raise Exception(f"CodeLLaMA completion failed: {str(e)}")
    
    def _extract_code_from_response(self, response: str) -> str:
        """Extract code block from response."""
        # Try to extract code from markdown code blocks
        if "```" in response:
            # Find code blocks
            code_blocks = []
            lines = response.split("\n")
            in_code_block = False
            current_block = []
            
            for line in lines:
                if line.strip().startswith("```"):
                    if in_code_block:
                        # End of code block
                        code_blocks.append("\n".join(current_block))
                        current_block = []
                        in_code_block = False
                    else:
                        # Start of code block
                        in_code_block = True
                elif in_code_block:
                    current_block.append(line)
            
            if code_blocks:
                return code_blocks[0]  # Return first code block
        
        # If no code blocks found, return the whole response
        return response
    
    def get_available_models(self) -> List[str]:
        """Get list of available CodeLLaMA models."""
        url = f"{self.url}/api/tags"
        
        try:
            req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                models = result.get("models", [])
                return [model["name"] for model in models if "codellama" in model["name"].lower()]
        except Exception as e:
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """Pull a CodeLLaMA model from Ollama."""
        url = f"{self.url}/api/pull"
        
        payload = {
            "name": model_name,
            "stream": False
        }
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=300) as response:
                result = json.loads(response.read().decode("utf-8"))
                return "status" in result
        except Exception as e:
            print(f"Failed to pull model {model_name}: {str(e)}")
            return False
    
    def check_model_available(self, model_name: str) -> bool:
        """Check if a model is available locally."""
        available_models = self.get_available_models()
        return model_name in available_models


# Convenience functions
def create_codellama_provider(
    url: str = "http://localhost:11434",
    model: str = "codellama:python",
    temperature: float = 0.3
) -> CodeLLaMAProvider:
    """Create a configured CodeLLaMA provider."""
    config = CodeGenerationConfig(temperature=temperature)
    return CodeLLaMAProvider(url=url, model=model, config=config)


def setup_codellama_models(url: str = "http://localhost:11434") -> Dict[str, bool]:
    """
    Setup and pull CodeLLaMA models.
    
    Returns:
        Dictionary with model names and pull status
    """
    provider = CodeLLaMAProvider(url=url)
    results = {}
    
    # Models to pull
    models_to_pull = [
        "codellama:python",
        "codellama:js",
        "codellama:instruct",
    ]
    
    for model in models_to_pull:
        print(f"Checking {model}...")
        if provider.check_model_available(model):
            print(f"{model} already available")
            results[model] = True
        else:
            print(f"Pulling {model}...")
            success = provider.pull_model(model)
            results[model] = success
            if success:
                print(f"{model} pulled successfully")
            else:
                print(f"Failed to pull {model}")
    
    return results


if __name__ == "__main__":
    # Test CodeLLaMA provider
    print("Testing CodeLLaMA Provider...")
    
    # Create provider
    provider = create_codellama_provider()
    
    # Test code generation
    print("\n=== Testing Code Generation ===")
    code = provider.generate_code(
        "Create a function that sorts a list of dictionaries by a specific key",
        language="python"
    )
    print(f"Generated code:\n{code}")
    
    # Test code explanation
    print("\n=== Testing Code Explanation ===")
    explanation = provider.explain_code(
        "def sort_dicts(lst, key):\n    return sorted(lst, key=lambda x: x[key])",
        language="python"
    )
    print(f"Explanation:\n{explanation}")
    
    # Check available models
    print("\n=== Available Models ===")
    models = provider.get_available_models()
    print(f"Available CodeLLaMA models: {models}")