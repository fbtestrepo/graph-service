from __future__ import annotations

from abc import ABC, abstractmethod

from src.core.domain.component_payload_record import ComponentPayloadRecord


class ComponentPayloadRepository(ABC):
    @abstractmethod
    def add(self, record: ComponentPayloadRecord) -> None:
        raise NotImplementedError
