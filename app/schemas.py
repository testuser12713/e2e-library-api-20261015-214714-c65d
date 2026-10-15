"""Pydantic v2 schemas for the frozen API contract."""

from datetime import UTC, date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, PlainSerializer


def _serialize_utc(value: datetime) -> str:
    """Serialize a datetime as ISO-8601 in UTC, always ending in ``Z``."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


UtcDatetime = Annotated[
    datetime,
    PlainSerializer(_serialize_utc, return_type=str, when_used="json"),
]


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class DeletedResponse(BaseModel):
    id: int


class BookCreate(BaseModel):
    title: str
    author: str
    isbn: str
    year: int
    copies_total: int


class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    isbn: str | None = None
    year: int | None = None
    copies_total: int | None = None


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    isbn: str
    year: int
    copies_total: int
    copies_available: int


class BookBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    isbn: str
    year: int


class MemberCreate(BaseModel):
    name: str
    email: EmailStr
    member_since: date | None = None


class MemberUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    member_since: date | None = None


class MemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    member_since: date


class MemberBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class LoanCreate(BaseModel):
    book_id: int
    member_id: int


class LoanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    member_id: int
    loaned_at: UtcDatetime
    due_at: UtcDatetime
    returned_at: UtcDatetime | None = None


class OverdueLoan(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    member_id: int
    loaned_at: UtcDatetime
    due_at: UtcDatetime
    book: BookBrief
    member: MemberBrief
