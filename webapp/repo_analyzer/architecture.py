from __future__ import annotations
import json
import logging
import re
from collections import defaultdict, Counter
from pathlib import Path
from typing import Any

logger = logging.getLogger("webapp.repo_analyzer.architecture")


class ArchitectureDetector:
    def __init__(self):
        self.architecture_type: str = "unknown"
        self.layers: list[dict] = []
        self.patterns_detected: list[str] = []
        self.smells: list[str] = []
        self.framework: str = ""

    def analyze(self, files: list[dict], repo_manager=None, repo_path: str = ""):
        if not files:
            return
        file_paths = [f["path"] for f in files]
        self._detect_framework(files, file_paths)
        self._detect_architecture_type(files, file_paths, repo_path, repo_manager)
        self._detect_patterns(files, file_paths)
        self._detect_smells(files, file_paths)

    def _detect_framework(self, files: list[dict], file_paths: list[str]):
        patterns = {
            "Django": ["manage.py", "django"],
            "Flask": ["flask"],
            "FastAPI": ["fastapi"],
            "React": ["react", "jsx", "tsx"],
            "Vue": [".vue"],
            "Angular": ["angular"],
            "Express": ["express"],
            "Next.js": ["next"],
            "Laravel": ["laravel", "artisan"],
            "Rails": ["rails", "Gemfile"],
            "Spring": ["spring", "pom.xml", "build.gradle"],
            "ASP.NET": [".csproj", "Microsoft.AspNetCore"],
            "Svelte": [".svelte"],
        }
        all_content = " ".join(file_paths).lower()
        for fw, indicators in patterns.items():
            if any(ind in all_content for ind in indicators):
                self.patterns_detected.append(f"framework:{fw}")
                if not self.framework:
                    self.framework = fw

    def _detect_architecture_type(self, files: list[dict], file_paths: list[str],
                                   repo_path: str = "", repo_manager=None):
        dir_structure = defaultdict(int)
        for p in file_paths:
            parts = p.replace("\\", "/").split("/")
            if len(parts) >= 2:
                dir_structure[parts[0]] += 1
            if len(parts) >= 3:
                dir_structure[f"{parts[0]}/{parts[1]}"] += 1

        top_dirs = [d for d in dir_structure if "/" not in d]
        layer_indicators = {
            "controllers": "api/controllers/handlers/routes/views/web",
            "models": "models/entities/domain/db",
            "services": "services/usecases/logic/business",
            "repositories": "repositories/dao/data/dal",
            "templates": "templates/views/pages/components",
            "middleware": "middleware/auth/session",
            "config": "config/settings/conf/env",
            "migrations": "migrations/alembic",
            "tests": "tests/spec/__test__",
        }
        layer_keywords = {
            layer: set(kws.split("/"))
            for layer, kws in layer_indicators.items()
        }

        for layer, kws in layer_keywords.items():
            layer_files = [p for p in file_paths if any(kw in p.lower().split("/") for kw in kws)]
            if layer_files:
                self.layers.append({
                    "name": layer,
                    "file_count": len(layer_files),
                    "sample_files": layer_files[:5],
                })

        if len(top_dirs) >= 5 and len(files) >= 50:
            self.architecture_type = "modular"
        elif len(top_dirs) <= 2 and len(files) >= 30:
            self.architecture_type = "monolithic"
        elif any("service" in d.lower() or "micro" in d.lower() for d in top_dirs):
            self.architecture_type = "microservices"
        elif any(d in ("api", "app", "src", "lib") for d in top_dirs):
            self.architecture_type = "layered"

        if self.layers:
            self.architecture_type = "layered"

    def _detect_patterns(self, files: list[dict], file_paths: list[str]):
        patterns_found = set()

        mvc_dirs = ["models", "views", "controllers", "templates"]
        if any(d in p.split("/")[0] for p in file_paths for d in mvc_dirs):
            patterns_found.add("MVC")

        if any("factory" in p.lower() for p in file_paths):
            patterns_found.add("Factory")

        if any("singleton" in p.lower() for p in file_paths):
            patterns_found.add("Singleton")

        if any("observer" in p.lower() or "event" in p.lower() for p in file_paths):
            patterns_found.add("Observer/Observable")

        if any("middleware" in p.lower() for p in file_paths):
            patterns_found.add("Middleware/Pipeline")

        if any("plugin" in p.lower() or "extension" in p.lower() for p in file_paths):
            patterns_found.add("Plugin/Extension")

        if any("mixin" in p.lower() for p in file_paths):
            patterns_found.add("Mixin")

        if any("proxy" in p.lower() for p in file_paths):
            patterns_found.add("Proxy")

        if any("decorator" in p.lower() for p in file_paths):
            patterns_found.add("Decorator")

        if any("strategy" in p.lower() for p in file_paths):
            patterns_found.add("Strategy")

        self.patterns_detected.extend(f"pattern:{p}" for p in patterns_found)

    def _detect_smells(self, files: list[dict], file_paths: list[str]):
        smells = []

        if len(files) > 3 and len(self.layers) <= 1:
            smells.append("No clear layer separation - consider organizing into layers")

        dir_counts = Counter(p.split("/")[0] for p in file_paths if "/" in p)
        big_dirs = [d for d, c in dir_counts.items() if c > 20]
        for d in big_dirs[:3]:
            smells.append(f"Directory '{d}' has {dir_counts[d]} files - consider splitting")

        if self.framework:
            fw_files = [p for p in file_paths if self.framework.lower() in p.lower()]
            if len(fw_files) > len(files) * 0.5:
                smells.append(f"High framework coupling ({len(fw_files)}/{len(files)} files reference {self.framework})")

        self.smells = smells

    def to_dict(self) -> dict:
        return {
            "type": self.architecture_type,
            "framework": self.framework,
            "layers": self.layers,
            "patterns": self.patterns_detected,
            "smells": self.smells,
        }
