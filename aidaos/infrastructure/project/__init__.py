"""Project repository adapter — wraps the existing project management."""

from __future__ import annotations
import logging
import os
from pathlib import Path
from typing import Any

from ...domain.entities import Project
from ...domain.interfaces import ProjectRepository

logger = logging.getLogger("aidaos.infrastructure.project")


class ProjectRepoAdapter(ProjectRepository):
    def __init__(self):
        self._projects: dict[str, Project] = {}

    async def open(self, path: str) -> Project:
        p = Path(path).resolve()
        proj = Project(
            id=str(abs(hash(str(p))) % (2**31)),
            name=p.name,
            path=str(p),
        )
        try:
            ext_counts = {}
            for f in p.rglob("*"):
                if f.is_file() and f.suffix:
                    ext = f.suffix.lower()
                    ext_counts[ext] = ext_counts.get(ext, 0) + 1
                    proj.file_count += 1
            if ext_counts:
                proj.language = max(ext_counts, key=ext_counts.get).lstrip(".")
        except Exception:
            pass
        self._projects[proj.id] = proj
        return proj

    async def close(self, project_id: str) -> bool:
        return self._projects.pop(project_id, None) is not None

    async def get(self, project_id: str) -> Project | None:
        return self._projects.get(project_id)

    async def list(self) -> list[Project]:
        return list(self._projects.values())

    async def get_files(self, project_id: str) -> list[dict]:
        proj = self._projects.get(project_id)
        if not proj:
            return []
        files = []
        base = Path(proj.path)
        try:
            for f in sorted(base.rglob("*")):
                if f.is_file() and "node_modules" not in str(f) and ".git" not in str(f):
                    try:
                        rel = str(f.relative_to(base))
                        files.append({"path": rel, "size": f.stat().st_size, "ext": f.suffix})
                    except ValueError:
                        continue
        except Exception:
            pass
        return files

    async def read_file(self, project_id: str, file_path: str) -> str:
        proj = self._projects.get(project_id)
        if not proj:
            return ""
        try:
            return (Path(proj.path) / file_path).read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""

    async def write_file(self, project_id: str, file_path: str, content: str) -> bool:
        proj = self._projects.get(project_id)
        if not proj:
            return False
        try:
            target = Path(proj.path) / file_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"Write file failed: {e}")
            return False
