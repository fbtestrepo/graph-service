from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


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
