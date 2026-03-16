from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from src.adapters.inbound.api.schemas.health_response import HealthResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="dependency-graph-service",
        version="dev",
        time=datetime.now(timezone.utc),
    )

