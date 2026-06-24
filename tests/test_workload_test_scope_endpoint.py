from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from src.infrastructure.main import create_app
from tests.conftest import MICRO_AFFINITY_GROUPS_PATH


def _path(environment: str) -> str:
    return f"{MICRO_AFFINITY_GROUPS_PATH}/workloads/test-scope?environment={environment}"


def _request_payload(*asset_ids: str) -> dict[str, Any]:
    return {
        "changed_workloads": [{"workload_asset_id": asset_id} for asset_id in asset_ids]
    }


@dataclass(slots=True)
class FakeMicroAffinityGroupProcessedRepository:
    relationship_rows: list[dict[str, str]] = field(default_factory=list)
    ownership_rows: list[dict[str, str]] = field(default_factory=list)
    calls: int = 0

    def list_relationship_candidates_for_workload_test_scope(
        self,
        changed_asset_ids: list[str],
        environment: str,
        session: Any | None = None,
    ) -> list[dict[str, str]]:
        self.calls += 1
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



def _configured_client(
    relationship_rows: list[dict[str, str]],
    ownership_rows: list[dict[str, str]],
) -> tuple[TestClient, FakeMicroAffinityGroupProcessedRepository]:
    app = create_app()
    repo = FakeMicroAffinityGroupProcessedRepository(
        relationship_rows=relationship_rows,
        ownership_rows=ownership_rows,
    )
    client = TestClient(app, raise_server_exceptions=False)
    client.app.state.micro_affinity_group_processed_repository = repo
    client.app.state.micro_affinity_group_deployment_scope_clock = lambda: datetime(
        2026, 6, 12, 10, 30, 0, tzinfo=UTC
    )
    return client, repo


def test_endpoint_source_destination_dual_role_success() -> None:
    relationship_rows = [
        {
            "source_workload_asset_id": "asset_1",
            "destination_workload_asset_id": "asset_2",
            "source_micro_ag_id": "mAG_A",
        },
        {
            "source_workload_asset_id": "asset_3",
            "destination_workload_asset_id": "asset_1",
            "source_micro_ag_id": "mAG_C",
        },
    ]
    ownership_rows = [
        {"workload_asset_id": "asset_1", "micro_ag_id": "mAG_A"},
        {"workload_asset_id": "asset_2", "micro_ag_id": "mAG_B"},
        {"workload_asset_id": "asset_3", "micro_ag_id": "mAG_C"},
    ]
    client, _ = _configured_client(relationship_rows, ownership_rows)

    with client:
        response = client.post(_path("preproduction"), json=_request_payload("asset_1"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["environment"] == "preproduction"
    assert payload["changed_workloads"] == [
        {"workload_asset_id": "asset_1", "micro_ag_id": "mAG_A"}
    ]
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


def test_endpoint_empty_changed_workloads_returns_200_with_zero_summary() -> None:
    client, _ = _configured_client([], [])

    with client:
        response = client.post(_path("preproduction"), json={"changed_workloads": []})

    assert response.status_code == 200
    assert response.json()["summary"] == {
        "total_affected_workload_relationships": 0,
        "total_affected_workloads": 0,
        "total_affected_micro_ags": 0,
        "total_unknown_workloads": 0,
    }


def test_endpoint_no_records_environment_returns_200_unknowns_from_deduped_input() -> None:
    client, _ = _configured_client([], [])

    with client:
        response = client.post(
            _path("preproduction"),
            json=_request_payload("asset_2", "asset_2", "asset_1"),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["changed_workloads"] == []
    assert payload["unknown_workloads"] == [
        {"workload_asset_id": "asset_2"},
        {"workload_asset_id": "asset_1"},
    ]


def test_endpoint_contract_parity_and_snake_case_keys() -> None:
    relationship_rows = [
        {
            "source_workload_asset_id": "asset_1",
            "destination_workload_asset_id": "asset_2",
            "source_micro_ag_id": "mAG_A",
        },
        {
            "source_workload_asset_id": "asset_3",
            "destination_workload_asset_id": "asset_1",
            "source_micro_ag_id": "mAG_C",
        },
    ]
    ownership_rows = [
        {"workload_asset_id": "asset_1", "micro_ag_id": "mAG_A"},
        {"workload_asset_id": "asset_2", "micro_ag_id": "mAG_B"},
        {"workload_asset_id": "asset_3", "micro_ag_id": "mAG_C"},
        {"workload_asset_id": "unknown_asset_id", "micro_ag_id": "mAG_X"},
    ]
    client, _ = _configured_client(relationship_rows, ownership_rows)

    with client:
        response = client.post(
            _path("preproduction"),
            json=_request_payload("asset_1", "unknown_asset_id"),
        )

    assert response.status_code == 200
    payload = response.json()
    expected_shape = json.loads(
        Path("specs/samples/micro-affinity-group/workload/test-scope.json").read_text(
            encoding="utf-8"
        )
    )
    assert set(payload.keys()) == set(expected_shape.keys())
    assert set(payload["summary"].keys()) == set(expected_shape["summary"].keys())
    assert all("-" not in key for key in payload.keys())


def test_endpoint_missing_and_blank_environment_return_422_and_no_processing() -> None:
    client, repo = _configured_client([], [])

    with client:
        missing_response = client.post(
            f"{MICRO_AFFINITY_GROUPS_PATH}/workloads/test-scope",
            json=_request_payload("asset_1"),
        )
        blank_response = client.post(
            _path(" "),
            json=_request_payload("asset_1"),
        )

    assert missing_response.status_code == 422
    assert blank_response.status_code == 422
    assert repo.calls == 0


def test_endpoint_malformed_json_returns_400_problem_details() -> None:
    client, _ = _configured_client([], [])

    with client:
        response = client.post(
            _path("preproduction"),
            data="{",
            headers={"content-type": "application/json"},
        )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["title"] == "Malformed JSON"


def test_endpoint_ambiguous_ownership_returns_422() -> None:
    relationship_rows = [
        {
            "source_workload_asset_id": "asset_1",
            "destination_workload_asset_id": "asset_2",
            "source_micro_ag_id": "mAG_A",
        }
    ]
    ownership_rows = [
        {"workload_asset_id": "asset_1", "micro_ag_id": "mAG_A"},
        {"workload_asset_id": "asset_2", "micro_ag_id": "mAG_B"},
        {"workload_asset_id": "asset_2", "micro_ag_id": "mAG_C"},
    ]
    client, _ = _configured_client(relationship_rows, ownership_rows)

    with client:
        response = client.post(_path("preproduction"), json=_request_payload("asset_1"))

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["error_code"] == "ambiguous_workload_ownership"
