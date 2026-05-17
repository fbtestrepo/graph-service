from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from src.adapters.outbound.mongodb.collection_names import (
    APPLICATION_ARCHITECTURES_COLLECTION,
    MICRO_AFFINITY_GROUPS_COLLECTION,
    MICRO_AFFINITY_GROUPS_PROCESSED_COLLECTION,
)
from tests.conftest import MICRO_AFFINITY_GROUPS_PATH


def _application_architecture_payload(*, include_relationship: bool = True) -> dict[str, Any]:
    relationships: list[dict[str, Any]] = []
    if include_relationship:
        relationships.append(
            {
                "relationship-type": {
                    "connects": {
                        "source": {"node": "node-1"},
                        "destination": {"node": "node-2"},
                    }
                }
            }
        )

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
        "relationships": relationships,
    }


def _application_architecture_payload_for_version(version: str) -> dict[str, Any]:
    payload = _application_architecture_payload()
    payload["metadata"]["version"] = version
    return payload


def _valid_payload(
    *,
    architecture_version: str = "1.0.0",
    include_name: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "micro_ag_id": "mAG_A",
        "parent_asset_id": "ba0270",
        "architecture_version": architecture_version,
        "environment": "production",
        "effective_date": "2025-01-01T14:00:00Z",
        "workloads": [
            {
                "id": "AIMC/repos/rw-orchestrator-svc_ba0116_pq0177",
                "asset_id": "pq0177",
            }
        ],
    }
    if include_name:
        payload["name"] = "Micro Affinity Group A"
    return payload


def test_post_micro_affinity_groups_creates_raw_and_processed_documents(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app, raise_server_exceptions=False) as client:
        architecture_collection = client.app.state.mongo_db.get_collection(
            APPLICATION_ARCHITECTURES_COLLECTION
        )
        raw_collection = client.app.state.mongo_db.get_collection(MICRO_AFFINITY_GROUPS_COLLECTION)
        processed_collection = client.app.state.mongo_db.get_collection(
            MICRO_AFFINITY_GROUPS_PROCESSED_COLLECTION
        )

        architecture_collection.insert_one(_application_architecture_payload())
        response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=_valid_payload())

        assert response.status_code == 201
        assert raw_collection.count_documents({}) == 1
        assert processed_collection.count_documents({}) == 1

        raw_record = raw_collection.find_one(
            {
                "micro_ag_id": "mAG_A",
                "environment": "production",
            }
        )
        processed_record = processed_collection.find_one(
            {
                "micro_ag_id": "mAG_A",
                "environment": "production",
            }
        )

    assert raw_record is not None
    assert processed_record is not None
    raw_record.pop("_id", None)
    processed_record.pop("_id", None)
    assert raw_record == _valid_payload()
    assert processed_record["relationships"] == [
        {
            "source_workload": _valid_payload()["workloads"][0],
            "destination_workload": {
                "id": "AIMC/repos/rw-cap-svc_ba0116_dh6980",
                "asset_id": "dh6980",
            },
        }
    ]


def test_post_micro_affinity_groups_zero_relationships_persists_empty_processed_list(
    app_with_mongodb,
) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        architecture_collection = client.app.state.mongo_db.get_collection(
            APPLICATION_ARCHITECTURES_COLLECTION
        )
        processed_collection = client.app.state.mongo_db.get_collection(
            MICRO_AFFINITY_GROUPS_PROCESSED_COLLECTION
        )

        architecture_collection.insert_one(_application_architecture_payload(include_relationship=False))
        response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=_valid_payload())

        assert response.status_code == 201
        assert response.json()["relationships"] == []

        processed_record = processed_collection.find_one(
            {
                "micro_ag_id": "mAG_A",
                "environment": "production",
            }
        )

    assert processed_record is not None
    processed_record.pop("_id", None)
    assert processed_record["relationships"] == []


def test_post_micro_affinity_groups_updates_existing_pair_with_new_version_and_returns_200(
    app_with_mongodb,
) -> None:
    app = app_with_mongodb

    with TestClient(app, raise_server_exceptions=False) as client:
        architecture_collection = client.app.state.mongo_db.get_collection(
            APPLICATION_ARCHITECTURES_COLLECTION
        )
        raw_collection = client.app.state.mongo_db.get_collection(MICRO_AFFINITY_GROUPS_COLLECTION)
        processed_collection = client.app.state.mongo_db.get_collection(
            MICRO_AFFINITY_GROUPS_PROCESSED_COLLECTION
        )

        architecture_collection.insert_many(
            [
                _application_architecture_payload_for_version("1.0.0"),
                _application_architecture_payload_for_version("2.0.0"),
            ]
        )

        first_response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=_valid_payload())
        assert first_response.status_code == 201

        updated_payload = _valid_payload(architecture_version="2.0.0", include_name=False)
        updated_payload["effective_date"] = "2025-02-01T10:00:00Z"

        second_response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=updated_payload)

        assert second_response.status_code == 200
        assert raw_collection.count_documents({}) == 1
        assert processed_collection.count_documents({}) == 1

        raw_record = raw_collection.find_one(
            {
                "micro_ag_id": "mAG_A",
                "environment": "production",
            }
        )
        processed_record = processed_collection.find_one(
            {
                "micro_ag_id": "mAG_A",
                "environment": "production",
            }
        )

    assert raw_record is not None
    assert processed_record is not None
    raw_record.pop("_id", None)
    processed_record.pop("_id", None)
    assert raw_record == updated_payload
    assert processed_record["architecture_version"] == "2.0.0"
    assert processed_record["effective_date"] == "2025-02-01T10:00:00Z"
    assert "name" not in processed_record


