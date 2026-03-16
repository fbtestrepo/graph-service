from __future__ import annotations


class ComponentNotFound(Exception):
    def __init__(self, component_id: str):
        super().__init__(f"Component not found: {component_id}")
        self.component_id = component_id
