"""Map domain errors to HTTP status codes. Unexpected errors stay uncaught."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shoul_donation.domain.errors import (
    AuthenticationError,
    ConflictError,
    DomainError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)


def register_error_handlers(app: FastAPI) -> None:
    _register(app, AuthenticationError, 401)
    _register(app, ForbiddenError, 403)
    _register(app, NotFoundError, 404)
    _register(app, ConflictError, 409)
    _register(app, ValidationError, 422)


def _register(app: FastAPI, error_type: type[DomainError], status_code: int) -> None:
    def handler(_request: Request, error: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(error)})

    app.add_exception_handler(error_type, handler)
