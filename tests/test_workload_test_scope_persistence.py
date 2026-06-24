from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from src.adapters.outbound.mongodb.collection_names import (
    MICRO_AFFINITY_GROUPS_PROCESSED_COLLECTION,
)
from tests.conftest import MICRO_AFFINITY_GROUPS_PATH


def _path(environment: str) -> str:
    return f"{MICRO_AFFINITY_GROUPS_PATH}/workloads/test-scope?environment={environment}"


def _request_payload(*asset_ids: str) -> dict[str, Any]:
    return {"changed_workloads": [{"workload_asset_id": asset_id} for asset_id in asset_ids]}


def _doc(
    micro_ag_id: str,
    environment: str,
    workloads: list[str],
    relationships: list[tuple[str, str]],
) -> dict[str, Any]:
    workload_rows = [
        {"id": f"{micro_ag_id}-{index}", "asset_id": asset_id}
        for index, asset_id in enumerate(workloads, start=1)
    ]
    return {
        "micro_ag_id": micro_ag_id,
        "name": micro_ag_id,
        "parent_asset_id": "ba0270",
        "architecture_version": "1.0.0",
        "environment": environment,
        "effective_date": "2025-01-01T00:00:00Z",
        "workloads": workload_rows,
        "relationships": [
            {
                "source_workload": {"id": "src", "asset_id": source_asset_id},
                "destination_workload": {"id": "dst", "asset_id": destination_asset_id},
            }
            for source_asset_id, destination_asset_id in relationships
        ],
    }


def test_persistence_environment_isolation_and_deterministic_relationship_order(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        collection = client.app.state.mongo_db.get_collection(
            MICRO_AFFINITY_GROUPS_PROCESSED_COLLECTION
        )
        collection.insert_many(
            [
                _doc("mAG_A", "preproduction", ["asset_1"], [("asset_1", "asset_2")]),
                _doc("mAG_B", "preproduction", ["asset_2"], []),
                _doc("mAG_C", "preproduction", ["asset_3"], [("asset_3", "asset_1")]),
                _doc("mAG_A_STAGE", "staging", ["asset_1"], [("asset_1", "asset_9")]),
                _doc("mAG_Z", "preproduction", ["asset_9"], []),
            ]
        )

        response = client.post(_path("preproduction"), json=_request_payload("asset_1"))

    assert response.status_code == 200
    assert response.json()["affected_workload_relationships"] == [
        {
            "source_workload": {"workload_asset_id": "asset_1", "micro_ag_id": "mAG_A"},
            "destination_workload": {"workload_asset_id": "asset_2", "micro_ag_id": "mAG_B"},
        },
        {
            "source_workload": {"workload_asset_id": "asset_3", "micro_ag_id": "mAG_C"},
            "destination_workload": {"workload_asset_id": "asset_1", "micro_ag_id": "mAG_A"},
        },
    ]


def test_persistence_unresolved_endpoint_is_excluded_and_reported_unknown(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        collection = client.app.state.mongo_db.get_collection(
            MICRO_AFFINITY_GROUPS_PROCESSED_COLLECTION
        )
        collection.insert_many(
            [
                _doc("mAG_A", "preproduction", ["asset_1"], [("asset_1", "asset_missing")]),
            ]
        )

        response = client.post(_path("preproduction"), json=_request_payload("asset_1"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["affected_workload_relationships"] == []
    assert payload["unknown_workloads"] == [{"workload_asset_id": "asset_missing"}]


def test_persistence_ambiguous_ownership_returns_422(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app, raise_server_exceptions=False) as client:
        collection = client.app.state.mongo_db.get_collection(
            MICRO_AFFINITY_GROUPS_PROCESSED_COLLECTION
        )
        collection.insert_many(
            [
                _doc("mAG_A", "preproduction", ["asset_1"], [("asset_1", "asset_shared")]),
                _doc("mAG_B", "preproduction", ["asset_shared"], []),
                _doc("mAG_C", "preproduction", ["asset_shared"], []),
            ]
        )

        response = client.post(_path("preproduction"), json=_request_payload("asset_1"))

    assert response.status_code == 422
    assert response.json()["error_code"] == "ambiguous_workload_ownership"
