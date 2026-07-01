from __future__ import annotations
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from .config import AnalyzerConfig

logger = logging.getLogger("webapp.repo_analyzer.github")


@dataclass
class RepoInfo:
    full_name: str = ""
    name: str = ""
    owner: str = ""
    description: str = ""
    url: str = ""
    default_branch: str = "main"
    language: str = ""
    stars: int = 0
    forks: int = 0
    topics: list[str] = field(default_factory=list)
    license_name: str = ""
    created_at: str = ""
    updated_at: str = ""
    size_kb: int = 0
    file_count: int = 0

    def to_dict(self) -> dict:
        return {
            "full_name": self.full_name,
            "name": self.name,
            "owner": self.owner,
            "description": self.description,
            "url": self.url,
            "default_branch": self.default_branch,
            "language": self.language,
            "stars": self.stars,
            "forks": self.forks,
            "topics": self.topics,
            "license": self.license_name,
        }


class GitHubClient:
    def __init__(self, config: AnalyzerConfig | None = None):
        self.config = config or AnalyzerConfig()
        self._client = httpx.AsyncClient(timeout=30)

    async def get_repo_info(self, repo_full_name: str) -> RepoInfo | None:
        url = f"{self.config.github_api_url}/repos/{repo_full_name}"
        headers = self._headers()
        try:
            resp = await self._client.get(url, headers=headers)
            if resp.status_code != 200:
                logger.warning(f"GitHub API error: {resp.status_code} for {repo_full_name}")
                return None
            data = resp.json()
            return RepoInfo(
                full_name=data.get("full_name", repo_full_name),
                name=data.get("name", ""),
                owner=data.get("owner", {}).get("login", ""),
                description=data.get("description", "") or "",
                url=data.get("html_url", ""),
                default_branch=data.get("default_branch", "main"),
                language=data.get("language") or "",
                stars=data.get("stargazers_count", 0),
                forks=data.get("forks_count", 0),
                topics=data.get("topics", []),
                license_name=(data.get("license") or {}).get("spdx_id", "") or "",
                created_at=data.get("created_at", ""),
                updated_at=data.get("updated_at", ""),
                size_kb=data.get("size", 0),
            )
        except Exception as e:
            logger.error(f"Failed to fetch repo info: {e}")
            return None

    async def list_contents(self, repo_full_name: str, path: str = "") -> list[dict]:
        url = f"{self.config.github_api_url}/repos/{repo_full_name}/contents/{path}"
        headers = self._headers()
        try:
            resp = await self._client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception:
            return []

    async def get_file_content(self, repo_full_name: str, path: str) -> str | None:
        url = f"{self.config.github_api_url}/repos/{repo_full_name}/contents/{path}"
        headers = self._headers()
        try:
            resp = await self._client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("encoding") == "base64":
                    import base64
                    return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
                return data.get("content", "")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch file: {e}")
            return None

    async def get_repo_tree(self, repo_full_name: str, branch: str = "main") -> list[dict]:
        url = f"{self.config.github_api_url}/repos/{repo_full_name}/git/trees/{branch}?recursive=1"
        headers = self._headers()
        try:
            resp = await self._client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("tree", [])
            return []
        except Exception as e:
            logger.error(f"Failed to fetch tree: {e}")
            return []

    async def search_code(self, query: str, per_page: int = 10) -> list[dict]:
        url = f"{self.config.github_api_url}/search/code"
        headers = self._headers()
        params = {"q": query, "per_page": per_page}
        try:
            resp = await self._client.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                return resp.json().get("items", [])
            return []
        except Exception:
            return []

    def _headers(self) -> dict:
        h = {"Accept": "application/vnd.github.v3+json"}
        if self.config.github_token:
            h["Authorization"] = f"Bearer {self.config.github_token}"
        return h

    async def close(self):
        await self._client.aclose()
