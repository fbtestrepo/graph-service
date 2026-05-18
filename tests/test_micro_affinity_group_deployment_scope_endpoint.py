from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from src.infrastructure.main import create_app
from tests.conftest import MICRO_AFFINITY_GROUPS_PATH


def _asset_id(micro_ag_id: str) -> str:
    return f"asset-{micro_ag_id.lower()}"


def _deployment_scope_path(micro_ag_id: str, environment: str) -> str:
    return f"{MICRO_AFFINITY_GROUPS_PATH}/{micro_ag_id}/deployment-scope?environment={environment}"


def _processed_mag_payload(
    micro_ag_id: str,
    environment: str,
    *,
    dependency_micro_ag_ids: list[str] | None = None,
) -> dict[str, Any]:
    dependency_ids = dependency_micro_ag_ids or []
    return {
        "micro_ag_id": micro_ag_id,
        "environment": environment,
        "effective_date": "2025-01-01T00:00:00Z",
        "workloads": [{"id": f"{micro_ag_id}-workload-1", "asset_id": _asset_id(micro_ag_id)}],
        "relationships": [
            {
                "source_workload": {
                    "id": f"{micro_ag_id}-workload-1",
                    "asset_id": _asset_id(micro_ag_id),
                },
                "destination_workload": {
                    "id": f"{dependency_micro_ag_id}-workload-1",
                    "asset_id": _asset_id(dependency_micro_ag_id),
                },
            }
            for dependency_micro_ag_id in dependency_ids
        ],
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
            for (_, payload_environment), payload in self.store.items()
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


def _configured_client(store: dict[tuple[str, str], dict[str, Any]]) -> TestClient:
    app = create_app()
    client = TestClient(app, raise_server_exceptions=False)
    client.app.state.micro_affinity_group_processed_repository = (
        FakeMicroAffinityGroupProcessedRepository(store=store)
    )
    client.app.state.micro_affinity_group_deployment_scope_clock = lambda: datetime(
        2025, 1, 1, 14, 0, 0, tzinfo=UTC
    )
    return client


def test_get_deployment_scope_returns_sample_contract_for_seeded_cycle_graph() -> None:
    store = {
        ("A", "preproduction"): _processed_mag_payload(
            "A", "preproduction", dependency_micro_ag_ids=["B"]
        ),
        ("B", "preproduction"): _processed_mag_payload(
            "B", "preproduction", dependency_micro_ag_ids=["C"]
        ),
        ("C", "preproduction"): _processed_mag_payload(
            "C", "preproduction", dependency_micro_ag_ids=["D"]
        ),
        ("D", "preproduction"): _processed_mag_payload(
            "D", "preproduction", dependency_micro_ag_ids=["E"]
        ),
        ("E", "preproduction"): _processed_mag_payload(
            "E", "preproduction", dependency_micro_ag_ids=["A"]
        ),
    }

    with _configured_client(store) as client:
        response = client.get(_deployment_scope_path("C", "preproduction"))

    assert response.status_code == 200
    expected = json.loads(
        Path("specs/samples/micro-affinity-group/deployment-scope.json").read_text(
            encoding="utf-8"
        )
    )
    assert response.json() == expected


def test_get_deployment_scope_missing_root_returns_404_problem_details() -> None:
    with _configured_client({}) as client:
        response = client.get(_deployment_scope_path("missing", "preproduction"))

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    payload = response.json()
    assert payload["status"] == 404
    assert payload["error_code"] == "micro_affinity_group_not_found"


def test_get_deployment_scope_unresolvable_graph_returns_422_problem_details() -> None:
    store = {
        ("C", "preproduction"): _processed_mag_payload("C", "preproduction"),
    }
    store[("C", "preproduction")]["relationships"] = [
        {
            "source_workload": {"id": "C-workload-1", "asset_id": _asset_id("C")},
            "destination_workload": {"id": "missing-workload-1", "asset_id": "asset-missing"},
        }
    ]

    with _configured_client(store) as client:
        response = client.get(_deployment_scope_path("C", "preproduction"))

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    payload = response.json()
    assert payload["status"] == 422
    assert payload["error_code"] == "micro_affinity_group_graph_resolution_error"