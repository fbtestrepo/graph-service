from __future__ import annotations

from pymongo.database import Database

from src.adapters.outbound.mongodb.collection_names import (
    MICRO_AFFINITY_GROUPS_COLLECTION,
)
from src.core.ports.micro_affinity_group_repository import (
    MicroAffinityGroupPayload,
    MicroAffinityGroupRepository,
)


class MongoMicroAffinityGroupRepository(MicroAffinityGroupRepository):
    def __init__(self, db: Database):
        self._db = db

    def count_by_identity(
        self,
        micro_ag_id: str,
        environment: str,
        session: object | None = None,
    ) -> int:
        return int(
            self._db.get_collection(MICRO_AFFINITY_GROUPS_COLLECTION).count_documents(
                {
                    "micro_ag_id": micro_ag_id,
                    "environment": environment,
                },
                session=session,
            )
        )

    def upsert(
        self,
        micro_ag_id: str,
        environment: str,
        payload: MicroAffinityGroupPayload,
        session: object | None = None,
    ) -> bool:
        result = self._db.get_collection(MICRO_AFFINITY_GROUPS_COLLECTION).replace_one(
            {
                "micro_ag_id": micro_ag_id,
                "environment": environment,
            },
            payload,
            upsert=True,
            session=session,
        )
        return result.upserted_id is not None