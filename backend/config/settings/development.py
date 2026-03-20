"""
Development settings — DEBUG=True, SQLite OK, console email.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# ── Database (SQLite for local dev — swap to postgres via ENV) ───────────────
import os
from decouple import config

DATABASE_URL = config("DATABASE_URL", default="")

if DATABASE_URL:
    import dj_database_url
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
        }
    }

# ── Email (console backend in dev) ───────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@usam.dev"

# ── CORS ─────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True

# ── Django Debug Toolbar (optional — not installed by default) ───────────────
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

# ── Account email verification (off in dev so you can log in immediately) ────
ACCOUNT_EMAIL_VERIFICATION = "none"

# ── Logging override for dev ─────────────────────────────────────────────────
LOGGING["loggers"]["apps"]["level"] = "DEBUG"  # noqa: F405
