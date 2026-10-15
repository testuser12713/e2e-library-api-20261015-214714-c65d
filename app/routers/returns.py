"""Loan return endpoint: closing an open loan."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db, require_api_key
from ..models import Loan
from ..schemas import LoanRead
from ..services.returns import return_loan as return_loan_service

router = APIRouter(tags=["loans"])


@router.post("/loans/{loan_id}/return", response_model=LoanRead)
def return_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    _api_key: None = Depends(require_api_key),
) -> Loan:
    """Return one copy by closing the loan identified by ``loan_id``."""
    return return_loan_service(db, loan_id)
