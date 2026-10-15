"""Application configuration read from the environment.

Both values are read lazily so that importing this module never crashes a process
that is only being inspected. The API key has no default: :func:`get_settings` is
called once during application startup and raises :class:`ConfigError` naming the
missing variable if it is absent.
"""

import os
from dataclasses import dataclass

DEFAULT_DB_PATH = "library.db"
API_KEY_ENV_VAR = "LIBRARY_API_KEY"
DB_PATH_ENV_VAR = "LIBRARY_DB_PATH"


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    """The validated settings the application runs with."""

    api_key: str
    db_path: str


def get_db_path() -> str:
    """Return the SQLite file path, falling back to the non-secret default."""
    return os.environ.get(DB_PATH_ENV_VAR, DEFAULT_DB_PATH)


def get_settings() -> Settings:
    """Read and validate the configuration.

    Raises:
        ConfigError: when ``LIBRARY_API_KEY`` is not set. The message names the
            variable so the operator knows exactly what to provide.
    """
    api_key = os.environ.get(API_KEY_ENV_VAR)
    if not api_key:
        raise ConfigError(
            f"Required environment variable {API_KEY_ENV_VAR} is not set. "
            "Set it before starting the API (see RUN.json and .env.example)."
        )
    return Settings(api_key=api_key, db_path=get_db_path())
