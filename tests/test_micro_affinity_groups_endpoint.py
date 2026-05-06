from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.main import create_app


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


def _valid_payload(*, include_name: bool = True) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "micro-ag-id": "mAG_A",
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
    if include_name:
        payload["name"] = "Micro Affinity Group A"
    return payload


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


def _configured_client() -> tuple[TestClient, FakeMicroAffinityGroupRepository]:
    app = create_app()
    client = TestClient(app)
    architecture_repo = FakeApplicationArchitectureRepository(
        store={("ba0270", "1.0.0"): _application_architecture_payload()}
    )
    repository = FakeMicroAffinityGroupRepository()
    client.app.state.application_architecture_repository = architecture_repo
    client.app.state.micro_affinity_group_repository = repository
    return client, repository


def test_post_micro_affinity_groups_first_time_returns_201_and_stored_payload() -> None:
    app = create_app()
    with TestClient(app) as client:
        architecture_repo = FakeApplicationArchitectureRepository(
            store={("ba0270", "1.0.0"): _application_architecture_payload()}
        )
        repository = FakeMicroAffinityGroupRepository()
        client.app.state.application_architecture_repository = architecture_repo
        client.app.state.micro_affinity_group_repository = repository

        request_payload = _valid_payload(include_name=True)
        response = client.post("/micro-affinity-groups", json=request_payload)

    assert response.status_code == 201
    assert response.json() == request_payload


def test_post_micro_affinity_groups_accepts_omitted_name() -> None:
    app = create_app()
    with TestClient(app) as client:
        architecture_repo = FakeApplicationArchitectureRepository(
            store={("ba0270", "1.0.0"): _application_architecture_payload()}
        )
        repository = FakeMicroAffinityGroupRepository()
        client.app.state.application_architecture_repository = architecture_repo
        client.app.state.micro_affinity_group_repository = repository

        request_payload = _valid_payload(include_name=False)
        response = client.post("/micro-affinity-groups", json=request_payload)

    assert response.status_code == 201
    assert response.json() == request_payload


def test_post_micro_affinity_groups_malformed_json_returns_400_problem_details() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/micro-affinity-groups",
            data="{",
            headers={"content-type": "application/json"},
        )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    payload = response.json()
    assert payload["status"] == 400
    assert payload["title"] == "Malformed JSON"


@pytest.mark.parametrize(
    "payload_builder",
    [
        pytest.param(
            lambda p: {**p, "architecture-version": "v1.0.0"},
            id="invalid-architecture-version",
        ),
        pytest.param(
            lambda p: {**p, "effective-date": "2025-01-01"},
            id="invalid-effective-date",
        ),
        pytest.param(lambda p: {**p, "unexpected": 1}, id="unknown-top-level-field"),
        pytest.param(
            lambda p: {
                **p,
                "workloads": [{**p["workloads"][0], "unexpected": "x"}],
            },
            id="unknown-workload-field",
        ),
        pytest.param(
            lambda p: {
                **p,
                "workloads": [p["workloads"][0], dict(p["workloads"][0])],
            },
            id="duplicate-workload-id",
        ),
        pytest.param(lambda p: {**p, "workloads": []}, id="empty-workloads"),
        pytest.param(lambda p: {**p, "architecture-version": 100}, id="wrong-type-version"),
    ],
)
def test_post_micro_affinity_groups_invalid_payloads_return_422_problem_details(
    payload_builder,
) -> None:
    client, repository = _configured_client()
    with client:
        request_payload = payload_builder(_valid_payload())
        response = client.post("/micro-affinity-groups", json=request_payload)

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == 422
    assert body.get("error_code") == "validation_failed"
    assert repository.store == {}


def test_post_micro_affinity_groups_missing_architecture_returns_422_problem_details() -> None:
    app = create_app()
    with TestClient(app) as client:
        client.app.state.application_architecture_repository = FakeApplicationArchitectureRepository()
        repository = FakeMicroAffinityGroupRepository()
        client.app.state.micro_affinity_group_repository = repository

        response = client.post("/micro-affinity-groups", json=_valid_payload())

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    payload = response.json()
    assert payload["status"] == 422
    assert repository.store == {}


def test_post_micro_affinity_groups_missing_service_node_returns_422_problem_details() -> None:
    app = create_app()
    with TestClient(app) as client:
        architecture = _application_architecture_payload()
        architecture["nodes"][0]["metadata"]["code-repo"] = "AIMC/repos/another-service"
        client.app.state.application_architecture_repository = FakeApplicationArchitectureRepository(
            store={("ba0270", "1.0.0"): architecture}
        )
        repository = FakeMicroAffinityGroupRepository()
        client.app.state.micro_affinity_group_repository = repository

        response = client.post("/micro-affinity-groups", json=_valid_payload())

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    payload = response.json()
    assert payload["status"] == 422
    assert repository.store == {}


def test_post_micro_affinity_groups_asset_id_mismatch_returns_422_problem_details() -> None:
    app = create_app()
    with TestClient(app) as client:
        architecture = _application_architecture_payload()
        architecture["nodes"][0]["metadata"]["asset-id"] = "different-asset"
        client.app.state.application_architecture_repository = FakeApplicationArchitectureRepository(
            store={("ba0270", "1.0.0"): architecture}
        )
        repository = FakeMicroAffinityGroupRepository()
        client.app.state.micro_affinity_group_repository = repository

        response = client.post("/micro-affinity-groups", json=_valid_payload())

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    payload = response.json()
    assert payload["status"] == 422
    assert repository.store == {}


def test_post_micro_affinity_groups_second_time_returns_200_and_overwrites_payload() -> None:
    app = create_app()
    with TestClient(app) as client:
        architecture_repo = FakeApplicationArchitectureRepository(
            store={("ba0270", "1.0.0"): _application_architecture_payload()}
        )
        repository = FakeMicroAffinityGroupRepository()
        client.app.state.application_architecture_repository = architecture_repo
        client.app.state.micro_affinity_group_repository = repository

        first_payload = _valid_payload(include_name=True)
        first_response = client.post("/micro-affinity-groups", json=first_payload)
        assert first_response.status_code == 201

        second_payload = _valid_payload(include_name=False)
        second_payload["environment"] = "production"
        second_payload["effective-date"] = "2025-02-01T10:00:00Z"

        second_response = client.post("/micro-affinity-groups", json=second_payload)

    assert second_response.status_code == 200
    assert second_response.json() == second_payload


def test_post_micro_affinity_groups_different_environment_returns_201_and_coexists() -> None:
    app = create_app()
    with TestClient(app) as client:
        architecture_repo = FakeApplicationArchitectureRepository(
            store={("ba0270", "1.0.0"): _application_architecture_payload()}
        )
        repository = FakeMicroAffinityGroupRepository()
        client.app.state.application_architecture_repository = architecture_repo
        client.app.state.micro_affinity_group_repository = repository

        first_response = client.post("/micro-affinity-groups", json=_valid_payload(include_name=True))
        assert first_response.status_code == 201

        second_payload = _valid_payload(include_name=True)
        second_payload["environment"] = "staging"
        second_response = client.post("/micro-affinity-groups", json=second_payload)

    assert second_response.status_code == 201
    assert second_response.json() == second_payload