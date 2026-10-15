"""Loan service — stub completed by the loan creation ticket."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.errors import LibraryError
from app.models import Loan


def create_loan(db: Session, book_id: int, member_id: int) -> Loan:
    raise LibraryError(501, "not_implemented", "create_loan is not implemented yet.")
