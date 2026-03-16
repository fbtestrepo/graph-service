from __future__ import annotations

from fastapi.testclient import TestClient

from src.infrastructure.main import create_app


def test_component_validate_success_returns_204() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/components/validate",
            json={"component_id": "comp-1", "name": "Component"},
        )

    assert response.status_code == 204
    assert response.content == b""


def test_component_validate_malformed_json_returns_400_problem_details() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/components/validate",
            data="{",
            headers={"content-type": "application/json"},
        )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")

    payload = response.json()
    assert payload["status"] == 400
    assert payload["title"] == "Malformed JSON"


def test_component_validate_schema_violation_returns_422_problem_details() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/components/validate",
            json={"component_id": "", "name": "Component"},
        )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")

    payload = response.json()
    assert payload["status"] == 422
    assert payload["title"] == "Validation Error"