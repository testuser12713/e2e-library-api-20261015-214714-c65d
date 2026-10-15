"""Tests for book CRUD, search and pagination."""

from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Book, Loan, Member


def _book_payload(**overrides: object) -> dict:
    payload = {
        "title": "Harry Potter",
        "author": "J. K. Rowling",
        "isbn": "978-0747532699",
        "year": 1997,
        "copies_total": 3,
    }
    payload.update(overrides)
    return payload


def _create_book(client: TestClient, api_key: str, **overrides: object) -> dict:
    response = client.post(
        "/books",
        json=_book_payload(**overrides),
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 201
    return response.json()


def test_create_book_returns_201_with_available_equal_total(
    client: TestClient,
    api_key: str,
) -> None:
    body = _create_book(client, api_key)
    assert body["id"] > 0
    assert body["title"] == "Harry Potter"
    assert body["author"] == "J. K. Rowling"
    assert body["isbn"] == "978-0747532699"
    assert body["year"] == 1997
    assert body["copies_total"] == 3
    assert body["copies_available"] == 3


def test_create_book_duplicate_isbn_is_conflict(
    client: TestClient,
    api_key: str,
) -> None:
    _create_book(client, api_key)
    response = client.post(
        "/books",
        json=_book_payload(title="Other", isbn="978-0747532699"),
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"

    listing = client.get("/books")
    assert listing.json()["total"] == 1


def test_list_books_defaults_and_pagination(
    client: TestClient,
    api_key: str,
) -> None:
    for index in range(25):
        _create_book(client, api_key, isbn=f"isbn-{index}")

    response = client.get("/books")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 25
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert len(body["items"]) == 20

    page = client.get("/books", params={"limit": 5, "offset": 20}).json()
    assert page["limit"] == 5
    assert page["offset"] == 20
    assert len(page["items"]) == 5


def test_list_books_over_limit_is_rejected(
    client: TestClient,
) -> None:
    response = client.get("/books", params={"limit": 101})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_search_is_case_insensitive_substring_of_author(
    client: TestClient,
    api_key: str,
) -> None:
    _create_book(client, api_key)
    _create_book(
        client,
        api_key,
        title="Clean Code",
        author="Robert C. Martin",
        isbn="isbn-clean",
    )

    response = client.get("/books", params={"q": "rowl"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["author"] == "J. K. Rowling"


def test_search_is_case_insensitive_substring_of_title(
    client: TestClient,
    api_key: str,
) -> None:
    _create_book(client, api_key)
    response = client.get("/books", params={"q": "POTTER"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1


def test_search_without_matches_returns_empty_page(
    client: TestClient,
    api_key: str,
) -> None:
    _create_book(client, api_key)
    response = client.get("/books", params={"q": "zzz-no-such-book"})
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_get_book_returns_all_fields(
    client: TestClient,
    api_key: str,
) -> None:
    created = _create_book(client, api_key)
    response = client.get(f"/books/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_get_unknown_book_is_404(client: TestClient) -> None:
    response = client.get("/books/9999")
    assert response.status_code == 404
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "not_found"


def test_update_book_changes_fields(
    client: TestClient,
    api_key: str,
) -> None:
    created = _create_book(client, api_key)
    response = client.put(
        f"/books/{created['id']}",
        json={"title": "New Title", "copies_total": 5},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "New Title"
    assert body["copies_total"] == 5
    assert body["copies_available"] == 5
    assert body["author"] == "J. K. Rowling"


def test_update_book_duplicate_isbn_is_conflict(
    client: TestClient,
    api_key: str,
) -> None:
    _create_book(client, api_key)
    other = _create_book(client, api_key, title="Other", isbn="isbn-other")

    response = client.put(
        f"/books/{other['id']}",
        json={"isbn": "978-0747532699"},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"

    unchanged = client.get(f"/books/{other['id']}").json()
    assert unchanged["isbn"] == "isbn-other"


def test_update_below_open_loans_is_rejected_and_unchanged(
    client: TestClient,
    api_key: str,
    session: Session,
) -> None:
    created = _create_book(client, api_key, copies_total=3)
    member = Member(name="Reader", email="reader@example.com", member_since=date.today())
    session.add(member)
    session.commit()
    session.add(
        Loan(
            book_id=created["id"],
            member_id=member.id,
            loaned_at=datetime.now(UTC).replace(tzinfo=None),
            due_at=datetime.now(UTC).replace(tzinfo=None),
            returned_at=None,
        )
    )
    session.commit()

    response = client.put(
        f"/books/{created['id']}",
        json={"copies_total": 0},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"

    unchanged = client.get(f"/books/{created['id']}").json()
    assert unchanged["copies_total"] == 3


def test_update_unknown_book_is_404(
    client: TestClient,
    api_key: str,
) -> None:
    response = client.put(
        "/books/9999",
        json={"title": "Nope"},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 404


def test_delete_book_without_loans(
    client: TestClient,
    api_key: str,
) -> None:
    created = _create_book(client, api_key)
    response = client.delete(
        f"/books/{created['id']}",
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 200
    assert response.json() == {"id": created["id"]}
    assert client.get(f"/books/{created['id']}").status_code == 404


def test_delete_book_with_loan_is_conflict(
    client: TestClient,
    api_key: str,
    session: Session,
) -> None:
    created = _create_book(client, api_key)
    member = Member(name="Reader", email="reader@example.com", member_since=date.today())
    session.add(member)
    session.commit()
    session.add(
        Loan(
            book_id=created["id"],
            member_id=member.id,
            loaned_at=datetime.now(UTC).replace(tzinfo=None),
            due_at=datetime.now(UTC).replace(tzinfo=None),
            returned_at=None,
        )
    )
    session.commit()

    response = client.delete(
        f"/books/{created['id']}",
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"
    assert session.get(Book, created["id"]) is not None


def test_delete_unknown_book_is_404(
    client: TestClient,
    api_key: str,
) -> None:
    response = client.delete("/books/9999", headers={"X-API-Key": api_key})
    assert response.status_code == 404


def test_write_without_key_is_unauthorized(client: TestClient) -> None:
    response = client.post("/books", json=_book_payload())
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_write_with_wrong_key_is_unauthorized(
    client: TestClient,
    api_key: str,
) -> None:
    response = client.post(
        "/books",
        json=_book_payload(),
        headers={"X-API-Key": "not-the-key"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_invalid_body_with_key_is_validation_error(
    client: TestClient,
    api_key: str,
) -> None:
    response = client.post(
        "/books",
        json={"title": "Incomplete"},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert isinstance(error["details"], list)
    assert error["details"]


def test_get_endpoints_need_no_key(
    client: TestClient,
    api_key: str,
) -> None:
    created = _create_book(client, api_key)
    assert client.get("/books").status_code == 200
    assert client.get(f"/books/{created['id']}").status_code == 200
