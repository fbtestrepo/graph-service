from __future__ import annotations

from typing import Any

from pymongo.database import Database

from src.core.domain.component import Component
from src.core.ports.graph_repository import GraphRepository


class MongoGraphRepository(GraphRepository):
    def __init__(self, db: Database):
        self._db = db

    def get_component(self, component_id: str) -> Component | None:
        doc: dict[str, Any] | None = self._db.get_collection("components").find_one(
            {"component_id": component_id}
        )
        if doc is None:
            return None
        return Component(
            component_id=str(doc.get("component_id", component_id)),
            name=str(doc.get("name", "")),
            version=doc.get("version"),
            metadata=dict(doc.get("metadata") or {}),
        )
