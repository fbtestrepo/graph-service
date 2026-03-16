from __future__ import annotations


class DuplicateDependencyEdge(Exception):
    def __init__(self, from_component_id: str, to_component_id: str):
        super().__init__(f"Duplicate dependency edge: {from_component_id} -> {to_component_id}")
        self.from_component_id = from_component_id
        self.to_component_id = to_component_id
