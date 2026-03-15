from __future__ import annotations

from dataclasses import dataclass

from fastapi.testclient import TestClient

from src.core.domain.component import Component as DomainComponent
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