def test_post_micro_affinity_groups_different_keys_coexist(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        architecture_collection = client.app.state.mongo_db.get_collection(
            APPLICATION_ARCHITECTURES_COLLECTION
        )
        processed_collection = client.app.state.mongo_db.get_collection(
            MICRO_AFFINITY_GROUPS_PROCESSED_COLLECTION
        )

        architecture_collection.insert_one(_application_architecture_payload())

        first_response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=_valid_payload())
        assert first_response.status_code == 201

        second_payload = _valid_payload()
        second_payload["environment"] = "staging"
        second_response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=second_payload)

        assert second_response.status_code == 201

        records = list(
            processed_collection.find(
                {"micro_ag_id": "mAG_A"},
                projection={"_id": False},
            )
        )

    environments = sorted(record["environment"] for record in records)
    assert environments == ["production", "staging"]


def test_post_micro_affinity_groups_processed_write_failure_rolls_back_raw_and_processed(
    app_with_mongodb,
) -> None:
    app = app_with_mongodb

    class FailingProcessedRepository:
        def count_by_identity(
            self,
            micro_ag_id: str,
            environment: str,
            session: object | None = None,
        ) -> int:
            return 0

        def upsert(
            self,
            micro_ag_id: str,
            environment: str,
            payload: dict[str, Any],
            session: object | None = None,
        ) -> bool:
            raise RuntimeError("processed write failed")

    with TestClient(app, raise_server_exceptions=False) as client:
        architecture_collection = client.app.state.mongo_db.get_collection(
            APPLICATION_ARCHITECTURES_COLLECTION
        )
        raw_collection = client.app.state.mongo_db.get_collection(MICRO_AFFINITY_GROUPS_COLLECTION)
        processed_collection = client.app.state.mongo_db.get_collection(
            MICRO_AFFINITY_GROUPS_PROCESSED_COLLECTION
        )

        architecture_collection.insert_one(_application_architecture_payload())
        client.app.state.micro_affinity_group_processed_repository = FailingProcessedRepository()

        response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=_valid_payload())

        assert response.status_code == 500
        assert raw_collection.count_documents({}) == 0
        assert processed_collection.count_documents({}) == 0


def test_post_micro_affinity_groups_duplicate_raw_pair_returns_409_without_modification(
    app_with_mongodb,
) -> None:
    app = app_with_mongodb

    with TestClient(app, raise_server_exceptions=False) as client:
        architecture_collection = client.app.state.mongo_db.get_collection(
            APPLICATION_ARCHITECTURES_COLLECTION
        )
        raw_collection = client.app.state.mongo_db.get_collection(MICRO_AFFINITY_GROUPS_COLLECTION)
        processed_collection = client.app.state.mongo_db.get_collection(
            MICRO_AFFINITY_GROUPS_PROCESSED_COLLECTION
        )

        architecture_collection.insert_one(_application_architecture_payload_for_version("2.0.0"))
        raw_collection.insert_many(
            [
                _valid_payload(architecture_version="1.0.0"),
                _valid_payload(architecture_version="9.9.9"),
            ]
        )

        response = client.post(
            MICRO_AFFINITY_GROUPS_PATH,
            json=_valid_payload(architecture_version="2.0.0"),
        )

        assert response.status_code == 409
        assert response.headers["content-type"].startswith("application/problem+json")
        assert response.json()["error_code"] == "duplicate_micro_affinity_group_identity"
        assert raw_collection.count_documents({"micro_ag_id": "mAG_A", "environment": "production"}) == 2
        assert processed_collection.count_documents({"micro_ag_id": "mAG_A", "environment": "production"}) == 0


def test_post_micro_affinity_groups_partial_existing_pair_is_repaired_with_200(
    app_with_mongodb,
) -> None:
    app = app_with_mongodb

    with TestClient(app, raise_server_exceptions=False) as client:
        architecture_collection = client.app.state.mongo_db.get_collection(
            APPLICATION_ARCHITECTURES_COLLECTION
        )
        raw_collection = client.app.state.mongo_db.get_collection(MICRO_AFFINITY_GROUPS_COLLECTION)
        processed_collection = client.app.state.mongo_db.get_collection(
            MICRO_AFFINITY_GROUPS_PROCESSED_COLLECTION
        )

        architecture_collection.insert_one(_application_architecture_payload_for_version("2.0.0"))
        raw_collection.insert_one(_valid_payload(architecture_version="1.0.0"))

        replacement_payload = _valid_payload(architecture_version="2.0.0", include_name=False)
        replacement_payload["effective_date"] = "2025-02-01T10:00:00Z"
        response = client.post(MICRO_AFFINITY_GROUPS_PATH, json=replacement_payload)

        assert response.status_code == 200
        assert raw_collection.count_documents({"micro_ag_id": "mAG_A", "environment": "production"}) == 1
        assert processed_collection.count_documents({"micro_ag_id": "mAG_A", "environment": "production"}) == 1

        raw_record = raw_collection.find_one(
            {"micro_ag_id": "mAG_A", "environment": "production"},
            projection={"_id": False},
        )
        processed_record = processed_collection.find_one(
            {"micro_ag_id": "mAG_A", "environment": "production"},
            projection={"_id": False},
        )

    assert raw_record == replacement_payload
    assert processed_record is not None
    assert processed_record["architecture_version"] == "2.0.0"
    assert processed_record["effective_date"] == "2025-02-01T10:00:00Z"
    assert "name" not in raw_record