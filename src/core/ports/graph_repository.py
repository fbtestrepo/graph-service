from __future__ import annotations

from abc import ABC, abstractmethod

from src.core.domain.component import Component


class GraphRepository(ABC):
    @abstractmethod
    def get_component(self, component_id: str) -> Component | None:
        raise NotImplementedError
