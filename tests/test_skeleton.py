"""Skeleton tests: the API starts, is wired, and enforces the shared contract.

These assert what holds both before and after every stub is filled: the routes
exist, the error envelope is uniform and the persisted data survives a restart.
They deliberately do NOT assert the 501 answer of a stub.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import ConfigError
from app.main import app

CONTRACT_PATHS = {
    "/books",
    "/books/{book_id}",
    "/members",
    "/members/{member_id}",
    "/loans",
    "/loans/{loan_id}/return",
    "/loans/overdue",
    "/health",
}


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_lists_every_contract_path(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    assert set(schema["paths"]) >= CONTRACT_PATHS


def test_post_books_without_key_is_unauthorized(client: TestClient) -> None:
    response = client.post(
        "/books",
        json={
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "isbn": "978-0132350884",
            "year": 2008,
            "copies_total": 1,
        },
    )
    assert response.status_code == 401
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "unauthorized"
    assert isinstance(body["error"]["message"], str)


def test_post_books_with_key_and_invalid_body_is_validation_error(
    client: TestClient,
    api_key: str,
) -> None:
    response = client.post(
        "/books",
        json={"title": "Missing everything else"},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert isinstance(error["details"], list)
    assert error["details"]


def test_startup_without_api_key_fails_naming_the_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LIBRARY_API_KEY", raising=False)
    with pytest.raises(ConfigError) as exc_info, TestClient(app):
        pass
    assert "LIBRARY_API_KEY" in str(exc_info.value)


def test_book_persists_across_engine_restart(session: Session) -> None:
    from app.db import get_engine, get_session_factory
    from app.models import Book

    book = Book(
        title="Persisted Title",
        author="Persisted Author",
        isbn="persist-0001",
        year=2020,
        copies_total=2,
    )
    session.add(book)
    session.commit()
    book_id = book.id

    get_engine().dispose()
    session.close()

    reopened = get_session_factory()()
    try:
        fetched = reopened.get(Book, book_id)
        assert fetched is not None
        assert fetched.title == "Persisted Title"
    finally:
        reopened.close()
