from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest

from src.core.exceptions.micro_affinity_group_graph_resolution_error import (
    MicroAffinityGroupGraphResolutionError,
)
from src.core.exceptions.micro_affinity_group_not_found import MicroAffinityGroupNotFound
from src.core.use_cases.get_micro_affinity_group_deployment_scope import (
    GetMicroAffinityGroupDeploymentScope,
)


def _asset_id(micro_ag_id: str) -> str:
    return f"asset-{micro_ag_id.lower()}"


def _processed_mag_payload(
    micro_ag_id: str,
    environment: str,
    *,
    workload_asset_ids: list[str] | None = None,
    dependency_micro_ag_ids: list[str] | None = None,
) -> dict[str, Any]:
    source_asset_ids = workload_asset_ids or [_asset_id(micro_ag_id)]
    dependency_ids = dependency_micro_ag_ids or []
    return {
        "micro_ag_id": micro_ag_id,
        "environment": environment,
        "effective_date": "2025-01-01T00:00:00Z",
        "workloads": [
            {
                "id": f"{micro_ag_id}-workload-{index}",
                "asset_id": asset_id,
            }
            for index, asset_id in enumerate(source_asset_ids, start=1)
        ],
        "relationships": [
            {
                "source_workload": {
                    "id": f"{micro_ag_id}-workload-1",
                    "asset_id": source_asset_ids[0],
                },
                "destination_workload": {
                    "id": f"{dependency_micro_ag_id}-workload-1",
                    "asset_id": _asset_id(dependency_micro_ag_id),
                },
            }
            for dependency_micro_ag_id in dependency_ids
        ],
    }


def _reported_cycle_store(*, include_back_edge: bool) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        ("A", "preproduction"): _processed_mag_payload(
            "A",
            "preproduction",
            dependency_micro_ag_ids=["C"],
        ),
        ("B", "preproduction"): _processed_mag_payload(
            "B",
            "preproduction",
            dependency_micro_ag_ids=["C"],
        ),
        ("C", "preproduction"): _processed_mag_payload(
            "C",
            "preproduction",
            dependency_micro_ag_ids=["D"],
        ),
        ("D", "preproduction"): _processed_mag_payload(
            "D",
            "preproduction",
            dependency_micro_ag_ids=["E"],
        ),
        ("E", "preproduction"): _processed_mag_payload(
            "E",
            "preproduction",
            dependency_micro_ag_ids=["E1", "E2", "E3"],
        ),
        ("E1", "preproduction"): _processed_mag_payload(
            "E1",
            "preproduction",
            dependency_micro_ag_ids=["C"] if include_back_edge else [],
        ),
        ("E2", "preproduction"): _processed_mag_payload("E2", "preproduction"),
        ("E3", "preproduction"): _processed_mag_payload("E3", "preproduction"),
        ("F", "preproduction"): _processed_mag_payload(
            "F",
            "preproduction",
            dependency_micro_ag_ids=["E"],
        ),
        ("G", "preproduction"): _processed_mag_payload(
            "G",
            "preproduction",
            dependency_micro_ag_ids=["F"],
        ),
    }


@dataclass(slots=True)
class FakeMicroAffinityGroupProcessedRepository:
    store: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)

    def count_by_identity(self, *args, **kwargs) -> int:  # pragma: no cover
        raise NotImplementedError

    def upsert(self, *args, **kwargs) -> bool:  # pragma: no cover
        raise NotImplementedError

    def get_by_identity(
        self,
        micro_ag_id: str,
        environment: str,
        session: Any | None = None,
    ) -> dict[str, Any] | None:
        return self.store.get((micro_ag_id, environment))

    def list_by_workload_asset_ids(
        self,
        asset_ids: list[str],
        environment: str,
        session: Any | None = None,
    ) -> list[dict[str, Any]]:
        requested_asset_ids = set(asset_ids)
        return [
            payload
            for (micro_ag_id, payload_environment), payload in self.store.items()
            if payload_environment == environment
            and any(
                workload.get("asset_id") in requested_asset_ids
                for workload in payload.get("workloads", [])
                if isinstance(workload, dict)
            )
        ]

    def list_by_relationship_destination_asset_ids(
        self,
        asset_ids: list[str],
        environment: str,
        session: Any | None = None,
    ) -> list[dict[str, Any]]:
        requested_asset_ids = set(asset_ids)
        return [
            payload
            for (_, payload_environment), payload in self.store.items()
            if payload_environment == environment
            and any(
                relationship.get("destination_workload", {}).get("asset_id") in requested_asset_ids
                for relationship in payload.get("relationships", [])
                if isinstance(relationship, dict)
            )
        ]


