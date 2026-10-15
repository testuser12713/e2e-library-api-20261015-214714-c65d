"""Loan service: opening a loan under the library's borrowing rules."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..errors import LibraryError
from ..models import Book, Loan, Member

LOAN_PERIOD = timedelta(days=14)
MAX_OPEN_LOANS = 3


def create_loan(db: Session, book_id: int, member_id: int) -> Loan:
    """Open a new loan of a book copy for a member.

    Every borrowing rule is checked before the first write, so a rejected attempt
    leaves the session and the stored rows untouched:

    1. the book and the member must exist (404 otherwise);
    2. the member may hold at most ``MAX_OPEN_LOANS`` open loans (409 otherwise);
    3. the book must have at least one free copy (409 otherwise).

    On success the loan is persisted with ``loaned_at`` set to the current UTC
    time, ``due_at`` exactly ``LOAN_PERIOD`` later and ``returned_at`` empty.

    Raises:
        LibraryError: 404 when the book or the member is unknown, 409 when the
            member already holds three open loans or no copy of the book is free.
    """
    book = db.get(Book, book_id)
    if book is None:
        raise LibraryError(
            status_code=404,
            code="not_found",
            message=f"Book {book_id} was not found.",
        )

    member = db.get(Member, member_id)
    if member is None:
        raise LibraryError(
            status_code=404,
            code="not_found",
            message=f"Member {member_id} was not found.",
        )

    open_loans = db.scalar(
        select(func.count())
        .select_from(Loan)
        .where(Loan.member_id == member_id, Loan.returned_at.is_(None))
    )
    if open_loans is not None and open_loans >= MAX_OPEN_LOANS:
        raise LibraryError(
            status_code=409,
            code="conflict",
            message=f"Member {member_id} already has {MAX_OPEN_LOANS} open loans.",
        )

    if book.copies_available <= 0:
        raise LibraryError(
            status_code=409,
            code="conflict",
            message=f"No free copy of '{book.title}' is available.",
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
