from __future__ import annotations

from typing import Any

from pymongo.database import Database

from src.adapters.outbound.mongodb.collection_names import (
    MICRO_AFFINITY_GROUPS_PROCESSED_COLLECTION,
)
from src.core.ports.micro_affinity_group_processed_repository import (
    MicroAffinityGroupProcessedPayload,
    MicroAffinityGroupProcessedRepository,
)


class MongoMicroAffinityGroupProcessedRepository(MicroAffinityGroupProcessedRepository):
    def __init__(self, db: Database):
        self._db = db

    @property
    def _collection(self):
        return self._db.get_collection(MICRO_AFFINITY_GROUPS_PROCESSED_COLLECTION)

    def count_by_identity(
        self,
        micro_ag_id: str,
        environment: str,
        session: Any | None = None,
    ) -> int:
        return int(
            self._collection.count_documents(
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
        payload: MicroAffinityGroupProcessedPayload,
        session: Any | None = None,
    ) -> bool:
        result = self._collection.replace_one(
            {
                "micro_ag_id": micro_ag_id,
                "environment": environment,
            },
            payload,
            upsert=True,
            session=session,
        )
        return result.upserted_id is not None

    def get_by_identity(
        self,
        micro_ag_id: str,
        environment: str,
        session: Any | None = None,
    ) -> MicroAffinityGroupProcessedPayload | None:
        return self._collection.find_one(
            {
                "micro_ag_id": micro_ag_id,
                "environment": environment,
            },
            projection={"_id": False},
            session=session,
        )

    def list_by_workload_asset_ids(
        self,
        asset_ids: list[str],
        environment: str,
        session: Any | None = None,
    ) -> list[MicroAffinityGroupProcessedPayload]:
        if not asset_ids:
            return []

        return list(
            self._collection.find(
                {
                    "environment": environment,
                    "workloads.asset_id": {"$in": asset_ids},
                },
                projection={"_id": False},
                session=session,
            )
        )

    def list_by_relationship_destination_asset_ids(
        self,
        asset_ids: list[str],
        environment: str,
        session: Any | None = None,
    ) -> list[MicroAffinityGroupProcessedPayload]:
        if not asset_ids:
            return []

        return list(
            self._collection.find(
                {
                    "environment": environment,
                    "relationships.destination_workload.asset_id": {"$in": asset_ids},
                },
                projection={"_id": False},
                session=session,
            )
        )