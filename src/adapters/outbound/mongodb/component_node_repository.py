from __future__ import annotations

from typing import Any

from pymongo.database import Database

from src.core.ports.component_node_repository import ComponentNodePayload, ComponentNodeRepository


class MongoComponentNodeRepository(ComponentNodeRepository):
    def __init__(self, db: Database):
        self._db = db

    def upsert(self, node_id: str, payload: ComponentNodePayload) -> bool:
        result = self._db.get_collection("components").replace_one(
            filter={"node-id": node_id}, replacement=payload, upsert=True
        )
        return result.upserted_id is not None

    def get_by_node_id(self, node_id: str) -> dict[str, Any] | None:
        doc: dict[str, Any] | None = self._db.get_collection("components").find_one(
            {"node-id": node_id}
        )
        if doc is None:
            return None
        doc.pop("_id", None)
        return doc
