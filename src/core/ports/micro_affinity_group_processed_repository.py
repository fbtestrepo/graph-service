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

    def get_by_identity(
        self,
        micro_ag_id: str,
        environment: str,
        session: Any | None = None,
    ) -> MicroAffinityGroupProcessedPayload | None:
        """Return one processed MAG payload matching a micro_ag_id + environment pair."""

        raise NotImplementedError

    def list_by_workload_asset_ids(
        self,
        asset_ids: list[str],
        environment: str,
        session: Any | None = None,
    ) -> list[MicroAffinityGroupProcessedPayload]:
        """Return processed MAG payloads that own any of the given workload asset ids."""

        raise NotImplementedError

    def list_by_relationship_destination_asset_ids(
        self,
        asset_ids: list[str],
        environment: str,
        session: Any | None = None,
    ) -> list[MicroAffinityGroupProcessedPayload]:
        """Return processed MAG payloads whose relationships target any of the given asset ids."""

        raise NotImplementedError

    def list_relationship_candidates_for_workload_test_scope(
        self,
        changed_asset_ids: list[str],
        environment: str,
        session: Any | None = None,
    ) -> list[dict[str, str]]:
        """Return relationship rows touching any changed workload asset id in one environment.

        Each row contains:
        - source_workload_asset_id
        - destination_workload_asset_id
        - source_micro_ag_id
        """

        raise NotImplementedError

    def list_workload_ownership_for_asset_ids(
        self,
        asset_ids: list[str],
        environment: str,
        session: Any | None = None,
    ) -> list[dict[str, str]]:
        """Return workload ownership rows for asset ids in one environment.

        Each row contains:
        - workload_asset_id
        - micro_ag_id
        """

        raise NotImplementedError