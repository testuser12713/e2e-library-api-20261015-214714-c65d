"""Member service: the borrowing-side CRUD rules.

Every rule violation is reported as a :class:`LibraryError` carrying one of the
contract's codes, with an English message. The caller passes the SQLAlchemy
session; this module only talks to the ORM.
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..errors import LibraryError
from ..models import Loan, Member
from ..schemas import MemberCreate, MemberUpdate

_NON_NULLABLE_FIELDS = ("name", "email", "member_since")


def list_members(
    db: Session,
    *,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Member], int]:
    """Return one page of members and the total number of members.

    The total is independent of ``limit``/``offset`` and the page is ordered by
    ``id`` so that repeated calls yield stable pages.
    """
    total = db.scalar(select(func.count()).select_from(Member)) or 0
    members = list(db.scalars(select(Member).order_by(Member.id).limit(limit).offset(offset)))
    return members, total


def get_member(db: Session, member_id: int) -> Member:
    """Return the member with this id or raise ``not_found``."""
    member = db.get(Member, member_id)
    if member is None:
        raise LibraryError(
            status_code=404,
            code="not_found",
            message=f"Member {member_id} not found.",
        )
    return member


def _member_with_email(db: Session, email: str, *, exclude_id: int | None = None) -> Member | None:
    """Return a member holding this email, optionally excluding one id."""
    stmt = select(Member).where(Member.email == email)
    if exclude_id is not None:
        stmt = stmt.where(Member.id != exclude_id)
    return db.scalar(stmt)


def create_member(db: Session, data: MemberCreate) -> Member:
    """Persist and return a new member, defaulting ``member_since`` to today."""
    if _member_with_email(db, data.email) is not None:
        raise LibraryError(
            status_code=409,
            code="conflict",
            message=f"A member with email {data.email} already exists.",
        )
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
    """Apply the given changes to an existing member.

    Only fields present in the request body are written. An explicit ``null``
    for a column that cannot be null is a validation failure rather than a
    database error.
    """
    member = get_member(db, member_id)
    changes = data.model_dump(exclude_unset=True)

    invalid = [
        {
            "type": "value_error",
            "loc": ["body", field],
            "msg": "Input should not be null",
            "input": None,
        }
        for field in _NON_NULLABLE_FIELDS
        if field in changes and changes[field] is None
    ]
    if invalid:
        raise LibraryError(
            status_code=422,
            code="validation_error",
            message="Request validation failed.",
            details=invalid,
        )

    new_email = changes.get("email")
    if (
        new_email is not None
        and _member_with_email(db, new_email, exclude_id=member_id) is not None
    ):
        raise LibraryError(
            status_code=409,
            code="conflict",
            message=f"A member with email {new_email} already exists.",
        )

    for field, value in changes.items():
        setattr(member, field, value)
    db.commit()
    db.refresh(member)
    return member


def delete_member(db: Session, member_id: int) -> None:
    """Delete a member that has no loans.

    Any loan referencing the member blocks the delete, whether it is still open
    or already returned.
    """
    member = get_member(db, member_id)
    referencing_loan = db.scalar(select(Loan.id).where(Loan.member_id == member_id).limit(1))
    if referencing_loan is not None:
        raise LibraryError(
            status_code=409,
            code="conflict",
            message=f"Member {member_id} has loans and cannot be deleted.",
        )
    db.delete(member)
    db.commit()
