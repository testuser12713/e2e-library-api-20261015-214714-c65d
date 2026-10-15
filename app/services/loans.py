"""Loan service — creating a loan under the borrowing rules."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import LibraryError
from app.models import Book, Loan, Member

LOAN_PERIOD = timedelta(days=14)
MAX_OPEN_LOANS = 3


def create_loan(db: Session, book_id: int, member_id: int) -> Loan:
    """Create a loan of one book copy to a member, enforcing the borrowing rules.

    Raises :class:`LibraryError` with 404 for an unknown book/member and 409 when
    no copy is free or the member already holds the maximum number of open loans.
    Nothing is written on a rejection.
    """
    book = db.get(Book, book_id)
    if book is None:
        raise LibraryError(404, "not_found", f"Book {book_id} was not found.")

    member = db.get(Member, member_id)
    if member is None:
        raise LibraryError(404, "not_found", f"Member {member_id} was not found.")

    if book.copies_available <= 0:
        raise LibraryError(
            409,
            "conflict",
            f"No free copy of '{book.title}' is available.",
        )

    open_loans = db.scalar(
        select(func.count())
        .select_from(Loan)
        .where(Loan.member_id == member_id, Loan.returned_at.is_(None))
    )
    if open_loans is not None and open_loans >= MAX_OPEN_LOANS:
        raise LibraryError(
            409,
            "conflict",
            f"Member {member_id} already has {MAX_OPEN_LOANS} open loans.",
        )

    loaned_at = datetime.now(UTC)
    loan = Loan(
        book_id=book_id,
        member_id=member_id,
        loaned_at=loaned_at,
        due_at=loaned_at + LOAN_PERIOD,
        returned_at=None,
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan
