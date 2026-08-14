"""
Production settings.

Selected when ``ENVIRONMENT=production`` (or ``DJANGO_ENV=production``) is set.
Never activated by default: local development stays on ``development.py``.

Enabled behaviors:
  - DEBUG=False
  - SECRET_KEY is required (startup fails when missing)
  - full HTTPS / secure-cookie / HSTS / CSP security settings
  - SMTP email backend
  - hashed (manifest) static storage for caching
"""

from tour_platform.security import resolve_secret_key
from tour_platform.settings.base import *  # noqa: F401,F403

# ==================== ENVIRONMENT SELECTION ====================

DEBUG = False
ENVIRONMENT = "production"


# ==================== SECURITY SETTINGS ====================

# In production SECRET_KEY must be explicitly provided via environment
# variable; startup raises ImproperlyConfigured when it is missing.
SECRET_KEY = resolve_secret_key(
    secret_key=env("SECRET_KEY", default=""),
    debug=DEBUG,
    environment=ENVIRONMENT,
)

ALLOWED_HOSTS = env("ALLOWED_HOSTS", default="yourdomain.com,www.yourdomain.com").split(",")

# When behind a proxy (nginx, haproxy, ngrok), respect X-Forwarded-Proto.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CSRF_TRUSTED_ORIGINS = env(
    "CSRF_TRUSTED_ORIGINS",
    default="https://yourdomain.com,https://www.yourdomain.com",
).split(",")

# Hardened production security settings (all overridable via environment).
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE", default=True)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = env("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_HSTS_PRELOAD = env("SECURE_HSTS_PRELOAD", default=True)
SECURE_CONTENT_SECURITY_POLICY = {
    "default-src": ("'self'",),
    "script-src": ("'self'", "'unsafe-inline'"),
    "style-src": ("'self'", "'unsafe-inline'"),
}


# ==================== EMAIL CONFIGURATION ====================

# Production default is SMTP; provide real credentials via environment.
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@localhost")


# ==================== STATIC FILES ====================

# Hashed filenames so browsers never serve stale static assets.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
}


# ==================== CORS CONFIGURATION ====================

CORS_ALLOWED_ORIGINS = env(
    "CORS_ALLOWED_ORIGINS",
    default="https://yourdomain.com,https://www.yourdomain.com",
).split(",")
