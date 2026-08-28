"""
AIDA Enterprise API — Standard Pagination
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from ..responses import APIResponse


class StandardPagination(PageNumberPagination):
    """
    Standart sahifalash.
    
    Query parameters:
    - page: Sahifa raqami (default: 1)
    - page_size: Sahifa hajmi (default: 20, max: 100)
    """
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        return Response(
            APIResponse.paginated(
                data=data,
                total=self.page.paginator.count,
                page=self.page.number,
                page_size=self.get_page_size(self.request) or self.page_size,
                metadata={
                    "api_version": "v1",
                },
            )
        )

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "data": schema,
                "pagination": {
                    "type": "object",
                    "properties": {
                        "total": {"type": "integer"},
                        "page": {"type": "integer"},
                        "page_size": {"type": "integer"},
                        "total_pages": {"type": "integer"},
                        "has_next": {"type": "boolean"},
                        "has_previous": {"type": "boolean"},
                    },
                },
                "request_id": {"type": "string"},
                "execution_time_ms": {"type": "integer"},
            },
        }
