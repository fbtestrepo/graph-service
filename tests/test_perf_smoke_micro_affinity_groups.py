from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.main import create_app
from tests.conftest import MICRO_AFFINITY_GROUPS_PATH


def _application_architecture_payload() -> dict[str, Any]:
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
        "relationships": [
            {
                "relationship-type": {
                    "connects": {
                        "source": {"node": "node-1"},
                        "destination": {"node": "node-2"},
                    }
                }
            }
        ],
    }


def _valid_payload(index: int) -> dict[str, Any]:
    return {
        "micro_ag_id": f"mAG_{index}",
        "name": "X" * 200000,
        "parent_asset_id": "ba0270",
        "architecture_version": "1.0.0",
        "environment": "production",
        "effective_date": "2025-01-01T14:00:00Z",
        "workloads": [
            {
                "id": "AIMC/repos/rw-orchestrator-svc_ba0116_pq0177",
                "asset_id": "pq0177",
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
class FakeTransactionManager:
    def execute(self, operation):
        return operation(None)


@pytest.mark.skipif(
    os.getenv("GRAPH_SERVICE_RUN_PERF_SMOKE") != "1",
    reason="Perf smoke is opt-in. Run with GRAPH_SERVICE_RUN_PERF_SMOKE=1.",
)
def test_micro_affinity_groups_upsert_perf_smoke() -> None:
    app = create_app()

    with TestClient(app) as client:
        client.app.state.application_architecture_repository = FakeApplicationArchitectureRepository(
            store={("ba0270", "1.0.0"): _application_architecture_payload()}
        )
        client.app.state.micro_affinity_group_repository = FakeMicroAffinityGroupRepository()
        client.app.state.micro_affinity_group_processed_repository = (
            FakeMicroAffinityGroupProcessedRepository()
        )
        client.app.state.transaction_manager = FakeTransactionManager()

        fast_successes = 0
        total_successes = 0

        for index in range(100):
            start = time.perf_counter()
            response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=_valid_payload(index))
            elapsed = time.perf_counter() - start


            if response.status_code in (200, 201):
                total_successes += 1
                if elapsed <= 2.0:
                    fast_successes += 1

        assert total_successes == 100
        assert fast_successes >= 95