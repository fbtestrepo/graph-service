from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from src.core.domain.micro_affinity_group_relationship_mapper import (
    MicroAffinityGroupRelationshipMapper,
)
from src.core.exceptions.application_architecture_not_found import ApplicationArchitectureNotFound
from src.core.exceptions.duplicate_micro_affinity_group_identity import (
    DuplicateMicroAffinityGroupIdentity,
)
from src.core.exceptions.micro_affinity_group_relationship_resolution_error import (
    MicroAffinityGroupRelationshipResolutionError,
)
from src.core.use_cases.upsert_micro_affinity_group import UpsertMicroAffinityGroup


def _application_architecture_payload(*, include_relationship: bool = True) -> dict[str, Any]:
    relationships: list[dict[str, Any]] = []
    if include_relationship:
        relationships.append(
            {
                "relationship-type": {
                    "connects": {
                        "source": {"node": "node-1"},
                        "destination": {"node": "node-2"},
                    }
                }
            }
        )

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
            },
            {
                "unique-id": "node-2",
                "node-type": "service",
                "name": "RW CAP Service",
                "description": "Service backing workload 2",
                "metadata": {
                    "code-repo": "AIMC/repos/rw-cap-svc_ba0116_dh6980",
                    "asset-id": "dh6980",
                },
            },
        ],
        "relationships": relationships,
    }


def _valid_payload() -> dict[str, Any]:
    return {
        "micro_ag_id": "mAG_A",
        "name": "Micro Affinity Group A",
        "parent_asset_id": "ba0270",
        "architecture_version": "1.0.0",
        "environment": "production",
        "effective_date": "2025-01-01T14:00:00Z",
        "workloads": [
            {
                "id": "AIMC/repos/rw-orchestrator-svc_ba0116_pq0177",
                "asset_id": "pq0177",
            }
        ],
    }


@dataclass(slots=True)
class FakeApplicationArchitectureRepository:
    store: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)

    def get_by_asset_id_and_version(
        self,
        asset_id: str,
        version: str,
        session: Any | None = None,
    ) -> dict[str, Any] | None:
        return self.store.get((asset_id, version))


@dataclass(slots=True)
class FakeMicroAffinityGroupRepository:
    store: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)
    duplicate_counts: dict[tuple[str, str], int] = field(default_factory=dict)

    def count_by_identity(
        self,
        micro_ag_id: str,
        environment: str,
        session: Any | None = None,
    ) -> int:
        key = (micro_ag_id, environment)
        return self.duplicate_counts.get(key, 1 if key in self.store else 0)

    def upsert(
        self,
        micro_ag_id: str,
        environment: str,
        payload: dict[str, Any],
        session: Any | None = None,
    ) -> bool:
        key = (micro_ag_id, environment)
        created = key not in self.store
        self.store[key] = payload
        return created


@dataclass(slots=True)
class FakeMicroAffinityGroupProcessedRepository:
    store: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)
    duplicate_counts: dict[tuple[str, str], int] = field(default_factory=dict)

    def count_by_identity(
        self,
        micro_ag_id: str,
        environment: str,
        session: Any | None = None,
    ) -> int:
        key = (micro_ag_id, environment)
        return self.duplicate_counts.get(key, 1 if key in self.store else 0)

    def upsert(
        self,
        micro_ag_id: str,
        environment: str,
        payload: dict[str, Any],
        session: Any | None = None,
    ) -> bool:
        key = (micro_ag_id, environment)
        created = key not in self.store
        self.store[key] = payload
        return created


@dataclass(slots=True)
class FakeTransactionManager:
    def execute(self, operation):
        return operation(None)


