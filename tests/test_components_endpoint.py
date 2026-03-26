from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.main import create_app


def _valid_payload(*, node_id: str = "node-1", include_optional: bool = True) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "node-id": node_id,
        "node-type": "component",
        "node-name": "Example Node",
        "metadata": {"parent-asset-id": "asset-1", "extra": "ok"},
    }
    if include_optional:
        payload["interfaces"] = [
            {"interface-local-id": "if-1", "interface-type": "ethernet"}
        ]
        payload["relationships"] = [
            {
                "relationship-type": "connects-to",
                "source": {"node-id": node_id, "interface-local-id": "if-1"},
                "target": {"node-id": "node-2", "interface-local-id": "if-2"},
            }
        ]
    return payload


@dataclass(slots=True)
class FakeComponentNodeRepository:
    store: dict[str, dict[str, Any]] = field(default_factory=dict)

    def upsert(self, node_id: str, payload: dict[str, Any]) -> bool:
        created = node_id not in self.store
        self.store[node_id] = payload
        return created

    def get_by_node_id(self, node_id: str) -> dict[str, Any] | None:
        return self.store.get(node_id)


def test_post_components_first_time_returns_201_and_echoes_payload() -> None:
    app = create_app()
    with TestClient(app) as client:
        repo = FakeComponentNodeRepository()
        client.app.state.component_node_repository = repo

        request_payload = _valid_payload(node_id="node-1")
        response = client.post("/components", json=request_payload)

    assert response.status_code == 201
    assert response.json() == request_payload


def test_post_components_second_time_returns_200_and_replaces_payload() -> None:
    app = create_app()
    with TestClient(app) as client:
        repo = FakeComponentNodeRepository()
        client.app.state.component_node_repository = repo

        first_payload = _valid_payload(node_id="node-1")
        first_response = client.post("/components", json=first_payload)
        assert first_response.status_code == 201

        second_payload = _valid_payload(node_id="node-1", include_optional=False)
        second_payload["node-name"] = "Updated Node"
        second_response = client.post("/components", json=second_payload)

        assert second_response.status_code == 200
        assert second_response.json() == second_payload

        get_response = client.get("/components/node-1")
        assert get_response.status_code == 200
        assert get_response.json() == second_payload


def test_get_component_node_not_found_returns_404_problem_details() -> None:
    app = create_app()
    with TestClient(app) as client:
        repo = FakeComponentNodeRepository()
        client.app.state.component_node_repository = repo

        response = client.get("/components/missing")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")

    payload = response.json()
    assert payload["status"] == 404
    assert payload.get("error_code") == "component_not_found"

def test_post_components_malformed_json_returns_400_problem_details() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/components",
            data="{",
            headers={"content-type": "application/json"},
        )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")

    payload = response.json()
    assert payload["status"] == 400
    assert payload["title"] == "Malformed JSON"


def test_post_components_missing_body_returns_422_problem_details() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post("/components")

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")

    payload = response.json()
    assert payload["status"] == 422
    assert payload["title"] == "Validation Error"


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(lambda p: {k: v for k, v in p.items() if k != "node-id"}, id="missing-node-id"),
        pytest.param(
            lambda p: {**p, "metadata": {}},
            id="missing-metadata-parent-asset-id",
        ),
        pytest.param(lambda p: {**p, "extra": 1}, id="unknown-top-level"),
        pytest.param(
            lambda p: {
                **p,
                "interfaces": [
                    {
                        "interface-local-id": "if-1",
                        "interface-type": "ethernet",
                        "unexpected": "x",
                    }
                ],
            },
            id="unknown-nested-interface-field",
        ),
        pytest.param(lambda p: {**p, "relationaships": []}, id="relationaships-typo"),
        pytest.param(lambda p: {**p, "node-id": 123}, id="wrong-type-node-id"),
        pytest.param(lambda p: {**p, "interfaces": "nope"}, id="wrong-type-interfaces"),
        pytest.param(lambda _p: [1, 2, 3], id="non-object-root"),
    ],
)
def test_post_components_invalid_payloads_return_422_problem_details(payload) -> None:
    app = create_app()
    with TestClient(app) as client:
        base = _valid_payload(node_id="node-1")
        request_payload = payload(base) if callable(payload) else payload
        response = client.post("/components", json=request_payload)

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == 422
    assert body.get("error_code") == "validation_failed"


def test_post_components_minimal_payload_returns_success() -> None:
    app = create_app()
    with TestClient(app) as client:
        repo = FakeComponentNodeRepository()
        client.app.state.component_node_repository = repo

        request_payload = _valid_payload(node_id="node-min", include_optional=False)
        response = client.post("/components", json=request_payload)

    assert response.status_code == 201
    assert response.json() == request_payload