import sys; sys.path.insert(0, ".")
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    INSTALLED_APPS=["webapp"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    CSRF_TRUSTED_ORIGINS=[],
)
django.setup()

from webapp.urls import urlpatterns
names = [p.name for p in urlpatterns]
for name in names:
    print(name)