def _build_use_case(store: dict[tuple[str, str], dict[str, Any]]) -> GetMicroAffinityGroupDeploymentScope:
    return GetMicroAffinityGroupDeploymentScope(
        micro_affinity_group_processed_repository=FakeMicroAffinityGroupProcessedRepository(
            store=store
        ),
        now_provider=lambda: datetime(2025, 1, 1, 14, 0, 0, tzinfo=UTC),
    )


def test_use_case_returns_root_only_deployment_scope_for_empty_graph() -> None:
    use_case = _build_use_case(
        {
            ("SOLO", "preproduction"): _processed_mag_payload("SOLO", "preproduction"),
        }
    )

    result = use_case.execute(micro_ag_id="SOLO", environment="preproduction")

    assert result == {
        "micro_ag_id": "SOLO",
        "environment": "preproduction",
        "effective_date": "2025-01-01T14:00:00Z",
        "graph_has_cycles": False,
        "dependency_graph": [],
        "deployment_sequence": {
            "bypassed_edges": [],
            "steps": [{"step_index": 1, "micro_ag_ids": ["SOLO"]}],
        },
    }


def test_use_case_resolves_one_hop_upstream_and_downstream_graph() -> None:
    store = {
        ("B", "preproduction"): _processed_mag_payload(
            "B",
            "preproduction",
            dependency_micro_ag_ids=["C"],
        ),
        ("C", "preproduction"): _processed_mag_payload(
            "C",
            "preproduction",
            dependency_micro_ag_ids=["D"],
        ),
        ("D", "preproduction"): _processed_mag_payload(
            "D",
            "preproduction",
            dependency_micro_ag_ids=["E"],
        ),
        ("E", "preproduction"): _processed_mag_payload("E", "preproduction"),
    }

    result = _build_use_case(store).execute(micro_ag_id="C", environment="preproduction")

    assert result["graph_has_cycles"] is False
    assert result["dependency_graph"] == [
        {"source_micro_ag_id": "B", "destination_micro_ag_id": "C"},
        {"source_micro_ag_id": "C", "destination_micro_ag_id": "D"},
        {"source_micro_ag_id": "D", "destination_micro_ag_id": "E"},
    ]
    assert result["deployment_sequence"] == {
        "bypassed_edges": [],
        "steps": [
            {"step_index": 1, "micro_ag_ids": ["E"]},
            {"step_index": 2, "micro_ag_ids": ["D"]},
            {"step_index": 3, "micro_ag_ids": ["C"]},
            {"step_index": 4, "micro_ag_ids": ["B"]},
        ],
    }


def test_use_case_raises_not_found_for_missing_root_pair() -> None:
    with pytest.raises(MicroAffinityGroupNotFound):
        _build_use_case({}).execute(micro_ag_id="missing", environment="preproduction")


def test_use_case_raises_422_for_missing_downstream_owner_after_root_exists() -> None:
    store = {
        ("C", "preproduction"): _processed_mag_payload(
            "C",
            "preproduction",
            workload_asset_ids=[_asset_id("C")],
        )
    }
    store[("C", "preproduction")]["relationships"] = [
        {
            "source_workload": {"id": "C-workload-1", "asset_id": _asset_id("C")},
            "destination_workload": {"id": "missing-workload-1", "asset_id": "asset-missing"},
        }
    ]

    with pytest.raises(MicroAffinityGroupGraphResolutionError):
        _build_use_case(store).execute(micro_ag_id="C", environment="preproduction")


def test_use_case_marks_reported_path_scoped_back_edge_and_preserves_root_upstream_edges() -> None:
    result = _build_use_case(_reported_cycle_store(include_back_edge=True)).execute(
        micro_ag_id="C",
        environment="preproduction",
    )

    assert result["graph_has_cycles"] is True
    assert result["dependency_graph"] == [
        {"source_micro_ag_id": "A", "destination_micro_ag_id": "C"},
        {"source_micro_ag_id": "B", "destination_micro_ag_id": "C"},
        {"source_micro_ag_id": "C", "destination_micro_ag_id": "D"},
        {"source_micro_ag_id": "D", "destination_micro_ag_id": "E"},
        {"source_micro_ag_id": "E", "destination_micro_ag_id": "E2"},
        {"source_micro_ag_id": "E", "destination_micro_ag_id": "E3"},
        {"source_micro_ag_id": "E1", "destination_micro_ag_id": "C"},
        {"source_micro_ag_id": "E", "destination_micro_ag_id": "E1", "is_cyclic": True},
    ]
    assert result["deployment_sequence"] == {
        "bypassed_edges": [{"source_micro_ag_id": "E", "destination_micro_ag_id": "E1"}],
        "steps": [
            {"step_index": 1, "micro_ag_ids": ["E2", "E3"]},
            {"step_index": 2, "micro_ag_ids": ["E"]},
            {"step_index": 3, "micro_ag_ids": ["D"]},
            {"step_index": 4, "micro_ag_ids": ["C"]},
            {"step_index": 5, "micro_ag_ids": ["A", "B", "E1"]},
        ],
    }


