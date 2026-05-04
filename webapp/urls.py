from django.urls import path, re_path

from .views import (
    api_chat,
    api_keys_create,
    api_keys_list,
    api_platform_chat,
    api_session_create,
    api_session_history,
    api_sessions_list,
    api_status,
    dist_asset,
    spa_index,
)


urlpatterns = [
    re_path(r"^assets/(?P<asset_path>.+)$", dist_asset, name="dist-asset"),
    path("api/keys/", api_keys_list, name="api-keys-list"),
    path("api/keys/create/", api_keys_create, name="api-keys-create"),
    path("api/status/", api_status, name="api-status"),
    path("api/chat/", api_chat, name="api-chat"),
    path("api/sessions/", api_sessions_list, name="api-sessions-list"),
    path("api/sessions/create/", api_session_create, name="api-session-create"),
    path("api/sessions/<str:session_id>/history/", api_session_history, name="api-session-history"),
    path("api/platform/chat/", api_platform_chat, name="api-platform-chat"),
    re_path(r"^(?:.*)?$", spa_index, name="spa-index"),
]
