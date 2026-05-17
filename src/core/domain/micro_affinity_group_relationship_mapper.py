from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any

from src.core.exceptions.micro_affinity_group_relationship_resolution_error import (
    MicroAffinityGroupRelationshipResolutionError,
)


class MicroAffinityGroupRelationshipMapper:
    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    def transform(self, payload: dict[str, Any], architecture: dict[str, Any]) -> dict[str, Any]:
        workloads = payload.get("workloads")
        nodes = architecture.get("nodes")
        relationships = architecture.get("relationships")

        if not isinstance(workloads, list):
            raise MicroAffinityGroupRelationshipResolutionError(
                "Micro affinity group payload is missing required workloads."
            )
        if not isinstance(nodes, list):
            raise MicroAffinityGroupRelationshipResolutionError(
                "Application architecture payload is missing required nodes."
            )
        if not isinstance(relationships, list):
            raise MicroAffinityGroupRelationshipResolutionError(
                "Application architecture payload is missing required relationships."
            )

        transformed = deepcopy(payload)
        transformed["relationships"] = []

        for workload in workloads:
            if not isinstance(workload, dict):
                raise MicroAffinityGroupRelationshipResolutionError(
                    "Each workload must be an object."
                )

            source_node = self._resolve_source_node(workload, nodes)
            source_node_id = self._require_unique_id(source_node, workload)
            outgoing_relationships = self._find_outgoing_relationships(source_node_id, relationships)

            workload_id = self._require_string(workload.get("id"), "workload id")
            workload_asset_id = self._require_string(
                workload.get("asset_id"),
                "workload asset_id",
            )

            if not outgoing_relationships:
                self._logger.info(
                    "No outgoing relationships found for workload %s (%s)",
                    workload_id,
                    workload_asset_id,
                )
                continue

            for relationship in outgoing_relationships:
                destination_node_id = self._extract_destination_node_id(relationship, workload)
                destination_node = self._resolve_destination_node(destination_node_id, nodes, workload)

                source_workload = self._workload_from_node(source_node, workload)
                destination_workload = self._workload_from_node(destination_node, workload)
                transformed["relationships"].append(
                    {
                        "source_workload": source_workload,
                        "destination_workload": destination_workload,
                    }
                )
                self._logger.info(
                    "Resolved relationship %s (%s) -> %s (%s)",
                    source_workload["id"],
                    source_workload["asset_id"],
                    destination_workload["id"],
                    destination_workload["asset_id"],
                )

        return transformed

    def _resolve_source_node(
        self,
        workload: dict[str, Any],
        nodes: list[Any],
    ) -> dict[str, Any]:
        workload_id = self._require_string(workload.get("id"), "workload id")
        workload_asset_id = self._require_string(workload.get("asset_id"), "workload asset_id")

        for node in nodes:
            if not isinstance(node, dict):
                continue
            if node.get("node-type") != "service":
                continue

            metadata = node.get("metadata")
            if not isinstance(metadata, dict):
                continue

            if (
                metadata.get("code-repo") == workload_id
                and metadata.get("asset-id") == workload_asset_id
            ):
                return node

        raise MicroAffinityGroupRelationshipResolutionError(
            f"No matching source service node found for workload id '{workload_id}' and asset_id '{workload_asset_id}'."
        )

    def _resolve_destination_node(
        self,
        destination_node_id: str,
        nodes: list[Any],
        workload: dict[str, Any],
    ) -> dict[str, Any]:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if node.get("unique-id") != destination_node_id:
                continue
            if node.get("node-type") != "service":
                break

            metadata = node.get("metadata")
            if not isinstance(metadata, dict):
                break
            if isinstance(metadata.get("code-repo"), str) and isinstance(
                metadata.get("asset-id"), str
            ):
                return node
            break

        workload_id = self._require_string(workload.get("id"), "workload id")
        raise MicroAffinityGroupRelationshipResolutionError(
            f"Relationship for workload id '{workload_id}' references unresolved destination service node '{destination_node_id}'."
        )

    def _find_outgoing_relationships(
        self,
        source_node_id: str,
        relationships: list[Any],
    ) -> list[dict[str, Any]]:
        outgoing: list[dict[str, Any]] = []
        for relationship in relationships:
            if not isinstance(relationship, dict):
                continue
            connects = self._get_connects(relationship)
            if connects is None:
                continue
            source = connects.get("source")
            if not isinstance(source, dict):
                continue
            if source.get("node") == source_node_id:
                outgoing.append(relationship)
        return outgoing

    def _extract_destination_node_id(
        self,
        relationship: dict[str, Any],
        workload: dict[str, Any],
    ) -> str:
        connects = self._get_connects(relationship)
        if connects is None:
            workload_id = self._require_string(workload.get("id"), "workload id")
            raise MicroAffinityGroupRelationshipResolutionError(
                f"Relationship for workload id '{workload_id}' is missing connects metadata."
            )

        destination = connects.get("destination")
        if not isinstance(destination, dict) or not isinstance(destination.get("node"), str):
            workload_id = self._require_string(workload.get("id"), "workload id")
            raise MicroAffinityGroupRelationshipResolutionError(
                f"Relationship for workload id '{workload_id}' is missing a destination node reference."
            )

        return destination["node"]

    def _get_connects(self, relationship: dict[str, Any]) -> dict[str, Any] | None:
        relationship_type = relationship.get("relationship-type")
        if not isinstance(relationship_type, dict):
            return None
        connects = relationship_type.get("connects")
        return connects if isinstance(connects, dict) else None

    def _require_unique_id(self, node: dict[str, Any], workload: dict[str, Any]) -> str:
        unique_id = node.get("unique-id")
        if isinstance(unique_id, str):
            return unique_id

        workload_id = self._require_string(workload.get("id"), "workload id")
        raise MicroAffinityGroupRelationshipResolutionError(
            f"Resolved source service node for workload id '{workload_id}' is missing unique-id."
        )

    def _workload_from_node(self, node: dict[str, Any], workload: dict[str, Any]) -> dict[str, str]:
        metadata = node.get("metadata")
        if not isinstance(metadata, dict):
            workload_id = self._require_string(workload.get("id"), "workload id")
            raise MicroAffinityGroupRelationshipResolutionError(
                f"Resolved service node for workload id '{workload_id}' is missing metadata."
            )

        return {
            "id": self._require_string(metadata.get("code-repo"), "service metadata.code-repo"),
            "asset_id": self._require_string(
                metadata.get("asset-id"),
                "service metadata.asset-id",
            ),
        }

    def _require_string(self, value: Any, field_name: str) -> str:
        if isinstance(value, str):
            return value
        raise MicroAffinityGroupRelationshipResolutionError(
            f"Expected {field_name} to be a string."
        )