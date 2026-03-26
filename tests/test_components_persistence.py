from __future__ import annotations

from fastapi.testclient import TestClient


def _valid_payload(*, node_id: str, include_optional: bool = True) -> dict:
    payload: dict = {
        "node-id": node_id,
        "node-type": "component",
        "node-name": "Example Node",
        "metadata": {"parent-asset-id": "asset-1"},
    }
    if include_optional:
        payload["interfaces"] = [
            {"interface-local-id": "if-1", "interface-type": "ethernet"}
        ]
        payload["relationships"] = [
            {
                "relationship-type": "connects-to",
                "source": {"node-id": node_id, "interface-local-id": "if-1"},
                "target": {"node-id": "node-2", "interface-local-id": "if-2"},
            }
        ]
    return payload


def test_post_components_creates_document_and_returns_201(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        collection = client.app.state.mongo_db.get_collection("components")
        before_count = collection.count_documents({})

        request_payload = _valid_payload(node_id="node-1")
        response = client.post("/components", json=request_payload)

        assert response.status_code == 201
        assert response.json() == request_payload

        assert collection.count_documents({}) == before_count + 1
        record = collection.find_one({"node-id": "node-1"})

    assert record is not None
    record.pop("_id", None)
    assert record == request_payload


def test_post_components_updates_existing_document_and_returns_200(app_with_mongodb) -> None:
    app = app_with_mongodb

    with TestClient(app) as client:
        collection = client.app.state.mongo_db.get_collection("components")
        before_count = collection.count_documents({})

        first_payload = _valid_payload(node_id="node-1")
        first_response = client.post("/components", json=first_payload)
        assert first_response.status_code == 201

        assert collection.count_documents({}) == before_count + 1

        second_payload = _valid_payload(node_id="node-1", include_optional=False)
        second_payload["node-name"] = "Updated Node"
        second_response = client.post("/components", json=second_payload)

        assert second_response.status_code == 200
        assert second_response.json() == second_payload

        assert collection.count_documents({}) == before_count + 1
        record = collection.find_one({"node-id": "node-1"})

    assert record is not None
    record.pop("_id", None)
    assert record == second_payload
