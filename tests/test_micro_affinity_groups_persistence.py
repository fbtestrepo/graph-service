from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


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


def _valid_payload() -> dict[str, Any]:
    return {
        "micro-ag-id": "mAG_A",
        "name": "Micro Affinity Group A",
        "parent-asset-id": "ba0270",
        "architecture-version": "1.0.0",
        "environment": "production",
        "effective-date": "2025-01-01T14:00:00Z",
        "workloads": [
            {
                "id": "AIMC/repos/rw-orchestrator-svc_ba0116_pq0177",
                "asset-id": "pq0177",
            }
        ],
    }


def test_post_micro_affinity_groups_creates_raw_and_processed_documents(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app, raise_server_exceptions=False) as client:
        architecture_collection = client.app.state.mongo_db.get_collection("application-architectures")
        raw_collection = client.app.state.mongo_db.get_collection("micro-affinity-groups")
        processed_collection = client.app.state.mongo_db.get_collection(
            "micro-affinity-groups-processed"
        )

        architecture_collection.insert_one(_application_architecture_payload())
        response = client.post("/micro-affinity-groups", json=_valid_payload())

        assert response.status_code == 201
        assert raw_collection.count_documents({}) == 1
        assert processed_collection.count_documents({}) == 1

        raw_record = raw_collection.find_one(
            {
                "micro-ag-id": "mAG_A",
                "environment": "production",
                "architecture-version": "1.0.0",
            }
        )
        processed_record = processed_collection.find_one(
            {
                "micro-ag-id": "mAG_A",
                "environment": "production",
                "architecture-version": "1.0.0",
            }
        )

    assert raw_record is not None
    assert processed_record is not None
    raw_record.pop("_id", None)
    processed_record.pop("_id", None)
    assert raw_record == _valid_payload()
    assert processed_record["relationships"] == [
        {
            "source-workload": _valid_payload()["workloads"][0],
            "destination-workload": {
                "id": "AIMC/repos/rw-cap-svc_ba0116_dh6980",
                "asset-id": "dh6980",
            },
        }
    ]


def test_post_micro_affinity_groups_zero_relationships_persists_empty_processed_list(
    app_with_mongodb,
) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        architecture_collection = client.app.state.mongo_db.get_collection("application-architectures")
        processed_collection = client.app.state.mongo_db.get_collection(
            "micro-affinity-groups-processed"
        )

        architecture_collection.insert_one(_application_architecture_payload(include_relationship=False))
        response = client.post("/micro-affinity-groups", json=_valid_payload())

        assert response.status_code == 201
        assert response.json()["relationships"] == []

        processed_record = processed_collection.find_one(
            {
                "micro-ag-id": "mAG_A",
                "environment": "production",
                "architecture-version": "1.0.0",
            }
        )

    assert processed_record is not None
    processed_record.pop("_id", None)
    assert processed_record["relationships"] == []


def test_post_micro_affinity_groups_updates_existing_documents_and_returns_200(
    app_with_mongodb,
) -> None:
    app = app_with_mongodb

    with TestClient(app, raise_server_exceptions=False) as client:
        architecture_collection = client.app.state.mongo_db.get_collection("application-architectures")
        raw_collection = client.app.state.mongo_db.get_collection("micro-affinity-groups")
        processed_collection = client.app.state.mongo_db.get_collection(
            "micro-affinity-groups-processed"
        )

        architecture_collection.insert_one(_application_architecture_payload())

        first_response = client.post("/micro-affinity-groups", json=_valid_payload())
        assert first_response.status_code == 201

        updated_payload = _valid_payload()
        updated_payload.pop("name")
        updated_payload["effective-date"] = "2025-02-01T10:00:00Z"

        second_response = client.post("/micro-affinity-groups", json=updated_payload)

        assert second_response.status_code == 200
        assert raw_collection.count_documents({}) == 1
        assert processed_collection.count_documents({}) == 1

        raw_record = raw_collection.find_one(
            {
                "micro-ag-id": "mAG_A",
                "environment": "production",
                "architecture-version": "1.0.0",
            }
        )
        processed_record = processed_collection.find_one(
            {
                "micro-ag-id": "mAG_A",
                "environment": "production",
                "architecture-version": "1.0.0",
            }
        )

    assert raw_record is not None
    assert processed_record is not None
    raw_record.pop("_id", None)
    processed_record.pop("_id", None)
    assert raw_record == updated_payload
    assert processed_record["effective-date"] == "2025-02-01T10:00:00Z"


def test_post_micro_affinity_groups_different_keys_coexist(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        architecture_collection = client.app.state.mongo_db.get_collection("application-architectures")
        processed_collection = client.app.state.mongo_db.get_collection(
            "micro-affinity-groups-processed"
        )

        architecture_collection.insert_one(_application_architecture_payload())

        first_response = client.post("/micro-affinity-groups", json=_valid_payload())
        assert first_response.status_code == 201

        second_payload = _valid_payload()
        second_payload["environment"] = "staging"
        second_response = client.post("/micro-affinity-groups", json=second_payload)

        assert second_response.status_code == 201

        records = list(
            processed_collection.find(
                {"micro-ag-id": "mAG_A"},
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
        def upsert(
            self,
            micro_ag_id: str,
            environment: str,
            architecture_version: str,
            payload: dict[str, Any],
            session: object | None = None,
        ) -> bool:
            raise RuntimeError("processed write failed")

    with TestClient(app, raise_server_exceptions=False) as client:
        architecture_collection = client.app.state.mongo_db.get_collection("application-architectures")
        raw_collection = client.app.state.mongo_db.get_collection("micro-affinity-groups")
        processed_collection = client.app.state.mongo_db.get_collection(
            "micro-affinity-groups-processed"
        )

        architecture_collection.insert_one(_application_architecture_payload())
        client.app.state.micro_affinity_group_processed_repository = FailingProcessedRepository()

        response = client.post("/micro-affinity-groups", json=_valid_payload())

        assert response.status_code == 500
        assert raw_collection.count_documents({}) == 0
        assert processed_collection.count_documents({}) == 0