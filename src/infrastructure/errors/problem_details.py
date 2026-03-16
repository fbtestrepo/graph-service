from __future__ import annotations

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.adapters.inbound.api.schemas.problem_details import ProblemDetails


PROBLEM_JSON_MEDIA_TYPE = "application/problem+json"


def problem_details_response(
    *,
    status: int,
    title: str,
    detail: str,
    type: str = "about:blank",
    error_code: str | None = None,
    errors: dict[str, list[str]] | None = None,
) -> JSONResponse:
    problem = ProblemDetails(
        type=type,
        title=title,
        status=status,
        detail=detail,
        error_code=error_code,
        errors=errors,
    )
    return JSONResponse(
        status_code=status,
        content=jsonable_encoder(problem),
        media_type=PROBLEM_JSON_MEDIA_TYPE,
    )
