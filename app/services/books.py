"""Book service — stubs completed by the book CRUD ticket."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.errors import LibraryError
from app.models import Book
from app.schemas import BookCreate, BookUpdate


def list_books(
    db: Session,
    *,
    q: str | None,
    limit: int,
    offset: int,
) -> tuple[list[Book], int]:
    raise LibraryError(501, "not_implemented", "list_books is not implemented yet.")


def get_book(db: Session, book_id: int) -> Book:
    raise LibraryError(501, "not_implemented", "get_book is not implemented yet.")


def create_book(db: Session, data: BookCreate) -> Book:
    raise LibraryError(501, "not_implemented", "create_book is not implemented yet.")


def update_book(db: Session, book_id: int, data: BookUpdate) -> Book:
    raise LibraryError(501, "not_implemented", "update_book is not implemented yet.")


def delete_book(db: Session, book_id: int) -> None:
    raise LibraryError(501, "not_implemented", "delete_book is not implemented yet.")
