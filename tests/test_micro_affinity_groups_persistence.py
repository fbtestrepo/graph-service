from __future__ import annotations

from fastapi.testclient import TestClient


def _application_architecture_payload() -> dict:
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
            }
        ],
        "relationships": [],
    }


def _valid_payload() -> dict:
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


def test_post_micro_affinity_groups_creates_document_and_returns_201(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        architecture_collection = client.app.state.mongo_db.get_collection("application-architectures")
        micro_affinity_collection = client.app.state.mongo_db.get_collection("micro-affinity-groups")

        architecture_collection.insert_one(_application_architecture_payload())
        before_count = micro_affinity_collection.count_documents({})

        request_payload = _valid_payload()
        response = client.post("/micro-affinity-groups", json=request_payload)

        assert response.status_code == 201
        assert response.json() == request_payload
        assert micro_affinity_collection.count_documents({}) == before_count + 1

        record = micro_affinity_collection.find_one(
            {
                "micro-ag-id": "mAG_A",
                "environment": "production",
                "architecture-version": "1.0.0",
            }
        )

    assert record is not None
    record.pop("_id", None)
    assert record == request_payload


def test_post_micro_affinity_groups_updates_existing_document_and_returns_200(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        architecture_collection = client.app.state.mongo_db.get_collection("application-architectures")
        micro_affinity_collection = client.app.state.mongo_db.get_collection("micro-affinity-groups")

        architecture_collection.insert_one(_application_architecture_payload())
        before_count = micro_affinity_collection.count_documents({})

        first_payload = _valid_payload()
        first_response = client.post("/micro-affinity-groups", json=first_payload)
        assert first_response.status_code == 201

        second_payload = _valid_payload()
        second_payload["effective-date"] = "2025-02-01T10:00:00Z"
        second_payload.pop("name")
        second_response = client.post("/micro-affinity-groups", json=second_payload)

        assert second_response.status_code == 200
        assert second_response.json() == second_payload
        assert micro_affinity_collection.count_documents({}) == before_count + 1

        record = micro_affinity_collection.find_one(
            {
                "micro-ag-id": "mAG_A",
                "environment": "production",
                "architecture-version": "1.0.0",
            }
        )

    assert record is not None
    record.pop("_id", None)
    assert record == second_payload


def test_post_micro_affinity_groups_different_keys_coexist(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        architecture_collection = client.app.state.mongo_db.get_collection("application-architectures")
        micro_affinity_collection = client.app.state.mongo_db.get_collection("micro-affinity-groups")

        architecture_collection.insert_one(_application_architecture_payload())

        first_response = client.post("/micro-affinity-groups", json=_valid_payload())
        assert first_response.status_code == 201

        second_payload = _valid_payload()
        second_payload["environment"] = "staging"
        second_response = client.post("/micro-affinity-groups", json=second_payload)

        assert second_response.status_code == 201

        records = list(
            micro_affinity_collection.find(
                {"micro-ag-id": "mAG_A"},
                projection={"_id": False},
            )
        )

    environments = sorted(record["environment"] for record in records)
    assert environments == ["production", "staging"]