from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


MicroAffinityGroupProcessedPayload = dict[str, Any]


class MicroAffinityGroupProcessedRepository(ABC):
    @abstractmethod
    def count_by_identity(
        self,
        micro_ag_id: str,
        environment: str,
        session: Any | None = None,
    ) -> int:
        """Return the number of stored processed payloads matching one MAG write identity pair."""

        raise NotImplementedError

    @abstractmethod
    def upsert(
        self,
        micro_ag_id: str,
        environment: str,
        payload: MicroAffinityGroupProcessedPayload,
        session: Any | None = None,
    ) -> bool:
        """Upsert a processed micro affinity group payload by micro_ag_id + environment.

        Returns True if the payload was created (inserted), False if it updated/replaced an
        existing document.
        """

        raise NotImplementedError