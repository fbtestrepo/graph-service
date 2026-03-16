from __future__ import annotations

from dataclasses import dataclass

from src.core.domain.component import Component
from src.core.exceptions.component_not_found import ComponentNotFound
from src.core.ports.graph_repository import GraphRepository


@dataclass(frozen=True, slots=True)
class GetComponent:
    graph_repository: GraphRepository

    def execute(self, component_id: str) -> Component:
        component = self.graph_repository.get_component(component_id)
        if component is None:
            raise ComponentNotFound(component_id)
        return component
