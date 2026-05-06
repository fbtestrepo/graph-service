from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from src.core.exceptions.application_architecture_not_found import ApplicationArchitectureNotFound
from src.core.exceptions.micro_affinity_group_workload_mismatch import (
    MicroAffinityGroupWorkloadMismatch,
)
from src.core.use_cases.upsert_micro_affinity_group import UpsertMicroAffinityGroup


def _application_architecture_payload() -> dict[str, Any]:
    return {
        "metadata": {
            "AssetID": "ba0270",
            "version": "1.0.0",
            "created": "2026-05-05",
        },
        "nodes": [
            {
                "unique-id": "node-1",
                "node-type": "service",
                "name": "RW Orchestrator",
                "description": "Service backing workload 1",
                "metadata": {
                    "code-repo": "AIMC/repos/rw-orchestrator-svc_ba0116_pq0177",
                    "asset-id": "pq0177",
                },
            }
        ],
        "relationships": [],
    }


def _valid_payload() -> dict[str, Any]:
    return {
        "micro-ag-id": "mAG_A",
        "name": "Micro Affinity Group A",
        "parent-asset-id": "ba0270",
        "architecture-version": "1.0.0",
        "environment": "production",
        "effective-date": "2025-01-01T14:00:00Z",
        "workloads": [
            {
                "id": "AIMC/repos/rw-orchestrator-svc_ba0116_pq0177",
                "asset-id": "pq0177",
            }
        ],
    }


@dataclass(slots=True)
class FakeApplicationArchitectureRepository:
    store: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)

    def get_by_asset_id_and_version(self, asset_id: str, version: str) -> dict[str, Any] | None:
        return self.store.get((asset_id, version))


@dataclass(slots=True)
class FakeMicroAffinityGroupRepository:
    store: dict[tuple[str, str, str], dict[str, Any]] = field(default_factory=dict)

    def upsert(
        self,
        micro_ag_id: str,
        environment: str,
        architecture_version: str,
        payload: dict[str, Any],
    ) -> bool:
        key = (micro_ag_id, environment, architecture_version)
        created = key not in self.store
        self.store[key] = payload
        return created


def test_upsert_micro_affinity_group_missing_architecture_raises_domain_exception() -> None:
    use_case = UpsertMicroAffinityGroup(
        application_architecture_repository=FakeApplicationArchitectureRepository(),
        micro_affinity_group_repository=FakeMicroAffinityGroupRepository(),
    )

    with pytest.raises(ApplicationArchitectureNotFound):
        use_case.execute(_valid_payload())


def test_upsert_micro_affinity_group_missing_service_node_raises_domain_exception() -> None:
    architecture = _application_architecture_payload()
    architecture["nodes"][0]["metadata"]["code-repo"] = "AIMC/repos/another-service"
    use_case = UpsertMicroAffinityGroup(
        application_architecture_repository=FakeApplicationArchitectureRepository(
            store={("ba0270", "1.0.0"): architecture}
        ),
        micro_affinity_group_repository=FakeMicroAffinityGroupRepository(),
    )

    with pytest.raises(MicroAffinityGroupWorkloadMismatch):
        use_case.execute(_valid_payload())


def test_upsert_micro_affinity_group_asset_id_mismatch_raises_domain_exception() -> None:
    architecture = _application_architecture_payload()
    architecture["nodes"][0]["metadata"]["asset-id"] = "different-asset"
    use_case = UpsertMicroAffinityGroup(
        application_architecture_repository=FakeApplicationArchitectureRepository(
            store={("ba0270", "1.0.0"): architecture}
        ),
        micro_affinity_group_repository=FakeMicroAffinityGroupRepository(),
    )

    with pytest.raises(MicroAffinityGroupWorkloadMismatch):
        use_case.execute(_valid_payload())