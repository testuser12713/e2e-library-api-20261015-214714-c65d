"""Pydantic v2 schemas — the request/response contract of the library API."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, PlainSerializer


def serialize_utc_datetime(value: datetime) -> str:
    """Serialize a datetime as ISO-8601 UTC ending in 'Z'."""
    value = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    return value.isoformat().replace("+00:00", "Z")


UtcDatetime = Annotated[
    datetime,
    PlainSerializer(serialize_utc_datetime, return_type=str, when_used="json"),
]


class BookBase(BaseModel):
    title: str
    author: str
    isbn: str
    year: int
    copies_total: int


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    isbn: str | None = None
    year: int | None = None
    copies_total: int | None = None


class BookRead(BookBase):
    id: int
    copies_available: int

    model_config = ConfigDict(from_attributes=True)


class MemberCreate(BaseModel):
    name: str
    email: EmailStr
    member_since: date | None = None


class MemberUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    member_since: date | None = None


class MemberRead(BaseModel):
    id: int
    name: str
    email: str
    member_since: date

    model_config = ConfigDict(from_attributes=True)


class LoanCreate(BaseModel):
    book_id: int
    member_id: int


class LoanRead(BaseModel):
    id: int
    book_id: int
    member_id: int
    loaned_at: UtcDatetime
    due_at: UtcDatetime
    returned_at: UtcDatetime | None = None

    model_config = ConfigDict(from_attributes=True)


class BookBrief(BaseModel):
    id: int
    title: str
    author: str
    isbn: str
    year: int

    model_config = ConfigDict(from_attributes=True)


class MemberBrief(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class OverdueLoan(BaseModel):
    id: int
    book_id: int
    member_id: int
    loaned_at: UtcDatetime
    due_at: UtcDatetime
    book: BookBrief
    member: MemberBrief

    model_config = ConfigDict(from_attributes=True)


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class DeletedResponse(BaseModel):
    id: int
