"""Loan return endpoint. Body is a stub until the return ticket lands."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db, require_api_key
from ..errors import LibraryError
from ..schemas import LoanRead

router = APIRouter(tags=["loans"])

_NOT_IMPLEMENTED = "loan return is implemented by a later ticket"


@router.post("/loans/{loan_id}/return", response_model=LoanRead)
def return_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    _api_key: None = Depends(require_api_key),
) -> LoanRead:
    raise LibraryError(status_code=501, code="not_implemented", message=_NOT_IMPLEMENTED)
