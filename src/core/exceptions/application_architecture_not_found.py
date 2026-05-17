from __future__ import annotations


class ApplicationArchitectureNotFound(Exception):
    def __init__(self, asset_id: str, version: str):
        super().__init__(
            f"Application architecture not found for parent_asset_id '{asset_id}' and architecture_version '{version}'."
        )
        self.asset_id = asset_id
        self.version = version