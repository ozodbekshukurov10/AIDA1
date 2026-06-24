"""
Automatic Code Fixing, Performance Optimization, and Test Generation for AIDA
Provides linting fixes, type hints, documentation, refactoring, security, performance optimization, and test generation.
"""

import ast
import re
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class FixType(Enum):
    """Types of code fixes."""
    LINTING = "linting"
    TYPE_HINTS = "type_hints"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    SECURITY = "security"


class OptimizationType(Enum):
    """Types of performance optimizations."""
    ALGORITHM = "algorithm"
    MEMORY = "memory"
    CACHING = "caching"
    ASYNC = "async"
    DATABASE = "database"


class TestType(Enum):
    """Types of tests."""
    UNIT = "unit"
    INTEGRATION = "integration"
    EDGE_CASE = "edge_case"
    PERFORMANCE = "performance"
    SECURITY = "security"


@dataclass
class CodeFix:
    """Represents a code fix suggestion."""
    fix_type: FixType
    line: int
    original: str
    fixed: str
    description: str
    severity: str  # "error", "warning", "info"


@dataclass
class OptimizationSuggestion:
    """Represents a performance optimization suggestion."""
    opt_type: OptimizationType
    line: int
    description: str
    original: str
    suggested: str
    impact: str  # "high", "medium", "low"


@dataclass
class TestCase:
    """Represents a generated test case."""
    test_type: TestType
    name: str
    code: str
    description: str


