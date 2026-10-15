"""Member service — CRUD rules for library members."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import LibraryError
from app.models import Loan, Member
from app.schemas import MemberCreate, MemberUpdate


def _get_or_404(db: Session, member_id: int) -> Member:
    member = db.get(Member, member_id)
    if member is None:
        raise LibraryError(404, "not_found", f"Member {member_id} does not exist.")
    return member


def _ensure_email_free(db: Session, email: str, *, exclude_id: int | None = None) -> None:
    statement = select(Member.id).where(Member.email == email)
    if exclude_id is not None:
        statement = statement.where(Member.id != exclude_id)
    if db.execute(statement).first() is not None:
        raise LibraryError(409, "conflict", f"A member with email '{email}' already exists.")


def list_members(
    db: Session,
    *,
    limit: int,
    offset: int,
) -> tuple[list[Member], int]:
    total = db.execute(select(func.count()).select_from(Member)).scalar_one()
    members = (
        db.execute(select(Member).order_by(Member.id).limit(limit).offset(offset)).scalars().all()
    )
    return list(members), total


def get_member(db: Session, member_id: int) -> Member:
    return _get_or_404(db, member_id)


def create_member(db: Session, data: MemberCreate) -> Member:
    _ensure_email_free(db, data.email)
    member = Member(
        name=data.name,
        email=data.email,
        member_since=data.member_since or date.today(),
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def update_member(db: Session, member_id: int, data: MemberUpdate) -> Member:
    member = _get_or_404(db, member_id)
    changes = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if "email" in changes and changes["email"] != member.email:
        _ensure_email_free(db, changes["email"], exclude_id=member_id)
    for field, value in changes.items():
        setattr(member, field, value)
    db.commit()
    db.refresh(member)
    return member


def delete_member(db: Session, member_id: int) -> None:
    member = _get_or_404(db, member_id)
    has_loan = db.execute(select(Loan.id).where(Loan.member_id == member_id).limit(1)).first()
    if has_loan is not None:
        raise LibraryError(
            409,
            "conflict",
            f"Member {member_id} is referenced by a loan and cannot be deleted.",
        )
    db.delete(member)
    db.commit()
