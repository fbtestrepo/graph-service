from __future__ import annotations

from http import HTTPStatus
from typing import cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.exceptions.authentication_failed import AuthenticationFailed
from src.core.exceptions.authorization_denied import AuthorizationDenied
from src.core.exceptions.circular_dependency_detected import CircularDependencyDetected
from src.core.exceptions.component_not_found import ComponentNotFound
from src.core.exceptions.duplicate_dependency_edge import DuplicateDependencyEdge
from src.infrastructure.errors.mappers import map_domain_exception
from src.infrastructure.errors.problem_details import problem_details_response


def domain_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    mapping = map_domain_exception(exc)
    if mapping is None:
        return problem_details_response(
            status=500,
            title="Internal Server Error",
            detail="An unexpected error occurred.",
            error_code="internal_error",
        )

    return problem_details_response(
        status=mapping.status,
        title=mapping.title,
        detail=str(exc),
        error_code=mapping.error_code,
    )


def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    title = "HTTP Error"
    try:
        title = HTTPStatus(exc.status_code).phrase
    except ValueError:
        pass

    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return problem_details_response(
        status=exc.status_code,
        title=title,
        detail=detail,
    )


def unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return problem_details_response(
        status=500,
        title="Internal Server Error",
        detail="An unexpected error occurred.",
        error_code="internal_error",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ComponentNotFound, cast(object, domain_exception_handler))
    app.add_exception_handler(DuplicateDependencyEdge, cast(object, domain_exception_handler))
    app.add_exception_handler(CircularDependencyDetected, cast(object, domain_exception_handler))
    app.add_exception_handler(AuthenticationFailed, cast(object, domain_exception_handler))
    app.add_exception_handler(AuthorizationDenied, cast(object, domain_exception_handler))

    app.add_exception_handler(StarletteHTTPException, cast(object, http_exception_handler))
    app.add_exception_handler(Exception, cast(object, unhandled_exception_handler))
