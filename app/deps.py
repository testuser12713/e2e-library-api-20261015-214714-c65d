"""Shared FastAPI dependencies: database session, API key and pagination."""

import hmac
from dataclasses import dataclass

from fastapi import Header, Query

from .config import get_settings
from .db import get_db
from .errors import LibraryError

__all__ = ["Pagination", "get_db", "pagination", "require_api_key"]


@dataclass(frozen=True)
class Pagination:
    """A validated ``limit`` / ``offset`` pair."""

    limit: int
    offset: int


def pagination(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> Pagination:
    """Validate and bundle the pagination query parameters."""
    return Pagination(limit=limit, offset=offset)


def require_api_key(x_api_key: str | None = Header(None, alias="X-API-Key")) -> None:
    """Reject a write request unless it carries the configured API key."""
    settings = get_settings()
    if x_api_key is None or not hmac.compare_digest(x_api_key, settings.api_key):
        raise LibraryError(
            status_code=401,
            code="unauthorized",
            message="Missing or invalid API key.",
        )
