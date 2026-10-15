"""Member service. Bodies are filled in by the member CRUD ticket."""

from sqlalchemy.orm import Session

from ..models import Member
from ..schemas import MemberCreate, MemberUpdate


def list_members(
    db: Session,
    *,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Member], int]:
    """Return one page of members and the total number of members."""
    ...


def get_member(db: Session, member_id: int) -> Member:
    """Return the member with this id."""
    ...


def create_member(db: Session, data: MemberCreate) -> Member:
    """Persist and return a new member."""
    ...


def update_member(db: Session, member_id: int, data: MemberUpdate) -> Member:
    """Apply the given changes to an existing member."""
    ...


def delete_member(db: Session, member_id: int) -> None:
    """Delete a member that has no loans."""
    ...
