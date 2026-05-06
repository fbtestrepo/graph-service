from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


ApplicationArchitecturePayload = dict[str, Any]


class ApplicationArchitectureRepository(ABC):
    @abstractmethod
    def upsert(self, asset_id: str, version: str, payload: ApplicationArchitecturePayload) -> bool:
        """Upsert an application architecture payload by AssetID + version.

        Returns True if the payload was created (inserted), False if it updated an existing
        document.
        """

        raise NotImplementedError

    @abstractmethod
    def get_by_asset_id_and_version(
        self,
        asset_id: str,
        version: str,
    ) -> ApplicationArchitecturePayload | None:
        """Return one application architecture payload by AssetID + version."""

        raise NotImplementedError
