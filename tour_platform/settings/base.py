"""
Base Django settings shared by both development and production.

Environment values that only make sense in one environment (DEBUG, SECRET_KEY,
security headers, email backend, static storage, CORS origins) are defined in
``development.py`` and ``production.py``. Everything defined here is common to
both.

See https://docs.djangoproject.com/en/5.2/topics/settings/
"""

import os
from pathlib import Path

import environ

# ==================== PATH CONFIGURATION ====================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file (does not override values already
# present in the process environment).
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))


# ==================== APPLICATION DEFINITION ====================

INSTALLED_APPS = [
    # Django built-in apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party apps
    "rest_framework",  # DRF (opsionale - për API)
    "corsheaders",     # CORS handling
    "django_filters",  # Advanced filtering
    "django_extensions",  # Django extensions

    # Local apps
    "core.apps.CoreConfig",
    "users.apps.UsersConfig",
    "tours.apps.ToursConfig",
    "bookings.apps.BookingsConfig",
    "payments.apps.PaymentsConfig",
]

MIDDLEWARE = [
    # Security middleware
    "django.middleware.security.SecurityMiddleware",

    # CORS middleware (duhet të jetë para sesionit)
    "corsheaders.middleware.CorsMiddleware",

    # Session and authentication
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",

    # Security
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tour_platform.urls"

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
                "django.template.context_processors.media",
                "core.context_processors.site_stats",
            ],
        },
    },
]

WSGI_APPLICATION = "tour_platform.wsgi.application"


# ==================== DATABASE CONFIGURATION ====================

# Credentials come from environment variables (DB_*); used both locally and in
# production. See .env.example for the full list. USER and PASSWORD are
# required (no hardcoded fallbacks) so misconfiguration fails fast instead of
# silently connecting with a default credential.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="tour_platform"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env.int("DB_PORT", default="5432"),
        "ATOMIC_REQUESTS": True,
    }
}

# Connection pooling (opsionale - për production)
# DATABASES['default']['CONN_MAX_AGE'] = 600


# ==================== PASSWORD VALIDATION ====================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        }
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ==================== INTERNATIONALIZATION ====================

LANGUAGE_CODE = "sq"  # Albanian
LANGUAGES = [
    ("sq", "Shqip"),
    ("en", "English"),
    ("it", "Italiano"),
    ("de", "Deutsch"),
    ("fr", "Français"),
]

TIME_ZONE = "Europe/Tirane"  # Albania timezone
USE_I18N = True
USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / "locale",
]


# ==================== STATIC FILES ====================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# ==================== MEDIA FILES ====================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Image upload settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644


# ==================== AUTHENTICATION ====================

AUTH_USER_MODEL = "auth.User"  # Default user model
# Use namespaced URL names that exist in the project
LOGIN_URL = "users:login"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "core:home"

# Password reset timeout (në ditë)
PASSWORD_RESET_TIMEOUT = 3


# ==================== REST FRAMEWORK (API) ====================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}


# ==================== CORS CONFIGURATION ====================

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = env(
    "CSRF_TRUSTED_ORIGINS",
    default="http://127.0.0.1:8000,http://localhost:8000",
).split(",")


# ==================== LOGGING ====================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "tours": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "users": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "bookings": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)


# ==================== CACHING ====================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "tour-platform-cache",
        "TIMEOUT": 300,  # 5 minuta
    }
}

# Production - Redis cache
# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": "redis://127.0.0.1:6379/1",
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         }
#     }
# }


# ==================== SESSION CONFIGURATION ====================

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 1209600  # 2 javë
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_HTTPONLY = True


# ==================== SECURITY HEADERS ====================

X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"


# ==================== CUSTOM SETTINGS ====================

# Tours app settings
TOURS_DEFAULT_CURRENCY = "ALL"
TOURS_MAX_IMAGES = 10
TOURS_IMAGE_MAX_SIZE = 5242880  # 5MB

# Booking settings
BOOKING_CANCELLATION_DEADLINE = 48  # orë
BOOKING_AUTO_CONFIRM_HOURS = 24  # orë

# Authentication security settings
LOGIN_RATE_LIMIT_MAX_ATTEMPTS = env.int("LOGIN_RATE_LIMIT_MAX_ATTEMPTS", default=5)
LOGIN_RATE_LIMIT_WINDOW_SECONDS = env.int("LOGIN_RATE_LIMIT_WINDOW_SECONDS", default=600)

# Payment settings
PAYMENT_TIMEOUT = 3600  # 1 orë në sekonda
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLIC_KEY = env("STRIPE_PUBLIC_KEY", default="")

# Pagination
DEFAULT_PAGE_SIZE = 10

# File upload
ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "gif", "webp"]
ALLOWED_DOCUMENT_EXTENSIONS = ["pdf", "doc", "docx"]


# ==================== DEFAULT AUTO FIELD ====================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
