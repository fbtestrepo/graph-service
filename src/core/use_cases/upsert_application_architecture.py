from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.ports.application_architecture_repository import ApplicationArchitectureRepository


@dataclass(frozen=True, slots=True)
class UpsertApplicationArchitectureResult:
    created: bool


@dataclass(frozen=True, slots=True)
class UpsertApplicationArchitecture:
    application_architecture_repository: ApplicationArchitectureRepository

    def execute(self, payload: dict[str, Any]) -> UpsertApplicationArchitectureResult:
        metadata = payload["metadata"]
        asset_id = str(metadata["AssetID"])
        version = str(metadata["version"])
        created = self.application_architecture_repository.upsert(
            asset_id=asset_id,
            version=version,
            payload=payload,
        )
        return UpsertApplicationArchitectureResult(created=created)
