from __future__ import annotations


class MicroAffinityGroupNotFound(Exception):
    def __init__(self, micro_ag_id: str, environment: str):
        super().__init__(
            f"Micro affinity group not found for micro_ag_id={micro_ag_id!r}, environment={environment!r}"
        )
        self.micro_ag_id = micro_ag_id
        self.environment = environment