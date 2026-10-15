"""Loan creation endpoint."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..deps import get_db, require_api_key
from ..schemas import LoanCreate, LoanRead
from ..services.loans import create_loan as create_loan_service

router = APIRouter(tags=["loans"])


@router.post("/loans", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def create_loan(
    data: LoanCreate,
    db: Session = Depends(get_db),
    _api_key: None = Depends(require_api_key),
) -> LoanRead:
    """Create a loan of one book copy to a member."""
    return create_loan_service(db, data.book_id, data.member_id)
