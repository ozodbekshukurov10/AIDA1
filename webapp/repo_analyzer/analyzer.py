from __future__ import annotations
import asyncio
import logging
import time
from typing import Any

from .config import AnalyzerConfig
from .github_client import GitHubClient, RepoInfo
from .repo_manager import RepoManager
from .graph_analyzers import DependencyGraph, CallGraph, ImportGraph
from .structure import ASTAnalyzer, ClassDiagram, FunctionDiagram
from .documentation import DocumentationGenerator
from .architecture import ArchitectureDetector
from .quality import BugPredictor, SecurityAnalyzer, CodeQualityAnalyzer

logger = logging.getLogger("webapp.repo_analyzer.analyzer")


class RepositoryAnalyzer:
    def __init__(self, config: AnalyzerConfig | None = None):
        self.config = config or AnalyzerConfig()
        self.github = GitHubClient(self.config)
        self.repo_mgr = RepoManager(self.config)
        self.repo_info: RepoInfo | None = None

    async def analyze(self, repo_url: str, branch: str = "",
                      max_files: int = 1000, deep: bool = False) -> dict[str, Any]:
        start = time.time()
        result: dict[str, Any] = {
            "repository": {},
            "summary": {},
            "dependency_graph": {},
            "call_graph": {},
            "import_graph": {},
            "class_diagram": {},
            "function_diagram": {},
            "documentation": {},
            "architecture": {},
            "bug_prediction": {},
            "security": {},
            "code_quality": {},
            "timing": {},
        }

        try:
            repo_full_name = self._parse_repo_url(repo_url)
            self.repo_info = await self.github.get_repo_info(repo_full_name)
            if self.repo_info:
                result["repository"] = self.repo_info.to_dict()

            logger.info(f"Cloning/opening {repo_url}...")
            clone_start = time.time()
            repo_path = await self.repo_mgr.clone(repo_url, branch)
            if not repo_path:
                result["error"] = "Failed to clone repository"
                return result
            result["timing"]["clone"] = round(time.time() - clone_start, 2)

            files = self.repo_mgr.find_files(repo_path)
            if max_files and len(files) > max_files:
                logger.info(f"Limiting from {len(files)} to {max_files} files")
                files = files[:max_files]

            result["summary"] = self.repo_mgr.get_repo_stats(repo_path)

            logger.info(f"Analyzing {len(files)} files...")
            analyze_start = time.time()

            dep_graph = DependencyGraph()
            call_graph = CallGraph()
            import_graph = ImportGraph()
            ast_analyzer = ASTAnalyzer()
            class_diagram = ClassDiagram()
            func_diagram = FunctionDiagram()
            doc_gen = DocumentationGenerator()
            bug_pred = BugPredictor()
            sec_analyzer = SecurityAnalyzer()
            qual_analyzer = CodeQualityAnalyzer()

            for f in files:
                source = self.repo_mgr.read_file(f["abs_path"])
                if not source:
                    continue
                lang = f["language"]
                fp = f["path"]

                dep_graph.add_file(fp, source, lang)
                call_graph.add_file(fp, source, lang)
                import_graph.add_file(fp, source, lang)
                ast_analyzer.add_file(fp, source, lang)
                class_diagram.add_file(fp, source, lang)
                func_diagram.add_file(fp, source, lang)
                doc_gen.add_file(fp, source, lang)
                bug_pred.add_file(fp, source, lang)
                sec_analyzer.add_file(fp, source, lang)
                qual_analyzer.add_file(fp, source, lang)

                if deep:
                    dep_graph.add_dependency(fp, lang)

            result["dependency_graph"] = dep_graph.to_dict()
            result["call_graph"] = call_graph.to_dict()
            result["import_graph"] = import_graph.to_dict()
            result["ast"] = ast_analyzer.to_dict()
            result["class_diagram"] = class_diagram.to_dict()
            result["function_diagram"] = func_diagram.to_dict()
            result["documentation"] = doc_gen.to_dict()
            result["bug_prediction"] = bug_pred.to_dict()
            result["security"] = sec_analyzer.to_dict()
            result["code_quality"] = qual_analyzer.to_dict()

            result["timing"]["analysis"] = round(time.time() - analyze_start, 2)

            arch = ArchitectureDetector()
            arch.analyze(files, self.repo_mgr, repo_path)
            result["architecture"] = arch.to_dict()

            readme_path = self._find_readme(repo_path)
            if readme_path:
                result["readme"] = self.repo_mgr.read_file(readme_path)[:5000]

            result["summary"]["files_analyzed"] = len(files)
            result["summary"]["architecture"] = result["architecture"]["type"]
            result["summary"]["bug_risk"] = result["bug_prediction"].get("risk_score", 0)
            result["summary"]["security_score"] = result["security"].get("severity_score", 0)
            result["summary"]["quality_score"] = result["code_quality"].get("overall_score", 0)
            result["timing"]["total"] = round(time.time() - start, 2)

        except Exception as e:
            logger.exception(f"Analysis failed: {e}")
            result["error"] = str(e)
        finally:
            await self.github.close()

        return result

    def _parse_repo_url(self, url: str) -> str:
        url = url.rstrip("/").replace(".git", "")
        if "github.com/" in url:
            parts = url.split("github.com/")[-1]
            return parts
        return url

    def _find_readme(self, repo_path: str) -> str | None:
        import glob
        for p in glob.glob(f"{repo_path}/**/[Rr][Ee][Aa][Dd][Mm][Ee]*", recursive=True):
            return p
        return None
