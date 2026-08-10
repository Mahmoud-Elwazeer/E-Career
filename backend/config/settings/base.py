"""
Base settings shared across all environments.
"""
import os
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Security ────────────────────────────────────────────────────────────────
SECRET_KEY = config("SECRET_KEY", default="change-me-in-production-please")
DEBUG = False
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# ── Application Definition ──────────────────────────────────────────────────
INSTALLED_APPS = [
    # Daphne - must be BEFORE django.contrib.staticfiles
    "daphne",
    # Unfold admin - must be BEFORE django.contrib.admin
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.import_export",
    # Django built-ins
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
     "drf_spectacular",
     "import_export",
     "allauth",
     "allauth.account",
     "allauth.socialaccount",
     "allauth.socialaccount.providers.google",
    # Project apps
    "apps.core",
    # Monitoring & Observability
    "apps.monitoring",
    "apps.accounts",
    "apps.jobs",
    "apps.users",
    "apps.analytics",
    # New apps for Phase 1A
    "apps.rashid",
    "apps.emails",
    "apps.employers",
    # Phase 1B - Scraper
    "apps.scraper",
    # Phase 2A - Profiles
    "apps.profiles",
    # Phase 1 - Search
    "apps.search",
    # Phase 1 - Verification
    "apps.verification",
    # Phase 1 - Skills Taxonomy
    "apps.skills",
    # Phase 1 - Event System
    "apps.events",
    # Phase 1 - AI Intelligence
    "apps.intelligence",
    # Phase 1 - Vector Search
    "apps.vectors",
    # Phase 2 - Career Intelligence
    "apps.career",
    # Phase 3 - Salary Intelligence
    "apps.salary",
    # Phase 3 - Assessment Platform
    "apps.assessment",
    # Phase 4 - Interviews App
    "apps.interviews",
    # Phase 4 - Notifications
    "apps.notifications",
    # Phase 4 - Resume Builder
    "apps.resume",
    # Celery Beat
    "django_celery_beat",
    # WebSocket support (Phase 2B)
    "channels",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ── Auth ─────────────────────────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

SITE_ID = 1

# ── DRF ─────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "apps.core.renderers.CustomJSONRenderer",
    ],
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/minute",      # Anonymous: 30 requests per minute
        "user": "100/minute",     # Authenticated: 100 requests per minute
        "burst": "10/second",     # Burst protection: 10 per second
    },
}

# ── JWT ──────────────────────────────────────────────────────────────────────
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

# ── django-allauth ────────────────────────────────────────────────────────────
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_UNIQUE_EMAIL = True

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": config("GOOGLE_CLIENT_ID", default=""),
            "secret": config("GOOGLE_CLIENT_SECRET", default=""),
            "key": "",
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}

# ── Spectacular (API Docs) ───────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "USAM Career Compass API",
    "DESCRIPTION": "REST API for the USAM Career Compass job platform. Serves job listings, user profiles, saved jobs, alerts, and admin functionality.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "TAGS": [
        {"name": "Auth", "description": "Authentication endpoints"},
        {"name": "Users", "description": "User profile management"},
        {"name": "Jobs", "description": "Job listings"},
        {"name": "Companies", "description": "Company profiles"},
        {"name": "Sources", "description": "Job sources"},
        {"name": "Tags", "description": "Job tags"},
        {"name": "Saved Jobs", "description": "User saved jobs"},
        {"name": "Alerts", "description": "Job alert subscriptions"},
        {"name": "Notifications", "description": "In-app notifications"},
        {"name": "Analytics", "description": "Admin analytics"},
        {"name": "Feature Flags", "description": "Feature toggle management"},
        {"name": "System", "description": "Health check and utilities"},
    ],
}

# ── CORS ─────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173,http://localhost:3000",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

# ── Frontend ─────────────────────────────────────────────────────────────────
FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:5173")

# ── Internationalization ─────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ── Email defaults (override per environment) ────────────────────────────────
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@usam.jobs")
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ── Static & Media Files ─────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = config("MEDIA_ROOT", default=str(BASE_DIR / "media"))
MAX_UPLOAD_SIZE = config("MAX_UPLOAD_SIZE_MB", default=10, cast=int) * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Admin URL ────────────────────────────────────────────────────────────────
ADMIN_URL = config("ADMIN_URL", default="admin/")