def test_use_case_marks_correct_back_edge_for_root_e3() -> None:
    result = _build_use_case(_reported_cycle_store(include_back_edge=True)).execute(
        micro_ag_id="E3",
        environment="preproduction",
    )

    assert result["graph_has_cycles"] is True
    assert result["dependency_graph"] == [
        {"source_micro_ag_id": "C", "destination_micro_ag_id": "D"},
        {"source_micro_ag_id": "E", "destination_micro_ag_id": "E1"},
        {"source_micro_ag_id": "E", "destination_micro_ag_id": "E2"},
        {"source_micro_ag_id": "E", "destination_micro_ag_id": "E3"},
        {"source_micro_ag_id": "E1", "destination_micro_ag_id": "C"},
        {"source_micro_ag_id": "D", "destination_micro_ag_id": "E", "is_cyclic": True},
    ]
    assert result["deployment_sequence"] == {
        "bypassed_edges": [{"source_micro_ag_id": "D", "destination_micro_ag_id": "E"}],
        "steps": [
            {"step_index": 1, "micro_ag_ids": ["D", "E2", "E3"]},
            {"step_index": 2, "micro_ag_ids": ["C"]},
            {"step_index": 3, "micro_ag_ids": ["E1"]},
            {"step_index": 4, "micro_ag_ids": ["E"]},
        ],
    }


def test_use_case_marks_correct_back_edge_for_root_d() -> None:
    result = _build_use_case(_reported_cycle_store(include_back_edge=True)).execute(
        micro_ag_id="D",
        environment="preproduction",
    )

    assert result["graph_has_cycles"] is True
    assert result["dependency_graph"] == [
        {"source_micro_ag_id": "C", "destination_micro_ag_id": "D"},
        {"source_micro_ag_id": "D", "destination_micro_ag_id": "E"},
        {"source_micro_ag_id": "E", "destination_micro_ag_id": "E1"},
        {"source_micro_ag_id": "E", "destination_micro_ag_id": "E2"},
        {"source_micro_ag_id": "E", "destination_micro_ag_id": "E3"},
        {"source_micro_ag_id": "E1", "destination_micro_ag_id": "C", "is_cyclic": True},
    ]
    assert result["deployment_sequence"] == {
        "bypassed_edges": [{"source_micro_ag_id": "E1", "destination_micro_ag_id": "C"}],
        "steps": [
            {"step_index": 1, "micro_ag_ids": ["E1", "E2", "E3"]},
            {"step_index": 2, "micro_ag_ids": ["E"]},
            {"step_index": 3, "micro_ag_ids": ["D"]},
            {"step_index": 4, "micro_ag_ids": ["C"]},
        ],
    }


def test_use_case_marks_correct_back_edge_for_root_e() -> None:
    result = _build_use_case(_reported_cycle_store(include_back_edge=True)).execute(
        micro_ag_id="E",
        environment="preproduction",
    )

    assert result["graph_has_cycles"] is True
    assert result["dependency_graph"] == [
        {"source_micro_ag_id": "D", "destination_micro_ag_id": "E"},
        {"source_micro_ag_id": "E", "destination_micro_ag_id": "E1"},
        {"source_micro_ag_id": "E", "destination_micro_ag_id": "E2"},
        {"source_micro_ag_id": "E", "destination_micro_ag_id": "E3"},
        {"source_micro_ag_id": "E1", "destination_micro_ag_id": "C"},
        {"source_micro_ag_id": "F", "destination_micro_ag_id": "E"},
        {"source_micro_ag_id": "C", "destination_micro_ag_id": "D", "is_cyclic": True},
    ]
    assert result["deployment_sequence"] == {
        "bypassed_edges": [{"source_micro_ag_id": "C", "destination_micro_ag_id": "D"}],
        "steps": [
            {"step_index": 1, "micro_ag_ids": ["C", "E2", "E3"]},
            {"step_index": 2, "micro_ag_ids": ["E1"]},
            {"step_index": 3, "micro_ag_ids": ["E"]},
            {"step_index": 4, "micro_ag_ids": ["D", "F"]},
        ],
    }


