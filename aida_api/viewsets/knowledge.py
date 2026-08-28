"""
AIDA Enterprise API — Knowledge ViewSet

Bilim bazasini boshqarish uchun API endpointlari.
- Bilim elementlarini qo'shish, qidirish, o'chirish
"""
from __future__ import annotations
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..responses import APIResponse

MOCK_KNOWLEDGE = [
    {
        "id": "knl_001",
        "user_id": "usr_demo",
        "title": "Django REST Framework asoslari",
        "content": "DRF — Django uchun REST API yaratish frameworki. Serializer, ViewSet, Router asosiy tarkibiy qismlari.",
        "source": "documentation",
        "tags": ["django", "rest", "api"],
        "confidence": 0.95,
        "created_at": "2026-01-20T12:00:00Z",
        "updated_at": "2026-01-20T12:00:00Z",
    },
    {
        "id": "knl_002",
        "user_id": "usr_demo",
        "title": "PostgreSQL indekslash strategiyalari",
        "content": "B-tree, Hash, GIN, GiST indeks turlari. To'g'ri indeks tanlash so'rov tezligini sezilarli oshiradi.",
        "source": "research",
        "tags": ["postgresql", "database", "performance"],
        "confidence": 0.88,
        "created_at": "2026-02-15T09:30:00Z",
        "updated_at": "2026-02-18T14:20:00Z",
    },
    {
        "id": "knl_003",
        "user_id": "usr_demo",
        "title": "O'zbek tilida tabiiy tillar qayta ishlash",
        "content": "O'zbek tili uchun NLP vositalari: morphologik tahlil, tokenizatsiya, sentiment tahlili.",
        "source": "internal",
        "tags": ["nlp", "uzbek", "language"],
        "confidence": 0.75,
        "created_at": "2026-03-05T16:45:00Z",
        "updated_at": "2026-03-05T16:45:00Z",
    },
]


class KnowledgeViewSet(viewsets.ViewSet):
    """
    Bilim bazasini boshqarish.

    - GET    /knowledge/          — Bilim elementlari ro'yxati
    - POST   /knowledge/add/      — Yangi bilim qo'shish
    - POST   /knowledge/search/   — Bilim qidirish
    - POST   /knowledge/remove/   — Bilimni o'chirish
    - GET    /knowledge/{id}/     — Bitta bilim elementi
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Bilim elementlari ro'yxati."""
        tag = request.query_params.get("tag")
        source = request.query_params.get("source")

        items = list(MOCK_KNOWLEDGE)
        if tag:
            items = [k for k in items if tag in k["tags"]]
        if source:
            items = [k for k in items if k["source"] == source]

        return Response(
            APIResponse.paginated(
                data=items,
                total=len(items),
                page=1,
                page_size=20,
                message="Bilim elementlari ro'yxati",
            )
        )

    @action(detail=False, methods=["post"], url_path="add")
    def add_knowledge(self, request):
        """Yangi bilim qo'shish."""
        title = request.data.get("title")
        content = request.data.get("content")

        if not title or not content:
            return Response(
                APIResponse.bad_request(
                    message="title va content majburiy maydonlar",
                    recovery="request body ga 'title' va 'content' maydonlarini qo'shing",
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_knowledge = {
            "id": f"knl_{len(MOCK_KNOWLEDGE) + 1:03d}",
            "user_id": str(request.user.id) if hasattr(request.user, "id") else "usr_demo",
            "title": title,
            "content": content,
            "source": request.data.get("source", "manual"),
            "tags": request.data.get("tags", []),
            "confidence": request.data.get("confidence", 0.8),
            "created_at": "2026-07-04T00:00:00Z",
            "updated_at": "2026-07-04T00:00:00Z",
        }
        MOCK_KNOWLEDGE.append(new_knowledge)

        return Response(
            APIResponse.created(data=new_knowledge, message="Bilim qo'shildi"),
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="search")
    def search(self, request):
        """Bilim qidirish."""
        query = request.data.get("query", "")
        if not query:
            return Response(
                APIResponse.bad_request(message="query maydoni kerak"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        results = [
            k for k in MOCK_KNOWLEDGE
            if query.lower() in k["title"].lower()
            or query.lower() in k["content"].lower()
            or query.lower() in " ".join(k["tags"]).lower()
        ]

        results = [
            {**k, "relevance_score": round(0.9 - i * 0.1, 2)}
            for i, k in enumerate(results)
        ]

        return Response(
            APIResponse.success(
                data=results,
                metadata={"query": query, "result_count": len(results)},
            )
        )

    @action(detail=False, methods=["post"], url_path="remove")
    def remove_knowledge(self, request):
        """Bilimni o'chirish (id orqali)."""
        global MOCK_KNOWLEDGE
        item_id = request.data.get("id")
        if not item_id:
            return Response(
                APIResponse.bad_request(message="id maydoni kerak"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        knowledge = next((k for k in MOCK_KNOWLEDGE if k["id"] == item_id), None)
        if knowledge is None:
            return Response(
                APIResponse.not_found(message=f"Bilim topilmadi: {item_id}"),
                status=status.HTTP_404_NOT_FOUND,
            )

        MOCK_KNOWLEDGE = [k for k in MOCK_KNOWLEDGE if k["id"] != item_id]
        return Response(APIResponse.success(message="Bilim o'chirildi"))

    def retrieve(self, request, pk=None):
        """Bitta bilim elementini olish."""
        knowledge = next((k for k in MOCK_KNOWLEDGE if k["id"] == pk), None)
        if knowledge is None:
            return Response(
                APIResponse.not_found(message=f"Bilim topilmadi: {pk}"),
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(APIResponse.success(data=knowledge))
