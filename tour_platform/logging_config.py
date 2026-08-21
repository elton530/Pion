"""
Centralized logging configuration and sensitive-data scrubbing.

Development and production share one LOGGING builder so the two environments
cannot drift apart. The only difference is where logs go:

- development: stdout + ``logs/django.log`` (plain file, rotated externally)
- production:  stdout only, so systemd/journald collects and rotates them

Every handler runs through ``SensitiveDataFilter`` as defense in depth so that
passwords, tokens and secrets are never written to the logs, even if
application code accidentally logs them.
"""

import logging
import re

# Attribute / dict-key names that may carry sensitive values.
SENSITIVE_KEY_PATTERN = re.compile(
    r"(?i)(password|passwd|passphrase|secret|token|authorization|auth|"
    r"api[_-]?key|access[_-]?key|private[_-]?key|sessionid|csrftoken|"
    r"stripe[_-]?secret|client[_-]?secret|credit[_-]?card|cvv|cvc|ssn|jwt)"
)

# key=value / key: value pairs embedded in formatted log messages. The
# ``[a-z0-9_-]*`` suffix lets compound names (``secret_key=``, ``auth_token=``,
# ``password1=``) be matched even though only their root word is sensitive.
SENSITIVE_VALUE_PATTERN = re.compile(
    r"(?i)((?:password|passwd|passphrase|secret|token|api[_-]?key|"
    r"access[_-]?key|private[_-]?key|sessionid|csrftoken|authorization|"
    r"stripe[_-]?secret|client[_-]?secret|credit[_-]?card|cvv|cvc|ssn|jwt)"
    r"[a-z0-9_-]*[=:]\s*)([^\s,;&'\"]+)"
)

REDACTED = "[REDACTED]"


def _redact_value(value):
    if isinstance(value, str):
        return SENSITIVE_VALUE_PATTERN.sub(r"\1" + REDACTED, value)
    return value


class SensitiveDataFilter(logging.Filter):
    """Scrub passwords, tokens and secrets from log records.

    Redacts ``key=value``/``key: value`` pairs inside the message text and any
    record attribute whose name looks sensitive (e.g. an ``extra={...}`` dict
    that carries ``password``). Attribute values are replaced wholesale;
    positional ``%s`` arguments can only be scrubbed when the format string
    itself names the sensitive key.
    """

    def filter(self, record):
        for key in list(record.__dict__):
            if SENSITIVE_KEY_PATTERN.search(key):
                setattr(record, key, REDACTED)

        if isinstance(record.args, dict):
            redacted_args = {
                key: (
                    REDACTED
                    if SENSITIVE_KEY_PATTERN.search(str(key))
                    else value
                )
                for key, value in record.args.items()
            }
            try:
                message = str(record.msg) % redacted_args
            except Exception:
                message = str(record.msg)
        elif record.args:
            try:
                message = str(record.msg) % record.args
            except Exception:
                message = str(record.msg)
        else:
            message = str(record.msg)

        record.msg = _redact_value(message)
        record.args = ()
        return True


def build_logging_config(base_dir, use_file=True, app_level="DEBUG"):
    """Return a Django LOGGING dict.

    ``use_file=False`` targets systemd deployments: only the stdout handler is
    configured and journald becomes the single log sink.
    """
    handlers = {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "simple",
            "filters": ["sensitive"],
        }
    }
    handlers_list = ["console"]

    if use_file:
        handlers["file"] = {
            "level": "INFO",
            "class": "logging.handlers.WatchedFileHandler",
            "filename": str(base_dir / "logs" / "django.log"),
            "formatter": "verbose",
            "filters": ["sensitive"],
        }
        handlers_list = ["console", "file"]

    app_loggers = {
        "core": {"handlers": handlers_list, "level": app_level, "propagate": False},
        "users": {"handlers": handlers_list, "level": app_level, "propagate": False},
        "tours": {"handlers": handlers_list, "level": app_level, "propagate": False},
        "bookings": {"handlers": handlers_list, "level": app_level, "propagate": False},
        "payments": {"handlers": handlers_list, "level": app_level, "propagate": False},
    }

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "{levelname} {asctime} {name} {process:d} {thread:d} {message}",
                "style": "{",
            },
            "simple": {
                "format": "{levelname} {asctime} {name} {message}",
                "style": "{",
            },
        },
        "filters": {
            "sensitive": {
                "()": "tour_platform.logging_config.SensitiveDataFilter",
            },
        },
        "handlers": handlers,
        "root": {
            "handlers": handlers_list,
            "level": "INFO",
        },
        "loggers": {
            "django": {
                "handlers": handlers_list,
                "level": "INFO",
                "propagate": False,
            },
            "django.request": {
                "handlers": handlers_list,
                "level": "WARNING",
                "propagate": False,
            },
            "django.security": {
                "handlers": handlers_list,
                "level": "WARNING",
                "propagate": False,
            },
            **app_loggers,
        },
    }
