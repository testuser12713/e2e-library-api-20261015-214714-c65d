"""ORM models — the shared data contract of the sprint."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Book(Base):
    """A book title held by the library."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    isbn: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    copies_total: Mapped[int] = mapped_column(Integer, nullable=False)

    loans: Mapped[list[Loan]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
    )

    @property
    def copies_available(self) -> int:
        """Total copies minus the book's currently open loans."""
        return self.copies_total - sum(1 for loan in self.loans if loan.returned_at is None)


class Member(Base):
    """A library member."""

    __tablename__ = "members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    member_since: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)

    loans: Mapped[list[Loan]] = relationship(
        back_populates="member",
        cascade="all, delete-orphan",
    )


class Loan(Base):
    """A loan of one book copy to one member."""

    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False)
    loaned_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    book: Mapped[Book] = relationship(back_populates="loans")
    member: Mapped[Member] = relationship(back_populates="loans")
