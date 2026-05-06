from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.exceptions.application_architecture_not_found import (
    ApplicationArchitectureNotFound,
)
from src.core.exceptions.micro_affinity_group_workload_mismatch import (
    MicroAffinityGroupWorkloadMismatch,
)
from src.core.ports.application_architecture_repository import ApplicationArchitectureRepository
from src.core.ports.micro_affinity_group_repository import MicroAffinityGroupRepository


@dataclass(frozen=True, slots=True)
class UpsertMicroAffinityGroupResult:
    created: bool
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class UpsertMicroAffinityGroup:
    application_architecture_repository: ApplicationArchitectureRepository
    micro_affinity_group_repository: MicroAffinityGroupRepository

    def execute(self, payload: dict[str, Any]) -> UpsertMicroAffinityGroupResult:
        asset_id = str(payload["parent-asset-id"])
        architecture_version = str(payload["architecture-version"])
        environment = str(payload["environment"])
        micro_ag_id = str(payload["micro-ag-id"])

        architecture = self.application_architecture_repository.get_by_asset_id_and_version(
            asset_id=asset_id,
            version=architecture_version,
        )
        if architecture is None:
            raise ApplicationArchitectureNotFound(asset_id=asset_id, version=architecture_version)

        self._validate_workloads(payload, architecture)

        created = self.micro_affinity_group_repository.upsert(
            micro_ag_id=micro_ag_id,
            environment=environment,
            architecture_version=architecture_version,
            payload=payload,
        )
        return UpsertMicroAffinityGroupResult(created=created, payload=payload)

    def _validate_workloads(
        self,
        payload: dict[str, Any],
        architecture: dict[str, Any],
    ) -> None:
        workloads = payload.get("workloads")
        nodes = architecture.get("nodes")

        if not isinstance(workloads, list) or not isinstance(nodes, list):
            raise MicroAffinityGroupWorkloadMismatch(
                "Application architecture payload is missing required nodes."
            )

        for workload in workloads:
            if not isinstance(workload, dict):
                raise MicroAffinityGroupWorkloadMismatch("Each workload must be an object.")

            workload_id = workload.get("id")
            workload_asset_id = workload.get("asset-id")
            if not isinstance(workload_id, str) or not isinstance(workload_asset_id, str):
                raise MicroAffinityGroupWorkloadMismatch(
                    "Each workload must include string id and asset-id values."
                )

            matching_nodes = [
                node
                for node in nodes
                if self._is_matching_service_node(node, workload_id)
            ]
            if not matching_nodes:
                raise MicroAffinityGroupWorkloadMismatch(
                    f"No matching service node found for workload id '{workload_id}'."
                )

            if not any(self._node_asset_id(node) == workload_asset_id for node in matching_nodes):
                raise MicroAffinityGroupWorkloadMismatch(
                    f"Workload asset-id '{workload_asset_id}' does not match any resolved service node metadata.asset-id for workload id '{workload_id}'."
                )

    def _is_matching_service_node(self, node: Any, workload_id: str) -> bool:
        if not isinstance(node, dict):
            return False

        if node.get("node-type") != "service":
            return False

        metadata = node.get("metadata")
        if not isinstance(metadata, dict):
            return False

        return metadata.get("code-repo") == workload_id

    def _node_asset_id(self, node: dict[str, Any]) -> str | None:
        metadata = node.get("metadata")
        if not isinstance(metadata, dict):
            return None
        asset_id = metadata.get("asset-id")
        return asset_id if isinstance(asset_id, str) else None