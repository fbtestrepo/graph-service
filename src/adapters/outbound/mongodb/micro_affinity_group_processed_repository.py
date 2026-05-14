from __future__ import annotations

from typing import Any

from pymongo.database import Database

from src.core.ports.micro_affinity_group_processed_repository import (
    MicroAffinityGroupProcessedPayload,
    MicroAffinityGroupProcessedRepository,
)


class MongoMicroAffinityGroupProcessedRepository(MicroAffinityGroupProcessedRepository):
    def __init__(self, db: Database):
        self._db = db

    def upsert(
        self,
        micro_ag_id: str,
        environment: str,
        architecture_version: str,
        payload: MicroAffinityGroupProcessedPayload,
        session: Any | None = None,
    ) -> bool:
        result = self._db.get_collection("micro-affinity-groups-processed").replace_one(
            {
                "micro-ag-id": micro_ag_id,
                "environment": environment,
                "architecture-version": architecture_version,
            },
            payload,
            upsert=True,
            session=session,
        )
        return result.upserted_id is not None