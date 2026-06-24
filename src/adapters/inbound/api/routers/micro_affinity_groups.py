from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi import Query

from src.adapters.inbound.api.dependencies.wiring import (
    get_application_architecture_repository,
    get_micro_affinity_group_deployment_scope_clock,
    get_micro_affinity_group_repository,
    get_micro_affinity_group_processed_repository,
    get_transaction_manager,
)
from src.adapters.inbound.api.schemas.micro_affinity_group import MicroAffinityGroup
from src.adapters.inbound.api.schemas.micro_affinity_group_deployment_scope import (
    MicroAffinityGroupDeploymentScope,
)
from src.adapters.inbound.api.schemas.micro_affinity_group_processed import (
    MicroAffinityGroupProcessed,
)
from src.adapters.inbound.api.schemas.workload_test_scope import (
    WorkloadTestScopeRequest,
    WorkloadTestScopeResponse,
)
from src.core.domain.micro_affinity_group_relationship_mapper import (
    MicroAffinityGroupRelationshipMapper,
)
from src.core.use_cases.get_workload_test_scope import GetWorkloadTestScope
from src.core.ports.application_architecture_repository import ApplicationArchitectureRepository
from src.core.ports.micro_affinity_group_repository import MicroAffinityGroupRepository
from src.core.ports.micro_affinity_group_processed_repository import (
    MicroAffinityGroupProcessedRepository,
)
from src.core.ports.transaction_manager import TransactionManager
from src.core.use_cases.get_micro_affinity_group_deployment_scope import (
    GetMicroAffinityGroupDeploymentScope,
)
from src.core.use_cases.upsert_micro_affinity_group import UpsertMicroAffinityGroup


router = APIRouter(prefix="/micro-affinity-groups", tags=["micro-affinity-groups"])


@router.post(
    "",
    response_model=MicroAffinityGroupProcessed,
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
    micro_affinity_group_processed_repository: MicroAffinityGroupProcessedRepository = Depends(
        get_micro_affinity_group_processed_repository
    ),
    transaction_manager: TransactionManager = Depends(get_transaction_manager),
) -> MicroAffinityGroupProcessed:
    use_case = UpsertMicroAffinityGroup(
        application_architecture_repository=application_architecture_repository,
        micro_affinity_group_repository=micro_affinity_group_repository,
        micro_affinity_group_processed_repository=micro_affinity_group_processed_repository,
        transaction_manager=transaction_manager,
        relationship_mapper=MicroAffinityGroupRelationshipMapper(),
    )
    result = use_case.execute(
        payload.model_dump(
            exclude_none=True,
            exclude_defaults=True,
            mode="json",
        )
    )
    response.status_code = status.HTTP_201_CREATED if result.created else status.HTTP_200_OK
    return MicroAffinityGroupProcessed.model_validate(result.payload)


@router.get(
    "/{id}/deployment-scope",
    response_model=MicroAffinityGroupDeploymentScope,
    response_model_exclude_none=True,
)
def get_micro_affinity_group_deployment_scope(
    id: str,
    environment: str,
    micro_affinity_group_processed_repository: MicroAffinityGroupProcessedRepository = Depends(
        get_micro_affinity_group_processed_repository
    ),
    now_provider=Depends(get_micro_affinity_group_deployment_scope_clock),
) -> MicroAffinityGroupDeploymentScope:
    use_case = GetMicroAffinityGroupDeploymentScope(
        micro_affinity_group_processed_repository=micro_affinity_group_processed_repository,
        now_provider=now_provider,
    )
    payload = use_case.execute(micro_ag_id=id, environment=environment)
    return MicroAffinityGroupDeploymentScope.model_validate(payload)


@router.post(
    "/workloads/test-scope",
    response_model=WorkloadTestScopeResponse,
    response_model_exclude_none=True,
)
def get_workload_test_scope(
    payload: WorkloadTestScopeRequest,
    environment: Annotated[str, Query(min_length=1, pattern=r".*\S.*")],
    micro_affinity_group_processed_repository: MicroAffinityGroupProcessedRepository = Depends(
        get_micro_affinity_group_processed_repository
    ),
    now_provider=Depends(get_micro_affinity_group_deployment_scope_clock),
) -> WorkloadTestScopeResponse:
    use_case = GetWorkloadTestScope(
        micro_affinity_group_processed_repository=micro_affinity_group_processed_repository,
        now_provider=now_provider,
    )
    result = use_case.execute(
        environment=environment,
        changed_asset_ids=[item.workload_asset_id for item in payload.changed_workloads],
    )
    return WorkloadTestScopeResponse.model_validate(result)