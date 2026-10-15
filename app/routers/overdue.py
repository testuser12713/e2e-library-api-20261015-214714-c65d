"""HTTP route for the overdue loans list."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import Pagination, get_db, pagination
from app.schemas import OverdueLoan, Page
from app.services import overdue as overdue_service

router = APIRouter(tags=["loans"])


@router.get("/loans/overdue", response_model=Page[OverdueLoan])
def list_overdue(
    page: Pagination = Depends(pagination),
    db: Session = Depends(get_db),
) -> Page[OverdueLoan]:
    """List open loans whose due date has already passed."""
    loans, total = overdue_service.list_overdue(db, limit=page.limit, offset=page.offset)
    return Page[OverdueLoan](
        items=loans,
        total=total,
        limit=page.limit,
        offset=page.offset,
    )
