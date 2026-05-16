from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

import pytest
from fastapi.testclient import TestClient

from src.core.domain.dependency_edge import DependencyEdge
from src.infrastructure.main import create_app
from tests.conftest import component_dependencies_path


@dataclass(slots=True)
class FakeComponentNodeRepository:
    existing_nodes: set[str] = field(default_factory=set)
    outgoing_by_source: dict[str, list[DependencyEdge]] = field(default_factory=dict)
    incoming_by_target: dict[str, list[DependencyEdge]] = field(default_factory=dict)

    def upsert(self, node_id: str, payload: dict) -> bool:  # pragma: no cover
        raise NotImplementedError

    def get_by_node_id(self, node_id: str):
        return {"node-id": node_id} if node_id in self.existing_nodes else None

    def get_outgoing_relationship_edges(self, source_node_ids: set[str]) -> list[DependencyEdge]:
        edges: list[DependencyEdge] = []
        for source in source_node_ids:
            edges.extend(self.outgoing_by_source.get(source, []))
        return edges

    def get_incoming_relationship_edges(self, target_node_ids: set[str]) -> list[DependencyEdge]:
        edges: list[DependencyEdge] = []
        for target in target_node_ids:
            edges.extend(self.incoming_by_target.get(target, []))
        return edges


@pytest.mark.skipif(
    os.getenv("GRAPH_SERVICE_RUN_PERF_SMOKE") != "1",
    reason="Perf smoke is opt-in. Run with GRAPH_SERVICE_RUN_PERF_SMOKE=1.",
)
def test_dependencies_get_perf_smoke() -> None:
    app = create_app()

    root = "root"
    edges = [
        DependencyEdge("depends-on", root, f"n{i}")
        for i in range(120)
    ]

    repo = FakeComponentNodeRepository(
        existing_nodes={root} | {f"n{i}" for i in range(120)},
        outgoing_by_source={root: edges},
        incoming_by_target={},
    )

    with TestClient(app) as client:
        client.app.state.component_node_repository = repo

        fast_successes = 0
        total_successes = 0

        for _i in range(100):
            start = time.perf_counter()
            response = client.get(component_dependencies_path(root))
            elapsed = time.perf_counter() - start

            if response.status_code == 200:
                total_successes += 1
                if elapsed <= 1.0:
                    fast_successes += 1

        assert total_successes == 100
        assert fast_successes >= 95
