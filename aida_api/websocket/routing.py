"""
AIDA Enterprise API — WebSocket URL Routing
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r"ws/v1/chat/(?P<chat_id>[^/]+)/$",
        consumers.ChatConsumer.as_asgi(),
    ),
    re_path(
        r"ws/v1/agents/(?P<agent_id>[^/]+)/$",
        consumers.AgentConsumer.as_asgi(),
    ),
    re_path(
        r"ws/v1/notifications/$",
        consumers.NotificationConsumer.as_asgi(),
    ),
]
