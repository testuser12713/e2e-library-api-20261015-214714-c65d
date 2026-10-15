"""Return service. Body is filled in by the loan return ticket."""

from sqlalchemy.orm import Session

from ..models import Loan


def return_loan(db: Session, loan_id: int) -> Loan:
    """Close an open loan by setting its return timestamp."""
    ...
