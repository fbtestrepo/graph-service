from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


MicroAffinityGroupPayload = dict[str, Any]


class MicroAffinityGroupRepository(ABC):
    @abstractmethod
    def upsert(
        self,
        micro_ag_id: str,
        environment: str,
        architecture_version: str,
        payload: MicroAffinityGroupPayload,
    ) -> bool:
        """Upsert a micro affinity group payload by micro-ag-id + environment + version.

        Returns True if the payload was created (inserted), False if it updated/replaced an
        existing document.
        """

        raise NotImplementedError