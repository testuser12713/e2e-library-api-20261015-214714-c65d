"""Tests for loan creation (POST /loans) and the borrowing rules."""

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select

from app.models import Book, Loan, Member

LOAN_PERIOD = timedelta(days=14)


def _headers(api_key):
    return {"X-API-Key": api_key}


def _make_book(session, copies_total=1):
    book = Book(
        title="The Pragmatic Programmer",
        author="Andrew Hunt",
        isbn=f"isbn-{uuid.uuid4().hex}",
        year=1999,
        copies_total=copies_total,
    )
    session.add(book)
    session.commit()
    return book


def _make_member(session):
    member = Member(
        name="Ada Lovelace",
        email=f"member-{uuid.uuid4().hex}@example.com",
        member_since=date(2020, 1, 1),
    )
    session.add(member)
    session.commit()
    return member


def _make_open_loan(session, book, member):
    loaned_at = datetime.now(UTC)
    loan = Loan(
        book_id=book.id,
        member_id=member.id,
        loaned_at=loaned_at,
        due_at=loaned_at + LOAN_PERIOD,
        returned_at=None,
    )
    session.add(loan)
    session.commit()
    return loan


def _copies_available(session, book_id):
    """Read a book's available copies from a fresh transaction."""
    session.rollback()
    session.expire_all()
    book = session.get(Book, book_id)
    assert book is not None
    return book.copies_available


def _count_loans(session, **filters):
    """Count loan rows matching the given column filters from a fresh transaction."""
    session.rollback()
    session.expire_all()
    statement = select(func.count()).select_from(Loan)
    for column, value in filters.items():
        statement = statement.where(getattr(Loan, column) == value)
    return session.scalar(statement)


def test_create_loan_answers_201_with_a_fourteen_day_due_date(client, session, api_key):
    book = _make_book(session, copies_total=2)
    member = _make_member(session)
    before = _copies_available(session, book.id)

    response = client.post(
        "/loans",
        json={"book_id": book.id, "member_id": member.id},
        headers=_headers(api_key),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["book_id"] == book.id
    assert body["member_id"] == member.id
    assert body["returned_at"] is None
    assert body["id"] is not None

    loaned_at = datetime.fromisoformat(body["loaned_at"])
    due_at = datetime.fromisoformat(body["due_at"])
    assert due_at - loaned_at == LOAN_PERIOD

    assert _copies_available(session, book.id) == before - 1


def test_unknown_book_is_404_and_writes_no_loan(client, session, api_key):
    member = _make_member(session)

    response = client.post(
        "/loans",
        json={"book_id": 10_000_000, "member_id": member.id},
        headers=_headers(api_key),
    )

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "not_found"
    assert _count_loans(session, member_id=member.id) == 0


def test_unknown_member_is_404_and_writes_no_loan(client, session, api_key):
    book = _make_book(session, copies_total=1)

    response = client.post(
        "/loans",
        json={"book_id": book.id, "member_id": 10_000_000},
        headers=_headers(api_key),
    )

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "not_found"
    assert _count_loans(session, book_id=book.id) == 0


def test_book_without_free_copy_is_409_naming_the_book(client, session, api_key):
    book = _make_book(session, copies_total=1)
    member = _make_member(session)
    _make_open_loan(session, book, member)

    before = _copies_available(session, book.id)
    assert before == 0

    response = client.post(
        "/loans",
        json={"book_id": book.id, "member_id": member.id},
        headers=_headers(api_key),
    )

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "conflict"
    assert book.title in error["message"]
    assert _copies_available(session, book.id) == before
    assert _count_loans(session, book_id=book.id) == 1


def test_member_with_three_open_loans_is_409_and_writes_no_fourth(client, session, api_key):
    member = _make_member(session)
    for _ in range(3):
        _make_open_loan(session, _make_book(session, copies_total=1), member)

    extra = _make_book(session, copies_total=1)
    before = _copies_available(session, extra.id)

    response = client.post(
        "/loans",
        json={"book_id": extra.id, "member_id": member.id},
        headers=_headers(api_key),
    )

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "conflict"
    assert _count_loans(session, member_id=member.id) == 3
    assert _copies_available(session, extra.id) == before


def test_create_loan_without_key_is_401_and_writes_no_loan(client, session):
    book = _make_book(session, copies_total=1)
    member = _make_member(session)

    response = client.post(
        "/loans",
        json={"book_id": book.id, "member_id": member.id},
    )

    assert response.status_code == 401
    body = response.json()
    assert set(body.keys()) == {"error"}
    error = body["error"]
    assert set(error.keys()) == {"code", "message", "details"}
    assert error["code"] == "unauthorized"
    assert _count_loans(session, book_id=book.id) == 0
