from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.exceptions.application_architecture_not_found import (
    ApplicationArchitectureNotFound,
)
from src.core.domain.micro_affinity_group_relationship_mapper import (
    MicroAffinityGroupRelationshipMapper,
)
from src.core.ports.application_architecture_repository import ApplicationArchitectureRepository
from src.core.ports.micro_affinity_group_repository import MicroAffinityGroupRepository
from src.core.ports.micro_affinity_group_processed_repository import (
    MicroAffinityGroupProcessedRepository,
)
from src.core.ports.transaction_manager import TransactionManager


@dataclass(frozen=True, slots=True)
class UpsertMicroAffinityGroupResult:
    created: bool
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class UpsertMicroAffinityGroup:
    application_architecture_repository: ApplicationArchitectureRepository
    micro_affinity_group_repository: MicroAffinityGroupRepository
    micro_affinity_group_processed_repository: MicroAffinityGroupProcessedRepository
    transaction_manager: TransactionManager
    relationship_mapper: MicroAffinityGroupRelationshipMapper

    def execute(self, payload: dict[str, Any]) -> UpsertMicroAffinityGroupResult:
        asset_id = str(payload["parent_asset_id"])
        architecture_version = str(payload["architecture_version"])
        environment = str(payload["environment"])
        micro_ag_id = str(payload["micro_ag_id"])

        def _operation(session: object) -> UpsertMicroAffinityGroupResult:
            self.micro_affinity_group_repository.upsert(
                micro_ag_id=micro_ag_id,
                environment=environment,
                architecture_version=architecture_version,
                payload=payload,
                session=session,
            )

            architecture = self.application_architecture_repository.get_by_asset_id_and_version(
                asset_id=asset_id,
                version=architecture_version,
                session=session,
            )
            if architecture is None:
                raise ApplicationArchitectureNotFound(asset_id=asset_id, version=architecture_version)

            processed_payload = self.relationship_mapper.transform(payload, architecture)
            created = self.micro_affinity_group_processed_repository.upsert(
                micro_ag_id=micro_ag_id,
                environment=environment,
                architecture_version=architecture_version,
                payload=processed_payload,
                session=session,
            )
            return UpsertMicroAffinityGroupResult(created=created, payload=processed_payload)

        return self.transaction_manager.execute(_operation)