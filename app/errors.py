"""The uniform error contract: one body shape for every failure."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class LibraryError(Exception):
    """The only error the service layer raises."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: list[Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


_STATUS_CODE_MAP = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
    500: "internal_error",
    501: "not_implemented",
}


def error_body(code: str, message: str, details: list[Any] | None = None) -> dict[str, Any]:
    """Build the one error body every failure renders."""
    return {"error": {"code": code, "message": message, "details": details}}


async def library_error_handler(_request: Request, exc: LibraryError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.code, exc.message, exc.details),
    )


async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_body(
            "validation_error",
            "Request validation failed.",
            jsonable_encoder(exc.errors()),
        ),
    )


async def http_error_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _STATUS_CODE_MAP.get(exc.status_code, "error")
    message = exc.detail if isinstance(exc.detail, str) else "HTTP error."
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(code, message),
        headers=getattr(exc, "headers", None),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach every handler that renders the uniform error body."""
    app.add_exception_handler(LibraryError, library_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
