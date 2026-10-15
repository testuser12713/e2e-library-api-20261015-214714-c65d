"""HTTP routes for members."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import Pagination, get_db, pagination, require_api_key
from app.errors import LibraryError
from app.schemas import DeletedResponse, MemberCreate, MemberRead, MemberUpdate, Page

router = APIRouter(tags=["members"])


@router.get("/members", response_model=Page[MemberRead])
def list_members(
    page: Pagination = Depends(pagination),
    db: Session = Depends(get_db),
) -> Page[MemberRead]:
    raise LibraryError(501, "not_implemented", "Listing members is not implemented yet.")


@router.post("/members", response_model=MemberRead, status_code=201)
def create_member(
    data: MemberCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> MemberRead:
    raise LibraryError(501, "not_implemented", "Creating members is not implemented yet.")


@router.get("/members/{member_id}", response_model=MemberRead)
def get_member(
    member_id: int,
    db: Session = Depends(get_db),
) -> MemberRead:
    raise LibraryError(501, "not_implemented", "Reading a member is not implemented yet.")


@router.put("/members/{member_id}", response_model=MemberRead)
def update_member(
    member_id: int,
    data: MemberUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> MemberRead:
    raise LibraryError(501, "not_implemented", "Updating a member is not implemented yet.")


@router.delete("/members/{member_id}", response_model=DeletedResponse)
def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> DeletedResponse:
    raise LibraryError(501, "not_implemented", "Deleting a member is not implemented yet.")
