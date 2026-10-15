"""Loan creation endpoint. Body is a stub until the loan ticket lands."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..deps import get_db, require_api_key
from ..errors import LibraryError
from ..schemas import LoanCreate, LoanRead

router = APIRouter(tags=["loans"])

_NOT_IMPLEMENTED = "loan creation is implemented by a later ticket"


@router.post("/loans", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def create_loan(
    data: LoanCreate,
    db: Session = Depends(get_db),
    _api_key: None = Depends(require_api_key),
) -> LoanRead:
    raise LibraryError(status_code=501, code="not_implemented", message=_NOT_IMPLEMENTED)
