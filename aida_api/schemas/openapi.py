"""
AIDA Enterprise API — OpenAPI Schema

API hujjatlari uchun OpenAPI 3.0 schema.
"""
from __future__ import annotations
from drf_spectacular.generators import SchemaGenerator


class AIDASchemaGenerator(SchemaGenerator):
    """AIDA uchun maxsus schema generator."""

    title = "AIDA Enterprise API"
    description = """
AIDA (Artificial Intelligence Digital Assistant) Enterprise API — Sun'iy intellekt yordamchisi platformasi.

## Asosiy xususiyatlar
- **JWT Autentifikatsiya**: Token orqali kirish
- **API Kalitlari**: Service-to-service integratsiya
- **Streaming**: Real-time AI javoblari
- **WebSocket**: Real-time bildirishnomalar

## Versiyalar
- **v1**: Asosiy API (hozir)
- **v2**: Yangilangan API (kelajak)
    """
    version = "1.0.0"
    contact = {"name": "AIDA Team", "email": "support@aida.ai"}
    license = {"name": "MIT"}

    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema["info"]["contact"] = self.contact
        schema["info"]["license"] = self.license
        return schema
