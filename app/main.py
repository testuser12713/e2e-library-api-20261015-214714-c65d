"""FastAPI application entry point: wiring, startup and the health route."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import get_settings
from .db import init_db
from .errors import register_exception_handlers
from .routers import books, loans, members, overdue, returns


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Validate configuration and create the schema before serving."""
    get_settings()
    init_db()
    yield


app = FastAPI(
    title="Stadtbibliothek Ausleih-API",
    version="0.1.0",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(books.router)
app.include_router(members.router)
app.include_router(loans.router)
app.include_router(returns.router)
app.include_router(overdue.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe that needs no API key."""
    return {"status": "ok"}
