from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class DependencyEdge:
    from_component_id: str
    to_component_id: str
    edge_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
