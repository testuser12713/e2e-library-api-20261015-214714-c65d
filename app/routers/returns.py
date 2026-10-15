"""HTTP route for returning a loan."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db, require_api_key
from app.errors import LibraryError
from app.schemas import LoanRead

router = APIRouter(tags=["loans"])


@router.post("/loans/{loan_id}/return", response_model=LoanRead)
def return_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> LoanRead:
    raise LibraryError(501, "not_implemented", "Returning loans is not implemented yet.")