class AutoCodeFixer:
    """Automatic code fixing for linting, type hints, documentation, refactoring, and security."""
    
    def __init__(self):
        self.fixes: List[CodeFix] = []
    
    def fix_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Analyze and fix code issues."""
        self.fixes = []
        
        if language == "python":
            self._fix_python_linting(code)
            self._add_type_hints(code)
            self._generate_documentation(code)
            self._suggest_refactoring(code)
            self._fix_security_issues(code)
        elif language == "javascript":
            self._fix_javascript_linting(code)
            self._generate_js_documentation(code)
            self._fix_js_security(code)
        
        return {
            "fixes_applied": len(self.fixes),
            "fixes": [
                {
                    "type": fix.fix_type.value,
                    "line": fix.line,
                    "original": fix.original,
                    "fixed": fix.fixed,
                    "description": fix.description,
                    "severity": fix.severity,
                }
                for fix in self.fixes
            ],
        }
    
    def _fix_python_linting(self, code: str):
        """Fix common Python linting errors."""
        lines = code.split("\n")
        
        for i, line in enumerate(lines, 1):
            # Fix trailing whitespace
            if line != line.rstrip():
                self.fixes.append(CodeFix(
                    fix_type=FixType.LINTING,
                    line=i,
                    original=line,
                    fixed=line.rstrip(),
                    description="Remove trailing whitespace",
                    severity="warning",
                ))
            
            # Fix multiple blank lines
            if i > 1 and not line.strip() and not lines[i-2].strip():
                self.fixes.append(CodeFix(
                    fix_type=FixType.LINTING,
                    line=i,
                    original=line,
                    fixed="",
                    description="Remove extra blank line",
                    severity="info",
                ))
            
            # Fix line too long (PEP 8: 79 characters)
            if len(line) > 79 and not line.strip().startswith("#"):
                self.fixes.append(CodeFix(
                    fix_type=FixType.LINTING,
                    line=i,
                    original=line,
                    fixed=line[:79],
                    description="Line too long (PEP 8)",
                    severity="warning",
                ))
    
    def _add_type_hints(self, code: str):
        """Add type hints to Python functions."""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if function has type hints
                    has_return_hint = node.returns is not None
                    has_arg_hints = all(arg.annotation is not None for arg in node.args.args)
                    
                    if not has_return_hint or not has_arg_hints:
                        func_line = node.lineno
                        self.fixes.append(CodeFix(
                            fix_type=FixType.TYPE_HINTS,
                            line=func_line,
                            original=f"def {node.name}(...):",
                            fixed=f"def {node.name}(...) -> None:",
                            description="Add type hints to function signature",
                            severity="info",
                        ))
        except SyntaxError:
            pass
    
    def _generate_documentation(self, code: str):
        """Generate docstrings for functions and classes."""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        self.fixes.append(CodeFix(
                            fix_type=FixType.DOCUMENTATION,
                            line=node.lineno,
                            original=f"def {node.name}(...):",
                            fixed=f'def {node.name}(...):\n    """TODO: Add function documentation."""',
                            description="Add docstring to function",
                            severity="info",
                        ))
                
                elif isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        self.fixes.append(CodeFix(
                            fix_type=FixType.DOCUMENTATION,
                            line=node.lineno,
                            original=f"class {node.name}:",
                            fixed=f'class {node.name}:\n    """TODO: Add class documentation."""',
                            description="Add docstring to class",
                            severity="info",
                        ))
        except SyntaxError:
            pass
    
    def _suggest_refactoring(self, code: str):
        """Suggest code refactoring improvements."""
        lines = code.split("\n")
        
        # Detect code duplication (simplified)
        code_blocks = {}
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and len(stripped) > 20:
                if stripped in code_blocks:
                    self.fixes.append(CodeFix(
                        fix_type=FixType.REFACTORING,
                        line=i + 1,
                        original=line,
                        fixed="# Consider extracting to function",
                        description="Duplicate code detected - consider refactoring",
                        severity="info",
                    ))
                code_blocks[stripped] = i
        
        # Suggest list comprehensions
        for i, line in enumerate(lines):
            if re.search(r"for\s+\w+\s+in\s+.*:\s*\n\s+\w+\.append\(", code):
                self.fixes.append(CodeFix(
                    fix_type=FixType.REFACTORING,
                    line=i + 1,
                    original=line,
                    fixed="# Use list comprehension instead",
                    description="Consider using list comprehension for better readability",
                    severity="info",
                ))
    
    def _fix_security_issues(self, code: str):
        """Fix common security vulnerabilities."""
        lines = code.split("\n")
        
        dangerous_patterns = [
            (r"eval\s*\(", "eval() is dangerous - use ast.literal_eval() or safer alternative"),
            (r"exec\s*\(", "exec() is dangerous - avoid dynamic code execution"),
            (r"pickle\.loads?", "pickle is insecure - use json or safer serialization"),
            (r"subprocess\.call\s*\(\s*shell\s*=\s*True", "shell=True in subprocess is dangerous - avoid shell injection"),
            (r"input\s*\(\s*[^)]*password", "Don't use input() for passwords - use getpass module"),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, description in dangerous_patterns:
                if re.search(pattern, line):
                    self.fixes.append(CodeFix(
                        fix_type=FixType.SECURITY,
                        line=i,
                        original=line,
                        fixed=f"# SECURITY: {description}",
                        description=description,
                        severity="error",
                    ))
    
    def _fix_javascript_linting(self, code: str):
        """Fix common JavaScript linting errors."""
        lines = code.split("\n")
        
        for i, line in enumerate(lines, 1):
            # Fix var usage
            if re.search(r"\bvar\s+", line):
                self.fixes.append(CodeFix(
                    fix_type=FixType.LINTING,
                    line=i,
                    original=line,
                    fixed=line.replace("var ", "const "),
                    description="Use 'const' or 'let' instead of 'var'",
                    severity="warning",
                ))
            
            # Fix loose equality
            if re.search(r"==\s*(?!=)", line):
                self.fixes.append(CodeFix(
                    fix_type=FixType.LINTING,
                    line=i,
                    original=line,
                    fixed=line.replace("==", "==="),
                    description="Use '===' for strict equality",
                    severity="warning",
                ))
    
    def _generate_js_documentation(self, code: str):
        """Generate JSDoc comments for JavaScript functions."""
        function_pattern = r"(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s+)?\(|(\w+)\s*\([^)]*\)\s*=>)"
        
        for match in re.finditer(function_pattern, code):
            func_name = match.group(1) or match.group(2) or match.group(3)
            if func_name:
                line_num = code[:match.start()].count("\n") + 1
                self.fixes.append(CodeFix(
                    fix_type=FixType.DOCUMENTATION,
                    line=line_num,
                    original=match.group(0),
                    fixed=f"/**\n * TODO: Add JSDoc for {func_name}\n */\n{match.group(0)}",
                    description="Add JSDoc comment",
                    severity="info",
                ))
    
    def _fix_js_security(self, code: str):
        """Fix common JavaScript security issues."""
        lines = code.split("\n")
        
        dangerous_patterns = [
            (r"innerHTML\s*=", "innerHTML is vulnerable to XSS - use textContent or sanitize"),
            (r"eval\s*\(", "eval() is dangerous - avoid dynamic code execution"),
            (r"setTimeout\s*\(\s*['\"]", "setTimeout with string is dangerous - use function instead"),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, description in dangerous_patterns:
                if re.search(pattern, line):
                    self.fixes.append(CodeFix(
                        fix_type=FixType.SECURITY,
                        line=i,
                        original=line,
                        fixed=f"// SECURITY: {description}",
                        description=description,
                        severity="error",
                    ))


class PerformanceOptimizer:
    """Performance optimization suggestions for code."""
    
    def __init__(self):
        self.suggestions: List[OptimizationSuggestion] = []
    
    def optimize_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Analyze and suggest performance optimizations."""
        self.suggestions = []
        
        if language == "python":
            self._suggest_algorithm_improvements(code)
            self._suggest_memory_optimizations(code)
            self._suggest_caching(code)
            self._suggest_async_optimizations(code)
            self._suggest_db_optimizations(code)
        elif language == "javascript":
            self._suggest_js_optimizations(code)
        
        return {
            "suggestions": len(self.suggestions),
            "optimizations": [
                {
                    "type": opt.opt_type.value,
                    "line": opt.line,
                    "description": opt.description,
                    "original": opt.original,
                    "suggested": opt.suggested,
                    "impact": opt.impact,
                }
                for opt in self.suggestions
            ],
        }
    
    def _suggest_algorithm_improvements(self, code: str):
        """Suggest algorithm improvements."""
        lines = code.split("\n")
        
        # Detect nested loops (O(n^2) complexity)
        nested_loop_count = 0
        for i, line in enumerate(lines):
            if re.search(r"for\s+.*in\s+.*:", line):
                nested_loop_count += 1
                if nested_loop_count > 1:
                    self.suggestions.append(OptimizationSuggestion(
                        opt_type=OptimizationType.ALGORITHM,
                        line=i + 1,
                        description="Nested loop detected - consider using hash map or set for O(1) lookup",
                        original=line,
                        suggested="# Consider using dict/set for O(1) lookup",
                        impact="high",
                    ))
            elif not re.search(r"for\s+.*in\s+.*:", line):
                nested_loop_count = 0
        
        # Detect linear search in list
        if re.search(r"if\s+\w+\s+in\s+\w+:", code):
            self.suggestions.append(OptimizationSuggestion(
                opt_type=OptimizationType.ALGORITHM,
                line=0,
                description="Linear search in list - convert to set for O(1) membership test",
                original="if item in my_list:",
                suggested="if item in my_set:",
                impact="medium",
            ))
    
    def _suggest_memory_optimizations(self, code: str):
        """Suggest memory optimizations."""
        lines = code.split("\n")
        
        # Detect large list comprehensions
        for i, line in enumerate(lines):
            if re.search(r"\[.*for\s+.*in\s+.*\]", line):
                self.suggestions.append(OptimizationSuggestion(
                    opt_type=OptimizationType.MEMORY,
                    line=i + 1,
                    description="Consider using generator expression instead of list comprehension for memory efficiency",
                    original=line,
                    suggested=line.replace("[", "(").replace("]", ")"),
                    impact="medium",
                ))
        
        # Detect unnecessary copies
        if re.search(r"\w+\s*=\s*\w+\s*\[\s*:\s*\]", code):
            self.suggestions.append(OptimizationSuggestion(
                opt_type=OptimizationType.MEMORY,
                line=0,
                description="Unnecessary slice copy - use original list or copy() method explicitly",
                original="new_list = old_list[:]",
                suggested="new_list = old_list.copy()",
                impact="low",
            ))
    
    def _suggest_caching(self, code: str):
        """Suggest caching opportunities."""
        # Detect expensive operations without caching
        expensive_patterns = [
            (r"requests\.", "HTTP request without caching - consider using requests-cache or functools.lru_cache"),
            (r"json\.loads?\(", "JSON parsing without caching - cache parsed results if called repeatedly"),
            (r"re\.compile\s*\(", "Regex compilation without caching - compile once and reuse"),
        ]
        
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern, description in expensive_patterns:
                if re.search(pattern, line):
                    self.suggestions.append(OptimizationSuggestion(
                        opt_type=OptimizationType.CACHING,
                        line=i,
                        original=line,
                        suggested=f"@lru_cache(maxsize=128)\n{line}",
                        description=description,
                        impact="medium",
                    ))
    
    def _suggest_async_optimizations(self, code: str):
        """Suggest async/await optimizations."""
        lines = code.split("\n")
        
        # Detect blocking I/O operations
        blocking_patterns = [
            (r"time\.sleep\s*\(", "Use asyncio.sleep() instead of time.sleep() for async code"),
            (r"requests\.", "Use aiohttp or httpx instead of requests for async HTTP"),
            (r"subprocess\.", "Use asyncio.subprocess for async subprocess calls"),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, description in blocking_patterns:
                if re.search(pattern, line):
                    self.suggestions.append(OptimizationSuggestion(
                        opt_type=OptimizationType.ASYNC,
                        line=i,
                        original=line,
                        suggested=f"# {description}",
                        description=description,
                        impact="high",
                    ))
    
    def _suggest_db_optimizations(self, code: str):
        """Suggest database query optimizations."""
        # Detect N+1 query pattern
        if re.search(r"for\s+.*in\s+.*:\s*.*\.get\(", code):
            self.suggestions.append(OptimizationSuggestion(
                opt_type=OptimizationType.DATABASE,
                line=0,
                description="N+1 query pattern detected - use select_related/prefetch_related or bulk queries",
                original="for item in items:\n    obj = Model.objects.get(id=item.id)",
                suggested="objs = Model.objects.filter(id__in=[item.id for item in items])",
                impact="high",
            ))
        
        # Detect missing indexes hint
        if re.search(r"filter\([^)]*__contains", code):
            self.suggestions.append(OptimizationSuggestion(
                opt_type=OptimizationType.DATABASE,
                line=0,
                description="__contains queries are slow - consider adding database index or using search",
                original="Model.objects.filter(name__contains='search')",
                suggested="# Consider adding index or using full-text search",
                impact="medium",
            ))
    
    def _suggest_js_optimizations(self, code: str):
        """Suggest JavaScript performance optimizations."""
        lines = code.split("\n")
        
        # Detect DOM manipulation in loops
        for i, line in enumerate(lines):
            if re.search(r"for\s+.*\{[\s\S]*?document\.", code):
                self.suggestions.append(OptimizationSuggestion(
                    opt_type=OptimizationType.ALGORITHM,
                    line=i + 1,
                    description="DOM manipulation in loop - batch DOM updates or use DocumentFragment",
                    original=line,
                    suggested="# Batch DOM updates outside loop",
                    impact="high",
                ))
        
        # Detect synchronous AJAX
        if re.search(r"async:\s*false", code):
            self.suggestions.append(OptimizationSuggestion(
                opt_type=OptimizationType.ASYNC,
                line=0,
                description="Synchronous AJAX blocks UI - use async/await or promises",
                original="async: false",
                suggested="async: true",
                impact="high",
            ))


class TestGenerator:
    """Automatic test generation for unit, integration, edge cases, performance, and security."""
    
    def __init__(self):
        self.tests: List[TestCase] = []
    
    def generate_tests(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Generate comprehensive tests for code."""
        self.tests = []
        
        if language == "python":
            self._generate_unit_tests(code)
            self._generate_integration_tests(code)
            self._generate_edge_case_tests(code)
            self._generate_performance_tests(code)
            self._generate_security_tests(code)
        elif language == "javascript":
            self._generate_js_tests(code)
        
        return {
            "total_tests": len(self.tests),
            "tests": [
                {
                    "type": test.test_type.value,
                    "name": test.name,
                    "code": test.code,
                    "description": test.description,
                }
                for test in self.tests
            ],
        }
    
    def _generate_unit_tests(self, code: str):
        """Generate unit tests for functions."""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    test_code = f"""
def test_{node.name}():
    # Arrange
    # TODO: Add test data
    
    # Act
    # result = {node.name}(test_data)
    
    # Assert
    # assert result is not None
    # assert result == expected
    pass
"""
                    self.tests.append(TestCase(
                        test_type=TestType.UNIT,
                        name=f"test_{node.name}",
                        code=test_code.strip(),
                        description=f"Unit test for {node.name} function",
                    ))
        except SyntaxError:
            pass
    
    def _generate_integration_tests(self, code: str):
        """Generate integration tests."""
        # Detect database operations
        if re.search(r"Model\.objects\.", code):
            test_code = """
def test_database_integration():
    # Test database model integration
    # Create test data
    # Perform operations
    # Verify database state
    pass
"""
            self.tests.append(TestCase(
                test_type=TestType.INTEGRATION,
                name="test_database_integration",
                code=test_code.strip(),
                description="Integration test for database operations",
            ))
        
        # Detect API calls
        if re.search(r"requests\.|urllib\.", code):
            test_code = """
def test_api_integration():
    # Test API integration
    # Mock external API
    # Test request/response handling
    pass
"""
            self.tests.append(TestCase(
                test_type=TestType.INTEGRATION,
                name="test_api_integration",
                code=test_code.strip(),
                description="Integration test for API calls",
            ))
    
    def _generate_edge_case_tests(self, code: str):
        """Generate edge case tests."""
        edge_cases = [
            ("test_empty_input", "Test with empty input"),
            ("test_none_input", "Test with None input"),
            ("test_negative_values", "Test with negative values"),
            ("test_large_input", "Test with large input values"),
            ("test_boundary_conditions", "Test boundary conditions"),
        ]
        
        for test_name, description in edge_cases:
            test_code = f"""
def {test_name}():
    # {description}
    pass
"""
            self.tests.append(TestCase(
                test_type=TestType.EDGE_CASE,
                name=test_name,
                code=test_code.strip(),
                description=description,
            ))
    
    def _generate_performance_tests(self, code: str):
        """Generate performance tests."""
        test_code = """
import time

def test_performance():
    # Performance test
    start_time = time.time()
    
    # Execute function with typical workload
    # result = function_to_test(large_dataset)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Assert performance threshold
    # assert execution_time < 1.0, "Function too slow"
    print(f"Execution time: {execution_time:.2f}s")
"""
        self.tests.append(TestCase(
            test_type=TestType.PERFORMANCE,
            name="test_performance",
            code=test_code.strip(),
            description="Performance test for critical functions",
        ))
    
    def _generate_security_tests(self, code: str):
        """Generate security tests."""
        security_tests = [
            ("test_sql_injection", "Test SQL injection vulnerability"),
            ("test_xss", "Test XSS vulnerability"),
            ("test_authentication", "Test authentication bypass"),
            ("test_authorization", "Test authorization bypass"),
            ("test_input_validation", "Test input validation"),
        ]
        
        for test_name, description in security_tests:
            test_code = f"""
def {test_name}():
    # {description}
    # Test with malicious input
    # Verify proper sanitization/validation
    pass
"""
            self.tests.append(TestCase(
                test_type=TestType.SECURITY,
                name=test_name,
                code=test_code.strip(),
                description=description,
            ))
    
    def _generate_js_tests(self, code: str):
        """Generate JavaScript tests."""
        test_code = """
describe('Code Tests', () => {
    test('functionality', () => {
        // Test basic functionality
        expect(true).toBe(true);
    });
    
    test('edge cases', () => {
        // Test edge cases
        expect(null).toBeNull();
    });
    
    test('performance', () => {
        // Performance test
        const start = performance.now();
        // Execute function
        const duration = performance.now() - start;
        expect(duration).toBeLessThan(1000);
    });
});
"""
        self.tests.append(TestCase(
            test_type=TestType.UNIT,
            name="js_tests",
            code=test_code.strip(),
            description="JavaScript test suite",
        ))


# Convenience functions
def fix_code_automatically(code: str, language: str = "python") -> Dict[str, Any]:
    """Automatically fix code issues."""
    fixer = AutoCodeFixer()
    return fixer.fix_code(code, language)


def optimize_performance(code: str, language: str = "python") -> Dict[str, Any]:
    """Get performance optimization suggestions."""
    optimizer = PerformanceOptimizer()
    return optimizer.optimize_code(code, language)


def generate_comprehensive_tests(code: str, language: str = "python") -> Dict[str, Any]:
    """Generate comprehensive test suite."""
    generator = TestGenerator()
    return generator.generate_tests(code, language)


def analyze_and_improve(code: str, language: str = "python") -> Dict[str, Any]:
    """Complete analysis: fixing, optimization, and test generation."""
    return {
        "code_fixes": fix_code_automatically(code, language),
        "performance_optimizations": optimize_performance(code, language),
        "test_generation": generate_comprehensive_tests(code, language),
    }
