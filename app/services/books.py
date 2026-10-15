"""Book service: CRUD, case-insensitive search and pagination."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..errors import LibraryError
from ..models import Book, Loan
from ..schemas import BookCreate, BookUpdate


def _open_loan_count(db: Session, book_id: int) -> int:
    """Number of loans of this book that have not been returned yet."""
    count = db.scalar(
        select(func.count())
        .select_from(Loan)
        .where(Loan.book_id == book_id, Loan.returned_at.is_(None))
    )
    return int(count or 0)


def list_books(
    db: Session,
    *,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Book], int]:
    """Return one page of books and the total number of matches.

    With ``q`` the match is a case-insensitive substring on the title OR the
    author. ``total`` counts every match, independent of ``limit``/``offset``.
    Rows are ordered by id so consecutive pages stay stable.
    """
    stmt = select(Book)
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            func.lower(Book.title).like(pattern) | func.lower(Book.author).like(pattern)
        )

    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    rows = db.scalars(stmt.order_by(Book.id).limit(limit).offset(offset)).all()
    return list(rows), total


def get_book(db: Session, book_id: int) -> Book:
    """Return the book with this id or raise a not-found error."""
    book = db.get(Book, book_id)
    if book is None:
        raise LibraryError(
            status_code=404,
            code="not_found",
            message=f"Book {book_id} was not found.",
        )
    return book


def create_book(db: Session, data: BookCreate) -> Book:
    """Persist and return a new book; a taken isbn is a conflict."""
    taken = db.scalar(select(Book.id).where(Book.isbn == data.isbn))
    if taken is not None:
        raise LibraryError(
            status_code=409,
            code="conflict",
            message=f"A book with ISBN {data.isbn} already exists.",
        )

    book = Book(
        title=data.title,
        author=data.author,
        isbn=data.isbn,
        year=data.year,
        copies_total=data.copies_total,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def update_book(db: Session, book_id: int, data: BookUpdate) -> Book:
    """Apply the given changes to an existing book.

    Validation happens before anything is written, so a rejected update leaves
    the row and the session untouched.
    """
    book = get_book(db, book_id)
    changes = data.model_dump(exclude_unset=True)

    new_isbn = changes.get("isbn")
    if new_isbn is not None and new_isbn != book.isbn:
        taken = db.scalar(select(Book.id).where(Book.isbn == new_isbn, Book.id != book_id))
        if taken is not None:
            raise LibraryError(
                status_code=409,
                code="conflict",
                message=f"A book with ISBN {new_isbn} already exists.",
            )

    new_total = changes.get("copies_total")
    if new_total is not None:
        open_loans = _open_loan_count(db, book_id)
        if new_total < open_loans:
            raise LibraryError(
                status_code=409,
                code="conflict",
                message=(
                    f"copies_total {new_total} is below the {open_loans} open loans "
                    f"of book {book_id}."
                ),
            )

    for field, value in changes.items():
        if value is not None:
            setattr(book, field, value)

    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book_id: int) -> None:
    """Delete a book that no loan references; a referenced book is a conflict."""
    book = get_book(db, book_id)
    references = db.scalar(select(Loan.id).where(Loan.book_id == book_id).limit(1))
    if references is not None:
        raise LibraryError(
            status_code=409,
            code="conflict",
            message=f"Book {book_id} is referenced by a loan and cannot be deleted.",
        )

    db.delete(book)
    db.commit()
