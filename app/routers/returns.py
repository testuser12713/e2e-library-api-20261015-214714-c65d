"""HTTP route for returning a loan."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db, require_api_key
from app.models import Loan
from app.schemas import LoanRead
from app.services.returns import return_loan as return_loan_service

router = APIRouter(tags=["loans"])


@router.post("/loans/{loan_id}/return", response_model=LoanRead)
def return_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> Loan:
    return return_loan_service(db, loan_id)
