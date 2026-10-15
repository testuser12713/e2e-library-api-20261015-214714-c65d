"""HTTP route for creating a loan."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db, require_api_key
from app.schemas import LoanCreate, LoanRead
from app.services.loans import create_loan as create_loan_service

router = APIRouter(tags=["loans"])


@router.post("/loans", response_model=LoanRead, status_code=201)
def create_loan(
    data: LoanCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> LoanRead:
    """Create a loan of a book copy to a member."""
    return create_loan_service(db, data.book_id, data.member_id)
