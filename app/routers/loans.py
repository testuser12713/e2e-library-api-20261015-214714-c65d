"""HTTP route for creating a loan."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db, require_api_key
from app.errors import LibraryError
from app.schemas import LoanCreate, LoanRead

router = APIRouter(tags=["loans"])


@router.post("/loans", response_model=LoanRead, status_code=201)
def create_loan(
    data: LoanCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> LoanRead:
    raise LibraryError(501, "not_implemented", "Creating loans is not implemented yet.")
