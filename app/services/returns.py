"""Return service — completes a loan exactly once."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.errors import LibraryError
from app.models import Loan


def return_loan(db: Session, loan_id: int) -> Loan:
    """Set the loan's returned_at to now (UTC) and persist it.

    ``copies_available`` is a derived value (copies_total minus the book's open
    loans), so marking the loan returned raises it by exactly one within the
    same transaction/commit.
    """
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise LibraryError(404, "not_found", f"Loan {loan_id} was not found.")
    if loan.returned_at is not None:
        raise LibraryError(409, "conflict", f"Loan {loan_id} has already been returned.")

    loan.returned_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(loan)
    return loan
