import os
from pathlib import Path

from .env import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
DIST_DIR = BASE_DIR / "dist"
DIST_ASSETS_DIR = DIST_DIR / "assets"
TEMPLATES_DIR = BASE_DIR / "templates"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


import secrets
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "") or secrets.token_urlsafe(50)
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
] if os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS") else [
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]
if os.environ.get("DJANGO_SECURE_PROXY_SSL_HEADER", "false").lower() == "true":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'webapp',
    'aida_api',
    'self_improvement',
]

MIDDLEWARE = [
    'aida_api.middleware.request_id.RequestIDMiddleware',
    'aida_api.middleware.timing.TimingMiddleware',
    'aida_api.middleware.security_headers.SecurityHeadersMiddleware',
    'aida_api.middleware.localization.LocalizationMiddleware',
    'aida_api.middleware.rate_limit.RateLimitMiddleware',
    'aida_api.middleware.audit.AuditMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'aida_api.middleware.error_handler.ErrorHandlerMiddleware',
]

ROOT_URLCONF = 'AIDA.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIR, DIST_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'AIDA.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ── Custom User Model ─────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'aida_api.User'


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = True


STATIC_URL = '/assets/'
STATICFILES_DIRS = [DIST_ASSETS_DIR] if DIST_ASSETS_DIR.exists() else []
STATIC_ROOT = BASE_DIR / 'staticfiles'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{levelname} {asctime} {module} {message}', 'style': '{'},
        'simple': {'format': '{levelname} {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
        'file': {
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'aida.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'webapp': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False},
        'aida_api': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False},
        'aida_api.audit': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False},
        'aida_api.errors': {'handlers': ['console', 'file'], 'level': 'WARNING', 'propagate': False},
        'django': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ── Django REST Framework Settings ─────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'aida_api.auth.authentication.CombinedAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'aida_api.pagination.standard.StandardPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'aida_api.throttling.rates.AnonymousThrottle',
        'aida_api.throttling.rates.UserThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anonymous': '30/min',
        'user': '100/min',
        'premium': '500/min',
        'enterprise': '2000/min',
        'agent': '100/min',
    },
    'EXCEPTION_HANDLER': None,  # ErrorHandlerMiddleware ishlatiladi
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_VERSIONING_CLASS': None,
    'ALLOWED_VERSIONS': ['v1', 'v2'],
    'DEFAULT_VERSION': 'v1',
}


# ── JWT Settings ───────────────────────────────────────────────────────────────
import os as _os
AIDA_JWT_SECRET = _os.environ.get("AIDA_JWT_SECRET", SECRET_KEY)
AIDA_JWT_ACCESS_LIFETIME = 15 * 60  # 15 daqiqa
AIDA_JWT_REFRESH_LIFETIME = 7 * 24 * 60 * 60  # 7 kun


# ── Rate Limiting Settings ─────────────────────────────────────────────────────
RATE_LIMIT_ANONYMOUS = 30  # 1 daqiqada
RATE_LIMIT_AUTHENTICATED = 100
RATE_LIMIT_PREMIUM = 500
RATE_LIMIT_ENTERPRISE = 2000
RATE_LIMIT_WINDOW = 60  # soniya
