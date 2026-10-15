"""Overdue loans endpoint. Body is a stub until the overdue ticket lands."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import Pagination, get_db, pagination
from ..errors import LibraryError
from ..schemas import OverdueLoan, Page

router = APIRouter(tags=["loans"])

_NOT_IMPLEMENTED = "the overdue list is implemented by a later ticket"


@router.get("/loans/overdue", response_model=Page[OverdueLoan])
def list_overdue(
    page: Pagination = Depends(pagination),
    db: Session = Depends(get_db),
) -> Page[OverdueLoan]:
    raise LibraryError(status_code=501, code="not_implemented", message=_NOT_IMPLEMENTED)
