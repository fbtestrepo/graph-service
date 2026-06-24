from __future__ import annotations


class AmbiguousWorkloadOwnership(Exception):
    def __init__(self, *, environment: str, workload_asset_id: str):
        super().__init__(
            "Ambiguous workload ownership for workload_asset_id="
            f"{workload_asset_id!r} in environment={environment!r}."
        )
