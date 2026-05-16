from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from src.core.domain.dependency_edge import DependencyEdge
from src.infrastructure.main import create_app
from tests.conftest import component_dependencies_path


def _payload(*, node_id: str, relationships: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "node-id": node_id,
        "node-type": "micro-affinity-group",
        "node-name": f"{node_id}",
        "metadata": {"parent-asset-id": "asset-1"},
    }
    if relationships is not None:
        payload["interfaces"] = [
            {"interface-local-id": "workload_1", "interface-type": "workload"}
        ]
        payload["relationships"] = relationships
    return payload


def _depends_on(*, source_node_id: str, target_node_id: str) -> dict[str, Any]:
    return {
        "relationship-type": "depends-on",
        "source": {"node-id": source_node_id, "interface-local-id": "workload_1"},
        "target": {"node-id": target_node_id, "interface-local-id": "workload_1"},
    }


@dataclass(slots=True)
class FakeComponentNodeRepository:
    store: dict[str, dict[str, Any]] = field(default_factory=dict)

    def upsert(self, node_id: str, payload: dict[str, Any]) -> bool:
        created = node_id not in self.store
        self.store[node_id] = payload
        return created

    def get_by_node_id(self, node_id: str) -> dict[str, Any] | None:
        return self.store.get(node_id)

    def get_outgoing_relationship_edges(self, source_node_ids: set[str]) -> list[DependencyEdge]:
        edges: list[DependencyEdge] = []
        for source_node_id in source_node_ids:
            doc = self.store.get(source_node_id)
            if not doc:
                continue
            relationships = doc.get("relationships") or []
            if not isinstance(relationships, list):
                continue

            for relationship in relationships:
                if not isinstance(relationship, dict):
                    continue
                source = relationship.get("source")
                target = relationship.get("target")
                if not isinstance(source, dict) or not isinstance(target, dict):
                    continue
                if source.get("node-id") != source_node_id:
                    continue
                relationship_type = relationship.get("relationship-type")
                target_node_id = target.get("node-id")
                if not isinstance(relationship_type, str) or not isinstance(target_node_id, str):
                    continue

                edges.append(
                    DependencyEdge(
                        relationship_type=relationship_type,
                        source_node_id=source_node_id,
                        target_node_id=target_node_id,
                    )
                )

        return edges

    def get_incoming_relationship_edges(self, target_node_ids: set[str]) -> list[DependencyEdge]:
        edges: list[DependencyEdge] = []
        for doc_node_id, doc in self.store.items():
            relationships = doc.get("relationships") or []
            if not isinstance(relationships, list):
                continue

            for relationship in relationships:
                if not isinstance(relationship, dict):
                    continue
                source = relationship.get("source")
                target = relationship.get("target")
                if not isinstance(source, dict) or not isinstance(target, dict):
                    continue
                if source.get("node-id") != doc_node_id:
                    continue
                target_node_id = target.get("node-id")
                if target_node_id not in target_node_ids:
                    continue
                relationship_type = relationship.get("relationship-type")
                if not isinstance(relationship_type, str) or not isinstance(target_node_id, str):
                    continue

                edges.append(
                    DependencyEdge(
                        relationship_type=relationship_type,
                        source_node_id=doc_node_id,
                        target_node_id=target_node_id,
                    )
                )

        return edges


def test_get_component_dependencies_returns_sample_shape_for_seeded_chain() -> None:
    app = create_app()
    with TestClient(app) as client:
        repo = FakeComponentNodeRepository()
        client.app.state.component_node_repository = repo

        repo.upsert(
            "mAG_A",
            _payload(
                node_id="mAG_A",
                relationships=[_depends_on(source_node_id="mAG_A", target_node_id="mAG_B")],
            ),
        )
        repo.upsert(
            "mAG_B",
            _payload(
                node_id="mAG_B",
                relationships=[_depends_on(source_node_id="mAG_B", target_node_id="mAG_C")],
            ),
        )
        repo.upsert(
            "mAG_C",
            _payload(
                node_id="mAG_C",
                relationships=[_depends_on(source_node_id="mAG_C", target_node_id="mAG_D")],
            ),
        )
        repo.upsert("mAG_D", _payload(node_id="mAG_D", relationships=None))

        response = client.get(component_dependencies_path("mAG_A"))

    assert response.status_code == 200

    expected = json.loads(
        Path("specs/sample-component-dependencies/sample-mag-dependencies.json").read_text(
            encoding="utf-8"
        )
    )
    assert response.json() == expected


def test_get_component_dependencies_missing_root_returns_404_problem_details() -> None:
    app = create_app()
    with TestClient(app) as client:
        repo = FakeComponentNodeRepository()
        client.app.state.component_node_repository = repo

        response = client.get(component_dependencies_path("does-not-exist"))

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")

    payload = response.json()
    assert payload["status"] == 404
    assert payload.get("error_code") == "component_not_found"


def test_root_component_dependencies_path_is_not_supported() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.get(component_dependencies_path("mAG_A").removeprefix("/v1"))

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["title"] == "Not Found"
