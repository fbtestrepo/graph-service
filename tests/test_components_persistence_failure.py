from __future__ import annotations

from fastapi.testclient import TestClient

from src.infrastructure.main import create_app


def test_post_components_persistence_failure_returns_500_problem_details(monkeypatch) -> None:
    # Use an unreachable URI with short timeouts so the test fails fast.
    monkeypatch.setenv(
        "GRAPH_SERVICE_MONGODB_URI",
        "mongodb://127.0.0.1:27018/?serverSelectionTimeoutMS=200&connectTimeoutMS=200",
    )
    monkeypatch.setenv("GRAPH_SERVICE_MONGODB_DATABASE", "graph_service_test_failure")

    app = create_app()

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/components", json={"hello": "world"})

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")

    payload = response.json()
    assert payload["status"] == 500
    assert payload.get("error_code") == "internal_error"
