from __future__ import annotations

from pymongo.database import Database

from src.core.domain.component_payload_record import ComponentPayloadRecord
from src.core.ports.component_payload_repository import ComponentPayloadRepository


class MongoComponentPayloadRepository(ComponentPayloadRepository):
    def __init__(self, db: Database):
        self._db = db

    def add(self, record: ComponentPayloadRecord) -> None:
        self._db.get_collection("component_payload_records").insert_one(
            {"received_at": record.received_at, "payload": record.payload}
        )