def _build_use_case(
    architecture: dict[str, Any] | None,
    *,
    additional_architectures: dict[tuple[str, str], dict[str, Any]] | None = None,
) -> tuple[
    UpsertMicroAffinityGroup,
    FakeMicroAffinityGroupRepository,
    FakeMicroAffinityGroupProcessedRepository,
]:
    raw_repository = FakeMicroAffinityGroupRepository()
    processed_repository = FakeMicroAffinityGroupProcessedRepository()
    store: dict[tuple[str, str], dict[str, Any]] = {}
    if architecture is not None:
        store[("ba0270", "1.0.0")] = architecture
    if additional_architectures is not None:
        store.update(additional_architectures)

    use_case = UpsertMicroAffinityGroup(
        application_architecture_repository=FakeApplicationArchitectureRepository(store=store),
        micro_affinity_group_repository=raw_repository,
        micro_affinity_group_processed_repository=processed_repository,
        transaction_manager=FakeTransactionManager(),
        relationship_mapper=MicroAffinityGroupRelationshipMapper(),
    )
    return use_case, raw_repository, processed_repository


def test_upsert_micro_affinity_group_missing_architecture_raises_domain_exception() -> None:
    use_case, _, _ = _build_use_case(None)

    with pytest.raises(ApplicationArchitectureNotFound):
        use_case.execute(_valid_payload())


def test_upsert_micro_affinity_group_missing_service_node_raises_domain_exception() -> None:
    architecture = _application_architecture_payload()
    architecture["nodes"][0]["metadata"]["code-repo"] = "AIMC/repos/another-service"
    use_case, _, _ = _build_use_case(architecture)

    with pytest.raises(MicroAffinityGroupRelationshipResolutionError):
        use_case.execute(_valid_payload())


def test_upsert_micro_affinity_group_asset_id_mismatch_raises_domain_exception() -> None:
    architecture = _application_architecture_payload()
    architecture["nodes"][0]["metadata"]["asset-id"] = "different-asset"
    use_case, _, _ = _build_use_case(architecture)

    with pytest.raises(MicroAffinityGroupRelationshipResolutionError):
        use_case.execute(_valid_payload())


def test_upsert_micro_affinity_group_returns_processed_payload() -> None:
    use_case, raw_repository, processed_repository = _build_use_case(
        _application_architecture_payload()
    )

    result = use_case.execute(_valid_payload())

    assert result.created is True
    assert result.payload == {
        **_valid_payload(),
        "relationships": [
            {
                "source_workload": {
                    "id": "AIMC/repos/rw-orchestrator-svc_ba0116_pq0177",
                    "asset_id": "pq0177",
                },
                "destination_workload": {
                    "id": "AIMC/repos/rw-cap-svc_ba0116_dh6980",
                    "asset_id": "dh6980",
                },
            }
        ],
    }
    assert raw_repository.store[("mAG_A", "production")] == _valid_payload()
    assert processed_repository.store[("mAG_A", "production")] == result.payload


def test_upsert_micro_affinity_group_keeps_zero_relationships_non_fatal() -> None:
    use_case, _, processed_repository = _build_use_case(
        _application_architecture_payload(include_relationship=False)
    )

    result = use_case.execute(_valid_payload())

    assert result.payload["relationships"] == []
    assert processed_repository.store[("mAG_A", "production")]["relationships"] == []


def test_upsert_micro_affinity_group_same_pair_new_version_replaces_existing_pair() -> None:
    use_case, raw_repository, processed_repository = _build_use_case(
        _application_architecture_payload(),
        additional_architectures={("ba0270", "2.0.0"): _application_architecture_payload()},
    )

    first_result = use_case.execute(_valid_payload())
    assert first_result.created is True

    replacement_payload = _valid_payload()
    replacement_payload["architecture_version"] = "2.0.0"
    replacement_payload["effective_date"] = "2025-02-01T10:00:00Z"
    replacement_payload.pop("name")

    second_result = use_case.execute(replacement_payload)

    assert second_result.created is False
    assert raw_repository.store[("mAG_A", "production")] == replacement_payload
    assert processed_repository.store[("mAG_A", "production")]["architecture_version"] == "2.0.0"
    assert "name" not in raw_repository.store[("mAG_A", "production")]
    assert "name" not in processed_repository.store[("mAG_A", "production")]


def test_upsert_micro_affinity_group_duplicate_existing_pair_raises_conflict() -> None:
    use_case, raw_repository, _ = _build_use_case(_application_architecture_payload())
    raw_repository.duplicate_counts[("mAG_A", "production")] = 2

    with pytest.raises(DuplicateMicroAffinityGroupIdentity):
        use_case.execute(_valid_payload())