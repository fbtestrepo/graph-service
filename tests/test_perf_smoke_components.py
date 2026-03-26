from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.main import create_app


@dataclass(slots=True)
class FakeComponentNodeRepository:
    store: dict[str, dict[str, Any]] = field(default_factory=dict)

    def upsert(self, node_id: str, payload: dict[str, Any]) -> bool:
        created = node_id not in self.store
        self.store[node_id] = payload
        return created

    def get_by_node_id(self, node_id: str) -> dict[str, Any] | None:
        return self.store.get(node_id)


def _valid_payload(node_id: str) -> dict[str, Any]:
    return {
        "node-id": node_id,
        "node-type": "component",
        "node-name": "Perf Smoke Node",
        "metadata": {"parent-asset-id": "asset-1"},
    }


@pytest.mark.skipif(
    os.getenv("GRAPH_SERVICE_RUN_PERF_SMOKE") != "1",
    reason="Perf smoke is opt-in. Run with GRAPH_SERVICE_RUN_PERF_SMOKE=1.",
)
def test_components_upsert_perf_smoke() -> None:
    app = create_app()

    with TestClient(app) as client:
        client.app.state.component_node_repository = FakeComponentNodeRepository()

        fast_successes = 0
        total_successes = 0

        for i in range(100):
            request_payload = _valid_payload(node_id=f"node-{i}")

            start = time.perf_counter()
            response = client.post("/components", json=request_payload)
            elapsed = time.perf_counter() - start

            if response.status_code in (200, 201):
                total_successes += 1
                if elapsed <= 1.0:
                    fast_successes += 1

        assert total_successes == 100
        assert fast_successes >= 95
