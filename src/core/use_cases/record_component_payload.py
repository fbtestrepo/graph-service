from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from src.core.domain.component_payload_record import ComponentPayloadRecord
from src.core.ports.component_payload_repository import ComponentPayloadRepository


@dataclass(frozen=True, slots=True)
class RecordComponentPayload:
    component_payload_repository: ComponentPayloadRepository

    def execute(self, payload: Any) -> Any:
        record = ComponentPayloadRecord(received_at=datetime.now(timezone.utc), payload=payload)
        self.component_payload_repository.add(record)
        return payload
