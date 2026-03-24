from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from fastapi.testclient import TestClient

from src.core.domain.component import Component as DomainComponent
from src.core.domain.component_payload_record import ComponentPayloadRecord
from src.infrastructure.main import create_app


@dataclass(frozen=True, slots=True)
class FakeGraphRepository:
    component: DomainComponent | None

    def get_component(self, component_id: str) -> DomainComponent | None:
        if self.component is None:
            return None
        if self.component.component_id != component_id:
            return None
        return self.component


@dataclass(slots=True)
class FakeComponentPayloadRepository:
    records: list[ComponentPayloadRecord] = field(default_factory=list)

    def add(self, record: ComponentPayloadRecord) -> None:
        self.records.append(record)


def test_get_component_not_found_returns_404_problem_details() -> None:
    app = create_app()
    with TestClient(app) as client:
        client.app.state.graph_repository = FakeGraphRepository(component=None)
        response = client.get("/components/missing")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")

    payload = response.json()
    assert payload["status"] == 404
    assert payload.get("error_code") == "component_not_found"


def test_get_component_success_returns_component() -> None:
    component = DomainComponent(component_id="comp-1", name="Component", version=None, metadata={})

    app = create_app()
    with TestClient(app) as client:
        client.app.state.graph_repository = FakeGraphRepository(component=component)
        response = client.get("/components/comp-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["component_id"] == "comp-1"
    assert payload["name"] == "Component"


def test_post_components_echo_object_returns_same_json() -> None:
    app = create_app()
    with TestClient(app) as client:
        repo = FakeComponentPayloadRepository()
        client.app.state.component_payload_repository = repo
        request_payload = {"hello": "world", "n": 123, "ok": True, "none": None}
        response = client.post("/components", json=request_payload)

    assert response.status_code == 200
    assert response.json() == request_payload

    assert len(repo.records) == 1
    assert repo.records[0].payload == request_payload
    assert isinstance(repo.records[0].received_at, datetime)


def test_post_components_echo_array_returns_same_json() -> None:
    app = create_app()
    with TestClient(app) as client:
        repo = FakeComponentPayloadRepository()
        client.app.state.component_payload_repository = repo
        request_payload = [1, 2, 3, {"x": True}]
        response = client.post("/components", json=request_payload)

    assert response.status_code == 200
    assert response.json() == request_payload

    assert len(repo.records) == 1
    assert repo.records[0].payload == request_payload
    assert isinstance(repo.records[0].received_at, datetime)


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