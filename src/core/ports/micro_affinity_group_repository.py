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
        session: Any | None = None,
    ) -> bool:
        """Upsert a micro affinity group payload by micro_ag_id + environment + version.

        Returns True if the payload was created (inserted), False if it updated/replaced an
        existing document.
        """

        raise NotImplementedError