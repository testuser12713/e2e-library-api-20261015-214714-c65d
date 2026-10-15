"""Return service — stub completed by the loan return ticket."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.errors import LibraryError
from app.models import Loan


def return_loan(db: Session, loan_id: int) -> Loan:
    raise LibraryError(501, "not_implemented", "return_loan is not implemented yet.")
