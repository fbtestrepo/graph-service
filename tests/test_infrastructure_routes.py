from __future__ import annotations

from fastapi.testclient import TestClient

from src.infrastructure.main import create_app
from tests.conftest import DOCS_PATH, HEALTH_PATH, OPENAPI_PATH, REDOC_PATH


def test_root_health_route_remains_available() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get(HEALTH_PATH)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "dependency-graph-service"


def test_root_docs_routes_remain_available() -> None:
    app = create_app()

    with TestClient(app) as client:
        docs_response = client.get(DOCS_PATH)
        redoc_response = client.get(REDOC_PATH)
        openapi_response = client.get(OPENAPI_PATH)

    assert docs_response.status_code == 200
    assert redoc_response.status_code == 200
    assert openapi_response.status_code == 200


def test_root_openapi_publishes_only_v1_business_routes() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get(OPENAPI_PATH)

    assert response.status_code == 200
    paths = response.json()["paths"]

    assert "/v1/components/validate" in paths
    assert "/v1/components" in paths
    assert "/v1/components/{component_id}" in paths
    assert "/v1/components/{node_id}/dependencies" in paths
    assert "/v1/application-architectures" in paths
    assert "/v1/micro-affinity-groups" in paths
    assert HEALTH_PATH in paths

    assert "/components/validate" not in paths
    assert "/components" not in paths
    assert "/components/{component_id}" not in paths
    assert "/components/{node_id}/dependencies" not in paths
    assert "/application-architectures" not in paths
    assert "/micro-affinity-groups" not in paths