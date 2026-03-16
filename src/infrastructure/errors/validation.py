from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from src.infrastructure.errors.problem_details import PROBLEM_JSON_MEDIA_TYPE, problem_details_response


def _is_malformed_json_error(exc: RequestValidationError) -> bool:
    for error in exc.errors():
        error_type = error.get("type")
        if error_type in {"json_invalid", "value_error.jsondecode"}:
            return True
    return False


def _error_loc_to_key(loc: Any) -> str:
    if not isinstance(loc, (list, tuple)):
        return "body"

    parts = [str(part) for part in loc if part != "body"]
    if not parts:
        return "body"

    return ".".join(parts)


def _build_validation_errors(exc: RequestValidationError) -> dict[str, list[str]] | None:
    errors: defaultdict[str, list[str]] = defaultdict(list)
    for error in exc.errors():
        key = _error_loc_to_key(error.get("loc"))
        msg = error.get("msg") or "Invalid value"
        errors[key].append(msg)

    return dict(errors) if errors else None


def request_validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    if _is_malformed_json_error(exc):
        return problem_details_response(
            status=400,
            title="Malformed JSON",
            detail="Request body is not valid JSON.",
            error_code="invalid_json",
        )

    return problem_details_response(
        status=422,
        title="Validation Error",
        detail="Request payload failed validation.",
        error_code="validation_failed",
        errors=_build_validation_errors(exc),
    )


def register_validation_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)

