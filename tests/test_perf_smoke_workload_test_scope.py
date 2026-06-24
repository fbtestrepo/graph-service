from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.main import create_app
from tests.conftest import MICRO_AFFINITY_GROUPS_PATH


@dataclass(slots=True)
class FakeMicroAffinityGroupProcessedRepository:
    relationship_rows: list[dict[str, str]] = field(default_factory=list)
    ownership_rows: list[dict[str, str]] = field(default_factory=list)

    def list_relationship_candidates_for_workload_test_scope(
        self,
        changed_asset_ids: list[str],
        environment: str,
        session: Any | None = None,
    ) -> list[dict[str, str]]:
        changed = set(changed_asset_ids)
        return [
            row
            for row in self.relationship_rows
            if row["source_workload_asset_id"] in changed
            or row["destination_workload_asset_id"] in changed
        ]

    def list_workload_ownership_for_asset_ids(
        self,
        asset_ids: list[str],
        environment: str,
        session: Any | None = None,
    ) -> list[dict[str, str]]:
        requested = set(asset_ids)
        return [row for row in self.ownership_rows if row["workload_asset_id"] in requested]


@pytest.mark.skipif(
    os.getenv("GRAPH_SERVICE_RUN_PERF_SMOKE") != "1",
    reason="Perf smoke is opt-in. Run with GRAPH_SERVICE_RUN_PERF_SMOKE=1.",
)
def test_workload_test_scope_perf_smoke() -> None:
    app = create_app()

    relationship_rows = []
    ownership_rows = []
    for idx in range(1, 160):
        source = f"asset_{idx}"
        destination = f"asset_{idx + 1}"
        relationship_rows.append(
            {
                "source_workload_asset_id": source,
                "destination_workload_asset_id": destination,
                "source_micro_ag_id": f"mAG_{idx}",
            }
        )
        ownership_rows.append({"workload_asset_id": source, "micro_ag_id": f"mAG_{idx}"})
    ownership_rows.append({"workload_asset_id": "asset_160", "micro_ag_id": "mAG_160"})

    with TestClient(app) as client:
        client.app.state.micro_affinity_group_processed_repository = (
            FakeMicroAffinityGroupProcessedRepository(
                relationship_rows=relationship_rows,
                ownership_rows=ownership_rows,
            )
        )
        client.app.state.micro_affinity_group_deployment_scope_clock = lambda: datetime(
            2026, 6, 12, 10, 30, 0, tzinfo=UTC
        )

        latencies: list[float] = []
        total_successes = 0

        for _ in range(100):
            start = time.perf_counter()
            response = client.post(
                f"{MICRO_AFFINITY_GROUPS_PATH}/workloads/test-scope?environment=preproduction",
                json={
                    "changed_workloads": [
                        {"workload_asset_id": "asset_1"},
                        {"workload_asset_id": "asset_80"},
                        {"workload_asset_id": "asset_140"},
                    ]
                },
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies.append(elapsed_ms)
            if response.status_code == 200:
                total_successes += 1

        assert total_successes == 100

        sorted_latencies = sorted(latencies)
        p95 = sorted_latencies[max(0, int(0.95 * len(sorted_latencies)) - 1)]
        p99 = sorted_latencies[max(0, int(0.99 * len(sorted_latencies)) - 1)]

        assert p95 <= 300
        assert p99 <= 600
