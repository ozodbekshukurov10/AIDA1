"""
Project Context Injection System for AIDA
Provides intelligent context gathering and injection for code generation.
Uses vector embeddings and semantic search to find relevant code patterns.
"""

import os
import re
import json
import sqlite3
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CodeSnippet:
    """Represents a code snippet with metadata."""
    file_path: str
    language: str
    code: str
    description: str
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None


@dataclass
class ContextQuery:
    """Represents a context query."""
    query: str
    language: str
    max_results: int = 5
    include_related: bool = True
    semantic_search: bool = True


@dataclass
class ContextResult:
    """Represents context search results."""
    snippets: List[CodeSnippet]
    patterns: List[str]
    conventions: Dict[str, Any]
    dependencies: Dict[str, str]
    architecture_summary: str
    relevance_scores: List[float]


class ContextInjector:
    """
    Advanced context injection system for code generation.
    Provides semantic search, pattern matching, and context-aware suggestions.
    """
    
    def __init__(self, project_path: str = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.context_db = self.project_path / ".aida_context_injection.db"
        self.snippet_cache = {}
        self.pattern_cache = {}
        
        # Initialize database
        self._init_db()
        
        # Load existing context
        self._load_context()
    
    def _init_db(self):
        """Initialize the context injection database."""
        conn = sqlite3.connect(self.context_db)
        cursor = conn.cursor()
        
        # Code snippets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_snippets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                language TEXT NOT NULL,
                code TEXT NOT NULL,
                description TEXT,
                tags TEXT,
                dependencies TEXT,
                functions TEXT,
                classes TEXT,
                embedding BLOB,
                content_hash TEXT UNIQUE,
                created_at REAL,
                last_accessed REAL
            )
        """)
        
        # Patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT NOT NULL,
                language TEXT NOT NULL,
                category TEXT,
                usage_count INTEGER DEFAULT 0,
                last_used REAL
            )
        """)
        
        # Conventions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conventions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_path TEXT NOT NULL,
                language TEXT NOT NULL,
                convention_type TEXT NOT NULL,
                convention_value TEXT NOT NULL,
                confidence REAL DEFAULT 0.0
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snippets_language ON code_snippets(language)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snippets_file ON code_snippets(file_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns_language ON patterns(language)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conventions_project ON conventions(project_path)")
        
        conn.commit()
        conn.close()
    
    def _load_context(self):
        """Load existing context from database."""
        # This would load frequently used snippets into cache
        pass
    
    def inject_context(
        self,
        query: ContextQuery,
        max_context_length: int = 4000
    ) -> str:
        """
        Inject relevant context into a formatted string for code generation.
        
        Args:
            query: Context query with search parameters
            max_context_length: Maximum length of context string
        
        Returns:
            Formatted context string
        """
        # Search for relevant snippets
        results = self.search_context(query)
        
        # Build context string
        context_parts = []
        
        # Add architecture summary
        if results.architecture_summary:
            context_parts.append(f"PROJECT ARCHITECTURE:\n{results.architecture_summary}\n")
        
        # Add relevant code snippets
        if results.snippets:
            context_parts.append("RELEVANT CODE EXAMPLES:\n")
            for i, (snippet, score) in enumerate(zip(results.snippets, results.relevance_scores)):
                if score > 0.3:  # Only include highly relevant snippets
                    context_parts.append(f"Example {i+1} (relevance: {score:.2f}):")
                    context_parts.append(f"File: {snippet.file_path}")
                    context_parts.append(f"Description: {snippet.description}")
                    context_parts.append(f"```{snippet.language}")
                    context_parts.append(snippet.code)
                    context_parts.append("```\n")
        
        # Add patterns
        if results.patterns:
            context_parts.append("COMMON PATTERNS:\n")
            for pattern in results.patterns:
                context_parts.append(f"- {pattern}")
            context_parts.append("\n")
        
        # Add conventions
        if results.conventions:
            context_parts.append("CODING CONVENTIONS:\n")
            for conv_type, conv_value in results.conventions.items():
                context_parts.append(f"- {conv_type}: {conv_value}")
            context_parts.append("\n")
        
        # Add dependencies
        if results.dependencies:
            context_parts.append("PROJECT DEPENDENCIES:\n")
            for dep, version in results.dependencies.items():
                context_parts.append(f"- {dep}: {version}")
            context_parts.append("\n")
        
        # Combine and truncate if necessary
        full_context = "\n".join(context_parts)
        
        if len(full_context) > max_context_length:
            # Smart truncation - keep important parts
            full_context = self._smart_truncate(full_context, max_context_length)
        
        return full_context
    
    def search_context(self, query: ContextQuery) -> ContextResult:
        """
        Search for relevant context based on query.
        
        Args:
            query: Context query
        
        Returns:
            ContextResult with relevant information
        """
        # Perform semantic search if enabled
        if query.semantic_search:
            snippets = self._semantic_search(query)
        else:
            snippets = self._keyword_search(query)
        
        # Extract patterns
        patterns = self._extract_patterns(query.language)
        
        # Detect conventions
        conventions = self._detect_conventions(query.language)
        
        # Get dependencies
        dependencies = self._get_dependencies()
        
        # Generate architecture summary
        architecture_summary = self._generate_architecture_summary()
        
        # Calculate relevance scores
        relevance_scores = self._calculate_relevance(snippets, query.query)
        
        return ContextResult(
            snippets=snippets,
            patterns=patterns,
            conventions=conventions,
            dependencies=dependencies,
            architecture_summary=architecture_summary,
            relevance_scores=relevance_scores
        )
    
    def _semantic_search(self, query: ContextQuery) -> List[CodeSnippet]:
        """Perform semantic search using embeddings."""
        # In a real implementation, this would use vector embeddings
        # For now, we'll use keyword-based search as a fallback
        
        conn = sqlite3.connect(self.context_db)
        cursor = conn.cursor()
        
        # Search for snippets matching the language
        cursor.execute(
            "SELECT file_path, language, code, description, tags, dependencies, functions, classes FROM code_snippets WHERE language = ?",
            (query.language,)
        )
        
        results = []
        for row in cursor.fetchall():
            snippet = CodeSnippet(
                file_path=row[0],
                language=row[1],
                code=row[2],
                description=row[3],
                tags=json.loads(row[4]) if row[4] else [],
                dependencies=json.loads(row[5]) if row[5] else [],
                functions=json.loads(row[6]) if row[6] else [],
                classes=json.loads(row[7]) if row[7] else []
            )
            results.append(snippet)
        
        conn.close()
        
        # Sort by relevance (simple keyword matching for now)
        query_lower = query.query.lower()
        query_words = set(query_lower.split())
        
        def calculate_keyword_relevance(snippet: CodeSnippet) -> float:
            """Calculate relevance based on keyword matching."""
            score = 0.0
            
            # Check description
            desc_lower = snippet.description.lower()
            for word in query_words:
                if word in desc_lower:
                    score += 0.3
            
            # Check tags
            for tag in snippet.tags:
                if word in tag.lower():
                    score += 0.2
            
            # Check functions
            for func in snippet.functions:
                if word in func.lower():
                    score += 0.1
            
            return score
        
        results.sort(key=calculate_keyword_relevance, reverse=True)
        
        return results[:query.max_results]
    
    def _keyword_search(self, query: ContextQuery) -> List[CodeSnippet]:
        """Perform keyword-based search."""
        conn = sqlite3.connect(self.context_db)
        cursor = conn.cursor()
        
        # Extract keywords from query
        keywords = self._extract_keywords(query.query)
        
        # Build SQL query with keyword matching
        placeholders = ",".join(["?" for _ in keywords])
        sql = f"""
            SELECT file_path, language, code, description, tags, dependencies, functions, classes 
            FROM code_snippets 
            WHERE language = ? 
            AND (description LIKE ? OR code LIKE ? OR tags LIKE ?)
        """
        
        results = []
        for keyword in keywords:
            keyword_pattern = f"%{keyword}%"
            cursor.execute(sql, (query.language, keyword_pattern, keyword_pattern, keyword_pattern))
            
            for row in cursor.fetchall():
                snippet = CodeSnippet(
                    file_path=row[0],
                    language=row[1],
                    code=row[2],
                    description=row[3],
                    tags=json.loads(row[4]) if row[4] else [],
                    dependencies=json.loads(row[5]) if row[5] else [],
                    functions=json.loads(row[6]) if row[6] else [],
                    classes=json.loads(row[7]) if row[7] else []
                )
                results.append(snippet)
        
        conn.close()
        
        # Remove duplicates and limit results
        unique_results = []
        seen = set()
        for snippet in results:
            if snippet.file_path not in seen:
                seen.add(snippet.file_path)
                unique_results.append(snippet)
        
        return unique_results[:query.max_results]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Remove common stopwords
        stopwords = {
            "va", "yoki", "bilan", "uchun", "bu", "ham", "men", "sen", "u",
            "bir", "da", "ga", "ni", "dan", "the", "a", "an", "is", "in",
            "of", "to", "and", "or", "for", "that", "it", "as", "with"
        }
        
        words = re.findall(r'\w+', text.lower())
        keywords = [word for word in words if word not in stopwords and len(word) > 2]
        
        return keywords[:10]  # Limit to top 10 keywords
    
    def _extract_patterns(self, language: str) -> List[str]:
        """Extract common patterns for the language."""
        cache_key = f"patterns_{language}"
        
        if cache_key in self.pattern_cache:
            return self.pattern_cache[cache_key]
        
        conn = sqlite3.connect(self.context_db)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT pattern, usage_count FROM patterns WHERE language = ? ORDER BY usage_count DESC LIMIT 10",
            (language,)
        )
        
        patterns = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # If no patterns in database, use default patterns
        if not patterns:
            patterns = self._get_default_patterns(language)
        
        self.pattern_cache[cache_key] = patterns
        return patterns
    
    def _get_default_patterns(self, language: str) -> List[str]:
        """Get default patterns for a language."""
        default_patterns = {
            "python": [
                "Django models and views",
                "Class-based views",
                "Function-based views",
                "Async/await patterns",
                "Type hints usage",
                "Context managers",
                "Decorators pattern",
            ],
            "javascript": [
                "React functional components",
                "Hooks usage",
                "Async/await patterns",
                "Promise chains",
                "ES6 modules",
                "Arrow functions",
            ],
            "typescript": [
                "React functional components with TypeScript",
                "TypeScript interfaces",
                "Generic types",
                "Type guards",
                "Async/await patterns",
            ],
        }
        
        return default_patterns.get(language, [])
    
    def _detect_conventions(self, language: str) -> Dict[str, Any]:
        """Detect coding conventions used in the project."""
        conn = sqlite3.connect(self.context_db)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT convention_type, convention_value, confidence FROM conventions WHERE project_path = ? AND language = ?",
            (str(self.project_path), language)
        )
        
        conventions = {}
        for row in cursor.fetchall():
            conv_type, conv_value, confidence = row
            if confidence > 0.5:  # Only include high-confidence conventions
                conventions[conv_type] = conv_value
        
        conn.close()
        
        # If no conventions detected, use defaults
        if not conventions:
            conventions = self._get_default_conventions(language)
        
        return conventions
    
    def _get_default_conventions(self, language: str) -> Dict[str, Any]:
        """Get default conventions for a language."""
        default_conventions = {
            "python": {
                "naming": "snake_case",
                "indentation": 4,
                "documentation": "docstrings",
                "testing": "pytest",
                "import_style": "PEP 8",
            },
            "javascript": {
                "naming": "camelCase",
                "indentation": 2,
                "documentation": "JSDoc",
                "testing": "jest",
                "import_style": "ES6 modules",
            },
            "typescript": {
                "naming": "camelCase",
                "indentation": 2,
                "documentation": "JSDoc",
                "testing": "jest",
                "import_style": "ES6 modules",
            },
        }
        
        return default_conventions.get(language, {})
    
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
    
    def _generate_architecture_summary(self) -> str:
        """Generate a summary of project architecture."""
        summary_parts = []
        
        # Detect frameworks
        frameworks = []
        if (self.project_path / "package.json").exists():
            frameworks.append("React/Vite")
        if (self.project_path / "manage.py").exists():
            frameworks.append("Django")
        if (self.project_path / "requirements.txt").exists():
            frameworks.append("Python")
        
        if frameworks:
            summary_parts.append(f"Frameworks: {', '.join(frameworks)}")
        
        # Analyze directory structure
        main_dirs = []
        for item in self.project_path.iterdir():
            if item.is_dir() and not item.name.startswith(".") and item.name not in ["node_modules", ".venv"]:
                main_dirs.append(item.name)
        
        if main_dirs:
            summary_parts.append(f"Main directories: {', '.join(main_dirs[:5])}")
        
        return "\n".join(summary_parts)
    
    def _calculate_relevance(self, snippets: List[CodeSnippet], query: str) -> List[float]:
        """Calculate relevance scores for snippets."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scores = []
        for snippet in snippets:
            score = 0.0
            
            # Check description match
            desc_lower = snippet.description.lower()
            for word in query_words:
                if word in desc_lower:
                    score += 0.4
            
            # Check code content match
            code_lower = snippet.code.lower()
            for word in query_words:
                if word in code_lower:
                    score += 0.3
            
            # Check tags match
            for tag in snippet.tags:
                if word in tag.lower():
                    score += 0.2
            
            # Check functions/classes match
            for func in snippet.functions:
                if word in func.lower():
                    score += 0.1
            
            scores.append(min(score, 1.0))
        
        return scores
    
    def _smart_truncate(self, text: str, max_length: int) -> str:
        """Smart truncation that preserves important parts."""
        if len(text) <= max_length:
            return text
        
        # Split into sections
        sections = text.split("\n\n")
        result = []
        current_length = 0
        
        for section in sections:
            if current_length + len(section) <= max_length:
                result.append(section)
                current_length += len(section)
            else:
                # Try to include part of the section
                remaining = max_length - current_length
                if remaining > 100:  # Only if enough space
                    result.append(section[:remaining] + "...")
                break
        
        return "\n\n".join(result)
    
    def index_codebase(self, force_reindex: bool = False):
        """Index the codebase for context search."""
        # Supported file extensions
        code_extensions = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
        }
        
        conn = sqlite3.connect(self.context_db)
        cursor = conn.cursor()
        
        indexed_count = 0
        
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in code_extensions:
                try:
                    # Skip hidden files and common exclusions
                    if any(part.startswith(".") for part in file_path.parts):
                        continue
                    
                    if "node_modules" in str(file_path) or ".venv" in str(file_path):
                        continue
                    
                    rel_path = str(file_path.relative_to(self.project_path))
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    content_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    # Check if already indexed
                    cursor.execute(
                        "SELECT id FROM code_snippets WHERE content_hash = ?",
                        (content_hash,)
                    )
                    if not force_reindex and cursor.fetchone():
                        continue
                    
                    # Extract code information
                    language = code_extensions[file_path.suffix]
                    functions = self._extract_functions(content, language)
                    classes = self._extract_classes(content, language)
                    dependencies = self._extract_imports(content, language)
                    
                    # Create snippet
                    snippet = CodeSnippet(
                        file_path=rel_path,
                        language=language,
                        code=content,
                        description=self._generate_description(content, language),
                        tags=self._generate_tags(content, language),
                        dependencies=dependencies,
                        functions=functions,
                        classes=classes
                    )
                    
                    # Insert into database
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO code_snippets 
                        (file_path, language, code, description, tags, dependencies, functions, classes, content_hash, created_at, last_accessed)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            snippet.file_path,
                            snippet.language,
                            snippet.code,
                            snippet.description,
                            json.dumps(snippet.tags),
                            json.dumps(snippet.dependencies),
                            json.dumps(snippet.functions),
                            json.dumps(snippet.classes),
                            content_hash,
                            datetime.now().timestamp(),
                            datetime.now().timestamp()
                        )
                    )
                    
                    indexed_count += 1
                    
                except Exception as e:
                    print(f"Error indexing {file_path}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        print(f"Indexed {indexed_count} files")
    
    def _extract_functions(self, code: str, language: str) -> List[str]:
        """Extract function names from code."""
        functions = []
        
        if language == "python":
            import re
            pattern = r'def\s+(\w+)\s*\('
            functions = re.findall(pattern, code)
        elif language in ["javascript", "typescript"]:
            import re
            patterns = [
                r'function\s+(\w+)\s*\(',
                r'const\s+(\w+)\s*=\s*(?:async\s+)?\(',
                r'(\w+)\s*:\s*function',
            ]
            for pattern in patterns:
                functions.extend(re.findall(pattern, code))
        
        return functions
    
    def _extract_classes(self, code: str, language: str) -> List[str]:
        """Extract class names from code."""
        classes = []
        
        if language == "python":
            import re
            pattern = r'class\s+(\w+)'
            classes = re.findall(pattern, code)
        elif language in ["javascript", "typescript"]:
            import re
            pattern = r'class\s+(\w+)'
            classes = re.findall(pattern, code)
        
        return classes
    
    def _extract_imports(self, code: str, language: str) -> List[str]:
        """Extract import statements from code."""
        imports = []
        
        if language == "python":
            import re
            patterns = [
                r'import\s+(\w+)',
                r'from\s+\w+\s+import\s+(\w+)',
            ]
            for pattern in patterns:
                imports.extend(re.findall(pattern, code))
        elif language in ["javascript", "typescript"]:
            import re
            patterns = [
                r'import.*from\s+["\']([^"\']+)["\']',
                r'require\(["\']([^"\']+)["\']\)',
            ]
            for pattern in patterns:
                imports.extend(re.findall(pattern, code))
        
        return imports
    
    def _generate_description(self, code: str, language: str) -> str:
        """Generate description for code snippet."""
        lines = code.split("\n")
        
        # Extract comments as description
        comments = []
        for line in lines:
            stripped = line.strip()
            if language == "python" and stripped.startswith("#"):
                comments.append(stripped[1:].strip())
            elif language in ["javascript", "typescript"] and (stripped.startswith("//") or stripped.startswith("/*")):
                comments.append(stripped[2:].strip())
        
        if comments:
            return " ".join(comments[:3])  # First 3 comments
        
        # Generate basic description
        functions = self._extract_functions(code, language)
        classes = self._extract_classes(code, language)
        
        parts = []
        if functions:
            parts.append(f"Functions: {', '.join(functions[:3])}")
        if classes:
            parts.append(f"Classes: {', '.join(classes[:3])}")
        
        return "; ".join(parts) if parts else "Code snippet"
    
    def _generate_tags(self, code: str, language: str) -> List[str]:
        """Generate tags for code snippet."""
        tags = [language]
        
        # Add common pattern tags
        if "def " in code and "class " in code:
            tags.append("mixed")
        elif "def " in code:
            tags.append("functions")
        elif "class " in code:
            tags.append("classes")
        
        if "async " in code:
            tags.append("async")
        if "try:" in code or "catch" in code:
            tags.append("error_handling")
        if "import " in code or "require(" in code:
            tags.append("imports")
        
        return tags


# Convenience functions
def create_context_injector(project_path: str = None) -> ContextInjector:
    """Create a context injector for the project."""
    return ContextInjector(project_path)


def get_context_for_generation(
    query: str,
    language: str,
    project_path: str = None,
    max_length: int = 4000
) -> str:
    """
    Get context string for code generation.
    
    Args:
        query: Code generation query
        language: Programming language
        project_path: Project directory path
        max_length: Maximum context length
    
    Returns:
        Formatted context string
    """
    injector = ContextInjector(project_path)
    
    context_query = ContextQuery(
        query=query,
        language=language,
        max_results=5,
        semantic_search=True
    )
    
    return injector.inject_context(context_query, max_length)


if __name__ == "__main__":
    # Test context injection
    print("Testing Context Injection System...")
    
    # Create injector
    injector = create_context_injector()
    
    # Index codebase
    print("Indexing codebase...")
    injector.index_codebase()
    
    # Test context search
    query = ContextQuery(
        query="Create a function that processes user authentication",
        language="python",
        max_results=3
    )
    
    results = injector.search_context(query)
    print(f"Found {len(results.snippets)} relevant snippets")
    
    # Test context injection
    context = injector.inject_context(query)
    print(f"Generated context ({len(context)} chars):")
    print(context[:500])