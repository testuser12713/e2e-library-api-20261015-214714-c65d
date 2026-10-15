"""Member service — stubs completed by the member CRUD ticket."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.errors import LibraryError
from app.models import Member
from app.schemas import MemberCreate, MemberUpdate


def list_members(
    db: Session,
    *,
    limit: int,
    offset: int,
) -> tuple[list[Member], int]:
    raise LibraryError(501, "not_implemented", "list_members is not implemented yet.")


def get_member(db: Session, member_id: int) -> Member:
    raise LibraryError(501, "not_implemented", "get_member is not implemented yet.")


def create_member(db: Session, data: MemberCreate) -> Member:
    raise LibraryError(501, "not_implemented", "create_member is not implemented yet.")


def update_member(db: Session, member_id: int, data: MemberUpdate) -> Member:
    raise LibraryError(501, "not_implemented", "update_member is not implemented yet.")


def delete_member(db: Session, member_id: int) -> None:
    raise LibraryError(501, "not_implemented", "delete_member is not implemented yet.")
