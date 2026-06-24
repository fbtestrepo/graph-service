from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest

from src.core.exceptions.ambiguous_workload_ownership import AmbiguousWorkloadOwnership
from src.core.use_cases.get_workload_test_scope import GetWorkloadTestScope


def _relationship(
    source_asset_id: str,
    destination_asset_id: str,
    source_micro_ag_id: str,
) -> dict[str, str]:
    return {
        "source_workload_asset_id": source_asset_id,
        "destination_workload_asset_id": destination_asset_id,
        "source_micro_ag_id": source_micro_ag_id,
    }


@dataclass(slots=True)
class FakeMicroAffinityGroupProcessedRepository:
    relationship_rows: list[dict[str, str]] = field(default_factory=list)
    ownership_rows: list[dict[str, str]] = field(default_factory=list)

    def list_relationship_candidates_for_workload_test_scope(
        self,
        changed_asset_ids: list[str],
        environment: str,
        session: Any | None = None,
    ) -> list[dict[str, str]]:
        return [
            row
            for row in self.relationship_rows
            if row["source_workload_asset_id"] in changed_asset_ids
            or row["destination_workload_asset_id"] in changed_asset_ids
        ]

    def list_workload_ownership_for_asset_ids(
        self,
        asset_ids: list[str],
        environment: str,
        session: Any | None = None,
    ) -> list[dict[str, str]]:
        requested = set(asset_ids)
        return [row for row in self.ownership_rows if row["workload_asset_id"] in requested]



def _build_use_case(
    relationship_rows: list[dict[str, str]],
    ownership_rows: list[dict[str, str]],
) -> GetWorkloadTestScope:
    return GetWorkloadTestScope(
        micro_affinity_group_processed_repository=FakeMicroAffinityGroupProcessedRepository(
            relationship_rows=relationship_rows,
            ownership_rows=ownership_rows,
        ),
        now_provider=lambda: datetime(2026, 6, 12, 10, 30, 0, tzinfo=UTC),
    )


def test_source_side_relationship_traversal() -> None:
    use_case = _build_use_case(
        relationship_rows=[_relationship("asset_1", "asset_2", "mAG_A")],
        ownership_rows=[
            {"workload_asset_id": "asset_1", "micro_ag_id": "mAG_A"},
            {"workload_asset_id": "asset_2", "micro_ag_id": "mAG_B"},
        ],
    )

    payload = use_case.execute(environment="preproduction", changed_asset_ids=["asset_1"])

    assert payload["changed_workloads"] == [
        {"workload_asset_id": "asset_1", "micro_ag_id": "mAG_A"}
    ]
    assert payload["affected_workload_relationships"] == [
        {
            "source_workload": {"workload_asset_id": "asset_1", "micro_ag_id": "mAG_A"},
            "destination_workload": {"workload_asset_id": "asset_2", "micro_ag_id": "mAG_B"},
        }
    ]


def test_destination_side_relationship_traversal() -> None:
    use_case = _build_use_case(
        relationship_rows=[_relationship("asset_3", "asset_1", "mAG_C")],
        ownership_rows=[
            {"workload_asset_id": "asset_1", "micro_ag_id": "mAG_A"},
            {"workload_asset_id": "asset_3", "micro_ag_id": "mAG_C"},
        ],
    )

    payload = use_case.execute(environment="preproduction", changed_asset_ids=["asset_1"])

    assert payload["affected_workload_relationships"] == [
        {
            "source_workload": {"workload_asset_id": "asset_3", "micro_ag_id": "mAG_C"},
            "destination_workload": {"workload_asset_id": "asset_1", "micro_ag_id": "mAG_A"},
        }
    ]


def test_dual_role_deduplicates_relationship_pairs() -> None:
    use_case = _build_use_case(
        relationship_rows=[
            _relationship("asset_1", "asset_2", "mAG_A"),
            _relationship("asset_1", "asset_2", "mAG_A"),
            _relationship("asset_3", "asset_1", "mAG_C"),
        ],
        ownership_rows=[
            {"workload_asset_id": "asset_1", "micro_ag_id": "mAG_A"},
            {"workload_asset_id": "asset_2", "micro_ag_id": "mAG_B"},
            {"workload_asset_id": "asset_3", "micro_ag_id": "mAG_C"},
        ],
    )

    payload = use_case.execute(environment="preproduction", changed_asset_ids=["asset_1"])

    assert payload["summary"]["total_affected_workload_relationships"] == 2
    assert payload["affected_workload_relationships"] == [
        {
            "source_workload": {"workload_asset_id": "asset_1", "micro_ag_id": "mAG_A"},
            "destination_workload": {"workload_asset_id": "asset_2", "micro_ag_id": "mAG_B"},
        },
        {
            "source_workload": {"workload_asset_id": "asset_3", "micro_ag_id": "mAG_C"},
            "destination_workload": {"workload_asset_id": "asset_1", "micro_ag_id": "mAG_A"},
        },
    ]


