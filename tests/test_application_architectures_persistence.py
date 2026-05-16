from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import APPLICATION_ARCHITECTURES_PATH


def _valid_payload(*, asset_id: str, version: str, include_optional: bool = True) -> dict:
    payload: dict = {
        "metadata": {
            "AssetID": asset_id,
            "version": version,
            "created": "2026-05-02",
        },
        "nodes": [],
        "relationships": [],
    }
    if include_optional:
        payload["adrs"] = ["https://example.test/adr/1"]
    return payload


def test_post_application_architectures_creates_document_and_returns_201(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        collection = client.app.state.mongo_db.get_collection("application-architectures")
        before_count = collection.count_documents({})

        request_payload = _valid_payload(asset_id="Asset123", version="1.0.0")
        response = client.post(APPLICATION_ARCHITECTURES_PATH, json=request_payload)

        assert response.status_code == 201
        assert response.json() == request_payload

        assert collection.count_documents({}) == before_count + 1
        record = collection.find_one(
            {
                "metadata.AssetID": "Asset123",
                "metadata.version": "1.0.0",
            }
        )

    assert record is not None
    record.pop("_id", None)
    assert record == request_payload


def test_post_application_architectures_updates_existing_document_and_returns_200(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        collection = client.app.state.mongo_db.get_collection("application-architectures")
        before_count = collection.count_documents({})

        first_payload = _valid_payload(asset_id="Asset123", version="1.0.0")
        first_response = client.post(APPLICATION_ARCHITECTURES_PATH, json=first_payload)
        assert first_response.status_code == 201
        assert collection.count_documents({}) == before_count + 1

        second_payload = _valid_payload(
            asset_id="Asset123",
            version="1.0.0",
            include_optional=False,
        )
        second_payload["nodes"] = [
            {
                "unique-id": "service-1",
                "node-type": "service",
                "name": "Payments API",
                "description": "Updated node payload",
            }
        ]

        second_response = client.post(APPLICATION_ARCHITECTURES_PATH, json=second_payload)

        assert second_response.status_code == 200
        assert second_response.json() == second_payload
        assert collection.count_documents({}) == before_count + 1

        record = collection.find_one(
            {
                "metadata.AssetID": "Asset123",
                "metadata.version": "1.0.0",
            }
        )

    assert record is not None
    record.pop("_id", None)
    assert record == second_payload


def test_post_application_architectures_different_versions_coexist(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        collection = client.app.state.mongo_db.get_collection("application-architectures")

        first_response = client.post(
            APPLICATION_ARCHITECTURES_PATH,
            json=_valid_payload(asset_id="Asset123", version="1.0.0"),
        )
        assert first_response.status_code == 201

        second_response = client.post(
            APPLICATION_ARCHITECTURES_PATH,
            json=_valid_payload(asset_id="Asset123", version="1.0.1"),
        )
        assert second_response.status_code == 201

        records = list(
            collection.find(
                {"metadata.AssetID": "Asset123"},
                projection={"_id": False},
            )
        )

    versions = sorted(record["metadata"]["version"] for record in records)
    assert versions == ["1.0.0", "1.0.1"]
