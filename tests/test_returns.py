"""Tests of the loan return endpoint: AC-14, AC-15 and AC-16.

Books, members and loans are seeded through the direct ``session`` fixture because
their create endpoints belong to other tickets.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import Book, Loan, Member


def _seed_open_loan(session: Session, copies_total: int = 2) -> tuple[int, int]:
    """Create a book with one open loan and return ``(book_id, loan_id)``."""
    book = Book(
        title="The Hobbit",
        author="J. R. R. Tolkien",
        isbn=f"isbn-{uuid4().hex}",
        year=1937,
        copies_total=copies_total,
    )
    member = Member(
        name="Ada Lovelace",
        email=f"{uuid4().hex}@example.com",
        member_since=datetime.now(UTC).date(),
    )
    session.add_all([book, member])
    session.commit()

    loaned_at = datetime.now(UTC) - timedelta(days=1)
    loan = Loan(
        book_id=book.id,
        member_id=member.id,
        loaned_at=loaned_at,
        due_at=loaned_at + timedelta(days=14),
        returned_at=None,
    )
    session.add(loan)
    session.commit()
    return book.id, loan.id


def _copies(session: Session, book_id: int) -> int:
    """Report the book's copy count from a fresh read of the database."""
    session.expire_all()
    book = session.get(Book, book_id)
    assert book is not None
    return book.copies_available


def test_return_sets_returned_at_and_frees_a_copy(client, session, api_key):
    book_id, loan_id = _seed_open_loan(session)
    assert _copies(session, book_id) == 1

    response = client.post(f"/loans/{loan_id}/return", headers={"X-API-Key": api_key})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == loan_id
    assert body["returned_at"] is not None
    assert body["returned_at"].endswith("Z")
    assert "+" not in body["returned_at"]

    session.expire_all()
    stored = session.get(Loan, loan_id)
    assert stored is not None
    assert stored.returned_at is not None
    assert _copies(session, book_id) == 2


def test_second_return_conflicts_and_leaves_copies_unchanged(client, session, api_key):
    book_id, loan_id = _seed_open_loan(session)

    first = client.post(f"/loans/{loan_id}/return", headers={"X-API-Key": api_key})
    assert first.status_code == 200
    after_first = _copies(session, book_id)
    assert after_first == 2

    second = client.post(f"/loans/{loan_id}/return", headers={"X-API-Key": api_key})

    assert second.status_code == 409
    error = second.json()["error"]
    assert error["code"] == "conflict"
    assert _copies(session, book_id) == after_first


def test_unknown_loan_is_not_found_and_leaves_copies_unchanged(client, session, api_key):
    book_id, _loan_id = _seed_open_loan(session)
    before = _copies(session, book_id)

    response = client.post("/loans/999999999/return", headers={"X-API-Key": api_key})

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "not_found"
    assert _copies(session, book_id) == before


def test_return_without_key_is_unauthorized(client, session):
    book_id, loan_id = _seed_open_loan(session)
    before = _copies(session, book_id)

    response = client.post(f"/loans/{loan_id}/return")

    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "unauthorized"

    session.expire_all()
    stored = session.get(Loan, loan_id)
    assert stored is not None
    assert stored.returned_at is None
    assert _copies(session, book_id) == before
