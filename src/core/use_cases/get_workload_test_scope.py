from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from src.core.exceptions.ambiguous_workload_ownership import AmbiguousWorkloadOwnership
from src.core.ports.micro_affinity_group_processed_repository import (
    MicroAffinityGroupProcessedRepository,
)


@dataclass(frozen=True, slots=True)
class GetWorkloadTestScope:
    micro_affinity_group_processed_repository: MicroAffinityGroupProcessedRepository
    now_provider: Callable[[], datetime]

    def execute(self, *, environment: str, changed_asset_ids: list[str]) -> dict[str, Any]:
        deduped_input_asset_ids = _dedupe_first_seen(changed_asset_ids)
        if not deduped_input_asset_ids:
            return {
                "timestamp": _format_timestamp(self.now_provider()),
                "environment": environment,
                "changed_workloads": [],
                "affected_workload_relationships": [],
                "unknown_workloads": [],
                "summary": {
                    "total_affected_workload_relationships": 0,
                    "total_affected_workloads": 0,
                    "total_affected_micro_ags": 0,
                    "total_unknown_workloads": 0,
                },
            }

        relationship_rows = (
            self.micro_affinity_group_processed_repository.list_relationship_candidates_for_workload_test_scope(
                changed_asset_ids=deduped_input_asset_ids,
                environment=environment,
            )
        )

        ownership_rows = self.micro_affinity_group_processed_repository.list_workload_ownership_for_asset_ids(
            asset_ids=deduped_input_asset_ids
            + [
                row["source_workload_asset_id"]
                for row in relationship_rows
                if row.get("source_workload_asset_id")
            ]
            + [
                row["destination_workload_asset_id"]
                for row in relationship_rows
                if row.get("destination_workload_asset_id")
            ],
            environment=environment,
        )

        ownership_map: dict[str, set[str]] = defaultdict(set)
        for row in ownership_rows:
            workload_asset_id = row.get("workload_asset_id")
            micro_ag_id = row.get("micro_ag_id")
            if isinstance(workload_asset_id, str) and workload_asset_id and isinstance(micro_ag_id, str) and micro_ag_id:
                ownership_map[workload_asset_id].add(micro_ag_id)

        for workload_asset_id, owners in ownership_map.items():
            if len(owners) > 1:
                raise AmbiguousWorkloadOwnership(
                    environment=environment,
                    workload_asset_id=workload_asset_id,
                )

        unknown_first_seen: list[str] = []
        unknown_seen: set[str] = set()

        changed_workloads: list[dict[str, str]] = []
        for workload_asset_id in deduped_input_asset_ids:
            owner = _single_owner(ownership_map, workload_asset_id)
            if owner is None:
                unknown_seen.add(workload_asset_id)
                unknown_first_seen.append(workload_asset_id)
                continue
            changed_workloads.append(
                {
                    "workload_asset_id": workload_asset_id,
                    "micro_ag_id": owner,
                }
            )

        relationship_payload_by_key: dict[tuple[str, str], dict[str, Any]] = {}
        for row in relationship_rows:
            source_asset_id = row.get("source_workload_asset_id")
            destination_asset_id = row.get("destination_workload_asset_id")
            if not isinstance(source_asset_id, str) or not source_asset_id:
                continue
            if not isinstance(destination_asset_id, str) or not destination_asset_id:
                continue

            source_owner = _single_owner(ownership_map, source_asset_id)
            destination_owner = _single_owner(ownership_map, destination_asset_id)
            if source_owner is None or destination_owner is None:
                if source_owner is None and source_asset_id not in unknown_seen:
                    unknown_seen.add(source_asset_id)
                    unknown_first_seen.append(source_asset_id)
                if destination_owner is None and destination_asset_id not in unknown_seen:
                    unknown_seen.add(destination_asset_id)
                    unknown_first_seen.append(destination_asset_id)
                continue

            key = (source_asset_id, destination_asset_id)
            relationship_payload_by_key[key] = {
                "source_workload": {
                    "workload_asset_id": source_asset_id,
                    "micro_ag_id": source_owner,
                },
                "destination_workload": {
                    "workload_asset_id": destination_asset_id,
                    "micro_ag_id": destination_owner,
                },
            }

        affected_relationships = [
            relationship_payload_by_key[key] for key in sorted(relationship_payload_by_key)
        ]

        if not relationship_rows:
            unknown_first_seen = [
                workload_asset_id
                for workload_asset_id in deduped_input_asset_ids
                if workload_asset_id not in {item["workload_asset_id"] for item in changed_workloads}
            ]
            unknown_seen = set(unknown_first_seen)
            changed_workloads = []

        unknown_workloads = [
            {"workload_asset_id": workload_asset_id}
            for workload_asset_id in unknown_first_seen
            if workload_asset_id in unknown_seen
        ]

        affected_workload_asset_ids = {
            rel["source_workload"]["workload_asset_id"] for rel in affected_relationships
        } | {
            rel["destination_workload"]["workload_asset_id"] for rel in affected_relationships
        }
        affected_micro_ag_ids = {
            rel["source_workload"]["micro_ag_id"] for rel in affected_relationships
        } | {
            rel["destination_workload"]["micro_ag_id"] for rel in affected_relationships
        }

        return {
            "timestamp": _format_timestamp(self.now_provider()),
            "environment": environment,
            "changed_workloads": changed_workloads,
            "affected_workload_relationships": affected_relationships,
            "unknown_workloads": unknown_workloads,
            "summary": {
                "total_affected_workload_relationships": len(affected_relationships),
                "total_affected_workloads": len(affected_workload_asset_ids),
                "total_affected_micro_ags": len(affected_micro_ag_ids),
                "total_unknown_workloads": len(unknown_workloads),
            },
        }


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _dedupe_first_seen(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _single_owner(ownership_map: dict[str, set[str]], workload_asset_id: str) -> str | None:
    owners = ownership_map.get(workload_asset_id)
    if not owners:
        return None
    return sorted(owners)[0]
