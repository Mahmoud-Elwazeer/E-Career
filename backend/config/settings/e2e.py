"""
E2E settings — used ONLY to run a real local Django dev server for the
Playwright browser E2E pass (acceptance-pass item 5). Forces a dedicated
SQLite database file so this never touches the shared dev Postgres
container (`usam-postgres` / `ecareer_dev`) other work in this repo may
depend on. Not used anywhere else; not referenced by any deploy config.
"""
from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_e2e.sqlite3",  # noqa: F405
    }
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@usam.dev"
CORS_ALLOW_ALL_ORIGINS = True
ACCOUNT_EMAIL_VERIFICATION = "none"

# Redis is available locally on the host-mapped port of the existing
# `usamhub-dev-redis` dev container (0.0.0.0:6380->6379/tcp) rather than
# the in-container default of 6379 — used for DRF throttle caching and the
# Channels layer during this E2E run only.
CACHES["default"]["LOCATION"] = "redis://localhost:6380/1"  # noqa: F405
CELERY_BROKER_URL = "redis://localhost:6380/0"  # noqa: F405
CELERY_RESULT_BACKEND = "redis://localhost:6380/0"  # noqa: F405
CHANNEL_LAYERS["default"]["CONFIG"]["hosts"] = ["redis://localhost:6380/0"]  # noqa: F405
# Celery tasks run synchronously in-process for this local E2E run — no
# worker process needs to be started just to exercise the legal/privacy UI.
CELERY_ALWAYS_EAGER = True
CELERY_TASK_ALWAYS_EAGER = True
