from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.ports.component_node_repository import ComponentNodeRepository


@dataclass(frozen=True, slots=True)
class UpsertComponentNodeResult:
    created: bool


@dataclass(frozen=True, slots=True)
class UpsertComponentNode:
    component_node_repository: ComponentNodeRepository

    def execute(self, payload: dict[str, Any]) -> UpsertComponentNodeResult:
        node_id = str(payload["node-id"])
        created = self.component_node_repository.upsert(node_id=node_id, payload=payload)
        return UpsertComponentNodeResult(created=created)
