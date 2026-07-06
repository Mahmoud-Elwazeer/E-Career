"""
Production settings — DEBUG=False, PostgreSQL, SMTP email, full security.
"""
from .base import *  # noqa: F401, F403
from decouple import config
import dj_database_url

DEBUG = False

# ── Database ─────────────────────────────────────────────────────────────────
DATABASES = {
    "default": dj_database_url.parse(
        config("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=False,
    )
}

# ── Email ─────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@usam.jobs")

# ── Security ─────────────────────────────────────────────────────────────────
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"

# ── Logging (add file handler in prod) ───────────────────────────────────────
import os
LOG_DIR = BASE_DIR / "logs"  # noqa: F405
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING["root"]["handlers"] = ["console", "file"]  # noqa: F405
LOGGING["loggers"]["django"]["handlers"] = ["console", "file"]  # noqa: F405
LOGGING["loggers"]["apps"]["handlers"] = ["console", "file"]  # noqa: F405

# ── Override SSL redirect — nginx handles SSL termination ─────────────────────
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
