from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.main import create_app
from tests.conftest import APPLICATION_ARCHITECTURES_PATH


def _valid_payload(
    *,
    asset_id: str = "Asset123",
    version: str = "1.0.0",
    created: str = "2026-05-02",
    include_optional: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "metadata": {
            "AssetID": asset_id,
            "version": version,
            "created": created,
        },
        "nodes": [],
        "relationships": [],
    }
    if include_optional:
        payload["adrs"] = ["https://example.test/adr/1"]
    return payload


@dataclass(slots=True)
class FakeApplicationArchitectureRepository:
    store: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)

    def upsert(self, asset_id: str, version: str, payload: dict[str, Any]) -> bool:
        key = (asset_id, version)
        created = key not in self.store
        self.store[key] = payload
        return created


def test_post_application_architectures_first_time_returns_201_and_echoes_payload() -> None:
    app = create_app()
    with TestClient(app) as client:
        repo = FakeApplicationArchitectureRepository()
        client.app.state.application_architecture_repository = repo

        request_payload = _valid_payload(asset_id="Asset123", version="1.0.0")
        response = client.post(APPLICATION_ARCHITECTURES_PATH, json=request_payload)

    assert response.status_code == 201
    assert response.json() == request_payload


def test_post_application_architectures_second_time_returns_200_and_replaces_payload() -> None:
    app = create_app()
    with TestClient(app) as client:
        repo = FakeApplicationArchitectureRepository()
        client.app.state.application_architecture_repository = repo

        first_payload = _valid_payload(asset_id="Asset123", version="1.0.0")
        first_response = client.post(APPLICATION_ARCHITECTURES_PATH, json=first_payload)
        assert first_response.status_code == 201

        second_payload = _valid_payload(
            asset_id="Asset123",
            version="1.0.0",
            include_optional=False,
        )
        second_payload["nodes"] = [
            {
                "unique-id": "service-1",
                "node-type": "service",
                "name": "Payments API",
                "description": "Updated node payload",
            }
        ]
        second_response = client.post(APPLICATION_ARCHITECTURES_PATH, json=second_payload)

    assert second_response.status_code == 200
    assert second_response.json() == second_payload


def test_post_application_architectures_different_version_returns_201() -> None:
    app = create_app()
    with TestClient(app) as client:
        repo = FakeApplicationArchitectureRepository()
        client.app.state.application_architecture_repository = repo

        first_response = client.post(
            APPLICATION_ARCHITECTURES_PATH,
            json=_valid_payload(asset_id="Asset123", version="1.0.0"),
        )
        assert first_response.status_code == 201

        second_response = client.post(
            APPLICATION_ARCHITECTURES_PATH,
            json=_valid_payload(asset_id="Asset123", version="1.0.1"),
        )

    assert second_response.status_code == 201


def test_post_application_architectures_malformed_json_returns_400_problem_details() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            APPLICATION_ARCHITECTURES_PATH,
            data="{",
            headers={"content-type": "application/json"},
        )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")

    payload = response.json()
    assert payload["status"] == 400
    assert payload["title"] == "Malformed JSON"


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(lambda p: {k: v for k, v in p.items() if k != "metadata"}, id="missing-metadata"),
        pytest.param(lambda p: {**p, "metadata": []}, id="non-object-metadata"),
        pytest.param(lambda p: {**p, "metadata": {**p["metadata"], "AssetID": "Asset-123"}}, id="invalid-asset-id"),
        pytest.param(lambda p: {**p, "metadata": {**p["metadata"], "version": "v1.0.0"}}, id="invalid-version"),
        pytest.param(lambda p: {**p, "metadata": {**p["metadata"], "created": "2026-02-30"}}, id="invalid-created"),
        pytest.param(lambda p: {**p, "nodes": "nope"}, id="invalid-calm-shape"),
    ],
)
def test_post_application_architectures_invalid_payloads_return_422_problem_details(payload) -> None:
    app = create_app()
    with TestClient(app) as client:
        repo = FakeApplicationArchitectureRepository()
        client.app.state.application_architecture_repository = repo

        base = _valid_payload(asset_id="Asset123", version="1.0.0")
        response = client.post(APPLICATION_ARCHITECTURES_PATH, json=payload(base))

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == 422
    assert body.get("error_code") == "validation_failed"
    assert repo.store == {}


def test_root_application_architectures_path_is_not_supported() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            APPLICATION_ARCHITECTURES_PATH.removeprefix("/v1"),
            json=_valid_payload(asset_id="Asset123", version="1.0.0"),
        )

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["title"] == "Not Found"
