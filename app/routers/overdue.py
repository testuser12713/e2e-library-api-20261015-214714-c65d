"""HTTP route for the overdue loans list."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import Pagination, get_db, pagination
from app.errors import LibraryError
from app.schemas import OverdueLoan, Page

router = APIRouter(tags=["loans"])


@router.get("/loans/overdue", response_model=Page[OverdueLoan])
def list_overdue(
    page: Pagination = Depends(pagination),
    db: Session = Depends(get_db),
) -> Page[OverdueLoan]:
    raise LibraryError(501, "not_implemented", "Listing overdue loans is not implemented yet.")
