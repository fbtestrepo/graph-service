from __future__ import annotations

from pymongo.database import Database

from src.core.ports.micro_affinity_group_repository import (
    MicroAffinityGroupPayload,
    MicroAffinityGroupRepository,
)


class MongoMicroAffinityGroupRepository(MicroAffinityGroupRepository):
    def __init__(self, db: Database):
        self._db = db

    def upsert(
        self,
        micro_ag_id: str,
        environment: str,
        architecture_version: str,
        payload: MicroAffinityGroupPayload,
    ) -> bool:
        result = self._db.get_collection("micro-affinity-groups").replace_one(
            {
                "micro-ag-id": micro_ag_id,
                "environment": environment,
                "architecture-version": architecture_version,
            },
            payload,
            upsert=True,
        )
        return result.upserted_id is not None