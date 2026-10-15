"""Configuration read lazily from the environment.

Values are never captured at import time: the startup hook touches every setting
once so a missing required variable refuses to start and names itself, while a
module import never crashes on a bare traceback.
"""

from __future__ import annotations

import os


class ConfigError(RuntimeError):
    """Raised when a required environment variable is missing."""


def get_api_key() -> str:
    """Return the configured API key, or fail naming the variable."""
    value = os.environ.get("LIBRARY_API_KEY")
    if not value:
        raise ConfigError(
            "LIBRARY_API_KEY is not set. The application refuses to start without it. "
            "Set LIBRARY_API_KEY in the environment (see .env.example and RUN.json)."
        )
    return value


def get_db_path() -> str:
    """Return the SQLite file path, defaulting to 'library.db'."""
    return os.environ.get("LIBRARY_DB_PATH", "library.db")
