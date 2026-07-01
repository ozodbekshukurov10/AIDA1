from __future__ import annotations
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any
import time

from .config import AnalyzerConfig

logger = logging.getLogger("webapp.repo_analyzer.repo_manager")


class RepoManager:
    def __init__(self, config: AnalyzerConfig | None = None):
        self.config = config or AnalyzerConfig()
        self._repos: dict[str, str] = {}

    async def clone(self, repo_url: str, branch: str = "") -> str | None:
        base_dir = Path(self.config.temp_dir)
        base_dir.mkdir(parents=True, exist_ok=True)

        repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        dest = base_dir / repo_name

        if dest.exists():
            logger.info(f"Repository already exists: {dest}, pulling...")
            try:
                subprocess.run(
                    ["git", "-C", str(dest), "pull"],
                    capture_output=True, timeout=60,
                )
            except Exception:
                pass
            self._repos[repo_url] = str(dest)
            return str(dest)

        try:
            cmd = ["git", "clone"]
            if branch:
                cmd.extend(["--branch", branch])
            cmd.extend([repo_url, str(dest)])
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            if result.returncode != 0:
                logger.error(f"Clone failed: {result.stderr.decode()[:200]}")
                return None
            self._repos[repo_url] = str(dest)
            logger.info(f"Cloned {repo_url} to {dest}")
            return str(dest)
        except subprocess.TimeoutExpired:
            logger.error("Clone timed out")
            return None
        except Exception as e:
            logger.error(f"Clone error: {e}")
            return None

    async def clone_from_github(self, repo_full_name: str, branch: str = "") -> str | None:
        url = f"https://github.com/{repo_full_name}.git"
        return await self.clone(url, branch)

    def get_path(self, repo_url: str) -> str | None:
        return self._repos.get(repo_url)

    def find_files(self, repo_path: str) -> list[dict]:
        found = []
        base = Path(repo_path)
        if not base.exists():
            return found

        for root, dirs, files in os.walk(base):
            rel_root = Path(root).relative_to(base)
            dirs[:] = [d for d in dirs if d not in self.config.exclude_dirs]

            for f in files:
                ext = Path(f).suffix.lower()
                if ext not in self.config.include_extensions:
                    continue

                fpath = Path(root) / f
                try:
                    fsize = fpath.stat().st_size
                except Exception:
                    fsize = 0

                if fsize > self.config.max_file_size:
                    continue

                rel_path = str(rel_root / f) if str(rel_root) != "." else f
                found.append({
                    "path": rel_path,
                    "abs_path": str(fpath),
                    "extension": ext,
                    "size": fsize,
                    "language": self._detect_language(ext),
                })

                if len(found) >= self.config.max_files:
                    return found

        found.sort(key=lambda x: x["path"])
        return found

    def read_file(self, abs_path: str) -> str:
        try:
            return Path(abs_path).read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""

    def detect_languages(self, repo_path: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for f in self.find_files(repo_path):
            lang = f["language"]
            counts[lang] = counts.get(lang, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def get_repo_stats(self, repo_path: str) -> dict:
        files = self.find_files(repo_path)
        total_lines = 0
        language_lines: dict[str, int] = {}
        for f in files:
            content = self.read_file(f["abs_path"])
            lines = content.count("\n") + 1
            total_lines += lines
            lang = f["language"]
            language_lines[lang] = language_lines.get(lang, 0) + lines
        return {
            "total_files": len(files),
            "total_lines": total_lines,
            "languages": dict(sorted(language_lines.items(), key=lambda x: x[1], reverse=True)),
        }

    def _detect_language(self, ext: str) -> str:
        mapping = {
            ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
            ".jsx": "React JSX", ".tsx": "React TSX",
            ".java": "Java", ".kt": "Kotlin",
            ".go": "Go", ".rs": "Rust",
            ".rb": "Ruby", ".php": "PHP",
            ".swift": "Swift",
            ".c": "C", ".cpp": "C++", ".h": "C Header", ".hpp": "C++ Header",
            ".cs": "C#", ".scala": "Scala",
            ".ex": "Elixir", ".exs": "Elixir Script",
            ".vue": "Vue", ".svelte": "Svelte",
        }
        return mapping.get(ext, "Unknown")

    def cleanup(self, repo_path: str | None = None):
        import shutil
        if repo_path:
            try:
                shutil.rmtree(repo_path)
                logger.info(f"Removed: {repo_path}")
            except Exception:
                pass
        else:
            base = Path(self.config.temp_dir)
            if base.exists():
                shutil.rmtree(base)
                logger.info(f"Removed all: {base}")
