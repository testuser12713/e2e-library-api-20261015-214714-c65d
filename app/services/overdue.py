"""Overdue service: list loans that are open and past their due date."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Loan


def list_overdue(
    db: Session,
    *,
    limit: int,
    offset: int,
) -> tuple[list[Loan], int]:
    """Return the page of open loans due before now, with book and member.

    A loan is overdue when ``returned_at`` is null and ``due_at`` lies before the
    current UTC moment. Timestamps are stored as naive UTC values, so the
    comparison uses a naive-UTC bound as well.
    """
    now = datetime.now(UTC).replace(tzinfo=None)
    conditions = (Loan.returned_at.is_(None), Loan.due_at < now)

    total = db.scalar(select(func.count()).select_from(Loan).where(*conditions)) or 0
    statement = (
        select(Loan)
        .where(*conditions)
        .order_by(Loan.due_at.asc(), Loan.id.asc())
        .offset(offset)
        .limit(limit)
        .options(selectinload(Loan.book), selectinload(Loan.member))
    )
    loans = list(db.scalars(statement).all())
    return loans, total
