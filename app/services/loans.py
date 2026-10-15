"""Loan service. Body is filled in by the loan creation ticket."""

from sqlalchemy.orm import Session

from ..models import Loan


def create_loan(db: Session, book_id: int, member_id: int) -> Loan:
    """Open a new loan for a book and a member."""
    ...
