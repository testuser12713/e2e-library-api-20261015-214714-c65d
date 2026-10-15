"""HTTP routes for books."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import Pagination, get_db, pagination, require_api_key
from app.errors import LibraryError
from app.schemas import BookCreate, BookRead, BookUpdate, DeletedResponse, Page

router = APIRouter(tags=["books"])


@router.get("/books", response_model=Page[BookRead])
def list_books(
    q: str | None = None,
    page: Pagination = Depends(pagination),
    db: Session = Depends(get_db),
) -> Page[BookRead]:
    raise LibraryError(501, "not_implemented", "Listing books is not implemented yet.")


@router.post("/books", response_model=BookRead, status_code=201)
def create_book(
    data: BookCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> BookRead:
    raise LibraryError(501, "not_implemented", "Creating books is not implemented yet.")


@router.get("/books/{book_id}", response_model=BookRead)
def get_book(
    book_id: int,
    db: Session = Depends(get_db),
) -> BookRead:
    raise LibraryError(501, "not_implemented", "Reading a book is not implemented yet.")


@router.put("/books/{book_id}", response_model=BookRead)
def update_book(
    book_id: int,
    data: BookUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> BookRead:
    raise LibraryError(501, "not_implemented", "Updating a book is not implemented yet.")


@router.delete("/books/{book_id}", response_model=DeletedResponse)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> DeletedResponse:
    raise LibraryError(501, "not_implemented", "Deleting a book is not implemented yet.")
