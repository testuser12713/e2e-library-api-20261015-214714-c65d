"""Application entry point: app, routers, error handlers, startup and /health."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_api_key, get_db_path
from app.db import init_db
from app.errors import register_error_handlers
from app.routers import books, loans, members, overdue, returns


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Validate the configuration once and create the schema on startup."""
    get_api_key()  # refuses to start and names the variable when it is missing
    get_db_path()
    init_db()
    yield


app = FastAPI(title="Library API", version="1.0.0", lifespan=lifespan)

register_error_handlers(app)

app.include_router(books.router)
app.include_router(members.router)
app.include_router(loans.router)
app.include_router(returns.router)
app.include_router(overdue.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Liveness probe — needs no API key."""
    return {"status": "ok"}
