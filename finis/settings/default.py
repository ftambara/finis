from pathlib import Path
from typing import Any

import structlog
from environs import Env

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = Env()
env.read_env()

logger = structlog.get_logger(__name__)

DEBUG = env.bool("DEBUG", default=False)

DEFAULT_SECRET_KEY = "django-insecure-k_@40wpb#=*-hdd_mi9k9y(5=$u4d&#v3x%he4nwedyb!=34kf"
SECRET_KEY = env.str("SECRET_KEY", default=DEFAULT_SECRET_KEY)

LOCAL_HTTPS = env.bool("LOCAL_HTTPS", default=True)

ALLOWED_HOSTS: list[str] = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "rest_framework",
    "accounts",
    "catalog",
    "scanning",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "accounts.middleware.tenant_middleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

posthog_enabled = env.bool("POSTHOG_ENABLED", default=True)

if posthog_enabled:
    MIDDLEWARE.append("posthog.integrations.django.PosthogContextMiddleware")

ROOT_URLCONF = "finis.urls"

TEMPLATES: list[dict[str, Any]] = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "finis.jinja2.environment",
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "finis.wsgi.application"

DEFAULT_DB_URL = "postgres://finis_customer:secret@localhost:5432/finis"
ADMIN_DB_URL = "postgres://finis:secret@localhost:5432/finis"
DATABASES = {
    "default": env.dj_db_url("DATABASE_URL", default=DEFAULT_DB_URL),
    "admin": env.dj_db_url("ADMIN_DATABASE_URL", default=ADMIN_DB_URL),
}

# In CLI mode, the 'default' connection uses the 'admin' role to bypass RLS.
if env.bool("FINIS_CLI_MODE", default=False):
    DATABASES["default"] = DATABASES["admin"]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env.str("REDIS_URL", default="redis://localhost:6379/1"),
    }
}

SESSION_ENGINE = "accounts.session_backend"
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=LOCAL_HTTPS)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if LOCAL_HTTPS else None
USE_X_FORWARDED_HOST = LOCAL_HTTPS
USE_X_FORWARDED_PORT = LOCAL_HTTPS

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "accounts.backends.AdminDBModelBackend",
]

SCANNING_LLM_PROVIDER = env.str("SCANNING_LLM_PROVIDER", default="")

GROK_API_KEY = env.str("GROK_API_KEY", default=None)
GROK_API_URL = env.str("GROK_API_URL", default="https://api.x.ai/v1/chat/completions")
GROK_MODEL = env.str("GROK_MODEL", default="grok-4.20-0309-non-reasoning")
GROK_MAX_TOKENS = env.int("GROK_MAX_TOKENS", default=8192)
GROK_API_TIMEOUT = env.int("GROK_API_TIMEOUT", default=180)

GEMINI_API_KEY = env.str("GEMINI_API_KEY", default=None)
GEMINI_API_URL = env.str(
    "GEMINI_API_URL", default="https://generativelanguage.googleapis.com/v1beta/models"
)
GEMINI_MODEL = env.str("GEMINI_MODEL", default="gemini-3-flash-preview")
GEMINI_MAX_TOKENS = env.int("GEMINI_MAX_TOKENS", default=8192)
GEMINI_API_TIMEOUT = env.int("GEMINI_API_TIMEOUT", default=180)

match SCANNING_LLM_PROVIDER:
    case "grok":
        SCANNING_MODEL = GROK_MODEL
    case "gemini":
        SCANNING_MODEL = GEMINI_MODEL
    case _:
        SCANNING_MODEL = ""

# PostHog configuration
POSTHOG_API_KEY = env.str("POSTHOG_API_KEY", default="")
POSTHOG_HOST = env.str("POSTHOG_HOST", default="")

# Celery configuration
CELERY_BROKER_URL = env.str("REDIS_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env.str("REDIS_URL", default="redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# Upload limits
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20 MB

# Structlog configuration
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}
