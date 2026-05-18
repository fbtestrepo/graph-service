from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from src.core.domain.micro_affinity_group_deployment_graph import (
    MicroAffinityGroupEdge,
    build_deployment_steps,
    reduce_cyclic_edges,
)
from src.core.exceptions.micro_affinity_group_graph_resolution_error import (
    MicroAffinityGroupGraphResolutionError,
)
from src.core.exceptions.micro_affinity_group_not_found import MicroAffinityGroupNotFound
from src.core.ports.micro_affinity_group_processed_repository import (
    MicroAffinityGroupProcessedPayload,
    MicroAffinityGroupProcessedRepository,
)


_MAX_DOWNSTREAM_HOPS = 30


@dataclass(frozen=True, slots=True)
class _ResolvedRelationship:
    destination_asset_id: str


@dataclass(frozen=True, slots=True)
class _ResolvedProcessedMicroAffinityGroup:
    micro_ag_id: str
    environment: str
    workload_asset_ids: frozenset[str]
    relationships: tuple[_ResolvedRelationship, ...]


@dataclass(frozen=True, slots=True)
class GetMicroAffinityGroupDeploymentScope:
    micro_affinity_group_processed_repository: MicroAffinityGroupProcessedRepository
    now_provider: Callable[[], datetime]

    def execute(self, micro_ag_id: str, environment: str) -> dict[str, Any]:
        document_cache: dict[tuple[str, str], _ResolvedProcessedMicroAffinityGroup] = {}

        root_payload = self.micro_affinity_group_processed_repository.get_by_identity(
            micro_ag_id=micro_ag_id,
            environment=environment,
        )
        if root_payload is None:
            raise MicroAffinityGroupNotFound(micro_ag_id=micro_ag_id, environment=environment)

        root_document = self._normalize_document(
            root_payload,
            expected_environment=environment,
            document_cache=document_cache,
            context="root processed MAG",
        )

        in_scope_nodes: set[str] = {root_document.micro_ag_id}
        dependency_edges = self._resolve_upstream_edges(
            root_document=root_document,
            environment=environment,
            document_cache=document_cache,
            in_scope_nodes=in_scope_nodes,
        )
        dependency_edges |= self._resolve_downstream_edges(
            root_document=root_document,
            environment=environment,
            document_cache=document_cache,
            in_scope_nodes=in_scope_nodes,
        )

        reduced_edges, bypassed_edges = reduce_cyclic_edges(dependency_edges)
        try:
            deployment_steps = build_deployment_steps(in_scope_nodes, reduced_edges)
        except ValueError as exc:
            raise MicroAffinityGroupGraphResolutionError(str(exc)) from exc

        bypassed_edge_set = set(bypassed_edges)
        return {
            "micro_ag_id": root_document.micro_ag_id,
            "environment": environment,
            "effective_date": self._format_effective_date(),
            "graph_has_cycles": bool(bypassed_edges),
            "dependency_graph": [
                {
                    **{
                        "source_micro_ag_id": edge.source_micro_ag_id,
                        "destination_micro_ag_id": edge.destination_micro_ag_id,
                    },
                    **({"is_cyclic": True} if edge in bypassed_edge_set else {}),
                }
                for edge in sorted(
                    dependency_edges,
                    key=lambda edge: (
                        edge in bypassed_edge_set,
                        edge.sort_key(),
                    ),
                )
            ],
            "deployment_sequence": {
                "bypassed_edges": [
                    {
                        "source_micro_ag_id": edge.source_micro_ag_id,
                        "destination_micro_ag_id": edge.destination_micro_ag_id,
                    }
                    for edge in bypassed_edges
                ],
                "steps": [
                    {
                        "step_index": step_index,
                        "micro_ag_ids": step_nodes,
                    }
                    for step_index, step_nodes in enumerate(deployment_steps, start=1)
                ],
            },
        }

    def _resolve_upstream_edges(
        self,
        *,
        root_document: _ResolvedProcessedMicroAffinityGroup,
        environment: str,
        document_cache: dict[tuple[str, str], _ResolvedProcessedMicroAffinityGroup],
        in_scope_nodes: set[str],
    ) -> set[MicroAffinityGroupEdge]:
        root_asset_ids = sorted(root_document.workload_asset_ids)
        if not root_asset_ids:
            return set()

        candidate_payloads = self.micro_affinity_group_processed_repository.list_by_relationship_destination_asset_ids(
            asset_ids=root_asset_ids,
            environment=environment,
        )

        upstream_edges: set[MicroAffinityGroupEdge] = set()
        for payload in candidate_payloads:
            candidate_document = self._normalize_document(
                payload,
                expected_environment=environment,
                document_cache=document_cache,
                context="upstream processed MAG",
            )
            if candidate_document.micro_ag_id == root_document.micro_ag_id:
                continue

            if any(
                relationship.destination_asset_id in root_document.workload_asset_ids
                for relationship in candidate_document.relationships
            ):
                upstream_edges.add(
                    MicroAffinityGroupEdge(
                        source_micro_ag_id=candidate_document.micro_ag_id,
                        destination_micro_ag_id=root_document.micro_ag_id,
                    )
                )
                in_scope_nodes.add(candidate_document.micro_ag_id)

        return upstream_edges

    def _resolve_downstream_edges(
        self,
        *,
        root_document: _ResolvedProcessedMicroAffinityGroup,
        environment: str,
        document_cache: dict[tuple[str, str], _ResolvedProcessedMicroAffinityGroup],
        in_scope_nodes: set[str],
    ) -> set[MicroAffinityGroupEdge]:
        downstream_edges: set[MicroAffinityGroupEdge] = set()
        downstream_depths: dict[str, int] = {root_document.micro_ag_id: 0}
        frontier_documents = [root_document]

        for depth in range(_MAX_DOWNSTREAM_HOPS):
            if not frontier_documents:
                break

            requested_asset_ids = sorted(
                {
                    relationship.destination_asset_id
                    for document in frontier_documents
                    for relationship in document.relationships
                }
            )
            if not requested_asset_ids:
                frontier_documents = []
                continue

            owner_payloads = self.micro_affinity_group_processed_repository.list_by_workload_asset_ids(
                asset_ids=requested_asset_ids,
                environment=environment,
            )
            owner_documents = [
                self._normalize_document(
                    payload,
                    expected_environment=environment,
                    document_cache=document_cache,
                    context="downstream processed MAG",
                )
                for payload in owner_payloads
            ]
            owner_map = self._build_owner_map(requested_asset_ids, owner_documents)

            next_frontier: list[_ResolvedProcessedMicroAffinityGroup] = []
            for document in frontier_documents:
                for relationship in document.relationships:
                    owner_document = self._resolve_unique_owner(
                        owner_map=owner_map,
                        asset_id=relationship.destination_asset_id,
                        source_micro_ag_id=document.micro_ag_id,
                    )
                    if owner_document.micro_ag_id == document.micro_ag_id:
                        continue

                    downstream_edges.add(
                        MicroAffinityGroupEdge(
                            source_micro_ag_id=document.micro_ag_id,
                            destination_micro_ag_id=owner_document.micro_ag_id,
                        )
                    )

                    if owner_document.micro_ag_id in downstream_depths:
                        continue

                    downstream_depths[owner_document.micro_ag_id] = depth + 1
                    in_scope_nodes.add(owner_document.micro_ag_id)
                    next_frontier.append(owner_document)

            frontier_documents = next_frontier

        boundary_documents = [
            document_cache[(micro_ag_id, environment)]
            for micro_ag_id, depth in downstream_depths.items()
            if depth == _MAX_DOWNSTREAM_HOPS
        ]
        downstream_edges |= self._resolve_boundary_cycle_edges(
            boundary_documents=boundary_documents,
            environment=environment,
            document_cache=document_cache,
            in_scope_nodes=in_scope_nodes,
        )

        return downstream_edges

    def _resolve_boundary_cycle_edges(
        self,
        *,
        boundary_documents: list[_ResolvedProcessedMicroAffinityGroup],
        environment: str,
        document_cache: dict[tuple[str, str], _ResolvedProcessedMicroAffinityGroup],
        in_scope_nodes: set[str],
    ) -> set[MicroAffinityGroupEdge]:
        if not boundary_documents:
            return set()

        in_scope_documents = [
            document
            for (micro_ag_id, cached_environment), document in document_cache.items()
            if cached_environment == environment and micro_ag_id in in_scope_nodes
        ]
        owner_map = self._build_owner_map(
            asset_ids=sorted(
                {
                    relationship.destination_asset_id
                    for document in boundary_documents
                    for relationship in document.relationships
                }
            ),
            documents=in_scope_documents,
        )

        boundary_edges: set[MicroAffinityGroupEdge] = set()
        for document in boundary_documents:
            for relationship in document.relationships:
                owners = owner_map.get(relationship.destination_asset_id, ())
                if not owners:
                    continue
                if len(owners) != 1:
                    raise MicroAffinityGroupGraphResolutionError(
                        "Ambiguous in-scope ownership match while evaluating boundary cycle edges "
                        f"for destination asset_id={relationship.destination_asset_id!r}"
                    )

                owner_document = owners[0]
                if owner_document.micro_ag_id == document.micro_ag_id:
                    continue
                boundary_edges.add(
                    MicroAffinityGroupEdge(
                        source_micro_ag_id=document.micro_ag_id,
                        destination_micro_ag_id=owner_document.micro_ag_id,
                    )
                )

        return boundary_edges

    def _build_owner_map(
        self,
        asset_ids: list[str],
        documents: list[_ResolvedProcessedMicroAffinityGroup],
    ) -> dict[str, tuple[_ResolvedProcessedMicroAffinityGroup, ...]]:
        requested_asset_ids = set(asset_ids)
        owner_map: dict[str, list[_ResolvedProcessedMicroAffinityGroup]] = defaultdict(list)

        for document in documents:
            for asset_id in document.workload_asset_ids & requested_asset_ids:
                owner_map[asset_id].append(document)

        return {asset_id: tuple(owner_map.get(asset_id, ())) for asset_id in asset_ids}

    def _resolve_unique_owner(
        self,
        *,
        owner_map: dict[str, tuple[_ResolvedProcessedMicroAffinityGroup, ...]],
        asset_id: str,
        source_micro_ag_id: str,
    ) -> _ResolvedProcessedMicroAffinityGroup:
        owners = owner_map.get(asset_id, ())
        if not owners:
            raise MicroAffinityGroupGraphResolutionError(
                "Missing workload ownership match for downstream destination asset_id="
                f"{asset_id!r} referenced from micro_ag_id={source_micro_ag_id!r}"
            )
        if len(owners) != 1:
            raise MicroAffinityGroupGraphResolutionError(
                "Ambiguous workload ownership match for downstream destination asset_id="
                f"{asset_id!r} referenced from micro_ag_id={source_micro_ag_id!r}"
            )
        return owners[0]

    def _normalize_document(
        self,
        payload: MicroAffinityGroupProcessedPayload,
        *,
        expected_environment: str,
        document_cache: dict[tuple[str, str], _ResolvedProcessedMicroAffinityGroup],
        context: str,
    ) -> _ResolvedProcessedMicroAffinityGroup:
        if not isinstance(payload, dict):
            raise MicroAffinityGroupGraphResolutionError(f"{context} payload must be an object")

        micro_ag_id = payload.get("micro_ag_id")
        environment = payload.get("environment")
        if not isinstance(micro_ag_id, str) or not micro_ag_id:
            raise MicroAffinityGroupGraphResolutionError(
                f"{context} must include a non-empty micro_ag_id"
            )
        if not isinstance(environment, str) or not environment:
            raise MicroAffinityGroupGraphResolutionError(
                f"{context} must include a non-empty environment"
            )
        if environment != expected_environment:
            raise MicroAffinityGroupGraphResolutionError(
                f"{context} environment mismatch for micro_ag_id={micro_ag_id!r}"
            )

        cache_key = (micro_ag_id, environment)
        cached_document = document_cache.get(cache_key)
        if cached_document is not None:
            return cached_document

        workloads = payload.get("workloads")
        if not isinstance(workloads, list) or not workloads:
            raise MicroAffinityGroupGraphResolutionError(
                f"{context} must include at least one workload"
            )

        workload_asset_ids: set[str] = set()
        for workload in workloads:
            if not isinstance(workload, dict):
                raise MicroAffinityGroupGraphResolutionError(
                    f"{context} workloads must contain objects"
                )
            asset_id = workload.get("asset_id")
            if not isinstance(asset_id, str) or not asset_id:
                raise MicroAffinityGroupGraphResolutionError(
                    f"{context} workloads must include non-empty asset_id values"
                )
            workload_asset_ids.add(asset_id)

        relationships_payload = payload.get("relationships")
        if not isinstance(relationships_payload, list):
            raise MicroAffinityGroupGraphResolutionError(
                f"{context} relationships must be a list"
            )

        relationships: list[_ResolvedRelationship] = []
        for relationship in relationships_payload:
            if not isinstance(relationship, dict):
                raise MicroAffinityGroupGraphResolutionError(
                    f"{context} relationships must contain objects"
                )
            source_workload = relationship.get("source_workload")
            destination_workload = relationship.get("destination_workload")
            if not isinstance(source_workload, dict) or not isinstance(destination_workload, dict):
                raise MicroAffinityGroupGraphResolutionError(
                    f"{context} relationship entries must include source_workload and destination_workload objects"
                )

            source_asset_id = source_workload.get("asset_id")
            destination_asset_id = destination_workload.get("asset_id")
            if not isinstance(source_asset_id, str) or not source_asset_id:
                raise MicroAffinityGroupGraphResolutionError(
                    f"{context} relationship source_workload.asset_id must be non-empty"
                )
            if source_asset_id not in workload_asset_ids:
                raise MicroAffinityGroupGraphResolutionError(
                    f"{context} relationship source_workload.asset_id={source_asset_id!r} is not owned by micro_ag_id={micro_ag_id!r}"
                )
            if not isinstance(destination_asset_id, str) or not destination_asset_id:
                raise MicroAffinityGroupGraphResolutionError(
                    f"{context} relationship destination_workload.asset_id must be non-empty"
                )

            relationships.append(
                _ResolvedRelationship(destination_asset_id=destination_asset_id)
            )

        normalized_document = _ResolvedProcessedMicroAffinityGroup(
            micro_ag_id=micro_ag_id,
            environment=environment,
            workload_asset_ids=frozenset(workload_asset_ids),
            relationships=tuple(relationships),
        )
        document_cache[cache_key] = normalized_document
        return normalized_document

    def _format_effective_date(self) -> str:
        current = self.now_provider()
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)
        return current.astimezone(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")