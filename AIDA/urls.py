from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    # Enterprise API v1 — Yangi REST API
    path('api/', include('aida_api.urls')),

    # Self-Improvement Engine API
    path('api/si/', include('self_improvement.urls')),

    # Legacy API v2 — Eski endpointlar
    path('', include('webapp.urls')),
]
