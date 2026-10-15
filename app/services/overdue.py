"""Overdue service — stub completed by the overdue list ticket."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.errors import LibraryError
from app.models import Loan


def list_overdue(
    db: Session,
    *,
    limit: int,
    offset: int,
) -> tuple[list[Loan], int]:
    raise LibraryError(501, "not_implemented", "list_overdue is not implemented yet.")
