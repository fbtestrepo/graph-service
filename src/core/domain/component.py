from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Component:
    component_id: str
    name: str
    version: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
