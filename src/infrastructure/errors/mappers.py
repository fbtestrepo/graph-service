from __future__ import annotations

from dataclasses import dataclass

from src.core.exceptions.application_architecture_not_found import ApplicationArchitectureNotFound
from src.core.exceptions.authentication_failed import AuthenticationFailed
from src.core.exceptions.authorization_denied import AuthorizationDenied
from src.core.exceptions.circular_dependency_detected import CircularDependencyDetected
from src.core.exceptions.component_not_found import ComponentNotFound
from src.core.exceptions.duplicate_dependency_edge import DuplicateDependencyEdge
from src.core.exceptions.duplicate_micro_affinity_group_identity import (
    DuplicateMicroAffinityGroupIdentity,
)
from src.core.exceptions.micro_affinity_group_graph_resolution_error import (
    MicroAffinityGroupGraphResolutionError,
)
from src.core.exceptions.micro_affinity_group_not_found import MicroAffinityGroupNotFound
from src.core.exceptions.micro_affinity_group_workload_mismatch import (
    MicroAffinityGroupWorkloadMismatch,
)
from src.core.exceptions.micro_affinity_group_relationship_resolution_error import (
    MicroAffinityGroupRelationshipResolutionError,
)


@dataclass(frozen=True, slots=True)
class DomainErrorMapping:
    status: int
    title: str
    error_code: str


_MAPPINGS: dict[type[Exception], DomainErrorMapping] = {
    ComponentNotFound: DomainErrorMapping(status=404, title="Not Found", error_code="component_not_found"),
    DuplicateDependencyEdge: DomainErrorMapping(status=409, title="Conflict", error_code="duplicate_dependency_edge"),
    DuplicateMicroAffinityGroupIdentity: DomainErrorMapping(
        status=409,
        title="Conflict",
        error_code="duplicate_micro_affinity_group_identity",
    ),
    MicroAffinityGroupNotFound: DomainErrorMapping(
        status=404,
        title="Not Found",
        error_code="micro_affinity_group_not_found",
    ),
    CircularDependencyDetected: DomainErrorMapping(
        status=409,
        title="Conflict",
        error_code="circular_dependency_detected",
    ),
    AuthenticationFailed: DomainErrorMapping(status=401, title="Unauthorized", error_code="authentication_failed"),
    AuthorizationDenied: DomainErrorMapping(status=403, title="Forbidden", error_code="authorization_denied"),
    ApplicationArchitectureNotFound: DomainErrorMapping(
        status=422,
        title="Unprocessable Entity",
        error_code="application_architecture_not_found",
    ),
    MicroAffinityGroupWorkloadMismatch: DomainErrorMapping(
        status=422,
        title="Unprocessable Entity",
        error_code="micro_affinity_group_workload_mismatch",
    ),
    MicroAffinityGroupRelationshipResolutionError: DomainErrorMapping(
        status=422,
        title="Unprocessable Entity",
        error_code="micro_affinity_group_relationship_resolution_error",
    ),
    MicroAffinityGroupGraphResolutionError: DomainErrorMapping(
        status=422,
        title="Unprocessable Entity",
        error_code="micro_affinity_group_graph_resolution_error",
    ),
}


def map_domain_exception(exc: Exception) -> DomainErrorMapping | None:
    for exc_type, mapping in _MAPPINGS.items():
        if isinstance(exc, exc_type):
            return mapping
    return None
