"""Shared pytest fixtures: a per-test database, test client and API key.

Every test runs against its own temporary SQLite file. The API key and the
database path are set before a fixture hands out a client or a session, the
schema is created for that file, and the engine is disposed and the file removed
when the test ends. No test can observe a row written by another test.
"""

from __future__ import annotations

import os
import secrets
import sys
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import db as db_module
from app import models
from app.db import Base
from app.main import app

API_KEY_ENV_VAR = "LIBRARY_API_KEY"
DB_PATH_ENV_VAR = "LIBRARY_DB_PATH"


def _rebind_imported_references(
    old_engine: Any, old_factory: Any, new_engine: Any, new_factory: Any
) -> None:
    """Repoint test modules that did ``from app.db import engine`` at the new ones.

    A per-test engine is a different object, so a test module that imported
    ``engine`` or ``SessionLocal`` by name at collection time would otherwise
    keep talking to the previous test's database.
    """
    for module in list(sys.modules.values()):
        name = getattr(module, "__name__", "")
        if not name.startswith("tests"):
            continue
        if getattr(module, "engine", None) is old_engine:
            module.engine = new_engine
        if getattr(module, "SessionLocal", None) is old_factory:
            module.SessionLocal = new_factory


@pytest.fixture(autouse=True)
def _isolated_database(tmp_path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Give the current test its own database file with a fresh schema."""
    monkeypatch.setenv(API_KEY_ENV_VAR, secrets.token_hex(32))
    db_path = tmp_path / "library-test.db"
    monkeypatch.setenv(DB_PATH_ENV_VAR, str(db_path))

    old_engine = db_module.engine
    old_factory = db_module.SessionLocal

    new_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    new_factory = sessionmaker(bind=new_engine, autoflush=False, expire_on_commit=False)

    db_module.engine = new_engine
    db_module.SessionLocal = new_factory
    db_module._engine = new_engine
    _rebind_imported_references(old_engine, old_factory, new_engine, new_factory)

    _ = models.Book
    Base.metadata.create_all(bind=new_engine)

    try:
        yield
    finally:
        db_module.engine = old_engine
        db_module.SessionLocal = old_factory
        db_module._engine = old_engine
        _rebind_imported_references(new_engine, new_factory, old_engine, old_factory)
        new_engine.dispose()
        db_path.unlink(missing_ok=True)


@pytest.fixture
def api_key(_isolated_database: None) -> str:
    """The API key the current test's app instance was configured with."""
    return os.environ[API_KEY_ENV_VAR]


@pytest.fixture
def session(_isolated_database: None) -> Iterator[Session]:
    """A direct session on the current test's isolated database."""
    db = db_module.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(_isolated_database: None) -> Iterator[TestClient]:
    """A TestClient whose context manager runs the app's real lifespan."""
    with TestClient(app) as test_client:
        yield test_client