def test_unknown_input_workload_detection() -> None:
    use_case = _build_use_case(
        relationship_rows=[_relationship("asset_1", "asset_2", "mAG_A")],
        ownership_rows=[
            {"workload_asset_id": "asset_1", "micro_ag_id": "mAG_A"},
            {"workload_asset_id": "asset_2", "micro_ag_id": "mAG_B"},
        ],
    )

    payload = use_case.execute(
        environment="preproduction",
        changed_asset_ids=["asset_1", "unknown_asset_id"],
    )

    assert payload["unknown_workloads"] == [{"workload_asset_id": "unknown_asset_id"}]


def test_unresolved_relationship_excluded_and_unknown_reported() -> None:
    use_case = _build_use_case(
        relationship_rows=[_relationship("asset_1", "asset_missing", "mAG_A")],
        ownership_rows=[{"workload_asset_id": "asset_1", "micro_ag_id": "mAG_A"}],
    )

    payload = use_case.execute(environment="preproduction", changed_asset_ids=["asset_1"])

    assert payload["affected_workload_relationships"] == []
    assert payload["unknown_workloads"] == [{"workload_asset_id": "asset_missing"}]


def test_ambiguous_workload_ownership_raises_domain_exception() -> None:
    use_case = _build_use_case(
        relationship_rows=[_relationship("asset_1", "asset_2", "mAG_A")],
        ownership_rows=[
            {"workload_asset_id": "asset_1", "micro_ag_id": "mAG_A"},
            {"workload_asset_id": "asset_2", "micro_ag_id": "mAG_B"},
            {"workload_asset_id": "asset_2", "micro_ag_id": "mAG_C"},
        ],
    )

    with pytest.raises(AmbiguousWorkloadOwnership):
        use_case.execute(environment="preproduction", changed_asset_ids=["asset_1"])


def test_summary_math_counts_distinct_workloads_and_micro_ags() -> None:
    use_case = _build_use_case(
        relationship_rows=[
            _relationship("asset_1", "asset_2", "mAG_A"),
            _relationship("asset_3", "asset_1", "mAG_C"),
        ],
        ownership_rows=[
            {"workload_asset_id": "asset_1", "micro_ag_id": "mAG_A"},
            {"workload_asset_id": "asset_2", "micro_ag_id": "mAG_B"},
            {"workload_asset_id": "asset_3", "micro_ag_id": "mAG_C"},
        ],
    )

    payload = use_case.execute(environment="preproduction", changed_asset_ids=["asset_1"])

    assert payload["summary"] == {
        "total_affected_workload_relationships": 2,
        "total_affected_workloads": 3,
        "total_affected_micro_ags": 3,
        "total_unknown_workloads": 0,
    }


def test_no_data_environment_returns_unknowns_from_deduped_input_and_empty_changed() -> None:
    use_case = _build_use_case(relationship_rows=[], ownership_rows=[])

    payload = use_case.execute(
        environment="no-data",
        changed_asset_ids=["asset_2", "asset_2", "asset_1"],
    )

    assert payload["changed_workloads"] == []
    assert payload["unknown_workloads"] == [
        {"workload_asset_id": "asset_2"},
        {"workload_asset_id": "asset_1"},
    ]
    assert payload["summary"] == {
        "total_affected_workload_relationships": 0,
        "total_affected_workloads": 0,
        "total_affected_micro_ags": 0,
        "total_unknown_workloads": 2,
    }


def test_empty_input_returns_zeroed_payload() -> None:
    use_case = _build_use_case(relationship_rows=[], ownership_rows=[])

    payload = use_case.execute(environment="preproduction", changed_asset_ids=[])

    assert payload["changed_workloads"] == []
    assert payload["affected_workload_relationships"] == []
    assert payload["unknown_workloads"] == []
    assert payload["summary"] == {
        "total_affected_workload_relationships": 0,
        "total_affected_workloads": 0,
        "total_affected_micro_ags": 0,
        "total_unknown_workloads": 0,
    }
