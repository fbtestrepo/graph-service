from __future__ import annotations

from dataclasses import dataclass

from src.core.exceptions.authentication_failed import AuthenticationFailed
from src.core.exceptions.authorization_denied import AuthorizationDenied
from src.core.exceptions.circular_dependency_detected import CircularDependencyDetected
from src.core.exceptions.component_not_found import ComponentNotFound
from src.core.exceptions.duplicate_dependency_edge import DuplicateDependencyEdge


@dataclass(frozen=True, slots=True)
class DomainErrorMapping:
    status: int
    title: str
    error_code: str


_MAPPINGS: dict[type[Exception], DomainErrorMapping] = {
    ComponentNotFound: DomainErrorMapping(status=404, title="Not Found", error_code="component_not_found"),
    DuplicateDependencyEdge: DomainErrorMapping(status=409, title="Conflict", error_code="duplicate_dependency_edge"),
    CircularDependencyDetected: DomainErrorMapping(
        status=409,
        title="Conflict",
        error_code="circular_dependency_detected",
    ),
    AuthenticationFailed: DomainErrorMapping(status=401, title="Unauthorized", error_code="authentication_failed"),
    AuthorizationDenied: DomainErrorMapping(status=403, title="Forbidden", error_code="authorization_denied"),
}


def map_domain_exception(exc: Exception) -> DomainErrorMapping | None:
    for exc_type, mapping in _MAPPINGS.items():
        if isinstance(exc, exc_type):
            return mapping
    return None
