from __future__ import annotations

from dataclasses import dataclass, field

from src.core.domain.component import Component
from src.core.domain.dependency_edge import DependencyEdge


@dataclass(frozen=True, slots=True)
class DependencyGraph:
    components: list[Component] = field(default_factory=list)
    edges: list[DependencyEdge] = field(default_factory=list)
