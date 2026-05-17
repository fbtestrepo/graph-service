from __future__ import annotations

from typing import Any

import pytest

from src.core.domain.micro_affinity_group_relationship_mapper import (
    MicroAffinityGroupRelationshipMapper,
)
from src.core.exceptions.micro_affinity_group_relationship_resolution_error import (
    MicroAffinityGroupRelationshipResolutionError,
)


def _payload() -> dict[str, Any]:
    return {
        "micro_ag_id": "mAG_A",
        "name": "Micro Affinity Group A",
        "parent_asset_id": "ba0270",
        "architecture_version": "1.0.0",
        "environment": "production",
        "effective_date": "2025-01-01T14:00:00Z",
        "workloads": [
            {
                "id": "AIMC/repos/rw-orchestrator-svc_ba0116_pq0177",
                "asset_id": "pq0177",
            }
        ],
    }


def _architecture(*, dangling_destination: bool = False) -> dict[str, Any]:
    destination_node = "node-external" if not dangling_destination else "node-missing"
    return {
        "metadata": {
            "AssetID": "ba0270",
            "version": "1.0.0",
            "created": "2026-05-05",
        },
        "nodes": [
            {
                "unique-id": "node-source",
                "node-type": "service",
                "name": "RW Orchestrator",
                "metadata": {
                    "code-repo": "AIMC/repos/rw-orchestrator-svc_ba0116_pq0177",
                    "asset-id": "pq0177",
                },
            },
            {
                "unique-id": "node-external",
                "node-type": "service",
                "name": "RW CAP Service",
                "metadata": {
                    "code-repo": "AIMC/repos/rw-cap-svc_ba0116_dh6980",
                    "asset-id": "dh6980",
                },
            },
        ],
        "relationships": [
            {
                "relationship-type": {
                    "connects": {
                        "source": {"node": "node-source"},
                        "destination": {"node": destination_node},
                    }
                }
            }
        ],
    }


def test_relationship_mapper_builds_relationships_for_destinations_outside_submission() -> None:
    mapper = MicroAffinityGroupRelationshipMapper()

    result = mapper.transform(_payload(), _architecture())

    assert result["workloads"] == _payload()["workloads"]
    assert result["relationships"] == [
        {
            "source_workload": {
                "id": "AIMC/repos/rw-orchestrator-svc_ba0116_pq0177",
                "asset_id": "pq0177",
            },
            "destination_workload": {
                "id": "AIMC/repos/rw-cap-svc_ba0116_dh6980",
                "asset_id": "dh6980",
            },
        }
    ]


def test_relationship_mapper_raises_for_unresolved_destination_service() -> None:
    mapper = MicroAffinityGroupRelationshipMapper()

    with pytest.raises(MicroAffinityGroupRelationshipResolutionError):
        mapper.transform(_payload(), _architecture(dangling_destination=True))