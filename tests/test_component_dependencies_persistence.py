from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def _node_payload(*, node_id: str, relationships: list[dict[str, Any]] | None = None) -> dict[str, Any]:
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


def test_get_component_dependencies_persistence_traverses_upstream_and_downstream(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        # mAG_A -> mAG_B -> mAG_C -> mAG_MISSING (missing target)
        # mAG_X -> mAG_A (upstream)
        # mAG_Y -> mAG_MISSING (should NOT be included; no expansion beyond missing)

        for payload in [
            _node_payload(
                node_id="mAG_A",
                relationships=[_depends_on(source_node_id="mAG_A", target_node_id="mAG_B")],
            ),
            _node_payload(
                node_id="mAG_B",
                relationships=[_depends_on(source_node_id="mAG_B", target_node_id="mAG_C")],
            ),
            _node_payload(
                node_id="mAG_C",
                relationships=[
                    _depends_on(source_node_id="mAG_C", target_node_id="mAG_MISSING")
                ],
            ),
            _node_payload(
                node_id="mAG_X",
                relationships=[_depends_on(source_node_id="mAG_X", target_node_id="mAG_A")],
            ),
            _node_payload(
                node_id="mAG_Y",
                relationships=[
                    _depends_on(source_node_id="mAG_Y", target_node_id="mAG_MISSING")
                ],
            ),
        ]:
            resp = client.post("/components", json=payload)
            assert resp.status_code in (200, 201)

        response = client.get("/components/mAG_A/dependencies")

    assert response.status_code == 200
    body = response.json()

    assert body["node-id"] == "mAG_A"

    edges = body["dependency-graph"]
    assert edges == [
        {
            "relationship-type": "depends-on",
            "source-node-id": "mAG_A",
            "target-node-id": "mAG_B",
        },
        {
            "relationship-type": "depends-on",
            "source-node-id": "mAG_B",
            "target-node-id": "mAG_C",
        },
        {
            "relationship-type": "depends-on",
            "source-node-id": "mAG_C",
            "target-node-id": "mAG_MISSING",
        },
        {
            "relationship-type": "depends-on",
            "source-node-id": "mAG_X",
            "target-node-id": "mAG_A",
        },
    ]

    # No expansion beyond missing nodes
    assert {
        "relationship-type": "depends-on",
        "source-node-id": "mAG_Y",
        "target-node-id": "mAG_MISSING",
    } not in edges
