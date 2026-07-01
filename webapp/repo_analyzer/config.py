from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnalyzerConfig:
    temp_dir: str = "projects/analyzed"
    max_file_size: int = 500000
    max_files: int = 5000
    max_depth: int = 10
    include_extensions: list[str] = field(default_factory=lambda: [
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".kt", ".go",
        ".rs", ".rb", ".php", ".swift", ".c", ".cpp", ".h", ".hpp",
        ".cs", ".scala", ".ex", ".exs", ".vue", ".svelte",
    ])
    exclude_dirs: list[str] = field(default_factory=lambda: [
        "node_modules", ".git", "__pycache__", ".venv", "venv",
        "dist", "build", ".tox", ".egg-info", "site-packages",
        "vendor", ".bundle", "target", "bin", "obj",
    ])
    github_api_url: str = "https://api.github.com"
    github_token: str = ""

    def to_dict(self) -> dict:
        return {
            "temp_dir": self.temp_dir,
            "max_file_size": self.max_file_size,
            "max_files": self.max_files,
            "include_extensions": self.include_extensions,
            "exclude_dirs": self.exclude_dirs,
        }
