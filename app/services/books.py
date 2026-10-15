"""Book service. Bodies are filled in by the book CRUD ticket."""

from sqlalchemy.orm import Session

from ..models import Book
from ..schemas import BookCreate, BookUpdate


def list_books(
    db: Session,
    *,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Book], int]:
    """Return one page of books and the total number of matches."""
    ...


def get_book(db: Session, book_id: int) -> Book:
    """Return the book with this id."""
    ...


def create_book(db: Session, data: BookCreate) -> Book:
    """Persist and return a new book."""
    ...


def update_book(db: Session, book_id: int, data: BookUpdate) -> Book:
    """Apply the given changes to an existing book."""
    ...


def delete_book(db: Session, book_id: int) -> None:
    """Delete a book that has no loans."""
    ...
