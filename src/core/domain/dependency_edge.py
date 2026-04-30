from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DependencyEdge:
    relationship_type: str
    source_node_id: str
    target_node_id: str

    def sort_key(self) -> tuple[str, str, str]:
        return (self.relationship_type, self.source_node_id, self.target_node_id)
