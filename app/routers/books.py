"""HTTP routes for books."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import Pagination, get_db, pagination, require_api_key
from app.schemas import BookCreate, BookRead, BookUpdate, DeletedResponse, Page
from app.services import books as books_service

router = APIRouter(tags=["books"])


@router.get("/books", response_model=Page[BookRead])
def list_books(
    q: str | None = None,
    page: Pagination = Depends(pagination),
    db: Session = Depends(get_db),
) -> Page[BookRead]:
    items, total = books_service.list_books(db, q=q, limit=page.limit, offset=page.offset)
    return Page[BookRead](
        items=[BookRead.model_validate(book) for book in items],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.post("/books", response_model=BookRead, status_code=201)
def create_book(
    data: BookCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> BookRead:
    book = books_service.create_book(db, data)
    return BookRead.model_validate(book)


@router.get("/books/{book_id}", response_model=BookRead)
def get_book(
    book_id: int,
    db: Session = Depends(get_db),
) -> BookRead:
    book = books_service.get_book(db, book_id)
    return BookRead.model_validate(book)


@router.put("/books/{book_id}", response_model=BookRead)
def update_book(
    book_id: int,
    data: BookUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> BookRead:
    book = books_service.update_book(db, book_id, data)
    return BookRead.model_validate(book)


@router.delete("/books/{book_id}", response_model=DeletedResponse)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> DeletedResponse:
    books_service.delete_book(db, book_id)
    return DeletedResponse(id=book_id)
