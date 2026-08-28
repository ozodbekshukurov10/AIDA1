"""
AIDA Enterprise API — Memory ViewSet

Xotira (memory) boshqarish uchun API endpointlari.
- Xotiralarni ro'yxatlash, qidirish, saqlash, o'chirish
- Semantik qidiruv
- Xotira statistikasi va texnik xizmat
"""
from __future__ import annotations
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..responses import APIResponse

MOCK_MEMORIES = [
    {
        "id": "mem_001",
        "user_id": "usr_demo",
        "content": "Foydalanuvchi Python va Django frameworkni yaxshi biladi.",
        "category": "preference",
        "tags": ["python", "django", "programming"],
        "importance": 0.8,
        "created_at": "2026-01-15T10:30:00Z",
        "updated_at": "2026-01-15T10:30:00Z",
    },
    {
        "id": "mem_002",
        "user_id": "usr_demo",
        "content": "Toshkent shahrida yashaydi. O'zbek va ingliz tillarida gaplashadi.",
        "category": "personal",
        "tags": ["location", "language"],
        "importance": 0.6,
        "created_at": "2026-02-01T08:15:00Z",
        "updated_at": "2026-02-01T08:15:00Z",
    },
    {
        "id": "mem_003",
        "user_id": "usr_demo",
        "content": "API loyihasi uchun RESTful arxitektura tanlandi. PostgreSQL bazasi ishlatilmoqda.",
        "category": "project",
        "tags": ["api", "postgresql", "architecture"],
        "importance": 0.9,
        "created_at": "2026-03-10T14:45:00Z",
        "updated_at": "2026-03-12T09:00:00Z",
    },
]


class MemoryViewSet(viewsets.ViewSet):
    """
    Xotira boshqarish.

    - GET    /memory/               — Xotiralar ro'yxati
    - POST   /memory/store/         — Xotirani saqlash
    - POST   /memory/search/        — Oddiy qidiruv
    - POST   /memory/semantic-search/ — Semantik qidiruv
    - GET    /memory/{id}/          — Bitta xotira
    - DELETE /memory/{id}/          — Xotirani o'chirish
    - GET    /memory/stats/         — Xotira statistikasi
    - POST   /memory/maintenance/   — Texnik xizmat
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Xotiralar ro'yxati."""
        category = request.query_params.get("category")
        tag = request.query_params.get("tag")

        items = list(MOCK_MEMORIES)
        if category:
            items = [m for m in items if m["category"] == category]
        if tag:
            items = [m for m in items if tag in m["tags"]]

        return Response(
            APIResponse.paginated(
                data=items,
                total=len(items),
                page=1,
                page_size=20,
                message="Xotiralar ro'yxati",
            )
        )

    @action(detail=False, methods=["post"], url_path="store")
    def store(self, request):
        """Xotirani saqlash."""
        content = request.data.get("content")
        if not content:
            return Response(
                APIResponse.bad_request(
                    message="content majburiy maydon",
                    recovery="request body ga 'content' maydonini qo'shing",
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_memory = {
            "id": f"mem_{len(MOCK_MEMORIES) + 1:03d}",
            "user_id": str(request.user.id) if hasattr(request.user, "id") else "usr_demo",
            "content": content,
            "category": request.data.get("category", "general"),
            "tags": request.data.get("tags", []),
            "importance": request.data.get("importance", 0.5),
            "created_at": "2026-07-04T00:00:00Z",
            "updated_at": "2026-07-04T00:00:00Z",
        }
        MOCK_MEMORIES.append(new_memory)

        return Response(
            APIResponse.created(data=new_memory, message="Xotira saqlandi"),
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="search")
    def search(self, request):
        """Oddiy matnga asoslangan qidiruv."""
        query = request.data.get("query", "")
        if not query:
            return Response(
                APIResponse.bad_request(message="query maydoni kerak"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        results = [
            m for m in MOCK_MEMORIES
            if query.lower() in m["content"].lower()
            or query.lower() in " ".join(m["tags"]).lower()
        ]

        return Response(
            APIResponse.success(
                data=results,
                metadata={"query": query, "result_count": len(results)},
            )
        )

    @action(detail=False, methods=["post"], url_path="semantic-search")
    def semantic_search(self, request):
        """Semantik qidiruv (mock natijalar)."""
        query = request.data.get("query", "")
        if not query:
            return Response(
                APIResponse.bad_request(message="query maydoni kerak"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        results = [
            {
                **m,
                "score": round(0.95 - i * 0.1, 2),
            }
            for i, m in enumerate(MOCK_MEMORIES[:3])
        ]

        return Response(
            APIResponse.success(
                data=results,
                metadata={
                    "query": query,
                    "result_count": len(results),
                    "method": "semantic",
                },
            )
        )

    def retrieve(self, request, pk=None):
        """Bitta xotirani olish."""
        memory = next((m for m in MOCK_MEMORIES if m["id"] == pk), None)
        if memory is None:
            return Response(
                APIResponse.not_found(message=f"Xotira topilmadi: {pk}"),
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(APIResponse.success(data=memory))

    def destroy(self, request, pk=None):
        """Xotirani o'chirish."""
        global MOCK_MEMORIES
        memory = next((m for m in MOCK_MEMORIES if m["id"] == pk), None)
        if memory is None:
            return Response(
                APIResponse.not_found(message=f"Xotira topilmadi: {pk}"),
                status=status.HTTP_404_NOT_FOUND,
            )
        MOCK_MEMORIES = [m for m in MOCK_MEMORIES if m["id"] != pk]
        return Response(APIResponse.success(message="Xotira o'chirildi"))

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        """Xotira statistikasi."""
        total = len(MOCK_MEMORIES)
        categories = {}
        for m in MOCK_MEMORIES:
            cat = m["category"]
            categories[cat] = categories.get(cat, 0) + 1

        all_tags = set()
        for m in MOCK_MEMORIES:
            all_tags.update(m["tags"])

        avg_importance = (
            round(sum(m["importance"] for m in MOCK_MEMORIES) / total, 2)
            if total > 0
            else 0
        )

        return Response(
            APIResponse.success(
                data={
                    "total_memories": total,
                    "categories": categories,
                    "unique_tags": sorted(all_tags),
                    "average_importance": avg_importance,
                },
                message="Xotira statistikasi",
            )
        )

    @action(detail=False, methods=["post"], url_path="maintenance")
    def maintenance(self, request):
        """Texnik xizmat — eski xotiralarni tozalash (mock)."""
        removed_count = 0
        global MOCK_MEMORIES
        before = len(MOCK_MEMORIES)
        MOCK_MEMORIES = [m for m in MOCK_MEMORIES if m["importance"] >= 0.3]
        removed_count = before - len(MOCK_MEMORIES)

        return Response(
            APIResponse.success(
                data={
                    "removed_count": removed_count,
                    "remaining_count": len(MOCK_MEMORIES),
                },
                message="Texnik xizmat bajarildi",
            )
        )
