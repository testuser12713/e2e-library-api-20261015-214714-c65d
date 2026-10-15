"""Tests for ``GET /loans/overdue`` (AC-17).

Loans are seeded through the direct session because creating them through
``POST /loans`` belongs to another ticket. Every test removes the rows it
created, so the shared test database is left as it was found.
"""

from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy.orm import Session

from app.models import Book, Loan, Member

NOW = datetime.now(UTC).replace(tzinfo=None)


@pytest.fixture
def seed(session: Session) -> Iterator[Callable[..., Any]]:
    """Add ORM objects, then delete exactly those objects again afterwards."""
    created: list[Any] = []

    def _add(obj: Any) -> Any:
        session.add(obj)
        session.commit()
        session.refresh(obj)
        created.append(obj)
        return obj

    yield _add

    for obj in reversed(created):
        session.delete(obj)
    session.commit()


def _book(seed: Callable[..., Any], *, isbn: str, title: str) -> Book:
    return seed(Book(title=title, author="Brett Slatkin", isbn=isbn, year=2019, copies_total=2))


def _member(seed: Callable[..., Any], *, email: str, name: str) -> Member:
    return seed(Member(name=name, email=email, member_since=NOW.date()))


def test_overdue_lists_only_expired_open_loans(client, seed):
    book = _book(seed, isbn="978-0134853989", title="Effective Python")
    member = _member(seed, email="ada@example.com", name="Ada Lovelace")
    overdue = seed(
        Loan(
            book_id=book.id,
            member_id=member.id,
            loaned_at=NOW - timedelta(days=20),
            due_at=NOW - timedelta(days=6),
            returned_at=None,
        )
    )
    returned_in_time = seed(
        Loan(
            book_id=book.id,
            member_id=member.id,
            loaned_at=NOW - timedelta(days=10),
            due_at=NOW - timedelta(days=3),
            returned_at=NOW - timedelta(days=4),
        )
    )
    not_yet_due = seed(
        Loan(
            book_id=book.id,
            member_id=member.id,
            loaned_at=NOW - timedelta(days=1),
            due_at=NOW + timedelta(days=3),
            returned_at=None,
        )
    )

    response = client.get("/loans/overdue")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["limit"] == 20
    assert body["offset"] == 0

    ids = [item["id"] for item in body["items"]]
    assert ids == [overdue.id]
    assert returned_in_time.id not in ids
    assert not_yet_due.id not in ids

    item = body["items"][0]
    assert item["book_id"] == book.id
    assert item["member_id"] == member.id
    assert item["book"]["title"] == "Effective Python"
    assert item["book"]["isbn"] == "978-0134853989"
    assert item["member"]["name"] == "Ada Lovelace"
    assert item["member"]["email"] == "ada@example.com"


def test_overdue_serves_without_api_key(client):
    response = client.get("/loans/overdue")
    assert response.status_code == 200


def test_overdue_empty_state(client):
    response = client.get("/loans/overdue")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
