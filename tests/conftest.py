"""Shared pytest fixtures: test client, direct session and the API key."""

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models
from app.db import Base, SessionLocal, engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _create_schema() -> Iterator[None]:
    """Make sure the ORM mappers are registered and the tables exist."""
    _ = models.Book
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def api_key() -> str:
    return os.environ["LIBRARY_API_KEY"]


@pytest.fixture
def session() -> Iterator[Session]:
    """A direct session on the test database, for seeding without the API."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A TestClient whose context manager runs the app's real lifespan."""
    with TestClient(app) as test_client:
        yield test_client
