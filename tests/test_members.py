"""Tests for member CRUD: creation, pagination, updates and the delete guard.

These tests use the shared ``client``, ``session`` and ``api_key`` fixtures. The
test database is the temporary file set up by ``tests/__init__.py``; nothing here
touches the development database or starts a server.
"""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.models import Book, Loan, Member


def _unique_email() -> str:
    return f"member-{uuid.uuid4().hex}@example.com"


def _member_payload(**overrides: object) -> dict:
    payload: dict = {"name": "Ada Lovelace", "email": _unique_email()}
    payload.update(overrides)
    return payload


def _error_payload(body: dict) -> dict:
    assert set(body.keys()) == {"error"}
    error = body["error"]
    assert set(error.keys()) == {"code", "message", "details"}
    return error


def _create_member(client, api_key, **overrides: object) -> dict:
    response = client.post(
        "/members", json=_member_payload(**overrides), headers={"X-API-Key": api_key}
    )
    assert response.status_code == 201
    return response.json()


def _seed_book(session) -> Book:
    book = Book(
        title="The Pragmatic Programmer",
        author="Andrew Hunt",
        isbn=f"isbn-{uuid.uuid4().hex}",
        year=1999,
        copies_total=1,
    )
    session.add(book)
    session.commit()
    return book


def _seed_loan(session, member_id: int, *, returned: bool) -> Loan:
    book = _seed_book(session)
    now = datetime.now(UTC).replace(tzinfo=None)
    loan = Loan(
        book_id=book.id,
        member_id=member_id,
        loaned_at=now - timedelta(days=20),
        due_at=now - timedelta(days=6),
        returned_at=now - timedelta(days=3) if returned else None,
    )
    session.add(loan)
    session.commit()
    return loan


def test_create_member_defaults_member_since_to_today(client, api_key):
    payload = _member_payload()
    response = client.post("/members", json=payload, headers={"X-API-Key": api_key})
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert body["name"] == payload["name"]
    assert body["email"] == payload["email"]
    assert body["member_since"] == datetime.now(UTC).date().isoformat()


def test_create_member_keeps_explicit_member_since(client, api_key):
    payload = _member_payload(member_since="2020-01-02")
    response = client.post("/members", json=payload, headers={"X-API-Key": api_key})
    assert response.status_code == 201
    assert response.json()["member_since"] == "2020-01-02"


def test_duplicate_email_is_conflict_and_does_not_add_row(client, session, api_key):
    email = _unique_email()
    _create_member(client, api_key, email=email)
    before = session.scalar(select(func.count()).select_from(Member))

    response = client.post(
        "/members",
        json={"name": "Someone Else", "email": email},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 409
    assert _error_payload(response.json())["code"] == "conflict"

    after = session.scalar(select(func.count()).select_from(Member))
    assert after == before


def test_invalid_email_is_validation_error(client, api_key):
    response = client.post(
        "/members",
        json={"name": "Grace Hopper", "email": "not-an-email"},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 422
    error = _error_payload(response.json())
    assert error["code"] == "validation_error"
    assert error["details"]


def test_list_members_returns_page(client, api_key):
    created = _create_member(client, api_key)
    response = client.get("/members", params={"limit": 5, "offset": 0})
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"items", "total", "limit", "offset"}
    assert body["limit"] == 5
    assert body["offset"] == 0
    assert body["total"] >= 1
    assert any(item["id"] == created["id"] for item in body["items"])


def test_list_members_respects_limit_and_offset(client, api_key):
    _create_member(client, api_key)
    _create_member(client, api_key)
    everything = client.get("/members", params={"limit": 100, "offset": 0}).json()
    ids = [item["id"] for item in everything["items"]]
    assert len(ids) >= 2
    assert everything["total"] == len(ids)

    first_page = client.get("/members", params={"limit": 1, "offset": 0}).json()
    second_page = client.get("/members", params={"limit": 1, "offset": 1}).json()
    assert [item["id"] for item in first_page["items"]] == [ids[0]]
    assert [item["id"] for item in second_page["items"]] == [ids[1]]
    assert first_page["limit"] == 1
    assert second_page["offset"] == 1


def test_get_member_by_id(client, api_key):
    created = _create_member(client, api_key)
    response = client.get(f"/members/{created['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["name"] == created["name"]
    assert body["email"] == created["email"]


def test_unknown_member_id_is_not_found(client):
    response = client.get("/members/999999999")
    assert response.status_code == 404
    assert _error_payload(response.json())["code"] == "not_found"


def test_update_member_changes_fields(client, api_key):
    created = _create_member(client, api_key)
    response = client.put(
        f"/members/{created['id']}",
        json={"name": "Updated Name"},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Updated Name"
    assert body["email"] == created["email"]
    assert body["member_since"] == created["member_since"]


def test_update_unknown_member_is_not_found(client, api_key):
    response = client.put(
        "/members/999999999",
        json={"name": "Nobody"},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 404
    assert _error_payload(response.json())["code"] == "not_found"


def test_update_member_rejects_taken_email(client, api_key):
    first = _create_member(client, api_key)
    second = _create_member(client, api_key)
    response = client.put(
        f"/members/{second['id']}",
        json={"email": first["email"]},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 409
    assert _error_payload(response.json())["code"] == "conflict"


def test_update_member_explicit_null_is_validation_error(client, api_key):
    created = _create_member(client, api_key)
    for field in ("name", "email"):
        response = client.put(
            f"/members/{created['id']}",
            json={field: None},
            headers={"X-API-Key": api_key},
        )
        assert response.status_code == 422, field
        error = _error_payload(response.json())
        assert error["code"] == "validation_error"
        assert error["details"]


def test_delete_member_with_open_loan_is_conflict(client, session, api_key):
    created = _create_member(client, api_key)
    _seed_loan(session, created["id"], returned=False)
    response = client.delete(f"/members/{created['id']}", headers={"X-API-Key": api_key})
    assert response.status_code == 409
    assert _error_payload(response.json())["code"] == "conflict"


def test_delete_member_with_returned_loan_is_conflict(client, session, api_key):
    created = _create_member(client, api_key)
    _seed_loan(session, created["id"], returned=True)
    response = client.delete(f"/members/{created['id']}", headers={"X-API-Key": api_key})
    assert response.status_code == 409
    assert _error_payload(response.json())["code"] == "conflict"


def test_delete_member_without_loan_succeeds(client, api_key):
    created = _create_member(client, api_key)
    response = client.delete(f"/members/{created['id']}", headers={"X-API-Key": api_key})
    assert response.status_code == 200
    assert response.json() == {"id": created["id"]}
    assert client.get(f"/members/{created['id']}").status_code == 404


def test_delete_unknown_member_is_not_found(client, api_key):
    response = client.delete("/members/999999999", headers={"X-API-Key": api_key})
    assert response.status_code == 404
    assert _error_payload(response.json())["code"] == "not_found"


def test_write_endpoints_require_api_key(client):
    payload = {"name": "No Key", "email": _unique_email()}
    post = client.post("/members", json=payload)
    assert post.status_code == 401
    assert _error_payload(post.json())["code"] == "unauthorized"

    put = client.put("/members/1", json={"name": "x"})
    assert put.status_code == 401
    assert _error_payload(put.json())["code"] == "unauthorized"

    delete = client.delete("/members/1")
    assert delete.status_code == 401
    assert _error_payload(delete.json())["code"] == "unauthorized"


def test_get_members_is_reachable_without_api_key(client):
    response = client.get("/members")
    assert response.status_code == 200
    assert set(response.json().keys()) == {"items", "total", "limit", "offset"}
