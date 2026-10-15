"""Tests for the book CRUD slice: create, read, search, update and delete.

The fixtures ``client``, ``session`` and ``api_key`` come from ``tests/conftest``;
``tests/__init__`` sets a per-run API key and a temporary SQLite file before the
application engine is imported.
"""

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select

from app.models import Book, Loan, Member


def _book_payload(**overrides) -> dict:
    payload = {
        "title": "Harry Potter",
        "author": "J. K. Rowling",
        "isbn": f"isbn-{uuid.uuid4().hex}",
        "year": 1997,
        "copies_total": 3,
    }
    payload.update(overrides)
    return payload


def _auth(api_key: str) -> dict:
    return {"X-API-Key": api_key}


def _error_payload(body: dict) -> dict:
    assert set(body.keys()) == {"error"}
    error = body["error"]
    assert set(error.keys()) == {"code", "message", "details"}
    return error


def _seed_loan(session, *, copies_total: int = 3, open_loans: int = 1) -> tuple[int, int]:
    """Seed a book, a member and ``open_loans`` loans; return (book_id, member_id)."""
    book = Book(
        title="Seeded",
        author="Seeder",
        isbn=f"seed-{uuid.uuid4().hex}",
        year=2000,
        copies_total=copies_total,
    )
    member = Member(
        name="Seed Reader",
        email=f"seed-{uuid.uuid4().hex}@example.com",
        member_since=date.today(),
    )
    session.add_all([book, member])
    session.commit()

    loaned_at = datetime.now(UTC)
    for _ in range(open_loans):
        session.add(
            Loan(
                book_id=book.id,
                member_id=member.id,
                loaned_at=loaned_at,
                due_at=loaned_at + timedelta(days=14),
                returned_at=None,
            )
        )
    session.commit()
    return book.id, member.id


def test_create_book_returns_201_with_available_equal_total(client, api_key):
    response = client.post("/books", json=_book_payload(copies_total=4), headers=_auth(api_key))
    assert response.status_code == 201
    body = response.json()
    assert body["copies_total"] == 4
    assert body["copies_available"] == 4
    assert body["id"]
    for field in ("title", "author", "isbn", "year"):
        assert field in body


def test_create_duplicate_isbn_conflict_leaves_one_row(client, session, api_key):
    payload = _book_payload()
    assert client.post("/books", json=payload, headers=_auth(api_key)).status_code == 201

    second = dict(payload, title="Another title")
    response = client.post("/books", json=second, headers=_auth(api_key))
    assert response.status_code == 409
    assert _error_payload(response.json())["code"] == "conflict"

    count = session.scalar(
        select(func.count()).select_from(Book).where(Book.isbn == payload["isbn"])
    )
    assert count == 1


def test_list_books_page_shape_and_default_limit(client, api_key):
    marker = uuid.uuid4().hex
    for index in range(25):
        payload = _book_payload(title=f"Page {index}", author=f"Paginator {marker}")
        assert client.post("/books", json=payload, headers=_auth(api_key)).status_code == 201

    response = client.get("/books", params={"q": marker})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 25
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert len(body["items"]) == 20


def test_list_books_respects_limit_and_offset(client, api_key):
    marker = uuid.uuid4().hex
    for index in range(5):
        payload = _book_payload(title=f"Slice {index}", author=f"Slicer {marker}")
        assert client.post("/books", json=payload, headers=_auth(api_key)).status_code == 201

    first = client.get("/books", params={"q": marker, "limit": 2, "offset": 0}).json()
    second = client.get("/books", params={"q": marker, "limit": 2, "offset": 2}).json()
    assert len(first["items"]) == 2
    assert len(second["items"]) == 2
    assert first["items"][0]["id"] != second["items"][0]["id"]


def test_search_matches_author_case_insensitively(client, api_key):
    payload = _book_payload(author="J. K. Rowling")
    created = client.post("/books", json=payload, headers=_auth(api_key)).json()

    lower = client.get("/books", params={"q": "rowl"})
    upper = client.get("/books", params={"q": "ROWL"})
    assert lower.status_code == 200
    assert upper.status_code == 200
    assert created["isbn"] in {item["isbn"] for item in lower.json()["items"]}
    assert created["isbn"] in {item["isbn"] for item in upper.json()["items"]}


def test_search_without_matches_is_empty_page(client):
    response = client.get("/books", params={"q": f"nomatch-{uuid.uuid4().hex}"})
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_get_unknown_book_is_404_in_uniform_body(client):
    response = client.get("/books/999999999")
    assert response.status_code == 404
    assert _error_payload(response.json())["code"] == "not_found"


def test_put_keeps_copies_available_invariant(client, api_key):
    created = client.post(
        "/books", json=_book_payload(copies_total=2), headers=_auth(api_key)
    ).json()

    response = client.put(
        f"/books/{created['id']}", json={"copies_total": 5}, headers=_auth(api_key)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["copies_total"] == 5
    assert body["copies_available"] == 5

    fetched = client.get(f"/books/{created['id']}").json()
    assert fetched["copies_available"] == 5


def test_put_below_open_loans_is_conflict_and_row_unchanged(client, session, api_key):
    book_id, _ = _seed_loan(session, copies_total=3, open_loans=2)

    response = client.put(f"/books/{book_id}", json={"copies_total": 1}, headers=_auth(api_key))
    assert response.status_code == 409
    assert _error_payload(response.json())["code"] == "conflict"

    fetched = client.get(f"/books/{book_id}").json()
    assert fetched["copies_total"] == 3
    assert fetched["copies_available"] == 1


def test_put_duplicate_isbn_is_conflict(client, api_key):
    first = client.post("/books", json=_book_payload(), headers=_auth(api_key)).json()
    second = client.post("/books", json=_book_payload(), headers=_auth(api_key)).json()

    response = client.put(
        f"/books/{second['id']}", json={"isbn": first["isbn"]}, headers=_auth(api_key)
    )
    assert response.status_code == 409
    assert _error_payload(response.json())["code"] == "conflict"


def test_delete_with_referencing_loan_is_conflict(client, session, api_key):
    book_id, _ = _seed_loan(session, copies_total=1, open_loans=1)

    response = client.delete(f"/books/{book_id}", headers=_auth(api_key))
    assert response.status_code == 409
    assert _error_payload(response.json())["code"] == "conflict"

    assert client.get(f"/books/{book_id}").status_code == 200


def test_delete_without_loan_succeeds(client, api_key):
    created = client.post("/books", json=_book_payload(), headers=_auth(api_key)).json()

    response = client.delete(f"/books/{created['id']}", headers=_auth(api_key))
    assert response.status_code == 200
    assert response.json() == {"id": created["id"]}

    assert client.get(f"/books/{created['id']}").status_code == 404


def test_write_without_api_key_is_unauthorized(client, api_key):
    created = client.post("/books", json=_book_payload(), headers=_auth(api_key)).json()

    assert client.post("/books", json=_book_payload()).status_code == 401
    assert client.put(f"/books/{created['id']}", json={"year": 1998}).status_code == 401
    assert client.delete(f"/books/{created['id']}").status_code == 401

    bad = {"X-API-Key": "definitely-wrong"}
    assert client.post("/books", json=_book_payload(), headers=bad).status_code == 401


def test_get_routes_are_open(client, api_key):
    created = client.post("/books", json=_book_payload(), headers=_auth(api_key)).json()

    assert client.get("/books").status_code == 200
    assert client.get(f"/books/{created['id']}").status_code == 200
