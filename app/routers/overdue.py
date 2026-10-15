"""Overdue loans endpoint: GET /loans/overdue."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import Pagination, get_db, pagination
from ..schemas import OverdueLoan, Page
from ..services import overdue as overdue_service

router = APIRouter(tags=["loans"])


@router.get("/loans/overdue", response_model=Page[OverdueLoan])
def list_overdue(
    page: Pagination = Depends(pagination),
    db: Session = Depends(get_db),
) -> Page[OverdueLoan]:
    """List the open loans whose due date has passed, oldest first.

    This is a read endpoint, so it deliberately declares no API-key
    dependency: an unauthenticated caller receives the list.
    """
    loans, total = overdue_service.list_overdue(db, limit=page.limit, offset=page.offset)
    return Page[OverdueLoan](
        items=[OverdueLoan.model_validate(loan) for loan in loans],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )
