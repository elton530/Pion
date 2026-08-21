"""
Django settings package.

Selects the active settings module based on the ``ENVIRONMENT`` variable
(optionally overridden by ``DJANGO_ENV``). Local development is the default:
production settings are only used when explicitly requested.

Selection order:
1. ``DJANGO_ENV`` from the process environment, else
2. ``ENVIRONMENT`` from the process environment or the ``.env`` file
   (``development`` / ``production``), else
3. defaults to ``development``.

Values other than ``production`` are treated as development, so a fresh
checkout with no configuration at all runs in development mode.
"""

import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file (does not override values already
# present in the process environment).
env = environ.Env(ENVIRONMENT=(str, "development"))
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

ENVIRONMENT = (
    os.environ.get("DJANGO_ENV")
    or env("ENVIRONMENT", default="development")
).strip().lower()

if ENVIRONMENT == "production":
    from tour_platform.settings.production import *  # noqa: F401,F403
else:
    from tour_platform.settings.development import *  # noqa: F401,F403
