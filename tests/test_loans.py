"""Tests for loan creation (POST /loans) and the borrowing rules."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.models import Book, Loan, Member


def _make_book(session, **overrides) -> Book:
    values = {
        "title": "The Pragmatic Programmer",
        "author": "Andrew Hunt",
        "isbn": "978-0201616224",
        "year": 1999,
        "copies_total": 2,
    }
    values.update(overrides)
    book = Book(**values)
    session.add(book)
    session.commit()
    return book


def _make_member(session, **overrides) -> Member:
    values = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "member_since": datetime(2020, 1, 1, tzinfo=UTC).date(),
    }
    values.update(overrides)
    member = Member(**values)
    session.add(member)
    session.commit()
    return member


def _make_open_loan(session, book: Book, member: Member) -> Loan:
    loaned_at = datetime.now(UTC)
    loan = Loan(
        book_id=book.id,
        member_id=member.id,
        loaned_at=loaned_at,
        due_at=loaned_at + timedelta(days=14),
        returned_at=None,
    )
    session.add(loan)
    session.commit()
    return loan


def _copies_available(session, book_id: int) -> int:
    session.expire_all()
    book = session.get(Book, book_id)
    assert book is not None
    return book.copies_available


def test_create_loan_returns_201_with_due_at_14_days_later(client, session, api_key):
    book = _make_book(session)
    member = _make_member(session)

    response = client.post(
        "/loans",
        json={"book_id": book.id, "member_id": member.id},
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["book_id"] == book.id
    assert body["member_id"] == member.id
    assert isinstance(body["id"], int)
    assert body["returned_at"] is None

    loaned_at = datetime.fromisoformat(body["loaned_at"].replace("Z", "+00:00"))
    due_at = datetime.fromisoformat(body["due_at"].replace("Z", "+00:00"))
    assert due_at - loaned_at == timedelta(days=14)

    assert _copies_available(session, book.id) == book.copies_total - 1


def test_create_loan_unknown_book_returns_404_and_creates_nothing(client, session, api_key):
    member = _make_member(session)

    response = client.post(
        "/loans",
        json={"book_id": 9999, "member_id": member.id},
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert session.query(Loan).count() == 0


def test_create_loan_unknown_member_returns_404_and_creates_nothing(client, session, api_key):
    book = _make_book(session)

    response = client.post(
        "/loans",
        json={"book_id": book.id, "member_id": 9999},
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert session.query(Loan).count() == 0


def test_create_loan_member_with_three_open_loans_returns_409(client, session, api_key):
    member = _make_member(session)
    for index in range(3):
        book = _make_book(session, isbn=f"978-000000000{index}", copies_total=1)
        _make_open_loan(session, book, member)

    fourth_book = _make_book(session, isbn="978-0000000099", copies_total=1)

    response = client.post(
        "/loans",
        json={"book_id": fourth_book.id, "member_id": member.id},
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"
    assert session.query(Loan).count() == 3
    assert _copies_available(session, fourth_book.id) == 1


def test_create_loan_without_free_copy_returns_409_naming_the_book(client, session, api_key):
    member = _make_member(session)
    book = _make_book(session, copies_total=1, title="Dune")
    _make_open_loan(session, book, member)

    other_member = _make_member(session, email="grace@example.com", name="Grace Hopper")

    response = client.post(
        "/loans",
        json={"book_id": book.id, "member_id": other_member.id},
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"
    assert "Dune" in response.json()["error"]["message"]
    assert session.query(Loan).count() == 1
    assert _copies_available(session, book.id) == 0


def test_copies_available_unchanged_after_rejected_loan(client, session, api_key):
    member = _make_member(session)
    book = _make_book(session, copies_total=1)
    _make_open_loan(session, book, member)
    before = _copies_available(session, book.id)

    other_member = _make_member(session, email="alan@example.com", name="Alan Turing")
    response = client.post(
        "/loans",
        json={"book_id": book.id, "member_id": other_member.id},
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 409
    assert _copies_available(session, book.id) == before


def test_create_loan_requires_api_key(client, session):
    book = _make_book(session)
    member = _make_member(session)

    response = client.post(
        "/loans",
        json={"book_id": book.id, "member_id": member.id},
    )

    assert response.status_code == 401
    assert session.query(Loan).count() == 0
