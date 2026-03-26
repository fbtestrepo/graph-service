from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.exceptions.component_not_found import ComponentNotFound
from src.core.ports.component_node_repository import ComponentNodeRepository


@dataclass(frozen=True, slots=True)
class GetComponentNode:
    component_node_repository: ComponentNodeRepository

    def execute(self, node_id: str) -> dict[str, Any]:
        payload = self.component_node_repository.get_by_node_id(node_id)
        if payload is None:
            raise ComponentNotFound(node_id)
        return payload
