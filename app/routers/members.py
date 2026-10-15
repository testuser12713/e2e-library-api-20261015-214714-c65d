"""HTTP routes for members."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import Pagination, get_db, pagination, require_api_key
from app.schemas import DeletedResponse, MemberCreate, MemberRead, MemberUpdate, Page
from app.services import members as members_service

router = APIRouter(tags=["members"])


@router.get("/members", response_model=Page[MemberRead])
def list_members(
    page: Pagination = Depends(pagination),
    db: Session = Depends(get_db),
) -> Page[MemberRead]:
    members, total = members_service.list_members(db, limit=page.limit, offset=page.offset)
    return Page[MemberRead](
        items=[MemberRead.model_validate(member) for member in members],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.post("/members", response_model=MemberRead, status_code=201)
def create_member(
    data: MemberCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> MemberRead:
    member = members_service.create_member(db, data)
    return MemberRead.model_validate(member)


@router.get("/members/{member_id}", response_model=MemberRead)
def get_member(
    member_id: int,
    db: Session = Depends(get_db),
) -> MemberRead:
    member = members_service.get_member(db, member_id)
    return MemberRead.model_validate(member)


@router.put("/members/{member_id}", response_model=MemberRead)
def update_member(
    member_id: int,
    data: MemberUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> MemberRead:
    member = members_service.update_member(db, member_id, data)
    return MemberRead.model_validate(member)


@router.delete("/members/{member_id}", response_model=DeletedResponse)
def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> DeletedResponse:
    members_service.delete_member(db, member_id)
    return DeletedResponse(id=member_id)
