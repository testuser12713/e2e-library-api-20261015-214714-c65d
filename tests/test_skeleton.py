"""Tests of the running skeleton: wiring, uniform errors and persistence.

This file asserts only facts the skeleton itself guarantees. It never asserts the
501 body a not-yet-implemented route returns, because such an assertion would have
to fail the day that route is implemented.
"""

import pytest

from app.config import ConfigError, get_settings
from app.db import SessionLocal, engine
from app.models import Book

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


def _error_payload(body: dict) -> dict:
    assert set(body.keys()) == {"error"}
    error = body["error"]
    assert set(error.keys()) == {"code", "message", "details"}
    return error


def test_health_answers_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_lists_every_contract_path(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = set(response.json()["paths"].keys())
    assert paths >= CONTRACT_PATHS


def test_write_without_api_key_is_unauthorized(client):
    payload = {
        "title": "Effective Python",
        "author": "Brett Slatkin",
        "isbn": "978-0134853989",
        "year": 2019,
        "copies_total": 2,
    }
    response = client.post("/books", json=payload)
    assert response.status_code == 401
    error = _error_payload(response.json())
    assert error["code"] == "unauthorized"


def test_write_with_invalid_body_is_validation_error(client, api_key):
    response = client.post("/books", json={}, headers={"X-API-Key": api_key})
    assert response.status_code == 422
    error = _error_payload(response.json())
    assert error["code"] == "validation_error"
    assert error["details"]


def test_missing_api_key_names_the_variable(monkeypatch):
    monkeypatch.delenv("LIBRARY_API_KEY", raising=False)
    with pytest.raises(ConfigError) as excinfo:
        get_settings()
    assert "LIBRARY_API_KEY" in str(excinfo.value)


def test_book_survives_engine_restart(session):
    book = Book(
        title="Fluent Python",
        author="Luciano Ramalho",
        isbn="978-1492056355",
        year=2022,
        copies_total=3,
    )
    session.add(book)
    session.commit()
    book_id = book.id
    session.close()

    engine.dispose()

    with SessionLocal() as reopened:
        found = reopened.get(Book, book_id)
        assert found is not None
        assert found.isbn == "978-1492056355"
        assert found.copies_available == 3
