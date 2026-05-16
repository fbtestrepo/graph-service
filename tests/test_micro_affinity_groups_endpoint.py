from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.main import create_app
from tests.conftest import MICRO_AFFINITY_GROUPS_PATH


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


def _expected_processed_payload(request_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **request_payload,
        "relationships": [
            {
                "source-workload": request_payload["workloads"][0],
                "destination-workload": {
                    "id": "AIMC/repos/rw-cap-svc_ba0116_dh6980",
                    "asset-id": "dh6980",
                },
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
    store: dict[tuple[str, str, str], dict[str, Any]] = field(default_factory=dict)

    def upsert(
        self,
        micro_ag_id: str,
        environment: str,
        architecture_version: str,
        payload: dict[str, Any],
        session: Any | None = None,
    ) -> bool:
        key = (micro_ag_id, environment, architecture_version)
        created = key not in self.store
        self.store[key] = payload
        return created


@dataclass(slots=True)
class FakeMicroAffinityGroupProcessedRepository:
    store: dict[tuple[str, str, str], dict[str, Any]] = field(default_factory=dict)
    fail_on_upsert: bool = False

    def upsert(
        self,
        micro_ag_id: str,
        environment: str,
        architecture_version: str,
        payload: dict[str, Any],
        session: Any | None = None,
    ) -> bool:
        if self.fail_on_upsert:
            raise RuntimeError("processed write failed")

        key = (micro_ag_id, environment, architecture_version)
        created = key not in self.store
        self.store[key] = payload
        return created


@dataclass(slots=True)
class FakeTransactionManager:
    repositories: tuple[Any, ...] = ()

    def execute(self, operation):
        snapshots = [deepcopy(repository.store) for repository in self.repositories]
        try:
            return operation(None)
        except Exception:
            for repository, snapshot in zip(self.repositories, snapshots, strict=True):
                repository.store = snapshot
            raise


def _configured_client(
    architecture: dict[str, Any] | None = None,
    *,
    processed_fail: bool = False,
) -> tuple[TestClient, FakeMicroAffinityGroupRepository, FakeMicroAffinityGroupProcessedRepository]:
    app = create_app()
    client = TestClient(app, raise_server_exceptions=False)
    architecture_repo = FakeApplicationArchitectureRepository()
    if architecture is not None:
        architecture_repo.store[("ba0270", "1.0.0")] = architecture

    repository = FakeMicroAffinityGroupRepository()
    processed_repository = FakeMicroAffinityGroupProcessedRepository(fail_on_upsert=processed_fail)
    client.app.state.application_architecture_repository = architecture_repo
    client.app.state.micro_affinity_group_repository = repository
    client.app.state.micro_affinity_group_processed_repository = processed_repository
    client.app.state.transaction_manager = FakeTransactionManager(
        repositories=(repository, processed_repository)
    )
    return client, repository, processed_repository


def test_post_micro_affinity_groups_first_time_returns_201_and_processed_payload() -> None:
    client, _, _ = _configured_client(_application_architecture_payload())

    with client:
        request_payload = _valid_payload(include_name=True)
        response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=request_payload)

    assert response.status_code == 201
    assert response.json() == _expected_processed_payload(request_payload)


def test_post_micro_affinity_groups_accepts_omitted_name() -> None:
    client, _, _ = _configured_client(_application_architecture_payload())

    with client:
        request_payload = _valid_payload(include_name=False)
        response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=request_payload)

    assert response.status_code == 201
    assert response.json() == _expected_processed_payload(request_payload)


def test_post_micro_affinity_groups_malformed_json_returns_400_problem_details() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            MICRO_AFFINITY_GROUPS_PATH,
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
        pytest.param(lambda p: {**p, "relationships": []}, id="client-supplied-relationships"),
    ],
)
def test_post_micro_affinity_groups_invalid_payloads_return_422_problem_details(
    payload_builder,
) -> None:
    client, repository, _ = _configured_client(_application_architecture_payload())

    with client:
        request_payload = payload_builder(_valid_payload())
        response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=request_payload)

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == 422
    assert body.get("error_code") == "validation_failed"
    assert repository.store == {}


def test_post_micro_affinity_groups_missing_architecture_returns_422_problem_details() -> None:
    client, repository, processed_repository = _configured_client(None)

    with client:
        response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=_valid_payload())

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["status"] == 422
    assert repository.store == {}
    assert processed_repository.store == {}


def test_post_micro_affinity_groups_missing_source_service_returns_422_problem_details() -> None:
    architecture = _application_architecture_payload()
    architecture["nodes"][0]["metadata"]["code-repo"] = "AIMC/repos/another-service"
    client, repository, processed_repository = _configured_client(architecture)

    with client:
        response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=_valid_payload())

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert repository.store == {}
    assert processed_repository.store == {}


def test_post_micro_affinity_groups_unresolved_destination_returns_422_problem_details() -> None:
    architecture = _application_architecture_payload()
    architecture["relationships"][0]["relationship-type"]["connects"]["destination"][
        "node"
    ] = "node-missing"
    client, repository, processed_repository = _configured_client(architecture)

    with client:
        response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=_valid_payload())

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert repository.store == {}
    assert processed_repository.store == {}


def test_post_micro_affinity_groups_processed_write_failure_returns_500() -> None:
    client, _, _ = _configured_client(
        _application_architecture_payload(),
        processed_fail=True,
    )

    with client:
        response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=_valid_payload())

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")


def test_post_micro_affinity_groups_second_time_returns_200_and_overwrites_payload() -> None:
    client, _, _ = _configured_client(_application_architecture_payload())

    with client:
        first_payload = _valid_payload(include_name=True)
        first_response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=first_payload)
        assert first_response.status_code == 201

        second_payload = _valid_payload(include_name=False)
        second_payload["effective-date"] = "2025-02-01T10:00:00Z"
        second_response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=second_payload)

    assert second_response.status_code == 200
    assert second_response.json() == _expected_processed_payload(second_payload)


def test_post_micro_affinity_groups_different_environment_returns_201_and_coexists() -> None:
    client, _, _ = _configured_client(_application_architecture_payload())

    with client:
        first_response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=_valid_payload(include_name=True))
        assert first_response.status_code == 201

        second_payload = _valid_payload(include_name=True)
        second_payload["environment"] = "staging"
        second_response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=second_payload)

    assert second_response.status_code == 201
    assert second_response.json() == _expected_processed_payload(second_payload)


def test_root_micro_affinity_groups_path_is_not_supported() -> None:
    client, _, _ = _configured_client(_application_architecture_payload())

    with client:
        response = client.post(MICRO_AFFINITY_GROUPS_PATH.removeprefix("/v1"), json=_valid_payload())

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["title"] == "Not Found"