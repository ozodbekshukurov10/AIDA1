"""
Project Context Engine and Vector Embeddings for AIDA
Provides Git repo scanning, codebase indexing, semantic search, and knowledge base management.
"""

import os
import re
import json
import sqlite3
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import hashlib


@dataclass
class CodeFile:
    """Represents a code file in the project."""
    path: str
    language: str
    content: str
    size: int
    last_modified: float
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)


@dataclass
class APISpec:
    """Represents an API specification."""
    endpoint: str
    method: str
    description: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    responses: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DatabaseSchema:
    """Represents a database schema."""
    table_name: str
    columns: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)


class ProjectContextEngine:
    """Engine for collecting and indexing project context."""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.index_db = self.project_path / ".aida_context.db"
        self.code_files: List[CodeFile] = []
        self.api_specs: List[APISpec] = []
        self.db_schemas: List[DatabaseSchema] = []
        self.architecture_docs: List[Dict[str, Any]] = []
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize the context database."""
        conn = sqlite3.connect(self.index_db)
        cursor = conn.cursor()
        
        # Code files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                language TEXT,
                content_hash TEXT,
                size INTEGER,
                last_modified REAL,
                indexed_at REAL,
                functions TEXT,
                classes TEXT,
                imports TEXT
            )
        """)
        
        # API specs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_specs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                method TEXT,
                description TEXT,
                parameters TEXT,
                responses TEXT,
                source_file TEXT
            )
        """)
        
        # Database schemas table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS db_schemas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                columns TEXT,
                indexes TEXT,
                relationships TEXT,
                source_file TEXT
            )
        """)
        
        # Architecture docs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS architecture_docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                file_path TEXT,
                doc_type TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_code_files_path ON code_files(path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_specs_endpoint ON api_specs(endpoint)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_db_schemas_table ON db_schemas(table_name)")
        
        conn.commit()
        conn.close()
    
    def scan_git_repo(self) -> Dict[str, Any]:
        """Scan Git repository for metadata."""
        if not (self.project_path / ".git").exists():
            return {"error": "Not a Git repository"}
        
        try:
            # Get git remote
            result = subprocess.run(
                ["git", "remote", "-v"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            remotes = result.stdout.strip() if result.returncode == 0 else ""
            
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            branch = result.stdout.strip() if result.returncode == 0 else ""
            
            # Get last commit
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H|%s|%ai"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            last_commit = result.stdout.strip() if result.returncode == 0 else ""
            
            if last_commit:
                commit_hash, commit_msg, commit_date = last_commit.split("|", 2)
            else:
                commit_hash, commit_msg, commit_date = "", "", ""
            
            return {
                "is_git_repo": True,
                "remotes": remotes,
                "branch": branch,
                "last_commit": {
                    "hash": commit_hash,
                    "message": commit_msg,
                    "date": commit_date,
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    def index_codebase(self, force_reindex: bool = False) -> Dict[str, Any]:
        """Index the entire codebase."""
        indexed_count = 0
        skipped_count = 0
        errors = []
        
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
            ".h": "c",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".sql": "sql",
        }
        
        # Get existing indexed files
        conn = sqlite3.connect(self.index_db)
        cursor = conn.cursor()
        cursor.execute("SELECT path, content_hash, last_modified FROM code_files")
        existing_files = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
        
        # Scan project
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
                    last_modified = file_path.stat().st_mtime
                    
                    # Check if reindex needed
                    if not force_reindex and rel_path in existing_files:
                        existing_hash, existing_mtime = existing_files[rel_path]
                        if existing_hash == content_hash and existing_mtime == last_modified:
                            skipped_count += 1
                            continue
                    
                    # Analyze file
                    language = code_extensions[file_path.suffix]
                    functions = self._extract_functions(content, language)
                    classes = self._extract_classes(content, language)
                    imports = self._extract_imports(content, language)
                    
                    # Store in database
                    cursor.execute("""
                        INSERT OR REPLACE INTO code_files 
                        (path, language, content_hash, size, last_modified, indexed_at, functions, classes, imports)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        rel_path,
                        language,
                        content_hash,
                        len(content),
                        last_modified,
                        datetime.now().timestamp(),
                        json.dumps(functions),
                        json.dumps(classes),
                        json.dumps(imports),
                    ))
                    
                    indexed_count += 1
                    
                except Exception as e:
                    errors.append(f"{file_path}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return {
            "indexed": indexed_count,
            "skipped": skipped_count,
            "errors": errors,
            "total_files": indexed_count + skipped_count,
        }
    
    def _extract_functions(self, content: str, language: str) -> List[str]:
        """Extract function names from code."""
        functions = []
        
        if language == "python":
            import re
            pattern = r"def\s+(\w+)\s*\("
            functions = re.findall(pattern, content)
        elif language in ["javascript", "typescript"]:
            pattern = r"function\s+(\w+)\s*\(|const\s+(\w+)\s*=\s*(?:async\s+)?\(|(\w+)\s*\([^)]*\)\s*=>"
            matches = re.findall(pattern, content)
            functions = [m[0] or m[1] or m[2] for m in matches if m]
        elif language == "java":
            pattern = r"(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\("
            functions = re.findall(pattern, content)
        
        return functions
    
    def _extract_classes(self, content: str, language: str) -> List[str]:
        """Extract class names from code."""
        classes = []
        
        if language == "python":
            pattern = r"class\s+(\w+)"
            classes = re.findall(pattern, content)
        elif language in ["javascript", "typescript", "java", "cpp", "csharp"]:
            pattern = r"class\s+(\w+)"
            classes = re.findall(pattern, content)
        
        return classes
    
    def _extract_imports(self, content: str, language: str) -> List[str]:
        """Extract import statements."""
        imports = []
        
        if language == "python":
            pattern = r"^(?:from\s+\S+\s+)?import\s+(.+)"
            imports = re.findall(pattern, content, re.MULTILINE)
        elif language in ["javascript", "typescript"]:
            pattern = r"import\s+.+from\s+['\"]([^'\"]+)['\"]"
            imports = re.findall(pattern, content)
        elif language == "java":
            pattern = r"^import\s+([^;]+);"
            imports = re.findall(pattern, content, re.MULTILINE)
        
        return imports
    
    def extract_architecture_docs(self) -> List[Dict[str, Any]]:
        """Extract architecture documentation from common files."""
        doc_files = [
            "README.md",
            "ARCHITECTURE.md",
            "DESIGN.md",
            "docs/architecture.md",
            "docs/design.md",
            "docs/api.md",
        ]
        
        docs = []
        
        for doc_file in doc_files:
            file_path = self.project_path / doc_file
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding="utf-8")
                    docs.append({
                        "title": doc_file,
                        "content": content,
                        "file_path": str(file_path.relative_to(self.project_path)),
                        "doc_type": self._classify_doc_type(doc_file),
                    })
                except Exception:
                    pass
        
        # Store in database
        conn = sqlite3.connect(self.index_db)
        cursor = conn.cursor()
        
        for doc in docs:
            cursor.execute("""
                INSERT OR REPLACE INTO architecture_docs 
                (title, content, file_path, doc_type)
                VALUES (?, ?, ?, ?)
            """, (doc["title"], doc["content"], doc["file_path"], doc["doc_type"]))
        
        conn.commit()
        conn.close()
        
        self.architecture_docs = docs
        return docs
    
    def _classify_doc_type(self, filename: str) -> str:
        """Classify document type based on filename."""
        filename_lower = filename.lower()
        
        if "readme" in filename_lower:
            return "readme"
        elif "architect" in filename_lower:
            return "architecture"
        elif "design" in filename_lower:
            return "design"
        elif "api" in filename_lower:
            return "api"
        else:
            return "general"
    
    def detect_api_specs(self) -> List[APISpec]:
        """Detect API specifications from code (Swagger/OpenAPI, decorators, etc.)."""
        specs = []
        
        # Check for OpenAPI/Swagger files
        swagger_files = ["swagger.json", "openapi.json", "swagger.yaml", "openapi.yaml"]
        for swagger_file in swagger_files:
            file_path = self.project_path / swagger_file
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding="utf-8")
                    # Parse and extract API specs (simplified)
                    if file_path.suffix == ".json":
                        data = json.loads(content)
                        paths = data.get("paths", {})
                        for path, methods in paths.items():
                            for method, details in methods.items():
                                specs.append(APISpec(
                                    endpoint=path,
                                    method=method.upper(),
                                    description=details.get("summary", ""),
                                ))
                except Exception:
                    pass
        
        # Check for Python Flask/FastAPI decorators
        for file_path in self.project_path.rglob("*.py"):
            try:
                content = file_path.read_text(encoding="utf-8")
                
                # Flask routes
                flask_pattern = r'@app\.route\([\'"]([^\'"]+)[\'"](?:,\s*methods=\[([^\]]+)\])?\)'
                for match in re.finditer(flask_pattern, content):
                    endpoint = match.group(1)
                    methods_str = match.group(2)
                    methods = ["GET"] if not methods_str else [m.strip().strip('"\'') for m in methods_str.split(",")]
                    for method in methods:
                        specs.append(APISpec(
                            endpoint=endpoint,
                            method=method,
                            description=f"Flask route from {file_path.name}",
                        ))
                
                # FastAPI decorators
                fastapi_pattern = r'@(?:app|router)\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]\)'
                for match in re.finditer(fastapi_pattern, content):
                    method = match.group(1).upper()
                    endpoint = match.group(2)
                    specs.append(APISpec(
                        endpoint=endpoint,
                        method=method,
                        description=f"FastAPI route from {file_path.name}",
                    ))
                
            except Exception:
                continue
        
        # Store in database
        conn = sqlite3.connect(self.index_db)
        cursor = conn.cursor()
        
        for spec in specs:
            cursor.execute("""
                INSERT OR REPLACE INTO api_specs 
                (endpoint, method, description, parameters, responses)
                VALUES (?, ?, ?, ?, ?)
            """, (
                spec.endpoint,
                spec.method,
                spec.description,
                json.dumps(spec.parameters),
                json.dumps(spec.responses),
            ))
        
        conn.commit()
        conn.close()
        
        self.api_specs = specs
        return specs
    
    def extract_database_schemas(self) -> List[DatabaseSchema]:
        """Extract database schemas from SQL files and ORM models."""
        schemas = []
        
        # Check for SQL files
        for file_path in self.project_path.rglob("*.sql"):
            try:
                content = file_path.read_text(encoding="utf-8")
                
                # Extract CREATE TABLE statements
                create_table_pattern = r"CREATE TABLE\s+(\w+)\s*\(([^;]+)\)"
                for match in re.finditer(create_table_pattern, content, re.IGNORECASE):
                    table_name = match.group(1)
                    columns_def = match.group(2)
                    
                    columns = []
                    for col_def in columns_def.split(","):
                        col_def = col_def.strip()
                        if col_def and not col_def.upper().startswith(("PRIMARY", "FOREIGN", "UNIQUE", "INDEX")):
                            parts = col_def.split()
                            if parts:
                                columns.append({
                                    "name": parts[0],
                                    "type": parts[1] if len(parts) > 1 else "unknown",
                                })
                    
                    schemas.append(DatabaseSchema(
                        table_name=table_name,
                        columns=columns,
                        source_file=str(file_path.relative_to(self.project_path)),
                    ))
            except Exception:
                continue
        
        # Check for Django models
        for file_path in self.project_path.rglob("models.py"):
            try:
                content = file_path.read_text(encoding="utf-8")
                
                # Extract Django model classes
                class_pattern = r"class\s+(\w+)\(models\.Model\):([^}]+?)(?=\n\s*class|\Z)"
                for match in re.finditer(class_pattern, content, re.MULTILINE | re.DOTALL):
                    class_name = match.group(1)
                    class_body = match.group(2)
                    
                    columns = []
                    field_pattern = r"(\w+)\s*=\s*models\.(\w+)(?:\([^)]*\))?"
                    for field_match in re.finditer(field_pattern, class_body):
                        columns.append({
                            "name": field_match.group(1),
                            "type": field_match.group(2),
                        })
                    
                    schemas.append(DatabaseSchema(
                        table_name=class_name.lower(),
                        columns=columns,
                        source_file=str(file_path.relative_to(self.project_path)),
                    ))
            except Exception:
                continue
        
        # Store in database
        conn = sqlite3.connect(self.index_db)
        cursor = conn.cursor()
        
        for schema in schemas:
            cursor.execute("""
                INSERT OR REPLACE INTO db_schemas 
                (table_name, columns, indexes, relationships, source_file)
                VALUES (?, ?, ?, ?, ?)
            """, (
                schema.table_name,
                json.dumps(schema.columns),
                json.dumps(schema.indexes),
                json.dumps(schema.relationships),
                schema.source_file,
            ))
        
        conn.commit()
        conn.close()
        
        self.db_schemas = schemas
        return schemas
    
    def search_code(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search indexed code for query."""
        conn = sqlite3.connect(self.index_db)
        cursor = conn.cursor()
        
        # Simple text search (can be enhanced with full-text search)
        cursor.execute("""
            SELECT path, language, functions, classes, imports
            FROM code_files
            WHERE path LIKE ? OR functions LIKE ? OR classes LIKE ? OR imports LIKE ?
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "path": row[0],
                "language": row[1],
                "functions": json.loads(row[2]) if row[2] else [],
                "classes": json.loads(row[3]) if row[3] else [],
                "imports": json.loads(row[4]) if row[4] else [],
            })
        
        conn.close()
        return results
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of indexed project context."""
        conn = sqlite3.connect(self.index_db)
        cursor = conn.cursor()
        
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM code_files")
        code_file_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM api_specs")
        api_spec_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM db_schemas")
        schema_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM architecture_docs")
        doc_count = cursor.fetchone()[0]
        
        # Get language distribution
        cursor.execute("SELECT language, COUNT(*) FROM code_files GROUP BY language")
        language_dist = dict(cursor.fetchall())
        
        conn.close()
        
        git_info = self.scan_git_repo()
        
        return {
            "project_path": str(self.project_path),
            "code_files": code_file_count,
            "api_specs": api_spec_count,
            "database_schemas": schema_count,
            "architecture_docs": doc_count,
            "language_distribution": language_dist,
            "git_info": git_info,
        }


class VectorEmbeddings:
    """Vector embeddings using Sentence Transformers and FAISS for offline semantic search."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.index = None
        self.documents = []
        self.embeddings = None
        self.dimension = 384  # Default for MiniLM
        
        # Try to load sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
        except ImportError:
            print("Warning: sentence-transformers not installed. Install with: pip install sentence-transformers")
        
        # Try to load FAISS
        try:
            import faiss
            self.faiss_available = True
        except ImportError:
            print("Warning: faiss not installed. Install with: pip install faiss-cpu")
            self.faiss_available = False
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text."""
        if not self.model:
            return None
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception:
            return None
    
    def embed_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Generate embeddings for batch of texts."""
        if not self.model:
            return None
        
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception:
            return None
    
    def build_index(self, documents: List[Dict[str, Any]], text_field: str = "content"):
        """Build FAISS index from documents."""
        if not self.faiss_available or not self.model:
            return False
        
        self.documents = documents
        texts = [doc.get(text_field, "") for doc in documents]
        
        # Generate embeddings
        embeddings = self.embed_batch(texts)
        if not embeddings:
            return False
        
        self.embeddings = embeddings
        
        # Build FAISS index
        import faiss
        import numpy as np
        
        embeddings_array = np.array(embeddings, dtype=np.float32)
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings_array)
        
        return True
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if not self.index or not self.model:
            return []
        
        # Generate query embedding
        query_embedding = self.embed_text(query)
        if not query_embedding:
            return []
        
        # Search
        import numpy as np
        query_array = np.array([query_embedding], dtype=np.float32)
        distances, indices = self.index.search(query_array, k)
        
        # Return results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents):
                result = self.documents[idx].copy()
                result["similarity_score"] = float(1 / (1 + dist))  # Convert distance to similarity
                results.append(result)
        
        return results
    
    def save_index(self, path: str):
        """Save FAISS index to disk."""
        if not self.index or not self.faiss_available:
            return False
        
        import faiss
        faiss.write_index(self.index, path)
        
        # Save documents
        docs_path = path.replace(".index", "_docs.json")
        with open(docs_path, "w", encoding="utf-8") as f:
            json.dump(self.documents, f)
        
        return True
    
    def load_index(self, path: str):
        """Load FAISS index from disk."""
        if not self.faiss_available:
            return False
        
        import faiss
        self.index = faiss.read_index(path)
        
        # Load documents
        docs_path = path.replace(".index", "_docs.json")
        with open(docs_path, "r", encoding="utf-8") as f:
            self.documents = json.load(f)
        
        return True


class KnowledgeBase:
    """Knowledge base for storing company docs, code examples, design patterns, and conventions."""
    
    def __init__(self, db_path: str = ".aida_knowledge.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize knowledge base database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Company docs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT,
                tags TEXT,
                created_at REAL,
                updated_at REAL
            )
        """)
        
        # Code examples table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_examples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                code TEXT NOT NULL,
                language TEXT,
                category TEXT,
                tags TEXT,
                created_at REAL
            )
        """)
        
        # Design patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS design_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                example_code TEXT,
                language TEXT,
                category TEXT,
                created_at REAL
            )
        """)
        
        # Common fixes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS common_fixes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem TEXT NOT NULL,
                solution TEXT NOT NULL,
                code_example TEXT,
                language TEXT,
                tags TEXT,
                created_at REAL
            )
        """)
        
        # Team conventions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_conventions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                rule TEXT,
                category TEXT,
                created_at REAL
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_docs_category ON company_docs(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_code_examples_language ON code_examples(language)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_design_patterns_category ON design_patterns(category)")
        
        conn.commit()
        conn.close()
    
    def add_company_doc(self, title: str, content: str, category: str = "", tags: List[str] = None) -> int:
        """Add company documentation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO company_docs (title, content, category, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, content, category, json.dumps(tags or []), datetime.now().timestamp(), datetime.now().timestamp()))
        
        doc_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return doc_id
    
    def add_code_example(self, title: str, code: str, language: str, description: str = "", category: str = "", tags: List[str] = None) -> int:
        """Add code example."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO code_examples (title, description, code, language, category, tags, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, description, code, language, category, json.dumps(tags or []), datetime.now().timestamp()))
        
        example_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return example_id
    
    def add_design_pattern(self, name: str, description: str, example_code: str, language: str = "", category: str = "") -> int:
        """Add design pattern."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO design_patterns (name, description, example_code, language, category, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, description, example_code, language, category, datetime.now().timestamp()))
        
        pattern_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return pattern_id
    
    def add_common_fix(self, problem: str, solution: str, code_example: str = "", language: str = "", tags: List[str] = None) -> int:
        """Add common fix."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO common_fixes (problem, solution, code_example, language, tags, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (problem, solution, code_example, language, json.dumps(tags or []), datetime.now().timestamp()))
        
        fix_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return fix_id
    
    def add_team_convention(self, name: str, description: str, rule: str = "", category: str = "") -> int:
        """Add team convention."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO team_conventions (name, description, rule, category, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, rule, category, datetime.now().timestamp()))
        
        conv_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return conv_id
    
    def search_docs(self, query: str, category: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Search company documentation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute("""
                SELECT id, title, content, category, tags
                FROM company_docs
                WHERE category = ? AND (title LIKE ? OR content LIKE ?)
                LIMIT ?
            """, (category, f"%{query}%", f"%{query}%", limit))
        else:
            cursor.execute("""
                SELECT id, title, content, category, tags
                FROM company_docs
                WHERE title LIKE ? OR content LIKE ?
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "category": row[3],
                "tags": json.loads(row[4]) if row[4] else [],
            })
        
        conn.close()
        return results
    
    def search_code_examples(self, query: str, language: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Search code examples."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if language:
            cursor.execute("""
                SELECT id, title, description, code, language, category, tags
                FROM code_examples
                WHERE language = ? AND (title LIKE ? OR description LIKE ? OR code LIKE ?)
                LIMIT ?
            """, (language, f"%{query}%", f"%{query}%", f"%{query}%", limit))
        else:
            cursor.execute("""
                SELECT id, title, description, code, language, category, tags
                FROM code_examples
                WHERE title LIKE ? OR description LIKE ? OR code LIKE ?
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "code": row[3],
                "language": row[4],
                "category": row[5],
                "tags": json.loads(row[6]) if row[6] else [],
            })
        
        conn.close()
        return results
    
    def get_design_patterns(self, category: str = "") -> List[Dict[str, Any]]:
        """Get design patterns."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute("""
                SELECT id, name, description, example_code, language, category
                FROM design_patterns
                WHERE category = ?
            """, (category,))
        else:
            cursor.execute("""
                SELECT id, name, description, example_code, language, category
                FROM design_patterns
            """)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "example_code": row[3],
                "language": row[4],
                "category": row[5],
            })
        
        conn.close()
        return results
    
    def get_common_fixes(self, language: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Get common fixes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if language:
            cursor.execute("""
                SELECT id, problem, solution, code_example, language, tags
                FROM common_fixes
                WHERE language = ?
                LIMIT ?
            """, (language, limit))
        else:
            cursor.execute("""
                SELECT id, problem, solution, code_example, language, tags
                FROM common_fixes
                LIMIT ?
            """, (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "problem": row[1],
                "solution": row[2],
                "code_example": row[3],
                "language": row[4],
                "tags": json.loads(row[5]) if row[5] else [],
            })
        
        conn.close()
        return results
    
    def get_team_conventions(self, category: str = "") -> List[Dict[str, Any]]:
        """Get team conventions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute("""
                SELECT id, name, description, rule, category
                FROM team_conventions
                WHERE category = ?
            """, (category,))
        else:
            cursor.execute("""
                SELECT id, name, description, rule, category
                FROM team_conventions
            """)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "rule": row[3],
                "category": row[4],
            })
        
        conn.close()
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get knowledge base summary."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM company_docs")
        doc_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM code_examples")
        example_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM design_patterns")
        pattern_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM common_fixes")
        fix_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM team_conventions")
        conv_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "company_docs": doc_count,
            "code_examples": example_count,
            "design_patterns": pattern_count,
            "common_fixes": fix_count,
            "team_conventions": conv_count,
        }


# Convenience functions
def index_project(project_path: str, force_reindex: bool = False) -> Dict[str, Any]:
    """Index a project for context collection."""
    engine = ProjectContextEngine(project_path)
    
    results = {
        "git_info": engine.scan_git_repo(),
        "codebase": engine.index_codebase(force_reindex=force_reindex),
        "architecture": engine.extract_architecture_docs(),
        "api_specs": len(engine.detect_api_specs()),
        "db_schemas": len(engine.extract_database_schemas()),
        "summary": engine.get_context_summary(),
    }
    
    return results


def create_vector_index(documents: List[Dict[str, Any]], save_path: str = "vector.index") -> bool:
    """Create and save vector index from documents."""
    embeddings = VectorEmbeddings()
    if embeddings.build_index(documents):
        return embeddings.save_index(save_path)
    return False
