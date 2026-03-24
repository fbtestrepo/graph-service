from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient


def test_post_components_persists_and_echoes_object_json(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        collection = client.app.state.mongo_db.get_collection("component_payload_records")
        before_count = collection.count_documents({})

        request_payload = {"hello": "world", "n": 123, "ok": True, "none": None}
        response = client.post("/components", json=request_payload)

        assert response.status_code == 200
        assert response.json() == request_payload

        assert collection.count_documents({}) == before_count + 1
        record = collection.find_one(sort=[("_id", -1)])

    assert record is not None
    assert record["payload"] == request_payload
    assert isinstance(record["received_at"], datetime)


def test_post_components_persists_and_echoes_non_object_json(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        collection = client.app.state.mongo_db.get_collection("component_payload_records")
        before_count = collection.count_documents({})

        request_payload = [1, 2, 3, {"x": True}]
        response = client.post("/components", json=request_payload)

        assert response.status_code == 200
        assert response.json() == request_payload

        assert collection.count_documents({}) == before_count + 1
        record = collection.find_one(sort=[("_id", -1)])

    assert record is not None
    assert record["payload"] == request_payload
    assert isinstance(record["received_at"], datetime)
