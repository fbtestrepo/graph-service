from __future__ import annotations

from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi import FastAPI

from src.infrastructure.main import create_app


@pytest.fixture(scope="session")
def mongodb_container() -> Iterator[object]:
    """Session-scoped MongoDB container for integration tests."""

    try:
        import docker

        docker.from_env().ping()
    except Exception:
        pytest.skip("Docker is required for MongoDB integration tests (testcontainers)")

    from testcontainers.mongodb import MongoDbContainer

    with MongoDbContainer("mongo:7.0") as container:
        yield container


@pytest.fixture()
def app_with_mongodb(monkeypatch: pytest.MonkeyPatch, mongodb_container: object) -> FastAPI:
    """Creates an app configured to use the test MongoDB container."""

    # The container exposes a connection URL; keep the attribute access dynamic to avoid
    # type-checker coupling to the dependency.
    mongodb_uri = mongodb_container.get_connection_url()  # type: ignore[attr-defined]
    mongodb_database = f"graph_service_test_{uuid4().hex}"

    monkeypatch.setenv("GRAPH_SERVICE_MONGODB_URI", mongodb_uri)
    monkeypatch.setenv("GRAPH_SERVICE_MONGODB_DATABASE", mongodb_database)

    return create_app()
