from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.exceptions.application_architecture_not_found import (
    ApplicationArchitectureNotFound,
)
from src.core.domain.micro_affinity_group_relationship_mapper import (
    MicroAffinityGroupRelationshipMapper,
)
from src.core.exceptions.duplicate_micro_affinity_group_identity import (
    DuplicateMicroAffinityGroupIdentity,
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
            raw_count = self.micro_affinity_group_repository.count_by_identity(
                micro_ag_id=micro_ag_id,
                environment=environment,
                session=session,
            )
            processed_count = self.micro_affinity_group_processed_repository.count_by_identity(
                micro_ag_id=micro_ag_id,
                environment=environment,
                session=session,
            )

            if raw_count > 1 or processed_count > 1:
                raise DuplicateMicroAffinityGroupIdentity(
                    micro_ag_id=micro_ag_id,
                    environment=environment,
                )

            self.micro_affinity_group_repository.upsert(
                micro_ag_id=micro_ag_id,
                environment=environment,
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
            self.micro_affinity_group_processed_repository.upsert(
                micro_ag_id=micro_ag_id,
                environment=environment,
                payload=processed_payload,
                session=session,
            )
            created = raw_count == 0 and processed_count == 0
            return UpsertMicroAffinityGroupResult(created=created, payload=processed_payload)

        return self.transaction_manager.execute(_operation)