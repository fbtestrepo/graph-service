from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


MicroAffinityGroupProcessedPayload = dict[str, Any]


class MicroAffinityGroupProcessedRepository(ABC):
    @abstractmethod
    def upsert(
        self,
        micro_ag_id: str,
        environment: str,
        architecture_version: str,
        payload: MicroAffinityGroupProcessedPayload,
        session: Any | None = None,
    ) -> bool:
        """Upsert a processed micro affinity group payload by micro-ag-id + environment + version.

        Returns True if the payload was created (inserted), False if it updated/replaced an
        existing document.
        """

        raise NotImplementedError