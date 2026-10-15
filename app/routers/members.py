"""Member endpoints: create, list, read, update and delete."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..deps import Pagination, get_db, pagination, require_api_key
from ..schemas import (
    DeletedResponse,
    MemberCreate,
    MemberRead,
    MemberUpdate,
    Page,
)
from ..services import members as member_service

router = APIRouter(tags=["members"])


@router.post("/members", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
def create_member(
    data: MemberCreate,
    db: Session = Depends(get_db),
    _api_key: None = Depends(require_api_key),
) -> MemberRead:
    member = member_service.create_member(db, data)
    return MemberRead.model_validate(member)


@router.get("/members", response_model=Page[MemberRead])
def list_members(
    page: Pagination = Depends(pagination),
    db: Session = Depends(get_db),
) -> Page[MemberRead]:
    members, total = member_service.list_members(db, limit=page.limit, offset=page.offset)
    return Page[MemberRead](
        items=[MemberRead.model_validate(member) for member in members],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/members/{member_id}", response_model=MemberRead)
def get_member(member_id: int, db: Session = Depends(get_db)) -> MemberRead:
    member = member_service.get_member(db, member_id)
    return MemberRead.model_validate(member)


@router.put("/members/{member_id}", response_model=MemberRead)
def update_member(
    member_id: int,
    data: MemberUpdate,
    db: Session = Depends(get_db),
    _api_key: None = Depends(require_api_key),
) -> MemberRead:
    member = member_service.update_member(db, member_id, data)
    return MemberRead.model_validate(member)


@router.delete("/members/{member_id}", response_model=DeletedResponse)
def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    _api_key: None = Depends(require_api_key),
) -> DeletedResponse:
    member_service.delete_member(db, member_id)
    return DeletedResponse(id=member_id)
