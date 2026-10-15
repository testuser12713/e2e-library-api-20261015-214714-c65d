"""Tests for POST /loans/{loan_id}/return and the return service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Book, Loan, Member

RETURN_SUFFIX = "Z"


def _seed_open_loan(session: Session, copies_total: int = 3) -> tuple[int, int]:
    """Insert a book, a member and one open loan; return (book_id, loan_id)."""
    book = Book(
        title="The Return Ticket",
        author="Ada Lovelace",
        isbn="returns-0001",
        year=2024,
        copies_total=copies_total,
    )
    member = Member(name="Return Reader", email="return.reader@example.com")
    session.add_all([book, member])
    session.commit()

    now = datetime.now(UTC)
    loan = Loan(
        book_id=book.id,
        member_id=member.id,
        loaned_at=now,
        due_at=now + timedelta(days=14),
    )
    session.add(loan)
    session.commit()
    return book.id, loan.id


def _copies_available(session: Session, book_id: int) -> int:
    session.expire_all()
    book = session.get(Book, book_id)
    assert book is not None
    return book.copies_available


def test_return_sets_returned_at_and_increments_copies_available(
    client: TestClient,
    session: Session,
    api_key: str,
) -> None:
    book_id, loan_id = _seed_open_loan(session)
    before = _copies_available(session, book_id)

    response = client.post(
        f"/loans/{loan_id}/return",
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == loan_id
    assert body["book_id"] == book_id
    assert body["returned_at"] is not None
    assert body["returned_at"].endswith(RETURN_SUFFIX)
    assert _copies_available(session, book_id) == before + 1


def test_second_return_conflicts_and_copies_available_unchanged(
    client: TestClient,
    session: Session,
    api_key: str,
) -> None:
    book_id, loan_id = _seed_open_loan(session)

    first = client.post(f"/loans/{loan_id}/return", headers={"X-API-Key": api_key})
    assert first.status_code == 200
    after_first = _copies_available(session, book_id)

    second = client.post(f"/loans/{loan_id}/return", headers={"X-API-Key": api_key})
    assert second.status_code == 409
    error = second.json()["error"]
    assert error["code"] == "conflict"
    assert _copies_available(session, book_id) == after_first


def test_return_unknown_loan_is_not_found(
    client: TestClient,
    session: Session,
    api_key: str,
) -> None:
    book_id, _ = _seed_open_loan(session)
    before = _copies_available(session, book_id)

    response = client.post("/loans/999999/return", headers={"X-API-Key": api_key})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert _copies_available(session, book_id) == before


def test_return_without_api_key_is_unauthorized(client: TestClient) -> None:
    response = client.post("/loans/1/return")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
