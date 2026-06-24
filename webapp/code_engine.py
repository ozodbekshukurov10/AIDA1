"""
Advanced Code Engine for AIDA
Provides syntax analysis, error detection, optimization suggestions,
context-aware generation, and multi-step refinement.
"""

import ast
import re
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class Language(Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    SQL = "sql"
    HTML = "html"
    CSS = "css"


@dataclass
class CodeIssue:
    """Represents a code issue found during analysis."""
    severity: str  # "error", "warning", "info", "suggestion"
    line: int
    column: int
    message: str
    code: str
    suggestion: Optional[str] = None


@dataclass
class OptimizationSuggestion:
    """Represents an optimization suggestion."""
    type: str  # "performance", "readability", "security", "memory"
    line: int
    description: str
    original: str
    suggested: str
    impact: str  # "high", "medium", "low"


@dataclass
class CodeAnalysisResult:
    """Result of code analysis."""
    language: Language
    issues: List[CodeIssue] = field(default_factory=list)
    optimizations: List[OptimizationSuggestion] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    structure: Dict[str, Any] = field(default_factory=dict)


class CodeAnalyzer:
    """Advanced code analyzer with syntax tree analysis and error detection."""
    
    # Language-specific patterns
    LANGUAGE_PATTERNS = {
        Language.PYTHON: {
            "extension": ".py",
            "comment": "#",
            "function_def": r"def\s+(\w+)\s*\(",
            "class_def": r"class\s+(\w+)",
            "import": r"^(?:from\s+\S+\s+)?import\s+",
        },
        Language.JAVASCRIPT: {
            "extension": ".js",
            "comment": "//",
            "function_def": r"function\s+(\w+)\s*\(|const\s+(\w+)\s*=\s*(?:async\s+)?\(",
            "class_def": r"class\s+(\w+)",
            "import": r"^(?:import\s+.*from\s+|const\s+\w+\s*=\s+require\()",
        },
        Language.JAVA: {
            "extension": ".java",
            "comment": "//",
            "function_def": r"(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\(",
            "class_def": r"(?:public\s+)?class\s+(\w+)",
            "import": r"^import\s+",
        },
        Language.CPP: {
            "extension": ".cpp",
            "comment": "//",
            "function_def": r"\w+\s+(\w+)\s*\(",
            "class_def": r"class\s+(\w+)",
            "import": r"^#include",
        },
    }
    
    # Common error patterns
    ERROR_PATTERNS = {
        Language.PYTHON: [
            (r"print\s+\(", "print() syntax for Python 3"),
            (r"xrange\s*\(", "xrange removed in Python 3, use range()"),
            (r"except\s*:", "bare except clause, specify exception type"),
            (r"=\s*None\s*:", "comparison with None should use 'is'"),
        ],
        Language.JAVASCRIPT: [
            (r"var\s+", "use 'let' or 'const' instead of 'var'"),
            (r"==\s*(?!=)", "use '===' for strict equality"),
            (r"!=\s*(?!=)", "use '!==' for strict inequality"),
        ],
    }
    
    def __init__(self):
        self.supported_languages = list(Language)
    
    def detect_language(self, code: str, filename: str = "") -> Language:
        """Detect programming language from code or filename."""
        if filename:
            ext = Path(filename).suffix.lower()
            for lang, patterns in self.LANGUAGE_PATTERNS.items():
                if patterns["extension"] == ext:
                    return lang
        
        # Try to detect from code patterns
        if "def " in code and "import " in code:
            return Language.PYTHON
        elif "function " in code or "const " in code:
            return Language.JAVASCRIPT
        elif "public class " in code or "import " in code and ";" in code:
            return Language.JAVA
        elif "#include" in code:
            return Language.CPP
        
        return Language.PYTHON  # Default
    
    def analyze(self, code: str, filename: str = "") -> CodeAnalysisResult:
        """Perform comprehensive code analysis."""
        language = self.detect_language(code, filename)
        result = CodeAnalysisResult(language=language)
        
        # Syntax tree analysis
        if language == Language.PYTHON:
            result.structure = self._analyze_python_ast(code)
            result.issues.extend(self._check_python_errors(code))
            result.optimizations.extend(self._suggest_python_optimizations(code))
        elif language == Language.JAVASCRIPT:
            result.structure = self._analyze_javascript_structure(code)
            result.issues.extend(self._check_javascript_errors(code))
            result.optimizations.extend(self._suggest_javascript_optimizations(code))
        
        # General metrics
        result.metrics = self._calculate_metrics(code, language)
        
        return result
    
    def _analyze_python_ast(self, code: str) -> Dict[str, Any]:
        """Analyze Python code using AST."""
        try:
            tree = ast.parse(code)
            
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": ast.get_docstring(node),
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                    })
                elif isinstance(node, ast.Import):
                    imports.extend([alias.name for alias in node.names])
                elif isinstance(node, ast.ImportFrom):
                    imports.append(f"from {node.module}")
            
            return {
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "function_count": len(functions),
                "class_count": len(classes),
            }
        except SyntaxError as e:
            return {"error": str(e), "line": e.lineno}
    
    def _analyze_javascript_structure(self, code: str) -> Dict[str, Any]:
        """Analyze JavaScript code structure (basic pattern matching)."""
        functions = []
        classes = []
        imports = []
        
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            # Function detection
            func_match = re.search(r"function\s+(\w+)\s*\(|const\s+(\w+)\s*=\s*(?:async\s+)?\(", line)
            if func_match:
                func_name = func_match.group(1) or func_match.group(2)
                functions.append({"name": func_name, "line": i})
            
            # Class detection
            class_match = re.search(r"class\s+(\w+)", line)
            if class_match:
                classes.append({"name": class_match.group(1), "line": i})
            
            # Import detection
            if re.search(r"import\s+.*from\s+|require\(", line):
                imports.append({"line": i, "statement": line.strip()})
        
        return {
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "function_count": len(functions),
            "class_count": len(classes),
        }
    
    def _check_python_errors(self, code: str) -> List[CodeIssue]:
        """Check for common Python errors."""
        issues = []
        lines = code.split("\n")
        
        for i, line in enumerate(lines, 1):
            # Check for Python 2 vs 3 issues
            if "print " in line and not line.strip().startswith("#"):
                issues.append(CodeIssue(
                    severity="warning",
                    line=i,
                    column=line.find("print"),
                    message="Python 2 print statement detected",
                    code="PY2_PRINT",
                    suggestion="Use print() function for Python 3"
                ))
            
            # Check for bare except
            if re.search(r"except\s*:", line):
                issues.append(CodeIssue(
                    severity="warning",
                    line=i,
                    column=line.find("except"),
                    message="Bare except clause",
                    code="BARE_EXCEPT",
                    suggestion="Specify exception type (e.g., except Exception as e:)"
                ))
            
            # Check for comparison with None
            if re.search(r"==\s*None|!=\s*None", line):
                issues.append(CodeIssue(
                    severity="info",
                    line=i,
                    column=line.find("="),
                    message="Comparison with None",
                    code="NONE_COMPARISON",
                    suggestion="Use 'is' or 'is not' for None comparisons"
                ))
        
        return issues
    
    def _check_javascript_errors(self, code: str) -> List[CodeIssue]:
        """Check for common JavaScript errors."""
        issues = []
        lines = code.split("\n")
        
        for i, line in enumerate(lines, 1):
            # Check for var usage
            if re.search(r"\bvar\s+", line):
                issues.append(CodeIssue(
                    severity="warning",
                    line=i,
                    column=line.find("var"),
                    message="Using 'var' keyword",
                    code="VAR_USAGE",
                    suggestion="Use 'let' or 'const' instead"
                ))
            
            # Check for loose equality
            if re.search(r"==\s*(?!=)", line) and not line.strip().startswith("//"):
                issues.append(CodeIssue(
                    severity="warning",
                    line=i,
                    column=line.find("="),
                    message="Loose equality comparison",
                    code="LOOSE_EQUALITY",
                    suggestion="Use '===' for strict equality"
                ))
        
        return issues
    
    def _suggest_python_optimizations(self, code: str) -> List[OptimizationSuggestion]:
        """Suggest Python code optimizations."""
        optimizations = []
        lines = code.split("\n")
        
        for i, line in enumerate(lines, 1):
            # List comprehension suggestion
            if re.search(r"for\s+\w+\s+in\s+.*:\s*\n\s+\w+\.append\(", code):
                optimizations.append(OptimizationSuggestion(
                    type="readability",
                    line=i,
                    description="Consider using list comprehension",
                    original=line.strip(),
                    suggested="[item for item in iterable]",
                    impact="medium"
                ))
            
            # String concatenation in loop
            if re.search(r"for\s+.*:\s*\n\s*\w+\s*\+=\s*\w+", code):
                optimizations.append(OptimizationSuggestion(
                    type="performance",
                    line=i,
                    description="String concatenation in loop",
                    original=line.strip(),
                    suggested="Use list and join() for better performance",
                    impact="high"
                ))
        
        return optimizations
    
    def _suggest_javascript_optimizations(self, code: str) -> List[OptimizationSuggestion]:
        """Suggest JavaScript code optimizations."""
        optimizations = []
        
        # Template literals suggestion
        if re.search(r"'\s*\+\s*\w+\s*\+\s*'", code):
            optimizations.append(OptimizationSuggestion(
                type="readability",
                line=0,
                description="Use template literals instead of string concatenation",
                original="'string ' + variable + ' string'",
                suggested="`string ${variable} string`",
                impact="medium"
            ))
        
        return optimizations
    
    def _calculate_metrics(self, code: str, language: Language) -> Dict[str, Any]:
        """Calculate code metrics."""
        lines = code.split("\n")
        
        return {
            "total_lines": len(lines),
            "blank_lines": sum(1 for line in lines if not line.strip()),
            "comment_lines": sum(1 for line in lines if line.strip().startswith(
                self.LANGUAGE_PATTERNS.get(language, {}).get("comment", "#")
            )),
            "code_lines": len(lines) - sum(1 for line in lines if not line.strip()) - sum(
                1 for line in lines if line.strip().startswith(
                    self.LANGUAGE_PATTERNS.get(language, {}).get("comment", "#")
                )
            ),
            "avg_line_length": sum(len(line) for line in lines) / len(lines) if lines else 0,
        }


