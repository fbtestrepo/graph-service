from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from src.adapters.inbound.api.dependencies.wiring import (
    get_application_architecture_repository,
    get_micro_affinity_group_repository,
)
from src.adapters.inbound.api.schemas.micro_affinity_group import MicroAffinityGroup
from src.core.ports.application_architecture_repository import ApplicationArchitectureRepository
from src.core.ports.micro_affinity_group_repository import MicroAffinityGroupRepository
from src.core.use_cases.upsert_micro_affinity_group import UpsertMicroAffinityGroup


router = APIRouter(prefix="/micro-affinity-groups", tags=["micro-affinity-groups"])


@router.post(
    "",
    response_model=MicroAffinityGroup,
    response_model_exclude_none=True,
    response_model_exclude_defaults=True,
)
def upsert_micro_affinity_group(
    payload: MicroAffinityGroup,
    response: Response,
    application_architecture_repository: ApplicationArchitectureRepository = Depends(
        get_application_architecture_repository
    ),
    micro_affinity_group_repository: MicroAffinityGroupRepository = Depends(
        get_micro_affinity_group_repository
    ),
) -> MicroAffinityGroup:
    use_case = UpsertMicroAffinityGroup(
        application_architecture_repository=application_architecture_repository,
        micro_affinity_group_repository=micro_affinity_group_repository,
    )
    result = use_case.execute(
        payload.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_defaults=True,
            mode="json",
        )
    )
    response.status_code = status.HTTP_201_CREATED if result.created else status.HTTP_200_OK
    return MicroAffinityGroup.model_validate(result.payload)