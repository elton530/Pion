from django.core.exceptions import ImproperlyConfigured


DEVELOPMENT_SECRET_KEY_FALLBACK = "django-insecure-development-only-secret-key"


def resolve_secret_key(secret_key, debug, environment):
    """Resolve SECRET_KEY with strict production rules.

    In production-like runtime, SECRET_KEY must be explicitly provided via
    environment variable. In local development, a fallback is allowed for
    convenience.
    """
    normalized_environment = (environment or "").strip().lower()
    is_production_like = (not debug) or (normalized_environment == "production")

    if secret_key:
        return secret_key

    if is_production_like:
        raise ImproperlyConfigured(
            "SECRET_KEY environment variable is required when running in production."
        )

    return DEVELOPMENT_SECRET_KEY_FALLBACK