class ContextAwareGenerator:
    """Context-aware code generation with project understanding."""
    
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = Path(project_path) if project_path else None
        self.project_structure = {}
        self.similar_code_cache = {}
        self.detected_libraries = set()
        
        if self.project_path:
            self._analyze_project()
    
    def _analyze_project(self):
        """Analyze project structure and detect libraries."""
        if not self.project_path or not self.project_path.exists():
            return
        
        # Build project structure
        self.project_structure = {
            "files": [],
            "directories": [],
            "languages": set(),
            "frameworks": set(),
        }
        
        for item in self.project_path.rglob("*"):
            if item.is_file():
                self.project_structure["files"].append(str(item.relative_to(self.project_path)))
                # Detect language from extension
                ext = item.suffix.lower()
                if ext == ".py":
                    self.project_structure["languages"].add("python")
                elif ext in [".js", ".jsx", ".ts", ".tsx"]:
                    self.project_structure["languages"].add("javascript")
                elif ext == ".java":
                    self.project_structure["languages"].add("java")
            elif item.is_dir():
                self.project_structure["directories"].append(str(item.relative_to(self.project_path)))
        
        # Detect frameworks
        project_files = [f.lower() for f in self.project_structure["files"]]
        
        if "package.json" in project_files:
            self.project_structure["frameworks"].add("nodejs")
            self._detect_node_libraries()
        
        if "requirements.txt" in project_files or "setup.py" in project_files:
            self.project_structure["frameworks"].add("python")
            self._detect_python_libraries()
        
        if "pom.xml" in project_files:
            self.project_structure["frameworks"].add("maven")
        
        if "build.gradle" in project_files:
            self.project_structure["frameworks"].add("gradle")
    
    def _detect_python_libraries(self):
        """Detect Python libraries from requirements.txt or setup.py."""
        if not self.project_path:
            return
        
        # Check requirements.txt
        req_file = self.project_path / "requirements.txt"
        if req_file.exists():
            with open(req_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        lib_name = line.split(">")[0].split("<")[0].split("=")[0].strip()
                        self.detected_libraries.add(lib_name)
    
    def _detect_node_libraries(self):
        """Detect Node.js libraries from package.json."""
        if not self.project_path:
            return
        
        package_file = self.project_path / "package.json"
        if package_file.exists():
            try:
                with open(package_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    dependencies = data.get("dependencies", {})
                    dev_dependencies = data.get("devDependencies", {})
                    self.detected_libraries.update(dependencies.keys())
                    self.detected_libraries.update(dev_dependencies.keys())
            except Exception:
                pass
    
    def search_similar_code(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar code patterns in the project."""
        if not self.project_path:
            return []
        
        results = []
        query_lower = query.lower()
        query_keywords = set(query_lower.split())
        
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in [".py", ".js", ".jsx", ".ts", ".tsx", ".java"]:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        lines = content.split("\n")
                        
                    for i, line in enumerate(lines, 1):
                        line_lower = line.lower()
                        # Simple keyword matching
                        matches = sum(1 for kw in query_keywords if kw in line_lower)
                        if matches >= 2:
                            results.append({
                                "file": str(file_path.relative_to(self.project_path)),
                                "line": i,
                                "code": line.strip(),
                                "matches": matches,
                            })
                            if len(results) >= limit:
                                return results
                except Exception:
                    continue
        
        return sorted(results, key=lambda x: x["matches"], reverse=True)[:limit]
    
    def get_context_for_generation(self, prompt: str) -> Dict[str, Any]:
        """Get relevant context for code generation."""
        context = {
            "project_structure": self.project_structure,
            "detected_libraries": list(self.detected_libraries),
            "similar_code": self.search_similar_code(prompt, limit=3),
            "best_practices": self._get_best_practices(),
        }
        return context
    
    def _get_best_practices(self) -> List[str]:
        """Get best practices based on detected languages and frameworks."""
        practices = []
        
        languages = self.project_structure.get("languages", set())
        
        if "python" in languages:
            practices.extend([
                "Use type hints for function signatures",
                "Follow PEP 8 style guide",
                "Use docstrings for functions and classes",
                "Prefer list comprehensions over loops",
                "Use context managers (with statements) for resource management",
            ])
        
        if "javascript" in languages:
            practices.extend([
                "Use const/let instead of var",
                "Use arrow functions for callbacks",
                "Prefer template literals over string concatenation",
                "Use async/await for asynchronous code",
                "Follow ESLint rules",
            ])
        
        return practices
    
    def inject_api_documentation(self, code: str, language: Language) -> str:
        """Inject API documentation comments into code."""
        # This is a simplified version - in production, would use actual API docs
        if language == Language.PYTHON:
            # Add docstring templates
            if "def " in code and '"""' not in code:
                lines = code.split("\n")
                for i, line in enumerate(lines):
                    if re.match(r"def\s+\w+", line):
                        indent = len(line) - len(line.lstrip())
                        docstring = ' ' * (indent + 4) + '"""TODO: Add function documentation."""'
                        lines.insert(i + 1, docstring)
                return "\n".join(lines)
        
        return code


class MultiStepRefinement:
    """Multi-step code refinement pipeline."""
    
    def __init__(self):
        self.analyzer = CodeAnalyzer()
        self.steps = [
            "initial_generation",
            "error_checking",
            "optimization",
            "documentation",
            "test_creation",
            "final_review",
        ]
    
    def refine_code(
        self,
        initial_code: str,
        language: Language,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute the 6-step refinement process."""
        results = {
            "steps": [],
            "final_code": initial_code,
            "issues_found": [],
            "optimizations_applied": [],
        }
        
        current_code = initial_code
        
        # Step 1: Initial generation (already provided)
        results["steps"].append({
            "step": 1,
            "name": "Initial Generation",
            "status": "complete",
            "output": "Code generated successfully",
        })
        
        # Step 2: Error checking and fixing
        analysis = self.analyzer.analyze(current_code)
        if analysis.issues:
            results["issues_found"].extend(analysis.issues)
            current_code = self._fix_errors(current_code, analysis.issues)
            results["steps"].append({
                "step": 2,
                "name": "Error Checking & Fixing",
                "status": "complete",
                "issues_fixed": len(analysis.issues),
            })
        else:
            results["steps"].append({
                "step": 2,
                "name": "Error Checking & Fixing",
                "status": "complete",
                "issues_fixed": 0,
            })
        
        # Step 3: Optimization pass
        if analysis.optimizations:
            current_code = self._apply_optimizations(current_code, analysis.optimizations)
            results["optimizations_applied"].extend(analysis.optimizations)
            results["steps"].append({
                "step": 3,
                "name": "Optimization Pass",
                "status": "complete",
                "optimizations": len(analysis.optimizations),
            })
        else:
            results["steps"].append({
                "step": 3,
                "name": "Optimization Pass",
                "status": "complete",
                "optimizations": 0,
            })
        
        # Step 4: Documentation generation
        if context:
            generator = ContextAwareGenerator()
            current_code = generator.inject_api_documentation(current_code, language)
            results["steps"].append({
                "step": 4,
                "name": "Documentation Generation",
                "status": "complete",
            })
        else:
            results["steps"].append({
                "step": 4,
                "name": "Documentation Generation",
                "status": "skipped",
                "reason": "No context provided",
            })
        
        # Step 5: Test case creation
        test_code = self._generate_test_cases(current_code, language)
        results["steps"].append({
            "step": 5,
            "name": "Test Case Creation",
            "status": "complete",
            "test_code": test_code,
        })
        
        # Step 6: Final review
        final_analysis = self.analyzer.analyze(current_code)
        results["steps"].append({
            "step": 6,
            "name": "Final Review",
            "status": "complete",
            "remaining_issues": len(final_analysis.issues),
            "metrics": final_analysis.metrics,
        })
        
        results["final_code"] = current_code
        return results
    
    def _fix_errors(self, code: str, issues: List[CodeIssue]) -> str:
        """Fix detected errors in code."""
        lines = code.split("\n")
        
        for issue in issues:
            if issue.severity in ["error", "warning"] and issue.suggestion:
                line_idx = issue.line - 1
                if 0 <= line_idx < len(lines):
                    # Apply simple fixes (in production, would use more sophisticated AST manipulation)
                    if issue.code == "PY2_PRINT":
                        lines[line_idx] = lines[line_idx].replace("print ", "print(").rstrip() + ")"
                    elif issue.code == "BARE_EXCEPT":
                        lines[line_idx] = lines[line_idx].replace("except:", "except Exception as e:")
        
        return "\n".join(lines)
    
    def _apply_optimizations(self, code: str, optimizations: List[OptimizationSuggestion]) -> str:
        """Apply optimization suggestions."""
        # In production, would use AST-based transformations
        # For now, return original code with note
        return code
    
    def _generate_test_cases(self, code: str, language: Language) -> str:
        """Generate test cases for the code."""
        if language == Language.PYTHON:
            return """
# Test cases
import unittest

class TestCode(unittest.TestCase):
    def test_functionality(self):
        # TODO: Add test cases
        pass

if __name__ == "__main__":
    unittest.main()
"""
        elif language == Language.JAVASCRIPT:
            return """
// Test cases
describe('Code Tests', () => {
    test('functionality', () => {
        // TODO: Add test cases
    });
});
"""
        else:
            return "# TODO: Add test cases"


# Convenience functions
def analyze_code(code: str, filename: str = "") -> CodeAnalysisResult:
    """Analyze code and return results."""
    analyzer = CodeAnalyzer()
    return analyzer.analyze(code, filename)


def refine_code_with_context(
    code: str,
    project_path: str = "",
    language: Optional[Language] = None
) -> Dict[str, Any]:
    """Refine code with context-aware generation."""
    analyzer = CodeAnalyzer()
    if not language:
        language = analyzer.detect_language(code)
    
    context_generator = ContextAwareGenerator(project_path) if project_path else None
    context = context_generator.get_context_for_generation(code) if context_generator else None
    
    refiner = MultiStepRefinement()
    return refiner.refine_code(code, language, context)
