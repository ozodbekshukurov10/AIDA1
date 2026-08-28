"""
AIDA Enterprise API — Repositories ViewSet

Git repozitoriyalarni boshqarish uchun CRUD va maxsus endpointlar.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..responses import APIResponse

MOCK_REPOS = {
    "repo_1": {
        "id": "repo_1",
        "name": "aida-core",
        "full_name": "aida-team/aida-core",
        "description": "AIDA yadro tizimi — asosiy backend xizmatlari",
        "visibility": "private",
        "language": "Python",
        "default_branch": "main",
        "stars": 124,
        "forks": 32,
        "open_issues": 7,
        "size_kb": 15360,
        "topics": ["ai", "nlp", "enterprise"],
        "created_at": "2025-06-10T08:00:00Z",
        "updated_at": "2026-07-01T12:00:00Z",
        "owner": "user_01",
    },
    "repo_2": {
        "id": "repo_2",
        "name": "aida-frontend",
        "full_name": "aida-team/aida-frontend",
        "description": "AIDA frontend ilovasi — React + TypeScript",
        "visibility": "public",
        "language": "TypeScript",
        "default_branch": "main",
        "stars": 89,
        "forks": 18,
        "open_issues": 3,
        "size_kb": 8192,
        "topics": ["react", "typescript", "dashboard"],
        "created_at": "2025-08-20T10:00:00Z",
        "updated_at": "2026-06-28T09:00:00Z",
        "owner": "user_02",
    },
    "repo_3": {
        "id": "repo_3",
        "name": "aida-plugins",
        "full_name": "aida-team/aida-plugins",
        "description": "AIDA plugin kutubxonasi — kengaytma modullari",
        "visibility": "public",
        "language": "Python",
        "default_branch": "main",
        "stars": 56,
        "forks": 12,
        "open_issues": 2,
        "size_kb": 4096,
        "topics": ["plugins", "extensions", "python"],
        "created_at": "2025-10-05T14:00:00Z",
        "updated_at": "2026-07-02T16:00:00Z",
        "owner": "user_01",
    },
}

MOCK_BRANCHES = {
    "repo_1": [
        {"name": "main", "is_default": True, "last_commit": "abc1234", "protected": True},
        {"name": "develop", "is_default": False, "last_commit": "def5678", "protected": True},
        {"name": "feature/auth-v2", "is_default": False, "last_commit": "ghi9012", "protected": False},
    ],
    "repo_2": [
        {"name": "main", "is_default": True, "last_commit": "xyz7890", "protected": True},
        {"name": "feature/dark-mode", "is_default": False, "last_commit": "uvw3456", "protected": False},
    ],
}

MOCK_COMMITS = {
    "repo_1": [
        {"sha": "abc1234", "message": "feat: auth v2 qo'shildi", "author": "dev_01", "date": "2026-07-01T12:00:00Z"},
        {"sha": "def5678", "message": "fix: token refresh xatosi tuzatildi", "author": "dev_02", "date": "2026-06-30T10:00:00Z"},
        {"sha": "ghi9012", "message": "docs: README yangilandi", "author": "dev_01", "date": "2026-06-28T14:00:00Z"},
    ],
}


class RepositoriesViewSet(viewsets.ViewSet):
    """
    Git repozitoriyalarni boshqarish.

    - GET    /repositories/                  — Repozitoriyalar ro'yxati
    - POST   /repositories/                  — Yangi repo yaratish
    - GET    /repositories/{id}/             — Bitta repo
    - PUT    /repositories/{id}/             — Reponi to'liq yangilash
    - PATCH  /repositories/{id}/             — Reponi qisman yangilash
    - DELETE /repositories/{id}/             — Reponi o'chirish
    - GET    /repositories/{id}/branches/    — Branchlar ro'yxati
    - GET    /repositories/{id}/commits/     — Commitlar tarixi
    - POST   /repositories/{id}/fork/        — Reponi forklash
    - POST   /repositories/{id}/archive/     — Reponi arxivlash
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Repozitoriyalar ro'yxati."""
        try:
            repos = list(MOCK_REPOS.values())

            language = request.query_params.get("language")
            if language:
                repos = [r for r in repos if r["language"].lower() == language.lower()]

            visibility = request.query_params.get("visibility")
            if visibility:
                repos = [r for r in repos if r["visibility"] == visibility]

            search = request.query_params.get("search")
            if search:
                repos = [r for r in repos if search.lower() in r["name"].lower()]

            return Response(APIResponse.success(data=repos))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    def create(self, request):
        """Yangi repozitoriya yaratish."""
        try:
            name = request.data.get("name")
            if not name:
                return Response(APIResponse.bad_request(message="Repo nomi kiritilishi shart."))

            repo_id = f"repo_{uuid.uuid4().hex[:8]}"
            now = datetime.utcnow().isoformat() + "Z"

            repo = {
                "id": repo_id,
                "name": name,
                "full_name": f"aida-team/{name}",
                "description": request.data.get("description", ""),
                "visibility": request.data.get("visibility", "private"),
                "language": request.data.get("language", ""),
                "default_branch": "main",
                "stars": 0,
                "forks": 0,
                "open_issues": 0,
                "size_kb": 0,
                "topics": request.data.get("topics", []),
                "created_at": now,
                "updated_at": now,
                "owner": str(request.user.id),
            }
            MOCK_REPOS[repo_id] = repo
            MOCK_BRANCHES[repo_id] = [
                {"name": "main", "is_default": True, "last_commit": "", "protected": True},
            ]

            return Response(
                APIResponse.created(data=repo, message="Repozitoriya yaratildi."),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    def retrieve(self, request, pk=None):
        """Bitta repozitoriyani olish."""
        try:
            repo = MOCK_REPOS.get(pk)
            if not repo:
                return Response(APIResponse.not_found(message=f"Repo topilmadi: {pk}"))
            return Response(APIResponse.success(data=repo))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    def update(self, request, pk=None):
        """Repozitoriyani to'liq yangilash."""
        try:
            repo = MOCK_REPOS.get(pk)
            if not repo:
                return Response(APIResponse.not_found(message=f"Repo topilmadi: {pk}"))

            repo.update({
                "name": request.data.get("name", repo["name"]),
                "description": request.data.get("description", repo["description"]),
                "visibility": request.data.get("visibility", repo["visibility"]),
                "language": request.data.get("language", repo["language"]),
                "topics": request.data.get("topics", repo["topics"]),
                "updated_at": datetime.utcnow().isoformat() + "Z",
            })
            repo["full_name"] = f"aida-team/{repo['name']}"

            return Response(APIResponse.success(data=repo, message="Repo yangilandi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    def partial_update(self, request, pk=None):
        """Repozitoriyani qisman yangilash."""
        try:
            repo = MOCK_REPOS.get(pk)
            if not repo:
                return Response(APIResponse.not_found(message=f"Repo topilmadi: {pk}"))

            for key in ["name", "description", "visibility", "language", "topics"]:
                if key in request.data:
                    repo[key] = request.data[key]
            if "name" in request.data:
                repo["full_name"] = f"aida-team/{repo['name']}"
            repo["updated_at"] = datetime.utcnow().isoformat() + "Z"

            return Response(APIResponse.success(data=repo, message="Repo yangilandi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    def destroy(self, request, pk=None):
        """Repozitoriyani o'chirish."""
        try:
            repo = MOCK_REPOS.pop(pk, None)
            if not repo:
                return Response(APIResponse.not_found(message=f"Repo topilmadi: {pk}"))
            MOCK_BRANCHES.pop(pk, None)
            MOCK_COMMITS.pop(pk, None)
            return Response(APIResponse.success(message="Repo o'chirildi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["get"])
    def branches(self, request, pk=None):
        """Repozitoriya branchlari ro'yxati."""
        try:
            repo = MOCK_REPOS.get(pk)
            if not repo:
                return Response(APIResponse.not_found(message=f"Repo topilmadi: {pk}"))

            branches = MOCK_BRANCHES.get(pk, [])
            return Response(APIResponse.success(data=branches))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["get"])
    def commits(self, request, pk=None):
        """Repozitoriya commitlari tarixi."""
        try:
            repo = MOCK_REPOS.get(pk)
            if not repo:
                return Response(APIResponse.not_found(message=f"Repo topilmadi: {pk}"))

            commits = MOCK_COMMITS.get(pk, [])
            branch = request.query_params.get("branch", "main")
            limit = int(request.query_params.get("limit", 10))

            return Response(
                APIResponse.success(
                    data=commits[:limit],
                    metadata={"branch": branch, "count": min(len(commits), limit)},
                )
            )
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["post"])
    def fork(self, request, pk=None):
        """Repozitoriyani forklash."""
        try:
            repo = MOCK_REPOS.get(pk)
            if not repo:
                return Response(APIResponse.not_found(message=f"Repo topilmadi: {pk}"))

            fork_id = f"repo_{uuid.uuid4().hex[:8]}"
            now = datetime.utcnow().isoformat() + "Z"
            fork_name = request.data.get("name", f"{repo['name']}-fork")

            forked_repo = {
                **repo,
                "id": fork_id,
                "name": fork_name,
                "full_name": f"aida-team/{fork_name}",
                "stars": 0,
                "forks": 0,
                "forked_from": pk,
                "created_at": now,
                "updated_at": now,
                "owner": str(request.user.id),
            }
            MOCK_REPOS[fork_id] = forked_repo

            return Response(
                APIResponse.created(data=forked_repo, message="Repo forklandi."),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """Repozitoriyani arxivlash."""
        try:
            repo = MOCK_REPOS.get(pk)
            if not repo:
                return Response(APIResponse.not_found(message=f"Repo topilmadi: {pk}"))

            repo["archived"] = True
            repo["archived_at"] = datetime.utcnow().isoformat() + "Z"
            repo["updated_at"] = repo["archived_at"]

            return Response(APIResponse.success(data=repo, message="Repo arxivlandi."))
        except Exception as e:
            return Response(APIResponse.server_error(message=str(e)))
