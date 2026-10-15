"""Overdue service. Body is filled in by the overdue list ticket."""

from sqlalchemy.orm import Session

from ..models import Loan


def list_overdue(
    db: Session,
    *,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Loan], int]:
    """Return one page of open loans whose due date has passed."""
    ...
