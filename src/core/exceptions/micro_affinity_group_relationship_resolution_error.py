from __future__ import annotations


class MicroAffinityGroupRelationshipResolutionError(Exception):
    def __init__(self, detail: str):
        super().__init__(detail)