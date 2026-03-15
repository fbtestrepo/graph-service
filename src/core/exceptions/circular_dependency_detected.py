from __future__ import annotations


class CircularDependencyDetected(Exception):
    def __init__(self, path: list[str] | None = None):
        super().__init__("Circular dependency detected")
        self.path = path or []
