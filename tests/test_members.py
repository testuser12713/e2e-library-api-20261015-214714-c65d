"""Tests for the member CRUD endpoints."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Book, Loan

VALID_MEMBER = {
    "name": "Ada Lovelace",
    "email": "ada@example.com",
    "member_since": "2024-01-15",
}


def _create_member(client: TestClient, api_key: str, **overrides) -> dict:
    payload = {**VALID_MEMBER, **overrides}
    response = client.post("/members", json=payload, headers={"X-API-Key": api_key})
    assert response.status_code == 201, response.text
    return response.json()


def test_create_member_without_key_is_unauthorized(client: TestClient) -> None:
    response = client.post("/members", json=VALID_MEMBER)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_create_member_defaults_member_since_to_today(client: TestClient, api_key: str) -> None:
    response = client.post(
        "/members",
        json={"name": "Grace Hopper", "email": "grace@example.com"},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["name"] == "Grace Hopper"
    assert body["email"] == "grace@example.com"
    assert body["member_since"] == date.today().isoformat()


def test_create_member_keeps_supplied_member_since(client: TestClient, api_key: str) -> None:
    body = _create_member(client, api_key)
    assert body["member_since"] == "2024-01-15"


def test_create_member_duplicate_email_conflicts(client: TestClient, api_key: str) -> None:
    _create_member(client, api_key)
    response = client.post(
        "/members",
        json={**VALID_MEMBER, "name": "Another Ada"},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_create_member_invalid_email_is_validation_error(client: TestClient, api_key: str) -> None:
    response = client.post(
        "/members",
        json={"name": "Bad Email", "email": "not-an-email"},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert isinstance(error["details"], list)
    assert error["details"]


def test_list_members_reports_items_and_total(client: TestClient, api_key: str) -> None:
    _create_member(client, api_key, email="a@example.com")
    _create_member(client, api_key, email="b@example.com")

    response = client.get("/members")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert {item["email"] for item in body["items"]} == {"a@example.com", "b@example.com"}


def test_list_members_paginates(client: TestClient, api_key: str) -> None:
    for index in range(3):
        _create_member(client, api_key, email=f"member{index}@example.com")

    first = client.get("/members", params={"limit": 2, "offset": 0}).json()
    assert first["total"] == 3
    assert len(first["items"]) == 2
    assert first["limit"] == 2

    second = client.get("/members", params={"limit": 2, "offset": 2}).json()
    assert second["total"] == 3
    assert len(second["items"]) == 1


def test_get_member_by_id(client: TestClient, api_key: str) -> None:
    created = _create_member(client, api_key)
    response = client.get(f"/members/{created['id']}")
    assert response.status_code == 200
    assert response.json()["email"] == "ada@example.com"


def test_get_unknown_member_is_not_found(client: TestClient) -> None:
    response = client.get("/members/999999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_update_member_partially(client: TestClient, api_key: str) -> None:
    created = _create_member(client, api_key)
    response = client.put(
        f"/members/{created['id']}",
        json={"name": "Ada Byron"},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Ada Byron"
    assert body["email"] == "ada@example.com"
    assert body["member_since"] == "2024-01-15"


def test_update_unknown_member_is_not_found(client: TestClient, api_key: str) -> None:
    response = client.put(
        "/members/999999",
        json={"name": "Nobody"},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 404


def test_update_member_duplicate_email_conflicts(client: TestClient, api_key: str) -> None:
    _create_member(client, api_key, email="first@example.com")
    second = _create_member(client, api_key, email="second@example.com")
    response = client.put(
        f"/members/{second['id']}",
        json={"email": "first@example.com"},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_update_member_invalid_email_is_validation_error(client: TestClient, api_key: str) -> None:
    created = _create_member(client, api_key)
    response = client.put(
        f"/members/{created['id']}",
        json={"email": "still-not-an-email"},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 422


def test_delete_member_without_loans(client: TestClient, api_key: str) -> None:
    created = _create_member(client, api_key)
    response = client.delete(f"/members/{created['id']}", headers={"X-API-Key": api_key})
    assert response.status_code == 200
    assert response.json() == {"id": created["id"]}
    assert client.get(f"/members/{created['id']}").status_code == 404


def test_delete_unknown_member_is_not_found(client: TestClient, api_key: str) -> None:
    response = client.delete("/members/999999", headers={"X-API-Key": api_key})
    assert response.status_code == 404


def test_delete_member_with_open_loan_conflicts(
    client: TestClient, session: Session, api_key: str
) -> None:
    created = _create_member(client, api_key)

    book = Book(
        title="Structural Engineering",
        author="I. Beam",
        isbn="loan-0001",
        year=2001,
        copies_total=1,
    )
    session.add(book)
    session.commit()

    now = datetime.now(UTC).replace(tzinfo=None)
    session.add(
        Loan(
            book_id=book.id,
            member_id=created["id"],
            loaned_at=now,
            due_at=now + timedelta(days=14),
        )
    )
    session.commit()

    response = client.delete(f"/members/{created['id']}", headers={"X-API-Key": api_key})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"
    assert client.get(f"/members/{created['id']}").status_code == 200
