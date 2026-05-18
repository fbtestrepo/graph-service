from __future__ import annotations

from copy import deepcopy
from typing import Any

from fastapi.testclient import TestClient

from src.adapters.outbound.mongodb.collection_names import (
    MICRO_AFFINITY_GROUPS_PROCESSED_COLLECTION,
)
from tests.conftest import MICRO_AFFINITY_GROUPS_PATH


def _asset_id(micro_ag_id: str) -> str:
    return f"asset-{micro_ag_id.lower()}"


def _deployment_scope_path(micro_ag_id: str, environment: str) -> str:
    return f"{MICRO_AFFINITY_GROUPS_PATH}/{micro_ag_id}/deployment-scope?environment={environment}"


def _processed_mag_payload(
    micro_ag_id: str,
    environment: str,
    *,
    dependency_micro_ag_ids: list[str] | None = None,
    workload_asset_ids: list[str] | None = None,
) -> dict[str, Any]:
    source_asset_ids = workload_asset_ids or [_asset_id(micro_ag_id)]
    dependency_ids = dependency_micro_ag_ids or []
    return {
        "micro_ag_id": micro_ag_id,
        "environment": environment,
        "effective_date": "2025-01-01T00:00:00Z",
        "workloads": [
            {"id": f"{micro_ag_id}-workload-{index}", "asset_id": asset_id}
            for index, asset_id in enumerate(source_asset_ids, start=1)
        ],
        "relationships": [
            {
                "source_workload": {
                    "id": f"{micro_ag_id}-workload-1",
                    "asset_id": source_asset_ids[0],
                },
                "destination_workload": {
                    "id": f"{dependency_micro_ag_id}-workload-1",
                    "asset_id": _asset_id(dependency_micro_ag_id),
                },
            }
            for dependency_micro_ag_id in dependency_ids
        ],
    }


def test_get_deployment_scope_persistence_is_environment_scoped_deduplicated_and_read_only(
    app_with_mongodb,
) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        collection = client.app.state.mongo_db.get_collection(
            MICRO_AFFINITY_GROUPS_PROCESSED_COLLECTION
        )
        root = _processed_mag_payload("C", "preproduction", dependency_micro_ag_ids=["D", "D", "C"])
        root["relationships"].append(
            {
                "source_workload": {"id": "C-workload-1", "asset_id": _asset_id("C")},
                "destination_workload": {"id": "D-staging-workload-1", "asset_id": _asset_id("D")},
            }
        )
        documents = [
            _processed_mag_payload("B", "preproduction", dependency_micro_ag_ids=["C"]),
            root,
            _processed_mag_payload("D", "preproduction"),
            _processed_mag_payload("D", "staging"),
        ]
        collection.insert_many(documents)
        before_documents = list(collection.find({}, projection={"_id": False}))

        response = client.get(_deployment_scope_path("C", "preproduction"))

        after_documents = list(collection.find({}, projection={"_id": False}))

    assert response.status_code == 200
    assert response.json()["dependency_graph"] == [
        {"source_micro_ag_id": "B", "destination_micro_ag_id": "C"},
        {"source_micro_ag_id": "C", "destination_micro_ag_id": "D"},
    ]
    assert len(after_documents) == len(before_documents)
    assert sorted(after_documents, key=lambda doc: (doc["environment"], doc["micro_ag_id"])) == sorted(
        deepcopy(before_documents),
        key=lambda doc: (doc["environment"], doc["micro_ag_id"]),
    )


def test_get_deployment_scope_persistence_ambiguous_join_returns_422(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app, raise_server_exceptions=False) as client:
        collection = client.app.state.mongo_db.get_collection(
            MICRO_AFFINITY_GROUPS_PROCESSED_COLLECTION
        )
        collection.insert_many(
            [
                {
                    **_processed_mag_payload("C", "preproduction"),
                    "relationships": [
                        {
                            "source_workload": {
                                "id": "C-workload-1",
                                "asset_id": _asset_id("C"),
                            },
                            "destination_workload": {
                                "id": "shared-workload-1",
                                "asset_id": "asset-shared",
                            },
                        }
                    ],
                },
                _processed_mag_payload(
                    "D1",
                    "preproduction",
                    workload_asset_ids=["asset-shared"],
                ),
                _processed_mag_payload(
                    "D2",
                    "preproduction",
                    workload_asset_ids=["asset-shared"],
                ),
            ]
        )

        response = client.get(_deployment_scope_path("C", "preproduction"))

    assert response.status_code == 422
    assert response.json()["error_code"] == "micro_affinity_group_graph_resolution_error"


def test_get_deployment_scope_persistence_returns_cyclic_deployment_sequence(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        collection = client.app.state.mongo_db.get_collection(
            MICRO_AFFINITY_GROUPS_PROCESSED_COLLECTION
        )
        collection.insert_many(
            [
                _processed_mag_payload("A", "preproduction", dependency_micro_ag_ids=["B"]),
                _processed_mag_payload("B", "preproduction", dependency_micro_ag_ids=["C"]),
                _processed_mag_payload("C", "preproduction", dependency_micro_ag_ids=["D"]),
                _processed_mag_payload("D", "preproduction", dependency_micro_ag_ids=["E"]),
                _processed_mag_payload("E", "preproduction", dependency_micro_ag_ids=["A"]),
            ]
        )

        response = client.get(_deployment_scope_path("C", "preproduction"))

    assert response.status_code == 200
    assert response.json()["graph_has_cycles"] is True
    assert response.json()["deployment_sequence"] == {
        "bypassed_edges": [{"source_micro_ag_id": "A", "destination_micro_ag_id": "B"}],
        "steps": [
            {"step_index": 1, "micro_ag_ids": ["A"]},
            {"step_index": 2, "micro_ag_ids": ["E"]},
            {"step_index": 3, "micro_ag_ids": ["D"]},
            {"step_index": 4, "micro_ag_ids": ["C"]},
            {"step_index": 5, "micro_ag_ids": ["B"]},
        ],
    }