def test_use_case_preserves_acyclic_behavior_for_reported_shape_without_back_edge() -> None:
    result = _build_use_case(_reported_cycle_store(include_back_edge=False)).execute(
        micro_ag_id="C",
        environment="preproduction",
    )

    assert result["graph_has_cycles"] is False
    assert result["dependency_graph"] == [
        {"source_micro_ag_id": "A", "destination_micro_ag_id": "C"},
        {"source_micro_ag_id": "B", "destination_micro_ag_id": "C"},
        {"source_micro_ag_id": "C", "destination_micro_ag_id": "D"},
        {"source_micro_ag_id": "D", "destination_micro_ag_id": "E"},
        {"source_micro_ag_id": "E", "destination_micro_ag_id": "E1"},
        {"source_micro_ag_id": "E", "destination_micro_ag_id": "E2"},
        {"source_micro_ag_id": "E", "destination_micro_ag_id": "E3"},
    ]
    assert result["deployment_sequence"] == {
        "bypassed_edges": [],
        "steps": [
            {"step_index": 1, "micro_ag_ids": ["E1", "E2", "E3"]},
            {"step_index": 2, "micro_ag_ids": ["E"]},
            {"step_index": 3, "micro_ag_ids": ["D"]},
            {"step_index": 4, "micro_ag_ids": ["C"]},
            {"step_index": 5, "micro_ag_ids": ["A", "B"]},
        ],
    }


def test_use_case_builds_deterministic_cycle_breaking_and_parallel_layers() -> None:
    store = {
        ("A", "preproduction"): _processed_mag_payload(
            "A",
            "preproduction",
            dependency_micro_ag_ids=["B"],
        ),
        ("B", "preproduction"): _processed_mag_payload(
            "B",
            "preproduction",
            dependency_micro_ag_ids=["C"],
        ),
        ("C", "preproduction"): _processed_mag_payload(
            "C",
            "preproduction",
            dependency_micro_ag_ids=["D"],
        ),
        ("D", "preproduction"): _processed_mag_payload(
            "D",
            "preproduction",
            dependency_micro_ag_ids=["E"],
        ),
        ("E", "preproduction"): _processed_mag_payload(
            "E",
            "preproduction",
            dependency_micro_ag_ids=["A"],
        ),
        ("X", "parallel"): _processed_mag_payload(
            "X",
            "parallel",
            dependency_micro_ag_ids=["Z"],
        ),
        ("Y", "parallel"): _processed_mag_payload(
            "Y",
            "parallel",
            dependency_micro_ag_ids=["Z"],
        ),
        ("Z", "parallel"): _processed_mag_payload("Z", "parallel"),
    }

    cycle_result = _build_use_case(store).execute(micro_ag_id="C", environment="preproduction")
    parallel_result = _build_use_case(store).execute(micro_ag_id="Z", environment="parallel")

    assert cycle_result["graph_has_cycles"] is True
    assert cycle_result["dependency_graph"] == [
        {"source_micro_ag_id": "B", "destination_micro_ag_id": "C"},
        {"source_micro_ag_id": "C", "destination_micro_ag_id": "D"},
        {"source_micro_ag_id": "D", "destination_micro_ag_id": "E"},
        {"source_micro_ag_id": "E", "destination_micro_ag_id": "A"},
        {"source_micro_ag_id": "A", "destination_micro_ag_id": "B", "is_cyclic": True},
    ]
    assert cycle_result["deployment_sequence"] == {
        "bypassed_edges": [
            {"source_micro_ag_id": "A", "destination_micro_ag_id": "B"}
        ],
        "steps": [
            {"step_index": 1, "micro_ag_ids": ["A"]},
            {"step_index": 2, "micro_ag_ids": ["E"]},
            {"step_index": 3, "micro_ag_ids": ["D"]},
            {"step_index": 4, "micro_ag_ids": ["C"]},
            {"step_index": 5, "micro_ag_ids": ["B"]},
        ],
    }
    assert parallel_result["deployment_sequence"] == {
        "bypassed_edges": [],
        "steps": [
            {"step_index": 1, "micro_ag_ids": ["Z"]},
            {"step_index": 2, "micro_ag_ids": ["X", "Y"]},
        ],
    }


def test_use_case_truncates_downstream_traversal_at_30_hops() -> None:
    store: dict[tuple[str, str], dict[str, Any]] = {}
    for index in range(32):
        micro_ag_id = f"N{index}"
        dependency_ids = [f"N{index + 1}"] if index < 31 else []
        store[(micro_ag_id, "preproduction")] = _processed_mag_payload(
            micro_ag_id,
            "preproduction",
            dependency_micro_ag_ids=dependency_ids,
        )

    result = _build_use_case(store).execute(micro_ag_id="N0", environment="preproduction")

    assert len(result["dependency_graph"]) == 30
    assert {
        "source_micro_ag_id": "N0",
        "destination_micro_ag_id": "N1",
    } in result["dependency_graph"]
    assert {
        "source_micro_ag_id": "N29",
        "destination_micro_ag_id": "N30",
    } in result["dependency_graph"]
    assert {
        "source_micro_ag_id": "N30",
        "destination_micro_ag_id": "N31",
    } not in result["dependency_graph"]