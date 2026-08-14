"""
Development settings.

These are the DEFAULT settings: ``tour_platform.settings`` dispatches here
unless ``ENVIRONMENT=production`` (or ``DJANGO_ENV=production``) is set.

Enabled behaviors:
  - DEBUG=True
  - console email backend (emails printed to stdout)
  - plain static storage (no collectstatic needed)
  - no HTTPS enforcement / no secure cookies
  - dev-only fallback SECRET_KEY when none is provided
"""

from tour_platform.security import resolve_secret_key
from tour_platform.settings.base import *  # noqa: F401,F403

# ==================== ENVIRONMENT SELECTION ====================

DEBUG = True
ENVIRONMENT = "development"


# ==================== SECURITY SETTINGS ====================

# SECRET_KEY: an explicit value from the environment always wins; otherwise a
# dev-only fallback is used (never do this in production).
SECRET_KEY = resolve_secret_key(
    secret_key=env("SECRET_KEY", default=""),
    debug=DEBUG,
    environment=ENVIRONMENT,
)

ALLOWED_HOSTS = env("ALLOWED_HOSTS", default="127.0.0.1,localhost").split(",")

# Development defaults: explicitly disable strict HTTPS-only behaviors. This
# ensures local testing (DEBUG=True) won't redirect or require TLS and avoids
# ERR_SSL_* errors while working without certificates. DO NOT keep these
# enabled in production.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Avoid enforcing a content security policy in dev (helps with local assets).
SECURE_CONTENT_SECURITY_POLICY = {}

# Development helper: with DEBUG=True we run locally without HTTPS. To avoid
# development-time errors (ERR_SSL_PROTOCOL_ERROR when someone visits
# https://127.0.0.1 while the dev server speaks HTTP), remove the
# SecurityMiddleware so Django won't enforce HTTPS-only behaviors.
# Safe for local development only; DO NOT do this in production.
try:
    MIDDLEWARE.remove("django.middleware.security.SecurityMiddleware")
    SECURITY_MIDDLEWARE_DISABLED = True
except ValueError:
    SECURITY_MIDDLEWARE_DISABLED = False


# ==================== EMAIL CONFIGURATION ====================

# Development default: emails are printed to stdout.
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@localhost")


# ==================== STATIC FILES ====================

# Plain backend so the dev server serves static files without running
# collectstatic first.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


# ==================== CORS CONFIGURATION ====================

CORS_ALLOWED_ORIGINS = env(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000",
).split(",")
