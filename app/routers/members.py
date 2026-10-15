"""Member endpoints. Bodies are stubs until the member CRUD ticket lands."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..deps import Pagination, get_db, pagination, require_api_key
from ..errors import LibraryError
from ..schemas import DeletedResponse, MemberCreate, MemberRead, MemberUpdate, Page

router = APIRouter(tags=["members"])

_NOT_IMPLEMENTED = "member CRUD is implemented by a later ticket"


@router.post("/members", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
def create_member(
    data: MemberCreate,
    db: Session = Depends(get_db),
    _api_key: None = Depends(require_api_key),
) -> MemberRead:
    raise LibraryError(status_code=501, code="not_implemented", message=_NOT_IMPLEMENTED)


@router.get("/members", response_model=Page[MemberRead])
def list_members(
    page: Pagination = Depends(pagination),
    db: Session = Depends(get_db),
) -> Page[MemberRead]:
    raise LibraryError(status_code=501, code="not_implemented", message=_NOT_IMPLEMENTED)


@router.get("/members/{member_id}", response_model=MemberRead)
def get_member(member_id: int, db: Session = Depends(get_db)) -> MemberRead:
    raise LibraryError(status_code=501, code="not_implemented", message=_NOT_IMPLEMENTED)


@router.put("/members/{member_id}", response_model=MemberRead)
def update_member(
    member_id: int,
    data: MemberUpdate,
    db: Session = Depends(get_db),
    _api_key: None = Depends(require_api_key),
) -> MemberRead:
    raise LibraryError(status_code=501, code="not_implemented", message=_NOT_IMPLEMENTED)


@router.delete("/members/{member_id}", response_model=DeletedResponse)
def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    _api_key: None = Depends(require_api_key),
) -> DeletedResponse:
    raise LibraryError(status_code=501, code="not_implemented", message=_NOT_IMPLEMENTED)
