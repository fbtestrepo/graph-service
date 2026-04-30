from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.core.domain.dependency_edge import DependencyEdge


ComponentNodePayload = dict[str, Any]


class ComponentNodeRepository(ABC):
    @abstractmethod
    def upsert(self, node_id: str, payload: ComponentNodePayload) -> bool:
        """Upsert a component node payload by node-id.

        Returns True if the payload was created (inserted), False if it updated/replaced an
        existing document.
        """

        raise NotImplementedError

    @abstractmethod
    def get_by_node_id(self, node_id: str) -> ComponentNodePayload | None:
        raise NotImplementedError

    @abstractmethod
    def get_outgoing_relationship_edges(self, source_node_ids: set[str]) -> list[DependencyEdge]:
        """Return relationship edges where the relationship source node-id is in source_node_ids.

        Implementations must return only “self-sourced” relationships, i.e. only include a
        relationship if `relationship.source.node-id == document.node-id`.
        """

        raise NotImplementedError

    @abstractmethod
    def get_incoming_relationship_edges(self, target_node_ids: set[str]) -> list[DependencyEdge]:
        """Return relationship edges where the relationship target node-id is in target_node_ids.

        Implementations must return only “self-sourced” relationships, i.e. only include a
        relationship if `relationship.source.node-id == document.node-id`.
        """

        raise NotImplementedError
