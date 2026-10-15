"""SQLAlchemy 2.0 engine, session factory and schema bootstrap."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_db_path


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model."""


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Return the process-wide engine, created lazily on first use."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            f"sqlite:///{get_db_path()}",
            connect_args={"check_same_thread": False},
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return the session factory bound to the engine."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            expire_on_commit=False,
        )
    return _session_factory


def init_db() -> None:
    """Create every table declared by the ORM models."""
    from app import models  # noqa: F401  (registers the models on Base.metadata)

    Base.metadata.create_all(bind=get_engine())


def get_db() -> Iterator[Session]:
    """Yield exactly one session per request and always close it."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
