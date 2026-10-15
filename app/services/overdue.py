"""Overdue service: open loans whose lending period has already expired."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..models import Loan

__all__ = ["list_overdue"]


def _utc_now_naive() -> datetime:
    """Return the current moment in UTC as a naive datetime.

    Loan timestamps are stored in UTC without tzinfo. The cutoff is therefore
    taken in the same representation so the comparison never falls back to the
    machine's local wall-clock time.
    """
    return datetime.now(UTC).replace(tzinfo=None)


def list_overdue(
    db: Session,
    *,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Loan], int]:
    """Return one page of open loans whose due date has passed.

    Only loans that are still open (``returned_at`` is null) and whose
    ``due_at`` is strictly before the current UTC moment are selected. The rows
    are ordered oldest-first by ``due_at`` and eager-load the book and the
    member, so the response can read them after the request session is closed.
    The total is the number of matching rows independent of ``limit`` and
    ``offset``.
    """
    cutoff = _utc_now_naive()
    conditions = (Loan.returned_at.is_(None), Loan.due_at < cutoff)

    total = db.scalar(select(func.count()).select_from(Loan).where(*conditions))

    statement = (
        select(Loan)
        .where(*conditions)
        .options(joinedload(Loan.book), joinedload(Loan.member))
        .order_by(Loan.due_at.asc(), Loan.id.asc())
        .limit(limit)
        .offset(offset)
    )
    rows = list(db.scalars(statement).all())

    return rows, total or 0
