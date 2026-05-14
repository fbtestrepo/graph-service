from __future__ import annotations

from collections.abc import Iterator
from time import monotonic, sleep
from uuid import uuid4

import pytest
from fastapi import FastAPI
from pymongo import MongoClient

from src.infrastructure.main import create_app


@pytest.fixture(scope="session")
def mongodb_replica_set_uri() -> Iterator[str]:
    """Session-scoped MongoDB replica-set URI for transaction-capable integration tests."""

    try:
        import docker

        docker.from_env().ping()
    except Exception:
        pytest.skip("Docker is required for MongoDB integration tests (testcontainers)")

    from testcontainers.core.container import DockerContainer

    with (
        DockerContainer("mongo:7.0")
        .with_exposed_ports(27017)
        .with_command("mongod --replSet rs0 --bind_ip_all") as container
    ):
        port = container.get_exposed_port(27017)
        direct_uri = f"mongodb://127.0.0.1:{port}/?directConnection=true"
        direct_client = MongoClient(direct_uri, serverSelectionTimeoutMS=5000)

        deadline = monotonic() + 30
        while True:
            try:
                direct_client.admin.command("ping")
                break
            except Exception:
                if monotonic() >= deadline:
                    raise
                sleep(0.5)

        try:
            direct_client.admin.command(
                "replSetInitiate",
                {"_id": "rs0", "members": [{"_id": 0, "host": "localhost:27017"}]},
            )
        except Exception as exc:
            if "already initialized" not in str(exc):
                raise

        replica_client = MongoClient(direct_uri, serverSelectionTimeoutMS=5000)

        deadline = monotonic() + 30
        while True:
            try:
                hello = replica_client.admin.command("hello")
                if hello.get("isWritablePrimary"):
                    break
            except Exception:
                pass

            if monotonic() >= deadline:
                raise RuntimeError("MongoDB replica set did not become writable in time")
            sleep(0.5)

        try:
            yield direct_uri
        finally:
            direct_client.close()
            replica_client.close()


@pytest.fixture()
def app_with_mongodb(monkeypatch: pytest.MonkeyPatch, mongodb_replica_set_uri: str) -> FastAPI:
    """Create an app configured to use the test MongoDB replica set."""

    mongodb_database = f"graph_service_test_{uuid4().hex}"

    monkeypatch.setenv("GRAPH_SERVICE_MONGODB_URI", mongodb_replica_set_uri)
    monkeypatch.setenv("GRAPH_SERVICE_MONGODB_DATABASE", mongodb_database)

    return create_app()