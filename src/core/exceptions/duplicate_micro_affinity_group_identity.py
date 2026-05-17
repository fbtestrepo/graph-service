from __future__ import annotations


class DuplicateMicroAffinityGroupIdentity(Exception):
    def __init__(self, micro_ag_id: str, environment: str):
        super().__init__(
            f"Duplicate micro affinity group identity: {micro_ag_id} in environment {environment}"
        )
        self.micro_ag_id = micro_ag_id
        self.environment = environment