from __future__ import annotations

from typing import Any

from pymongo.database import Database

from src.core.domain.dependency_edge import DependencyEdge
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

    def get_outgoing_relationship_edges(self, source_node_ids: set[str]) -> list[DependencyEdge]:
        if not source_node_ids:
            return []

        cursor = self._db.get_collection("components").find(
            {"node-id": {"$in": list(source_node_ids)}},
            projection={"_id": False, "node-id": True, "relationships": True},
        )

        edges: list[DependencyEdge] = []
        for doc in cursor:
            doc_node_id = doc.get("node-id")
            relationships = doc.get("relationships") or []
            if not isinstance(doc_node_id, str) or not isinstance(relationships, list):
                continue

            for relationship in relationships:
                if not isinstance(relationship, dict):
                    continue

                relationship_type = relationship.get("relationship-type")
                source = relationship.get("source")
                target = relationship.get("target")
                if not isinstance(relationship_type, str) or not relationship_type:
                    continue
                if not isinstance(source, dict) or not isinstance(target, dict):
                    continue

                source_node_id = source.get("node-id")
                target_node_id = target.get("node-id")
                if not isinstance(source_node_id, str) or not source_node_id:
                    continue
                if not isinstance(target_node_id, str) or not target_node_id:
                    continue

                if source_node_id != doc_node_id:
                    continue

                edges.append(
                    DependencyEdge(
                        relationship_type=relationship_type,
                        source_node_id=source_node_id,
                        target_node_id=target_node_id,
                    )
                )

        return edges

    def get_incoming_relationship_edges(self, target_node_ids: set[str]) -> list[DependencyEdge]:
        if not target_node_ids:
            return []

        cursor = self._db.get_collection("components").find(
            {"relationships.target.node-id": {"$in": list(target_node_ids)}},
            projection={"_id": False, "node-id": True, "relationships": True},
        )

        edges: list[DependencyEdge] = []
        for doc in cursor:
            doc_node_id = doc.get("node-id")
            relationships = doc.get("relationships") or []
            if not isinstance(doc_node_id, str) or not isinstance(relationships, list):
                continue

            for relationship in relationships:
                if not isinstance(relationship, dict):
                    continue

                relationship_type = relationship.get("relationship-type")
                source = relationship.get("source")
                target = relationship.get("target")
                if not isinstance(relationship_type, str) or not relationship_type:
                    continue
                if not isinstance(source, dict) or not isinstance(target, dict):
                    continue

                source_node_id = source.get("node-id")
                target_node_id = target.get("node-id")
                if not isinstance(source_node_id, str) or not source_node_id:
                    continue
                if not isinstance(target_node_id, str) or not target_node_id:
                    continue

                if target_node_id not in target_node_ids:
                    continue

                if source_node_id != doc_node_id:
                    continue

                edges.append(
                    DependencyEdge(
                        relationship_type=relationship_type,
                        source_node_id=source_node_id,
                        target_node_id=target_node_id,
                    )
                )

        return edges