# ── Unfold Admin Theme ───────────────────────────────────────────────────────
UNFOLD = {
    "SITE_TITLE": "USAM Admin",
    "SITE_HEADER": "USAM Career Compass",
    "SITE_URL": "/",
    "SITE_ICON": None,
    "STYLES": [],
    "SCRIPTS": [],
    "COLORS": {
        "primary": {
            "50": "240 253 250",
            "100": "204 251 241",
            "200": "153 246 228",
            "300": "94 234 212",
            "400": "45 212 191",
            "500": "10 56 54",
            "600": "9 50 48",
            "700": "8 44 42",
            "800": "7 38 36",
            "900": "6 32 30",
            "950": "5 26 24",
        },
    },
    "TABS": [],
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "ENVIRONMENT": "config.admin_dashboard.environment_callback",
    "DASHBOARD_CALLBACK": "config.admin_dashboard.dashboard_callback",
}

# ── Encryption ──────────────────────────────────────────────────────────────
FIELD_ENCRYPTION_KEY = config('FIELD_ENCRYPTION_KEY', default='')

if not FIELD_ENCRYPTION_KEY:
    import warnings
    warnings.warn(
        "FIELD_ENCRYPTION_KEY not set! Encrypted fields will not work. "
        "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    )

# ── Celery Configuration ──────────────────────────────────────────────────────
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ── AWS Bedrock Configuration ─────────────────────────────────────────────────
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
AWS_DEFAULT_REGION = config('AWS_DEFAULT_REGION', default='us-east-1')
BEDROCK_MODEL_ID = config('BEDROCK_MODEL_ID', default='anthropic.claude-sonnet-4-20250514-v1:0')

# ── AWS Billing Alerts Configuration ───────────────────────────────────────────
# CloudWatch billing alarm thresholds (in USD)
AWS_BILLING_ALERT_THRESHOLD = config('AWS_BILLING_ALERT_THRESHOLD', default=100, cast=float)
AWS_BILLING_ALERT_EMAIL = config('AWS_BILLING_ALERT_EMAIL', default='')
AWS_BILLING_MONITOR_ENABLED = config('AWS_BILLING_MONITOR_ENABLED', default=False, cast=bool)

# ── Django Channels Configuration ─────────────────────────────────────────────
ASGI_APPLICATION = 'config.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [config('REDIS_HOST', default='redis://localhost:6379/0')],
        },
    },
}

# ── Typesense Configuration ──────────────────────────────────────────────────
TYPESENSE_HOST = config('TYPESENSE_HOST', default='localhost')
TYPESENSE_PORT = config('TYPESENSE_PORT', default='8108')
TYPESENSE_PROTOCOL = config('TYPESENSE_PROTOCOL', default='http')
TYPESENSE_API_KEY = config('TYPESENSE_API_KEY', default='ecareer_typesense_dev_key')
SEARCH_TRUST_SCORE_THRESHOLD = config('SEARCH_TRUST_SCORE_THRESHOLD', default=0.4, cast=float)

# ── Qdrant Configuration ─────────────────────────────────────────────────────
QDRANT_HOST = config('QDRANT_HOST', default='localhost')
QDRANT_PORT = config('QDRANT_PORT', default='6333', cast=int)
QDRANT_API_KEY = config('QDRANT_API_KEY', default='ecareer_qdrant_dev_key')

# ── Rashid AI Configuration ───────────────────────────────────────────────────
RASHID_CONFIG = {
    'dialect': 'egyptian_arabic',
    'personality': 'supportive_mentor',
    'max_conversation_history': 50,
    'course_platform_url': 'https://edu.usamif.com',
    'privacy_mode': True,  # Admin cannot read conversation content
}

# ── Structlog Configuration ──────────────────────────────────────────────────
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# ── GZIP Compression (70-90% smaller payloads) ───────────────────────────────
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',  # Add first for compression
] + MIDDLEWARE

# ── Caching Configuration (API Response Caching) ───────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_CACHE_URL', default='redis://localhost:6379/1'),
        'TIMEOUT': 300,  # 5 minutes default
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# ── Logging ──────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
        "json": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
            "foreign_pre_chain": [
                structlog.contextvars.merge_contextvars,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
            ],
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "json_console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(BASE_DIR / "logs" / "django.log"),
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 3,
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# ── Sentry Error Tracking ─────────────────────────────────────────────────────
SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
