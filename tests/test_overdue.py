"""Tests for the overdue loans list."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Book, Loan, Member


def _utcnow() -> datetime:
    """Naive UTC now, matching the storage form of the loan timestamps."""
    return datetime.now(UTC).replace(tzinfo=None)


def test_overdue_list_contains_only_open_past_due_loans(
    session: Session,
    client: TestClient,
    api_key: str,
) -> None:
    now = _utcnow()

    book = Book(
        title="Dune",
        author="Frank Herbert",
        isbn="isbn-overdue-0001",
        year=1965,
        copies_total=3,
    )
    member = Member(name="Ada Lovelace", email="ada@example.com")
    session.add_all([book, member])
    session.commit()

    overdue = Loan(
        book_id=book.id,
        member_id=member.id,
        loaned_at=now - timedelta(days=20),
        due_at=now - timedelta(days=6),
        returned_at=None,
    )
    returned_in_time = Loan(
        book_id=book.id,
        member_id=member.id,
        loaned_at=now - timedelta(days=10),
        due_at=now - timedelta(days=1),
        returned_at=now - timedelta(days=2),
    )
    not_yet_due = Loan(
        book_id=book.id,
        member_id=member.id,
        loaned_at=now,
        due_at=now + timedelta(days=5),
        returned_at=None,
    )
    session.add_all([overdue, returned_in_time, not_yet_due])
    session.commit()

    response = client.get("/loans/overdue", headers={"X-API-Key": api_key})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["limit"] == 20
    assert body["offset"] == 0

    items = body["items"]
    assert len(items) == 1

    entry = items[0]
    assert entry["id"] == overdue.id
    assert entry["book_id"] == book.id
    assert entry["member_id"] == member.id
    assert entry["book"]["title"] == "Dune"
    assert entry["book"]["isbn"] == "isbn-overdue-0001"
    assert entry["book"]["author"] == "Frank Herbert"
    assert entry["book"]["year"] == 1965
    assert entry["member"]["name"] == "Ada Lovelace"
    assert entry["member"]["email"] == "ada@example.com"


def test_overdue_list_needs_no_api_key(
    session: Session,
    client: TestClient,
) -> None:
    response = client.get("/loans/overdue")
    assert response.status_code == 200
    assert response.json()["items"] == []
