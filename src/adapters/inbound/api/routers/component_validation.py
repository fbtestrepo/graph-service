from __future__ import annotations

from fastapi import APIRouter, Response, status

from src.adapters.inbound.api.schemas.component import Component


router = APIRouter(tags=["components"])


@router.post("/components/validate", status_code=status.HTTP_204_NO_CONTENT)
def validate_component(_component: Component) -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)
