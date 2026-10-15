"""Book service — CRUD, search and pagination.

Every failure is a ``LibraryError`` with one of the contract's codes:
``not_found`` (404) and ``conflict`` (409).
"""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.errors import LibraryError
from app.models import Book, Loan
from app.schemas import BookCreate, BookUpdate


def _open_loans_count(db: Session, book_id: int) -> int:
    """Number of the book's loans that have not been returned yet."""
    return db.execute(
        select(func.count())
        .select_from(Loan)
        .where(Loan.book_id == book_id, Loan.returned_at.is_(None))
    ).scalar_one()


def list_books(
    db: Session,
    *,
    q: str | None,
    limit: int,
    offset: int,
) -> tuple[list[Book], int]:
    """Return one page of books and the total number of matches."""
    stmt = select(Book)
    count_stmt = select(func.count()).select_from(Book)

    if q:
        pattern = f"%{q.lower()}%"
        condition = or_(
            func.lower(Book.title).like(pattern),
            func.lower(Book.author).like(pattern),
        )
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    total = db.execute(count_stmt).scalar_one()
    items = list(db.execute(stmt.order_by(Book.id).limit(limit).offset(offset)).scalars().all())
    return items, total


def get_book(db: Session, book_id: int) -> Book:
    """Return one book or raise 404."""
    book = db.get(Book, book_id)
    if book is None:
        raise LibraryError(404, "not_found", f"Book {book_id} was not found.")
    return book


def create_book(db: Session, data: BookCreate) -> Book:
    """Create a book; a duplicate ISBN is a 409 and creates no second row."""
    duplicate = db.execute(select(Book).where(Book.isbn == data.isbn)).scalar_one_or_none()
    if duplicate is not None:
        raise LibraryError(409, "conflict", f"A book with ISBN {data.isbn} already exists.")

    book = Book(**data.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def update_book(db: Session, book_id: int, data: BookUpdate) -> Book:
    """Apply a partial update; reject conflicts without mutating the row."""
    book = get_book(db, book_id)
    changes = data.model_dump(exclude_unset=True, exclude_none=True)

    new_isbn = changes.get("isbn")
    if new_isbn is not None and new_isbn != book.isbn:
        duplicate = db.execute(
            select(Book).where(Book.isbn == new_isbn, Book.id != book_id)
        ).scalar_one_or_none()
        if duplicate is not None:
            raise LibraryError(409, "conflict", f"A book with ISBN {new_isbn} already exists.")

    new_copies_total = changes.get("copies_total")
    if new_copies_total is not None:
        open_loans = _open_loans_count(db, book_id)
        if new_copies_total < open_loans:
            raise LibraryError(
                409,
                "conflict",
                (
                    f"copies_total {new_copies_total} is below the "
                    f"{open_loans} open loans for book {book_id}."
                ),
            )

    for field, value in changes.items():
        setattr(book, field, value)
    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book_id: int) -> None:
    """Delete a book; any loan referencing it makes this a 409."""
    book = get_book(db, book_id)
    referencing_loans = db.execute(
        select(func.count()).select_from(Loan).where(Loan.book_id == book_id)
    ).scalar_one()
    if referencing_loans:
        raise LibraryError(
            409,
            "conflict",
            f"Book {book_id} is referenced by {referencing_loans} loan(s).",
        )

    db.delete(book)
    db.commit()
