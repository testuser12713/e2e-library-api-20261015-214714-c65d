"""Request dependencies: database session, API key and pagination."""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from fastapi import Header, Query

from app.config import get_api_key
from app.db import get_db
from app.errors import LibraryError

__all__ = ["Pagination", "get_db", "pagination", "require_api_key"]


def require_api_key(x_api_key: str | None = Header(None, alias="X-API-Key")) -> None:
    """Reject a request whose X-API-Key header is missing or wrong."""
    expected = get_api_key()
    provided = x_api_key or ""
    if not secrets.compare_digest(provided, expected):
        raise LibraryError(401, "unauthorized", "A valid X-API-Key header is required.")


@dataclass(frozen=True)
class Pagination:
    limit: int
    offset: int


def pagination(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> Pagination:
    """Parse and bound the pagination query parameters."""
    return Pagination(limit=limit, offset=offset)
