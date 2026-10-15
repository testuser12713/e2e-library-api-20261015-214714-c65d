"""Book endpoints. Bodies are stubs until the book CRUD ticket lands."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..deps import Pagination, get_db, pagination, require_api_key
from ..errors import LibraryError
from ..schemas import BookCreate, BookRead, BookUpdate, DeletedResponse, Page

router = APIRouter(tags=["books"])

_NOT_IMPLEMENTED = "book CRUD is implemented by a later ticket"


@router.post("/books", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book(
    data: BookCreate,
    db: Session = Depends(get_db),
    _api_key: None = Depends(require_api_key),
) -> BookRead:
    raise LibraryError(status_code=501, code="not_implemented", message=_NOT_IMPLEMENTED)


@router.get("/books", response_model=Page[BookRead])
def list_books(
    q: str | None = None,
    page: Pagination = Depends(pagination),
    db: Session = Depends(get_db),
) -> Page[BookRead]:
    raise LibraryError(status_code=501, code="not_implemented", message=_NOT_IMPLEMENTED)


@router.get("/books/{book_id}", response_model=BookRead)
def get_book(book_id: int, db: Session = Depends(get_db)) -> BookRead:
    raise LibraryError(status_code=501, code="not_implemented", message=_NOT_IMPLEMENTED)


@router.put("/books/{book_id}", response_model=BookRead)
def update_book(
    book_id: int,
    data: BookUpdate,
    db: Session = Depends(get_db),
    _api_key: None = Depends(require_api_key),
) -> BookRead:
    raise LibraryError(status_code=501, code="not_implemented", message=_NOT_IMPLEMENTED)


@router.delete("/books/{book_id}", response_model=DeletedResponse)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    _api_key: None = Depends(require_api_key),
) -> DeletedResponse:
    raise LibraryError(status_code=501, code="not_implemented", message=_NOT_IMPLEMENTED)
