"""Project use case — manage development projects."""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Any

from ...domain.entities import Project
from ...domain.exceptions import ValidationError
from ...domain.interfaces import ProjectRepository

logger = logging.getLogger("aidaos.application.project")


class ProjectUseCase:
    def __init__(self, project_repo: ProjectRepository):
        self._projects = project_repo

    async def open_project(self, path: str) -> dict:
        if not path or not Path(path).exists():
            raise ValidationError(f"Path '{path}' does not exist")
        project = await self._projects.open(path)
        return project.to_dict()

    async def close_project(self, project_id: str) -> dict:
        ok = await self._projects.close(project_id)
        return {"success": ok}

    async def get_project(self, project_id: str) -> dict:
        project = await self._projects.get(project_id)
        if not project:
            return {"error": "Project not found"}
        return project.to_dict()

    async def list_projects(self) -> list[dict]:
        projects = await self._projects.list()
        return [p.to_dict() for p in projects]

    async def get_files(self, project_id: str) -> list[dict]:
        return await self._projects.get_files(project_id)

    async def read_file(self, project_id: str, file_path: str) -> dict:
        content = await self._projects.read_file(project_id, file_path)
        return {"content": content, "path": file_path}

    async def write_file(self, project_id: str, file_path: str, content: str) -> dict:
        ok = await self._projects.write_file(project_id, file_path, content)
        return {"success": ok, "path": file_path}
