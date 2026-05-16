from __future__ import annotations

from pymongo.database import Database

from src.adapters.outbound.mongodb.collection_names import (
    APPLICATION_ARCHITECTURES_COLLECTION,
)
from src.core.ports.application_architecture_repository import (
    ApplicationArchitecturePayload,
    ApplicationArchitectureRepository,
)


class MongoApplicationArchitectureRepository(ApplicationArchitectureRepository):
    def __init__(self, db: Database):
        self._db = db

    def upsert(
        self,
        asset_id: str,
        version: str,
        payload: ApplicationArchitecturePayload,
        session: object | None = None,
    ) -> bool:
        collection = self._db.get_collection(APPLICATION_ARCHITECTURES_COLLECTION)
        document_filter = {"metadata.AssetID": asset_id, "metadata.version": version}

        existing = collection.find_one(
            document_filter,
            projection={"_id": False},
            session=session,
        ) or {}
        unset_fields = {field_name: "" for field_name in existing.keys() - payload.keys()}

        update_document: dict[str, object] = {"$set": payload}
        if unset_fields:
            update_document["$unset"] = unset_fields

        result = collection.update_one(
            document_filter,
            update_document,
            upsert=True,
            session=session,
        )
        return result.upserted_id is not None

    def get_by_asset_id_and_version(
        self,
        asset_id: str,
        version: str,
        session: object | None = None,
    ) -> ApplicationArchitecturePayload | None:
        document = self._db.get_collection(APPLICATION_ARCHITECTURES_COLLECTION).find_one(
            {"metadata.AssetID": asset_id, "metadata.version": version},
            session=session,
        )
        if document is None:
            return None

        document.pop("_id", None)
        return document
