"""Database engine, session factory and the per-request session dependency."""

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_db_path


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model."""


_engine: Engine | None = None


def get_engine() -> Engine:
    """Return the SQLAlchemy engine for the configured database.

    The engine is built from ``LIBRARY_DB_PATH`` the first time it is needed and
    reused afterwards, so a caller can dispose its connection pool and let the
    next use rebuild it without losing the data written to the SQLite file.
    """
    global _engine
    if _engine is None:
        _engine = create_engine(
            f"sqlite:///{get_db_path()}",
            connect_args={"check_same_thread": False},
        )
    return _engine


engine = get_engine()

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Create the schema if it does not exist yet."""
    from . import models  # noqa: F401  (import registers the mappers)

    Base.metadata.create_all(bind=engine)


def get_db() -> Iterator[Session]:
    """Yield one session per request and always close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
