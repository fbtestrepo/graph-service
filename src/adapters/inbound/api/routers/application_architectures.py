from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from src.adapters.inbound.api.dependencies.wiring import get_application_architecture_repository
from src.adapters.inbound.api.schemas.application_architecture import ApplicationArchitecture
from src.core.ports.application_architecture_repository import ApplicationArchitectureRepository
from src.core.use_cases.upsert_application_architecture import UpsertApplicationArchitecture


router = APIRouter(prefix="/application-architectures", tags=["application-architectures"])


@router.post(
    "",
    response_model=ApplicationArchitecture,
    response_model_exclude_none=True,
    response_model_exclude_defaults=True,
)
def upsert_application_architecture(
    payload: ApplicationArchitecture,
    response: Response,
    application_architecture_repository: ApplicationArchitectureRepository = Depends(
        get_application_architecture_repository
    ),
) -> ApplicationArchitecture:
    use_case = UpsertApplicationArchitecture(application_architecture_repository)
    result = use_case.execute(
        payload.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_defaults=True,
            mode="json",
        )
    )
    response.status_code = status.HTTP_201_CREATED if result.created else status.HTTP_200_OK
    return payload
