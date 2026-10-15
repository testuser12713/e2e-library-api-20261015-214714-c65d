"""Shared fixtures for the library API tests.

The environment is configured BEFORE any application module is imported: the
API key and a temporary database path must be in place before ``app.main`` is
loaded, so the imports happen lazily inside the fixtures below.
"""

from __future__ import annotations

import os
import tempfile

os.environ.setdefault("LIBRARY_API_KEY", "test-api-key")
os.environ["LIBRARY_DB_PATH"] = os.path.join(
    tempfile.mkdtemp(prefix="library-api-tests-"),
    "test_library.db",
)

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def _create_schema() -> None:
    from app.db import init_db

    init_db()
    yield


@pytest.fixture(autouse=True)
def _clean_tables(_create_schema: None) -> None:
    from app.db import Base, get_engine

    engine = get_engine()
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
    yield


@pytest.fixture()
def api_key() -> str:
    return os.environ["LIBRARY_API_KEY"]


@pytest.fixture()
def client() -> TestClient:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def session():
    from app.db import get_session_factory

    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
